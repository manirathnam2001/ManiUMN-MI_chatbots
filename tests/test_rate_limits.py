"""Groq free-tier behaviour: pacing, 429 retries, limit classification,
single-call switch for long transcripts, and the transcript-only PDF.

Everything here runs against the FakeClient; no network. ``time.sleep`` is
replaced so the tests do not actually wait.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest  # noqa: E402

import mi_evaluation as me  # noqa: E402
import mi_pdf  # noqa: E402
from test_evaluation import (  # noqa: E402
    DEFAULT_TRANSCRIPT,
    FakeClient,
    _evidence_payload,
    _good_payload,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _Resp:
    def __init__(self, headers: Dict[str, str]) -> None:
        self.headers = headers


class _GroqError(Exception):
    """Mimics groq.APIStatusError: str(), .status_code and .response.headers."""

    def __init__(self, status: int, message: str, headers: Optional[Dict[str, str]] = None) -> None:
        super().__init__(f"Error code: {status} - {{'error': {{'message': '{message}'}}}}")
        self.status_code = status
        self.response = _Resp(headers or {})


def _tpm_429(retry_after: str = "7.5") -> _GroqError:
    return _GroqError(
        429,
        "Rate limit reached for model `openai/gpt-oss-120b` on tokens per minute (TPM): "
        "Limit 8000, Used 7600, Requested 2400. Please try again in 7.5s.",
        {"retry-after": retry_after},
    )


def _tpd_429() -> _GroqError:
    return _GroqError(
        429,
        "Rate limit reached for model `openai/gpt-oss-120b` on tokens per day (TPD): "
        "Limit 200000, Used 199500, Requested 2400. Please try again in 3h12m.",
        {"retry-after": "11520"},
    )


def _tpm_413() -> _GroqError:
    return _GroqError(
        413,
        "Request too large for model `openai/gpt-oss-120b` on tokens per minute (TPM): "
        "Limit 8000, Requested 9100, please reduce your message size and try again.",
    )


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> List[float]:
    slept: List[float] = []
    monkeypatch.setattr(me.time, "sleep", lambda s: slept.append(s))
    return slept


def _long_transcript(turns: int = 25) -> str:
    lines = []
    for i in range(turns):
        lines.append(
            f"Student: Turn {i}: could you tell me a bit more about how you feel "
            "about brushing at night and what gets in the way?"
        )
        lines.append(
            f"Patient: Turn {i}: honestly I am usually too tired, it slips my mind "
            "most evenings and I do not think about it until morning."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Duration parsing and pacer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("7.66s", 7.66),
        ("1m3.5s", 63.5),
        ("250ms", 0.25),
        ("2h1m", 7260.0),
        ("12", 12.0),  # bare retry-after seconds
        ("", None),
        ("soon", None),
    ],
)
def test_parse_duration_seconds(text: str, expected: Optional[float]) -> None:
    assert me.parse_duration_seconds(text) == expected


def test_pacer_waits_only_when_next_call_will_not_fit() -> None:
    slept: List[float] = []
    pacer = me.RateLimitPacer(sleep=slept.append)
    pacer.observe({"x-ratelimit-remaining-tokens": "3000", "x-ratelimit-reset-tokens": "12.5s"})

    pacer.before_call(2500)  # fits
    assert slept == []

    pacer.before_call(5000)  # does not fit -> sleep through the reset
    assert len(slept) == 1 and 12.5 <= slept[0] <= 13.5
    # After waiting the stale numbers are cleared; next call does not wait again.
    pacer.before_call(5000)
    assert len(slept) == 1


def test_pacer_wait_is_capped_and_reports_reason() -> None:
    reasons: List[str] = []
    pacer = me.RateLimitPacer(
        on_wait=lambda s, r: reasons.append(r), max_wait=10.0, sleep=lambda s: None
    )
    pacer.wait(900.0, "silly long")
    assert pacer.waits[0] <= 10.5
    assert reasons == ["silly long"]


def test_pacer_ignores_missing_or_bad_headers() -> None:
    pacer = me.RateLimitPacer(sleep=lambda s: None)
    pacer.observe(None)
    pacer.observe({"x-ratelimit-remaining-tokens": "not-a-number"})
    pacer.before_call(10_000)  # no state -> no wait, no error
    assert pacer.waits == []


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------


def test_limit_classification() -> None:
    assert me.is_rate_limit_error(_tpm_429())
    assert not me.is_daily_limit_error(_tpm_429())
    assert me.is_daily_limit_error(_tpd_429())
    assert me.is_request_too_large_error(_tpm_413())
    assert not me.is_rate_limit_error(RuntimeError("connection refused"))


def test_retry_after_prefers_header_then_message_text() -> None:
    assert me.retry_after_seconds(_tpm_429("9")) == 9.0
    no_header = _GroqError(429, "Rate limit reached ... Please try again in 4.25s.")
    assert me.retry_after_seconds(no_header) == 4.25
    assert me.retry_after_seconds(RuntimeError("nope")) is None


# ---------------------------------------------------------------------------
# _call_llm retry behaviour through evaluate_session
# ---------------------------------------------------------------------------


def test_per_minute_429_waits_retry_after_then_succeeds(no_sleep: List[float]) -> None:
    client = FakeClient([_tpm_429("7.5"), _evidence_payload(), _good_payload()])
    waits: List[float] = []
    result = me.evaluate_session(
        DEFAULT_TRANSCRIPT, "OHI", "S", client=client, on_wait=lambda s, r: waits.append(s)
    )
    assert result["partial"] is False
    assert len(client.chat.completions.calls) == 3
    assert waits and 7.5 <= waits[0] <= 8.5
    assert no_sleep and 7.5 <= no_sleep[0] <= 8.5


def test_per_minute_429_gives_up_after_retries(no_sleep: List[float]) -> None:
    client = FakeClient([_tpm_429(), _tpm_429(), _tpm_429()])
    with pytest.raises(me.EvaluationError) as info:
        me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert info.value.phase == "rate_limit"
    assert len(client.chat.completions.calls) == me.RATE_LIMIT_RETRIES + 1
    assert len(no_sleep) == me.RATE_LIMIT_RETRIES


def test_daily_limit_fails_fast_without_sleeping(no_sleep: List[float]) -> None:
    client = FakeClient([_tpd_429()])
    with pytest.raises(me.EvaluationError) as info:
        me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert info.value.phase == "rate_limit_daily"
    assert no_sleep == []
    assert len(client.chat.completions.calls) == 1


def test_request_too_large_fails_fast(no_sleep: List[float]) -> None:
    client = FakeClient([_tpm_413()])
    with pytest.raises(me.EvaluationError) as info:
        me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert info.value.phase == "rate_limit_size"
    assert no_sleep == []


def test_retry_after_longer_than_max_wait_fails_instead_of_hanging(no_sleep: List[float]) -> None:
    client = FakeClient([_tpm_429(str(me.MAX_RATE_LIMIT_WAIT_SECONDS + 100))])
    with pytest.raises(me.EvaluationError) as info:
        me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert info.value.phase == "rate_limit"
    assert no_sleep == []


# ---------------------------------------------------------------------------
# Single-call switch for long transcripts
# ---------------------------------------------------------------------------


def test_short_transcript_uses_two_calls() -> None:
    assert me.estimate_tokens(DEFAULT_TRANSCRIPT) <= me.SINGLE_CALL_THRESHOLD_TOKENS
    client = FakeClient([_evidence_payload(), _good_payload()])
    me.evaluate_session(DEFAULT_TRANSCRIPT, "OHI", "S", client=client)
    assert len(client.chat.completions.calls) == 2


def test_long_transcript_uses_single_call_with_legacy_prompt() -> None:
    transcript = _long_transcript(25)
    assert me.estimate_tokens(transcript) > me.SINGLE_CALL_THRESHOLD_TOKENS
    client = FakeClient([_good_payload()])
    result = me.evaluate_session(transcript, "OHI", "S", client=client)
    assert result["partial"] is False
    calls = client.chat.completions.calls
    assert len(calls) == 1, "long transcript must send the transcript once, not twice"
    assert calls[0]["messages"][0]["content"] == me.EVALUATOR_SYSTEM_PROMPT
    assert calls[0]["model"] == me.DEFAULT_EVAL_MODEL


def test_threshold_is_overridable() -> None:
    client = FakeClient([_good_payload()])
    me.evaluate_session(
        DEFAULT_TRANSCRIPT, "OHI", "S", client=client, single_call_threshold_tokens=1
    )
    assert len(client.chat.completions.calls) == 1


def test_completion_cap_leaves_room_under_free_tier_budget() -> None:
    # A 25-turn transcript in single-call mode must fit one 8k/min window:
    # prompt + transcript + requested cap.
    transcript = _long_transcript(25)
    client = FakeClient([_good_payload()])
    me.evaluate_session(transcript, "OHI", "S", client=client)
    call = client.chat.completions.calls[0]
    requested = sum(me.estimate_tokens(m["content"]) for m in call["messages"])
    requested += call["max_completion_tokens"]
    assert requested < 8000, f"~{requested} tokens requested; would 413 on a free key"


# ---------------------------------------------------------------------------
# Transcript-only PDF
# ---------------------------------------------------------------------------


def test_transcript_filename_is_loud() -> None:
    assert mi_pdf.construct_transcript_filename("Jane Doe", "HPV", "Diana") == (
        "Jane_Doe-HPV-Diana Transcript NEEDS-EVALUATION.pdf"
    )


def test_generate_transcript_pdf_renders_conversation() -> None:
    history: List[Dict[str, Any]] = [
        {"role": "user", "content": "Hi, how are you feeling about the vaccine?"},
        {"role": "assistant", "content": "Honestly a bit nervous about side effects."},
    ]
    pdf = mi_pdf.generate_transcript_pdf(
        student_name="Jane Doe",
        session_type="HPV",
        transcript=history,
        timestamp_cst="2026-09-20 10:00 AM CDT",
        reason="Groq daily limit reached.",
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_generate_transcript_pdf_requires_student_name() -> None:
    with pytest.raises(ValueError):
        mi_pdf.generate_transcript_pdf(
            student_name="", session_type="HPV", transcript=[], timestamp_cst="t", reason="r"
        )
