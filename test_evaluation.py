"""Standalone smoke test for mi_evaluation.py.

Run with::

    python3 test_evaluation.py

Prints a summary and exits 0 iff all 8 cases pass.

These tests do NOT require pytest, the Groq SDK, or network access. They use a
small in-process fake client. The pytest equivalents under
``tests/test_mi_evaluation.py`` exercise the same scenarios.
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any, Callable, List

import mi_evaluation as me


# ---------------------------------------------------------------------------
# Fake Groq client
# ---------------------------------------------------------------------------


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class FakeCompletions:
    def __init__(self, scripted: List[Any]) -> None:
        # scripted is a list of either str (response content) or Exception
        # (raised on that call).
        self.scripted = list(scripted)
        self.calls: List[dict] = []

    def create(self, *, model, messages, **kwargs):
        self.calls.append({"model": model, "messages": messages, **kwargs})
        if not self.scripted:
            raise AssertionError("FakeCompletions: no more scripted responses")
        head = self.scripted.pop(0)
        if isinstance(head, Exception):
            raise head
        return _FakeResponse(head)


class FakeChat:
    def __init__(self, scripted: List[Any]) -> None:
        self.completions = FakeCompletions(scripted)


class FakeClient:
    def __init__(self, scripted: List[Any]) -> None:
        self.chat = FakeChat(scripted)


# ---------------------------------------------------------------------------
# Sample valid evaluator output
# ---------------------------------------------------------------------------


def _good_payload(
    *,
    summary_level: str = "Fully Met",
    compassion_level: str = "Fully Met",
    acceptance_level: str = "Fully Met",
    summary_rationale: str = "Student summarized big picture and confirmed next steps.",
    compassion_rationale: str = "Student showed empathy throughout.",
    extra_rec: str = "",
) -> str:
    payload = {
        "categories": {
            "Collaboration": {"level": "Fully Met", "rationale": "Strong intro and partnership.", "evidence_quote": "Let's figure this out together."},
            "Acceptance": {"level": acceptance_level, "rationale": "Asked permission and reflected.", "evidence_quote": "Would it be okay if I shared some info?"},
            "Compassion": {"level": compassion_level, "rationale": compassion_rationale, "evidence_quote": "I can see this has been hard for you."},
            "Evocation": {"level": "Fully Met", "rationale": "Open-ended questions, supported autonomy.", "evidence_quote": "What feels most important to you?"},
            "Summary": {"level": summary_level, "rationale": summary_rationale, "evidence_quote": "So to recap, you'd like to start with..."},
            "Response Factor": {"level": "Fully Met", "rationale": "Responses were timely.", "evidence_quote": ""},
        },
        "recommendations": ["Keep using open-ended questions in future sessions." + (" " + extra_rec if extra_rec else "")],
    }
    return json.dumps(payload)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_happy_path() -> None:
    client = FakeClient([_good_payload()])
    result = me.evaluate_session(
        transcript="User: Hi.\nAssistant: Hello.",
        session_type="OHI",
        student_name="Test Student",
        client=client,
    )
    assert result["partial"] is False, "happy path should not be partial"
    assert result["max_possible_score"] == 40
    # All Fully Met = full marks: 9+6+6+6+3+10 = 40
    assert abs(result["total_score"] - 40.0) < 1e-6, f"expected 40, got {result['total_score']}"
    assert abs(result["percentage"] - 100.0) < 1e-6
    assert result["performance_band"], "performance band must be set"
    for cat in me.REQUIRED_CATEGORIES:
        assert cat in result["categories"]


def test_summary_not_met_enforced() -> None:
    """Rule 4: rationale signals no summary => Summary downgraded to Not Met."""
    client = FakeClient([_good_payload(
        summary_level="Fully Met",
        summary_rationale="The student did not summarize at all; the conversation just ended.",
    )])
    result = me.evaluate_session("transcript", "OHI", "S", client=client)
    assert result["categories"]["Summary"]["assessment"] == "Not Met", (
        f"expected Summary=Not Met, got {result['categories']['Summary']['assessment']}"
    )
    assert result["categories"]["Summary"]["points"] == 0.0


def test_belittling_caps_compassion_and_acceptance() -> None:
    """Rule 5: rationale signals belittling => Compassion <= Minimally Met, Acceptance <= Partially Met."""
    client = FakeClient([_good_payload(
        compassion_level="Fully Met",
        acceptance_level="Fully Met",
        compassion_rationale=(
            "Although the student asked some good questions, they were "
            "dismissive of the patient's concern and used lecturing language."
        ),
    )])
    result = me.evaluate_session("transcript", "OHI", "S", client=client)
    comp_level = result["categories"]["Compassion"]["assessment"]
    acc_level = result["categories"]["Acceptance"]["assessment"]
    assert comp_level == "Minimally Met", f"expected Compassion=Minimally Met, got {comp_level}"
    assert acc_level == "Partially Met", f"expected Acceptance=Partially Met, got {acc_level}"


def test_invalid_level_triggers_retry() -> None:
    """Schema check rejects bad level; retry succeeds."""
    bad = json.dumps({
        "categories": {c: {"level": "Sometimes Met", "rationale": "x", "evidence_quote": ""} for c in me.REQUIRED_CATEGORIES},
        "recommendations": ["fix it"],
    })
    client = FakeClient([bad, _good_payload()])
    result = me.evaluate_session("transcript", "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 2, (
        f"expected exactly 2 LLM calls (initial + retry), got {len(client.chat.completions.calls)}"
    )


def test_malformed_json_triggers_retry() -> None:
    client = FakeClient(["this is not json at all", _good_payload()])
    result = me.evaluate_session("transcript", "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 2


def test_two_failures_returns_partial_no_exception() -> None:
    client = FakeClient(["not json", "still not json"])
    result = me.evaluate_session("transcript", "OHI", "S", client=client)
    assert result["partial"] is True
    assert "Manual review required" in result["performance_band"]
    assert result["notes"], "partial result must include explanatory notes"
    assert "RAW EVALUATOR RESPONSE" in result["notes"]


def test_network_failure_raises_evaluation_error() -> None:
    client = FakeClient([RuntimeError("connection refused")])
    try:
        me.evaluate_session("transcript", "OHI", "S", client=client)
    except me.EvaluationError as exc:
        assert exc.phase == "llm_call", f"expected phase=llm_call, got phase={exc.phase}"
        return
    raise AssertionError("expected EvaluationError, none raised")


def test_recommendations_include_lowest_category() -> None:
    """If the LLM omits the lowest-scored category from recommendations, we inject it."""
    payload_dict = {
        "categories": {
            "Collaboration": {"level": "Fully Met", "rationale": "Good intro.", "evidence_quote": "Hi."},
            "Acceptance":    {"level": "Fully Met", "rationale": "Asked permission.", "evidence_quote": "May I share?"},
            "Compassion":    {"level": "Fully Met", "rationale": "Empathetic.", "evidence_quote": "I understand."},
            "Evocation":     {"level": "Fully Met", "rationale": "Open questions.", "evidence_quote": "What matters?"},
            "Summary":       {"level": "Not Met",   "rationale": "No closing summary at all.", "evidence_quote": ""},
            "Response Factor": {"level": "Fully Met", "rationale": "On time.", "evidence_quote": ""},
        },
        # Note: recommendations omit "Summary" entirely.
        "recommendations": ["Continue using open-ended questions."],
    }
    client = FakeClient([json.dumps(payload_dict)])
    result = me.evaluate_session("transcript", "OHI", "S", client=client)
    joined = " | ".join(result["recommendations"]).lower()
    assert "summary" in joined, (
        f"expected 'Summary' to appear in recommendations, got: {result['recommendations']}"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


_TESTS: List[Callable[[], None]] = [
    test_happy_path,
    test_summary_not_met_enforced,
    test_belittling_caps_compassion_and_acceptance,
    test_invalid_level_triggers_retry,
    test_malformed_json_triggers_retry,
    test_two_failures_returns_partial_no_exception,
    test_network_failure_raises_evaluation_error,
    test_recommendations_include_lowest_category,
]


def main() -> int:
    failures = 0
    for test in _TESTS:
        name = test.__name__
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {name}: {exc}")
            traceback.print_exc()
        except Exception as exc:  # pragma: no cover — surfaces unexpected errors
            failures += 1
            print(f"ERROR {name}: {exc}")
            traceback.print_exc()
        else:
            print(f"PASS  {name}")
    total = len(_TESTS)
    passed = total - failures
    print(f"\n{passed}/{total} tests passed.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
