"""Pytest equivalent of the standalone test_evaluation.py at the repo root.

These tests share the same scenarios. They reuse the FakeClient helper from
the root-level smoke test so we have a single source of truth for the fake
Groq client. This file is what runs in CI; the root file is for the
``python3 test_evaluation.py`` workflow documented in the plan.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the repo root importable regardless of how pytest was invoked.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest  # noqa: E402

import mi_evaluation as me  # noqa: E402
from test_evaluation import (  # noqa: E402
    DEFAULT_TRANSCRIPT,
    FakeClient,
    _evidence_payload,
    _good_payload,
)


def test_happy_path() -> None:
    client = FakeClient([_evidence_payload(), _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    assert result["max_possible_score"] == 40
    assert result["total_score"] == pytest.approx(40.0)
    assert result["percentage"] == pytest.approx(100.0)
    for cat in me.REQUIRED_CATEGORIES:
        assert cat in result["categories"]
    assert len(client.chat.completions.calls) == 2


def test_summary_not_met_enforced_legacy_keyword() -> None:
    client = FakeClient([
        _evidence_payload(has_closing_summary=True),
        _good_payload(
            summary_level="Fully Met",
            summary_rationale="The student did not summarize at all; the conversation just ended.",
        ),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["categories"]["Summary"]["assessment"] == "Not Met"
    assert result["categories"]["Summary"]["points"] == pytest.approx(0.0)


def test_belittling_caps_compassion_and_acceptance_legacy_keyword() -> None:
    client = FakeClient([
        _evidence_payload(belittling_instances=[]),
        _good_payload(
            compassion_level="Fully Met",
            acceptance_level="Fully Met",
            compassion_rationale=(
                "Student asked questions but was dismissive of patient concern and used lecturing language."
            ),
        ),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["categories"]["Compassion"]["assessment"] == "Minimally Met"
    assert result["categories"]["Acceptance"]["assessment"] == "Partially Met"


def test_invalid_level_triggers_retry() -> None:
    bad = json.dumps({
        "categories": {c: {"level": "Sometimes Met", "rationale": "x", "evidence_quote": ""} for c in me.REQUIRED_CATEGORIES},
        "recommendations": ["fix it"],
    })
    client = FakeClient([_evidence_payload(), bad, _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 3


def test_malformed_json_triggers_retry() -> None:
    client = FakeClient([_evidence_payload(), "not json", _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 3


def test_two_failures_returns_partial_no_exception() -> None:
    client = FakeClient([_evidence_payload(), "not json", "still not json"])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is True
    assert "Manual review required" in result["performance_band"]
    assert result["notes"]
    assert "RAW EVALUATOR RESPONSE" in result["notes"]


def test_network_failure_raises_evaluation_error() -> None:
    client = FakeClient([RuntimeError("connection refused")])
    with pytest.raises(me.EvaluationError) as info:
        me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert info.value.phase == "llm_call"


def test_recommendations_include_lowest_category() -> None:
    payload = {
        "categories": {
            "Collaboration": {"level": "Fully Met", "rationale": "Good.", "evidence_quote": ""},
            "Acceptance":    {"level": "Fully Met", "rationale": "Good.", "evidence_quote": ""},
            "Compassion":    {"level": "Fully Met", "rationale": "Good.", "evidence_quote": ""},
            "Evocation":     {"level": "Fully Met", "rationale": "Good.", "evidence_quote": ""},
            "Summary":       {"level": "Not Met",   "rationale": "No closing summary at all.", "evidence_quote": ""},
            "Response Factor": {"level": "Fully Met", "rationale": "On time.", "evidence_quote": ""},
        },
        "recommendations": ["Continue using open-ended questions."],
    }
    client = FakeClient([_evidence_payload(has_closing_summary=False), json.dumps(payload)])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    joined = " | ".join(result["recommendations"]).lower()
    assert "summary" in joined


# ---------------------------------------------------------------------------
# 2-call architecture coverage
# ---------------------------------------------------------------------------


def test_two_call_happy_path_uses_fast_extractor_model() -> None:
    client = FakeClient([_evidence_payload(), _good_payload()])
    me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert client.chat.completions.calls[0]["model"] == "llama-3.1-8b-instant"
    assert client.chat.completions.calls[1]["model"] == "llama-3.3-70b-versatile"


def test_extractor_failure_falls_back_to_single_call() -> None:
    client = FakeClient(["not json", "still not json", _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 3


def test_hallucinated_quote_is_dropped() -> None:
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
    scorer_user_content = client.chat.completions.calls[1]["messages"][-1]["content"]
    assert "This quote is not in the transcript at all." not in scorer_user_content
    assert "Another fake quote that is not present." not in scorer_user_content
    assert result["categories"]["Compassion"]["assessment"] == "Fully Met"


def test_evidence_flag_forces_summary_not_met() -> None:
    client = FakeClient([
        _evidence_payload(has_closing_summary=False),
        _good_payload(summary_level="Fully Met", summary_rationale="Student summarized everything clearly."),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["categories"]["Summary"]["assessment"] == "Not Met"
    assert result["categories"]["Summary"]["points"] == pytest.approx(0.0)
    assert "extractor flagged" in result["categories"]["Summary"]["rationale"]


def test_evidence_flag_caps_compassion_and_acceptance() -> None:
    client = FakeClient([
        _evidence_payload(belittling_instances=["Would it be okay if I shared some info?"]),
        _good_payload(
            compassion_level="Fully Met",
            acceptance_level="Fully Met",
            compassion_rationale="Student was warm and supportive.",
        ),
    ])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["categories"]["Compassion"]["assessment"] == "Minimally Met"
    assert result["categories"]["Acceptance"]["assessment"] == "Partially Met"


def test_extractor_schema_violation_retries() -> None:
    bad = json.dumps({"per_category": {c: [] for c in me.REQUIRED_CATEGORIES}})
    client = FakeClient([bad, _evidence_payload(), _good_payload()])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 3


def test_partial_result_when_scorer_fails_twice() -> None:
    client = FakeClient([_evidence_payload(), "not json", "still not json"])
    result = me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert result["partial"] is True
    assert "Manual review required" in result["performance_band"]
