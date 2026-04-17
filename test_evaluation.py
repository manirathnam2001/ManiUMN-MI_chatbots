"""Standalone smoke test for mi_evaluation.py.

Run with::

    python3 test_evaluation.py

Prints a summary and exits 0 iff all tests pass.

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
# Sample valid LLM outputs
# ---------------------------------------------------------------------------


# A "clean" evidence payload: every quote matches the default transcript below,
# closing summary present, no belittling. Use this when the test's focus is on
# the scoring pass.
DEFAULT_TRANSCRIPT = (
    "Student: Hi, I'm here to talk with you about your oral health.\n"
    "Patient: Hello.\n"
    "Student: Would it be okay if I shared some info?\n"
    "Patient: Sure.\n"
    "Student: What feels most important to you?\n"
    "Patient: Cleaning better.\n"
    "Student: So to recap, you'd like to start with flossing. Does that sound right?\n"
    "Patient: Yes.\n"
)


def _evidence_payload(
    *,
    has_closing_summary: bool = True,
    belittling_instances: List[str] | None = None,
    per_category_overrides: dict | None = None,
    notes: str = "",
) -> str:
    """Build a valid extractor JSON response.

    All quotes below are verbatim substrings of DEFAULT_TRANSCRIPT so they
    survive _verify_quotes. Tests that use a different transcript should
    override per_category_overrides / belittling_instances with quotes from
    that transcript (or empty arrays).
    """
    per_cat = {
        "Collaboration": ["Hi, I'm here to talk with you about your oral health."],
        "Acceptance": ["Would it be okay if I shared some info?"],
        "Compassion": [],
        "Evocation": ["What feels most important to you?"],
        "Summary": ["So to recap, you'd like to start with flossing. Does that sound right?"],
        "Response Factor": [],
    }
    if per_category_overrides:
        per_cat.update(per_category_overrides)
    payload = {
        "per_category": per_cat,
        "has_closing_summary": has_closing_summary,
        "belittling_instances": belittling_instances or [],
        "notes": notes,
    }
    return json.dumps(payload)


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
    client = FakeClient([_evidence_payload(), _good_payload()])
    result = me.evaluate_session(
        transcript=DEFAULT_TRANSCRIPT,
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
    # Two LLM calls: extractor + scorer.
    assert len(client.chat.completions.calls) == 2


def test_summary_not_met_enforced() -> None:
    """Rule 4 legacy path: extractor says summary present but rationale signals otherwise."""
    # Evidence says summary IS present — we want to exercise the legacy keyword
    # net so Compassion/Acceptance paths are unaffected.
    client = FakeClient([
        _evidence_payload(has_closing_summary=True),
        _good_payload(
            summary_level="Fully Met",
            summary_rationale="The student did not summarize at all; the conversation just ended.",
        ),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["categories"]["Summary"]["assessment"] == "Not Met", (
        f"expected Summary=Not Met, got {result['categories']['Summary']['assessment']}"
    )
    assert result["categories"]["Summary"]["points"] == 0.0


def test_belittling_caps_compassion_and_acceptance() -> None:
    """Rule 5 legacy path: extractor flags nothing, rationale contains belittling keywords."""
    client = FakeClient([
        _evidence_payload(belittling_instances=[]),  # no flag from extractor
        _good_payload(
            compassion_level="Fully Met",
            acceptance_level="Fully Met",
            compassion_rationale=(
                "Although the student asked some good questions, they were "
                "dismissive of the patient's concern and used lecturing language."
            ),
        ),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
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
    client = FakeClient([_evidence_payload(), bad, _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    # extractor + bad scorer + retry scorer = 3 calls.
    assert len(client.chat.completions.calls) == 3, (
        f"expected 3 LLM calls (extractor + scorer + retry), got {len(client.chat.completions.calls)}"
    )


def test_malformed_json_triggers_retry() -> None:
    client = FakeClient([_evidence_payload(), "this is not json at all", _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 3


def test_two_failures_returns_partial_no_exception() -> None:
    # Extractor succeeds; scorer fails twice => partial.
    client = FakeClient([_evidence_payload(), "not json", "still not json"])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is True
    assert "Manual review required" in result["performance_band"]
    assert result["notes"], "partial result must include explanatory notes"
    assert "RAW EVALUATOR RESPONSE" in result["notes"]


def test_network_failure_raises_evaluation_error() -> None:
    # RuntimeError fires on the extractor (first) call.
    client = FakeClient([RuntimeError("connection refused")])
    try:
        me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
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
    client = FakeClient([
        _evidence_payload(has_closing_summary=False),  # consistent with scorer
        json.dumps(payload_dict),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    joined = " | ".join(result["recommendations"]).lower()
    assert "summary" in joined, (
        f"expected 'Summary' to appear in recommendations, got: {result['recommendations']}"
    )


# ---------------------------------------------------------------------------
# New tests for the 2-call architecture
# ---------------------------------------------------------------------------


def test_two_call_happy_path_makes_two_calls() -> None:
    client = FakeClient([_evidence_payload(), _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 2
    # First call goes to the extractor model by default.
    assert client.chat.completions.calls[0]["model"] == "llama-3.1-8b-instant"
    # Second call goes to the scoring model.
    assert client.chat.completions.calls[1]["model"] == "llama-3.3-70b-versatile"


def test_extractor_failure_falls_back_to_single_call() -> None:
    """Both extractor attempts fail => evidence=None, scorer uses legacy prompt."""
    client = FakeClient([
        "not json from extractor",
        "still not json from extractor",
        _good_payload(),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    # 2 extractor + 1 scorer = 3 calls, no extra scorer retry needed.
    assert len(client.chat.completions.calls) == 3
    # The 3rd call (scorer) should have used the legacy prompt — we can check
    # for the hallmark "Remember rules 4 (Summary) and 5 (belittling)" string.
    scorer_call = client.chat.completions.calls[2]
    user_content = scorer_call["messages"][-1]["content"]
    assert "rules 4" in user_content.lower() or "belittling" in user_content.lower()


def test_hallucinated_quote_is_dropped() -> None:
    """Quotes in extractor output not in the transcript are filtered."""
    bad_evidence = json.dumps({
        "per_category": {
            "Collaboration": ["This quote is not in the transcript at all."],
            "Acceptance":    [],
            "Compassion":    [],
            "Evocation":     [],
            "Summary":       [],
            "Response Factor": [],
        },
        "has_closing_summary": True,
        "belittling_instances": ["Another fake quote that is not present."],
        "notes": "",
    })
    client = FakeClient([bad_evidence, _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    # The scorer call's user prompt should NOT contain the hallucinated quote.
    scorer_call = client.chat.completions.calls[1]
    user_content = scorer_call["messages"][-1]["content"]
    assert "This quote is not in the transcript at all." not in user_content
    assert "Another fake quote that is not present." not in user_content
    # And because belittling_instances ends up empty after verification, the
    # belittling cap should NOT fire from evidence.
    assert result["categories"]["Compassion"]["assessment"] == "Fully Met"


def test_evidence_flag_forces_summary_not_met() -> None:
    """has_closing_summary=False => Summary forced to Not Met even if scorer said Fully Met."""
    client = FakeClient([
        _evidence_payload(has_closing_summary=False),
        _good_payload(summary_level="Fully Met", summary_rationale="Student summarized everything."),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["categories"]["Summary"]["assessment"] == "Not Met"
    assert result["categories"]["Summary"]["points"] == 0.0
    assert "extractor flagged" in result["categories"]["Summary"]["rationale"]


def test_evidence_flag_caps_compassion_and_acceptance() -> None:
    """belittling_instances non-empty => hard caps on Compassion + Acceptance."""
    client = FakeClient([
        _evidence_payload(belittling_instances=["Would it be okay if I shared some info?"]),
        _good_payload(
            compassion_level="Fully Met",
            acceptance_level="Fully Met",
            compassion_rationale="Student was warm and supportive.",  # no keyword triggers
        ),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["categories"]["Compassion"]["assessment"] == "Minimally Met"
    assert result["categories"]["Acceptance"]["assessment"] == "Partially Met"
    assert "extractor flagged" in result["categories"]["Compassion"]["rationale"]


def test_extractor_schema_violation_retries() -> None:
    """Missing key in extractor output triggers retry, then succeeds."""
    bad = json.dumps({
        "per_category": {c: [] for c in me.REQUIRED_CATEGORIES},
        # missing has_closing_summary + belittling_instances
    })
    client = FakeClient([bad, _evidence_payload(), _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    # bad extractor + retry extractor + scorer = 3 calls.
    assert len(client.chat.completions.calls) == 3


def test_partial_result_when_scorer_fails_twice() -> None:
    """Scorer double-failure still returns partial=True even when evidence succeeded."""
    client = FakeClient([_evidence_payload(), "not json", "still not json"])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is True
    assert "Manual review required" in result["performance_band"]


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
    test_two_call_happy_path_makes_two_calls,
    test_extractor_failure_falls_back_to_single_call,
    test_hallucinated_quote_is_dropped,
    test_evidence_flag_forces_summary_not_met,
    test_evidence_flag_caps_compassion_and_acceptance,
    test_extractor_schema_violation_retries,
    test_partial_result_when_scorer_fails_twice,
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
