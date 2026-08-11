"""MI Evaluation: two-call evaluator (evidence extraction + scoring) with fallback.

Single source of truth for evaluating MI sessions. Consolidates the legacy
evaluation, feedback-template, and LLM-scoring paths into one strict-JSON
two-call pipeline.

Design goals:

* Two-stage LLM pipeline: Call 1 extracts evidence (quotes + structured flags),
  Call 2 scores the six categories using the verified evidence. Each stage is
  strict JSON.
* Graceful degradation: if Call 1 fails twice, we silently fall back to the
  legacy single-call scoring path — worst-case behavior matches the old system.
* Single function ``_validate_and_normalize`` owns all point math. Rules 4 and 5
  are enforced deterministically from Call 1's structured flags (when available)
  with the legacy keyword heuristic kept as a secondary safety net.
* On parse / schema failure at the scoring stage we **retry once** with a
  corrective system message; if that still fails we return
  ``EvaluationResult(partial=True, ...)`` instead of raising. Hard failures
  (network, auth) raise ``EvaluationError``.
* Quotes returned by Call 1 are verified as verbatim substrings of the
  transcript. Hallucinated quotes are silently dropped.

Public surface:

* ``EvaluationError`` (typed exception with ``phase`` + ``raw_response``)
* ``EvaluationResult`` (TypedDict)
* ``EVALUATOR_SYSTEM_PROMPT`` (legacy single-call contract, still used in
  fallback mode)
* ``evaluate_session(transcript, session_type, student_name, *, client, model=...,
  extractor_model=...)``
* ``format_evaluation_for_display(result) -> str``
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict

from llm_provider import (
    MODELS,
    is_unknown_model,
    is_unsupported_response_format,
)
from rubric.mi_rubric import (
    CategoryAssessment,
    MIRubric,
    RubricContext,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class CategoryResult(TypedDict):
    assessment: str
    points: float
    max_points: int
    rationale: str
    evidence_quote: str


class EvaluationResult(TypedDict):
    categories: Dict[str, CategoryResult]
    total_score: float
    max_possible_score: int
    percentage: float
    performance_band: str
    recommendations: List[str]
    partial: bool
    notes: str


class _Evidence(TypedDict):
    """Structured output of Call 1, with quotes already verified against the transcript."""
    per_category: Dict[str, List[str]]
    has_closing_summary: bool
    belittling_instances: List[str]
    notes: str


class EvaluationError(Exception):
    """Hard failure during evaluation.

    ``phase`` is one of ``"llm_call"``, ``"json_parse"``, ``"schema"``,
    ``"normalization"``. ``raw_response`` carries whatever text the LLM
    returned (or ``None`` if the call itself failed).
    """

    def __init__(self, message: str, *, phase: str, raw_response: Optional[str] = None) -> None:
        super().__init__(message)
        self.phase = phase
        self.raw_response = raw_response


# ---------------------------------------------------------------------------
# Constants — schema, level mapping, prompts
# ---------------------------------------------------------------------------


REQUIRED_CATEGORIES: List[str] = [
    "Collaboration",
    "Acceptance",
    "Compassion",
    "Evocation",
    "Summary",
    "Response Factor",
]


LEVEL_TO_ASSESSMENT: Dict[str, CategoryAssessment] = {
    "Not Met": CategoryAssessment.NOT_MET,
    "Minimally Met": CategoryAssessment.MINIMALLY_MET,
    "Partially Met": CategoryAssessment.PARTIALLY_MET,
    "Fully Met": CategoryAssessment.FULLY_MET,
}

LEVEL_RANK: Dict[str, int] = {
    "Not Met": 0,
    "Minimally Met": 1,
    "Partially Met": 2,
    "Fully Met": 3,
}


SESSION_TYPE_TO_CONTEXT: Dict[str, RubricContext] = {
    "HPV": RubricContext.HPV,
    "OHI": RubricContext.OHI,
    "Tobacco": RubricContext.TOBACCO,
    "Perio": RubricContext.PERIO,
}


# Legacy single-call prompt — still used as the fallback path when Call 1 fails.
EVALUATOR_SYSTEM_PROMPT = """You are an expert Motivational Interviewing (MI) evaluator for dental and healthcare education.

You will receive a session transcript between a dental student (the "user" / "Student") and a simulated patient (the "assistant" / "Patient"). Evaluate ONLY the student's MI skill, not the patient's responses and not spelling/grammar/English proficiency.

## Output contract — STRICT JSON ONLY

Return a single JSON object (no markdown fences, no commentary before or after) with EXACTLY this shape:

{
  "categories": {
    "Collaboration":     {"level": "<one of: Fully Met | Partially Met | Minimally Met | Not Met>", "rationale": "<1-3 sentences citing specific student behavior>", "evidence_quote": "<one direct quote from the student, or empty string if none>"},
    "Acceptance":        {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Compassion":        {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Evocation":         {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Summary":           {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Response Factor":   {"level": "...", "rationale": "...", "evidence_quote": "..."}
  },
  "recommendations": ["<concrete, actionable improvement>", "..."]
}

All six categories MUST be present. The four allowed level values are exactly: "Fully Met", "Partially Met", "Minimally Met", "Not Met".

## Grading rules

1. Grade ONLY MI technique. Ignore spelling, grammar, capitalization, informality.
2. Each rationale MUST cite specific student behavior. If you cannot find any student behavior to support a category, score it "Not Met" and say so in the rationale.
3. Each evidence_quote MUST be a verbatim substring of the student's actual words, or an empty string if you cannot find a relevant quote.
4. **Summary rule (mandatory)**: If the student did not provide a closing summary that reflects the big picture and/or checks accuracy of next steps, you MUST score Summary as "Not Met" regardless of how the rest of the conversation went. A polite goodbye is NOT a summary.
5. **Belittling rule (mandatory)**: If the student used dismissive, judgmental, fixing, lecturing, or belittling language toward the patient at any point — even briefly — then Compassion CANNOT exceed "Minimally Met" and Acceptance CANNOT exceed "Partially Met". This applies even if the student showed empathy elsewhere.
6. The recommendations array MUST contain at least one entry, and MUST address the lowest-scored category by name. Add up to 4 more entries for other notable gaps.

Return only the JSON object. Do not wrap it in code fences. Do not add a preamble."""


# Call 1: evidence extraction. No grading, no scores.
_EXTRACTOR_SYSTEM_PROMPT = """You are an evidence collector for Motivational Interviewing (MI) evaluation of dental and healthcare education sessions.

You will receive a transcript between a dental student ("Student") and a simulated patient ("Patient"). Your job is to extract EVIDENCE ONLY — do NOT score, grade, or assign levels. A separate scoring pass will do that.

## Output contract — STRICT JSON ONLY

Return a single JSON object (no markdown fences, no commentary) with EXACTLY this shape:

{
  "per_category": {
    "Collaboration":     ["<verbatim student quote>", "..."],
    "Acceptance":        ["..."],
    "Compassion":        ["..."],
    "Evocation":         ["..."],
    "Summary":           ["..."],
    "Response Factor":   ["..."]
  },
  "has_closing_summary": true | false,
  "belittling_instances": ["<verbatim student quote>", "..."],
  "notes": "<short plain-text observations, 1-3 sentences>"
}

## Rules

1. All six category keys MUST be present in per_category. Use an empty array if no relevant student behavior appeared.
2. Every string inside per_category and belittling_instances MUST be a verbatim substring of the student's words in the transcript — copy exactly, do not paraphrase. If you cannot find a relevant quote, return an empty array for that category.
3. Set has_closing_summary to true ONLY if the student explicitly reflected the big picture of the conversation and/or checked accuracy of next steps at the end. A polite goodbye, a single thank-you, or a short sign-off is NOT a closing summary.
4. Populate belittling_instances with any student utterance that is dismissive, judgmental, shaming, lecturing, fixing, condescending, or patronizing toward the patient. Quote the exact words. If there are none, return an empty array.
5. notes is free-form and may include general observations a downstream scorer should know (tone, pacing, missed opportunities). Keep it under 3 sentences.

Return only the JSON object. Do not wrap it in code fences. Do not add a preamble."""


# Call 2: scoring using pre-extracted evidence. Rules 4 and 5 are handled by
# code downstream, so we keep the prompt focused on interpretation.
_SCORER_SYSTEM_PROMPT = """You are an expert Motivational Interviewing (MI) evaluator for dental and healthcare education.

You will receive (1) a session transcript between a dental student and a simulated patient, and (2) a pre-extracted evidence block collected by a first-pass reader. Use both to score the student's MI skill across six categories.

Evaluate ONLY the student's MI skill, not the patient's responses, not spelling/grammar/English proficiency.

## Output contract — STRICT JSON ONLY

Return a single JSON object (no markdown fences, no commentary before or after) with EXACTLY this shape:

{
  "categories": {
    "Collaboration":     {"level": "<one of: Fully Met | Partially Met | Minimally Met | Not Met>", "rationale": "<1-3 sentences citing specific student behavior>", "evidence_quote": "<one direct student quote, or empty string>"},
    "Acceptance":        {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Compassion":        {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Evocation":         {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Summary":           {"level": "...", "rationale": "...", "evidence_quote": "..."},
    "Response Factor":   {"level": "...", "rationale": "...", "evidence_quote": "..."}
  },
  "recommendations": ["<concrete, actionable improvement>", "..."]
}

All six categories MUST be present. The four allowed level values are exactly: "Fully Met", "Partially Met", "Minimally Met", "Not Met".

## Grading rules

1. Grade ONLY MI technique. Ignore spelling, grammar, capitalization, informality.
2. Each rationale MUST cite specific student behavior. Prefer quotes from the pre-extracted evidence block, but you may also cite behavior you observe directly in the transcript.
3. Each evidence_quote MUST be a verbatim substring of the student's actual words, or an empty string if you cannot find a relevant quote. Reusing a quote from the evidence block is fine.
4. The recommendations array MUST contain at least one entry, and MUST address the lowest-scored category by name. Add up to 4 more entries for other notable gaps.

Scoring Summary and Compassion / Acceptance: base your level purely on what the transcript and evidence show. An automated post-processing step applies hard rules based on the evidence block's structured flags, so do not self-censor — just be honest.

Return only the JSON object. Do not wrap it in code fences. Do not add a preamble."""


_RETRY_CORRECTION_HINT = (
    "Your previous response was not valid JSON matching the required schema. "
    "Return ONLY a single JSON object with the exact shape described in the system prompt. "
    "Do not include code fences, prose, or any text outside the JSON object."
)


# ---------------------------------------------------------------------------
# Evaluation entry point
# ---------------------------------------------------------------------------


def evaluate_session(
    transcript: str,
    session_type: str,
    student_name: str,
    *,
    client: Any,
    model: str = MODELS["eval"],
    extractor_model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    extractor_max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
) -> EvaluationResult:
    """Evaluate one MI session and return a normalized result.

    ``client`` must expose an OpenAI-style ``chat.completions.create(...)``
    method. Both the Groq SDK and the ``openai`` SDK satisfy this, which is what
    lets the same code target Groq or a self-hosted vLLM server.
    ``transcript`` is the raw conversation text. ``session_type`` is one of
    ``"HPV"``, ``"OHI"``, ``"Tobacco"``, ``"Perio"`` (case-insensitive).

    ``model`` is used for the scoring pass (Call 2). ``extractor_model`` is
    used for the evidence pass (Call 1); when ``None`` we default to the faster
    registry model, falling back to ``model`` if the client rejects it. Callers
    that want to pin both stages to the same model can pass
    ``extractor_model=model``.

    ``max_tokens``, ``extractor_max_tokens`` and ``timeout`` bound the two
    calls. They matter far more against a self-hosted model than against Groq:
    vLLM defaults generation to the remaining context window, so a degenerate
    response can otherwise run for minutes.

    Returns a fully-validated :class:`EvaluationResult`. On JSON / schema
    failure that survives one retry, the result is returned with
    ``partial=True`` and a ``notes`` string explaining what went wrong.

    Raises :class:`EvaluationError` only for hard failures (network, auth,
    invalid arguments).
    """
    if not transcript or not transcript.strip():
        raise EvaluationError(
            "Transcript is empty; nothing to evaluate.",
            phase="normalization",
        )

    # Call 1: evidence extraction. On hard failure we let EvaluationError
    # propagate (network/auth are fatal). On parse/schema failure after one
    # retry, we silently drop evidence and fall back to the legacy single-call
    # path for Call 2.
    evidence = _extract_evidence(
        transcript,
        session_type,
        student_name,
        client=client,
        model=extractor_model or MODELS["extractor"],
        fallback_model=model,
        max_tokens=extractor_max_tokens,
        timeout=timeout,
    )

    # Call 2: scoring. If evidence is None we use the legacy single-call prompt
    # so the system still produces a result at least as good as the old code.
    return _score_with_evidence(
        transcript,
        session_type,
        student_name,
        evidence=evidence,
        client=client,
        model=model,
        max_tokens=max_tokens,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Call 1: evidence extraction
# ---------------------------------------------------------------------------


def _extract_evidence(
    transcript: str,
    session_type: str,
    student_name: str,
    *,
    client: Any,
    model: str,
    fallback_model: str,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
) -> Optional[_Evidence]:
    """Run Call 1 (evidence extraction). Return verified evidence, or None.

    Returns ``None`` iff both the initial call and the retry produced
    unparseable output. Hard failures (network / auth) are allowed to raise
    so the caller surfaces them as :class:`EvaluationError`.
    """
    user_prompt = _build_extractor_user_prompt(transcript, session_type, student_name)
    base_messages = [
        {"role": "system", "content": _EXTRACTOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # First attempt with the fast extractor model; if the client rejects it
    # (e.g. model not available on the account), retry once with fallback_model
    # before giving up.
    try:
        raw_first = _call_llm(client, model, base_messages, max_tokens=max_tokens, timeout=timeout)
    except EvaluationError as exc:
        if model != fallback_model and _looks_like_unknown_model(exc):
            logger.info("Extractor model %s unavailable; falling back to %s", model, fallback_model)
            raw_first = _call_llm(client, fallback_model, base_messages, max_tokens=max_tokens, timeout=timeout)
            model = fallback_model
        else:
            raise

    parsed = _try_parse_extractor(raw_first, transcript)
    if isinstance(parsed, dict) and parsed.get("__ok__"):
        return parsed["evidence"]  # type: ignore[return-value]

    first_error = parsed

    retry_messages = base_messages + [
        {"role": "system", "content": _RETRY_CORRECTION_HINT + f" (Previous failure: {first_error})"},
    ]
    raw_second = _call_llm(client, model, retry_messages, max_tokens=max_tokens, timeout=timeout)
    parsed_second = _try_parse_extractor(raw_second, transcript)
    if isinstance(parsed_second, dict) and parsed_second.get("__ok__"):
        return parsed_second["evidence"]  # type: ignore[return-value]

    logger.warning(
        "Evidence extractor returned unparseable output twice for student=%s session=%s. "
        "Falling back to single-call scoring. First error: %s. Second error: %s",
        student_name, session_type, first_error, parsed_second,
    )
    return None


def _try_parse_extractor(raw: str, transcript: str):
    """Parse + validate extractor output, returning verified :class:`_Evidence`.

    Returns ``{"__ok__": True, "evidence": _Evidence}`` on success, or an error
    message string on failure. Quotes are substring-verified against the
    transcript; hallucinated quotes are silently dropped (not treated as an
    error).
    """
    if not raw or not raw.strip():
        return "empty response"

    text = _strip_code_fences(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return f"json parse: {exc.msg} at line {exc.lineno} col {exc.colno}"

    schema_error = _check_extractor_schema(data)
    if schema_error:
        return f"schema: {schema_error}"

    per_category_raw = data["per_category"]
    per_category: Dict[str, List[str]] = {}
    for cat in REQUIRED_CATEGORIES:
        quotes = per_category_raw.get(cat, [])
        per_category[cat] = _verify_quotes(quotes, transcript)

    belittling = _verify_quotes(data.get("belittling_instances", []), transcript)

    evidence: _Evidence = {
        "per_category": per_category,
        "has_closing_summary": bool(data["has_closing_summary"]),
        "belittling_instances": belittling,
        "notes": str(data.get("notes", "")).strip(),
    }
    return {"__ok__": True, "evidence": evidence}


def _check_extractor_schema(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return "top-level value must be a JSON object"
    if "per_category" not in data:
        return "missing 'per_category' key"
    if "has_closing_summary" not in data:
        return "missing 'has_closing_summary' key"
    if "belittling_instances" not in data:
        return "missing 'belittling_instances' key"

    per_category = data["per_category"]
    if not isinstance(per_category, dict):
        return "'per_category' must be a JSON object"

    missing = [c for c in REQUIRED_CATEGORIES if c not in per_category]
    if missing:
        return f"missing per_category keys: {', '.join(missing)}"

    for cat in REQUIRED_CATEGORIES:
        quotes = per_category[cat]
        if not isinstance(quotes, list) or not all(isinstance(q, str) for q in quotes):
            return f"per_category['{cat}'] must be a list of strings"

    if not isinstance(data["has_closing_summary"], bool):
        return "'has_closing_summary' must be a boolean"

    belittling = data["belittling_instances"]
    if not isinstance(belittling, list) or not all(isinstance(q, str) for q in belittling):
        return "'belittling_instances' must be a list of strings"

    return None


def _verify_quotes(quotes: List[str], transcript: str) -> List[str]:
    """Keep only quotes that appear verbatim in the transcript."""
    verified: List[str] = []
    for q in quotes:
        if not isinstance(q, str):
            continue
        stripped = q.strip()
        if stripped and stripped in transcript:
            verified.append(stripped)
    return verified


def _build_extractor_user_prompt(transcript: str, session_type: str, student_name: str) -> str:
    context_label = _context_label(session_type)
    return (
        f"## Session\n\n"
        f"- Session type: {session_type} ({context_label})\n"
        f"- Student name: {student_name}\n\n"
        f"## Transcript\n\n{transcript}\n\n"
        f"Now produce the evidence JSON as specified in the system prompt. "
        f"Copy quotes verbatim and do not assign any scores."
    )


# ---------------------------------------------------------------------------
# Call 2: scoring with (or without) evidence
# ---------------------------------------------------------------------------


def _score_with_evidence(
    transcript: str,
    session_type: str,
    student_name: str,
    *,
    evidence: Optional[_Evidence],
    client: Any,
    model: str,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
) -> EvaluationResult:
    """Run Call 2 (scoring). Uses evidence when available, legacy prompt when not."""
    if evidence is None:
        # Fallback path: behave exactly like the pre-2-call system.
        system_prompt = EVALUATOR_SYSTEM_PROMPT
        user_prompt = _build_scorer_user_prompt_legacy(transcript, session_type, student_name)
    else:
        system_prompt = _SCORER_SYSTEM_PROMPT
        user_prompt = _build_scorer_user_prompt_with_evidence(
            transcript, session_type, student_name, evidence
        )

    base_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw_first = _call_llm(client, model, base_messages, max_tokens=max_tokens, timeout=timeout)
    parsed = _try_parse_and_validate(raw_first, session_type, evidence=evidence)
    if isinstance(parsed, dict) and parsed.get("__ok__"):
        return parsed["result"]  # type: ignore[return-value]

    first_error = parsed

    retry_messages = base_messages + [
        {"role": "system", "content": _RETRY_CORRECTION_HINT + f" (Previous failure: {first_error})"},
    ]
    raw_second = _call_llm(client, model, retry_messages, max_tokens=max_tokens, timeout=timeout)
    parsed_second = _try_parse_and_validate(raw_second, session_type, evidence=evidence)
    if isinstance(parsed_second, dict) and parsed_second.get("__ok__"):
        return parsed_second["result"]  # type: ignore[return-value]

    logger.warning(
        "Scorer returned unparseable output twice for student=%s session=%s. "
        "Returning partial result. First error: %s. Second error: %s",
        student_name, session_type, first_error, parsed_second,
    )
    return _build_partial_result(
        session_type=session_type,
        notes=(
            f"Scorer output could not be parsed after one retry. "
            f"First failure: {first_error}. "
            f"Second failure: {parsed_second}. "
            f"Raw final response preserved below for instructor review."
        ),
        raw_response=raw_second,
    )


def _build_scorer_user_prompt_legacy(transcript: str, session_type: str, student_name: str) -> str:
    context_label = _context_label(session_type)
    return (
        f"## Session\n\n"
        f"- Session type: {session_type} ({context_label})\n"
        f"- Student name: {student_name}\n\n"
        f"## Transcript\n\n{transcript}\n\n"
        f"Now produce the JSON object as specified in the system prompt. "
        f"Remember rules 4 (Summary) and 5 (belittling)."
    )


def _build_scorer_user_prompt_with_evidence(
    transcript: str,
    session_type: str,
    student_name: str,
    evidence: _Evidence,
) -> str:
    context_label = _context_label(session_type)
    per_cat_lines: List[str] = []
    for cat in REQUIRED_CATEGORIES:
        quotes = evidence["per_category"].get(cat, [])
        if quotes:
            joined = "; ".join(f"\"{q}\"" for q in quotes)
            per_cat_lines.append(f"- {cat}: {joined}")
        else:
            per_cat_lines.append(f"- {cat}: (no supporting quotes found)")

    belittling_block = (
        "; ".join(f"\"{q}\"" for q in evidence["belittling_instances"])
        if evidence["belittling_instances"]
        else "(none)"
    )

    evidence_block = (
        "## Pre-extracted evidence\n\n"
        "Per-category supporting student quotes:\n"
        + "\n".join(per_cat_lines)
        + f"\n\nClosing summary present: {str(evidence['has_closing_summary']).lower()}\n"
        + f"Belittling / dismissive instances: {belittling_block}\n"
    )
    if evidence["notes"]:
        evidence_block += f"Extractor notes: {evidence['notes']}\n"

    return (
        f"## Session\n\n"
        f"- Session type: {session_type} ({context_label})\n"
        f"- Student name: {student_name}\n\n"
        f"{evidence_block}\n"
        f"## Transcript\n\n{transcript}\n\n"
        f"Now produce the scoring JSON as specified in the system prompt."
    )


# ---------------------------------------------------------------------------
# LLM call (Groq client adapter)
# ---------------------------------------------------------------------------


def _call_llm(
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
    *,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
) -> str:
    """Call the LLM. Try with json_object response_format, fall back if unsupported.

    Works against any OpenAI-compatible endpoint, including Groq and vLLM.

    ``max_tokens`` and ``timeout`` are omitted from the request when ``None``,
    which keeps the previous behaviour for callers that do not set them and
    avoids sending nulls to endpoints that reject them.
    """
    bounds: Dict[str, Any] = {}
    if max_tokens is not None:
        bounds["max_tokens"] = max_tokens
    if timeout is not None:
        bounds["timeout"] = timeout

    try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
                **bounds,
            )
        except TypeError:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                **bounds,
            )
        except Exception as exc:
            if _looks_like_unsupported_format(exc):
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                    **bounds,
                )
            else:
                raise
    except Exception as exc:
        raise EvaluationError(
            f"LLM call failed: {exc}",
            phase="llm_call",
            raw_response=None,
        ) from exc

    try:
        return response.choices[0].message.content or ""
    except (AttributeError, IndexError, TypeError) as exc:
        raise EvaluationError(
            f"Unexpected LLM response shape: {exc}",
            phase="llm_call",
            raw_response=str(response),
        ) from exc


# Provider-portable error classification. These delegate to llm_provider, which
# inspects typed SDK exceptions first and falls back to substring matching.
#
# The previous implementations matched only on Groq's error text. Against vLLM
# the model-not-found strings would not have matched, so the extractor fallback
# above would never have triggered: instead of quietly retrying with the scoring
# model, the whole evaluation would have failed. That is the kind of bug that
# gets misdiagnosed as "vLLM is broken", so it is fixed here rather than at the
# point of migration.
#
# The thin wrappers are kept so the call sites and their tests read unchanged.


def _looks_like_unsupported_format(exc: Exception) -> bool:
    return is_unsupported_response_format(exc)


def _looks_like_unknown_model(exc: EvaluationError) -> bool:
    return is_unknown_model(exc)


# ---------------------------------------------------------------------------
# Scorer parse + validate + normalize
# ---------------------------------------------------------------------------


def _try_parse_and_validate(raw: str, session_type: str, *, evidence: Optional[_Evidence] = None):
    """Attempt JSON parse + schema check + normalization for the scorer output.

    Returns ``{"__ok__": True, "result": EvaluationResult}`` on success, or an
    error message string on failure.
    """
    if not raw or not raw.strip():
        return "empty response"

    text = _strip_code_fences(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return f"json parse: {exc.msg} at line {exc.lineno} col {exc.colno}"

    schema_error = _check_schema(data)
    if schema_error:
        return f"schema: {schema_error}"

    try:
        result = _validate_and_normalize(data, session_type, evidence=evidence)
    except ValueError as exc:
        return f"normalization: {exc}"

    return {"__ok__": True, "result": result}


def _strip_code_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def _check_schema(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return "top-level value must be a JSON object"
    if "categories" not in data:
        return "missing 'categories' key"
    if "recommendations" not in data:
        return "missing 'recommendations' key"

    categories = data["categories"]
    if not isinstance(categories, dict):
        return "'categories' must be a JSON object"

    missing = [c for c in REQUIRED_CATEGORIES if c not in categories]
    if missing:
        return f"missing categories: {', '.join(missing)}"

    for cat_name in REQUIRED_CATEGORIES:
        cat = categories[cat_name]
        if not isinstance(cat, dict):
            return f"category '{cat_name}' must be a JSON object"
        for field in ("level", "rationale", "evidence_quote"):
            if field not in cat:
                return f"category '{cat_name}' missing field '{field}'"
        if cat["level"] not in LEVEL_RANK:
            return (
                f"category '{cat_name}' has invalid level '{cat['level']}'. "
                f"Allowed: {sorted(LEVEL_RANK)}"
            )

    recs = data["recommendations"]
    if not isinstance(recs, list) or not all(isinstance(r, str) for r in recs):
        return "'recommendations' must be a list of strings"
    if not recs:
        return "'recommendations' must contain at least one entry"

    return None


def _validate_and_normalize(
    data: Dict[str, Any],
    session_type: str,
    *,
    evidence: Optional[_Evidence] = None,
) -> EvaluationResult:
    """Convert validated raw JSON into a fully-typed :class:`EvaluationResult`.

    This is the **single source of truth** for point math. It also enforces
    rules 4 and 5 as hard post-hoc invariants:

    * If ``evidence`` is provided, the structured flags
      (``has_closing_summary``, ``belittling_instances``) drive the cap
      deterministically.
    * The legacy keyword heuristic is kept as a secondary safety net when
      ``evidence`` is ``None`` (fallback mode) or when evidence did not flag
      something the LLM's rationale nevertheless reveals.
    """
    raw_categories = data["categories"]

    evidence_forced_summary = False
    evidence_forced_belittling = False

    # Evidence-driven rule 4 (deterministic): no closing summary => Not Met.
    if evidence is not None and not evidence["has_closing_summary"]:
        summary = raw_categories["Summary"]
        if summary["level"] != "Not Met":
            summary["level"] = "Not Met"
            summary["rationale"] = (
                summary.get("rationale", "")
                + " [Auto-corrected: rule 4 — extractor flagged no closing summary.]"
            ).strip()
        evidence_forced_summary = True

    # Evidence-driven rule 5 (deterministic): any belittling instance => caps.
    if evidence is not None and evidence["belittling_instances"]:
        _apply_belittling_caps(raw_categories, reason="extractor flagged dismissive/belittling language")
        evidence_forced_belittling = True

    # Legacy keyword heuristic for rule 4 — only when evidence didn't already
    # force the downgrade (avoids double-annotation).
    if not evidence_forced_summary:
        summary = raw_categories["Summary"]
        if summary["level"] != "Not Met":
            rationale_lower = (summary.get("rationale") or "").lower()
            if any(
                phrase in rationale_lower
                for phrase in (
                    "no summary", "did not summarize", "didn't summarize",
                    "no closing", "missing summary", "summary was not", "summary not provided",
                )
            ):
                summary["level"] = "Not Met"
                summary["rationale"] = (
                    summary.get("rationale", "") + " [Auto-corrected: rule 4 — no closing summary detected.]"
                ).strip()

    # Legacy keyword heuristic for rule 5 — secondary net.
    if not evidence_forced_belittling:
        belittling_signal = False
        for cat in raw_categories.values():
            rationale_lower = (cat.get("rationale") or "").lower()
            if any(
                phrase in rationale_lower
                for phrase in (
                    "belittl", "dismissive", "judgmental", "shamed", "shaming",
                    "lectur", "fixed the patient", "fixing behavior",
                    "condescend", "patroniz",
                )
            ):
                belittling_signal = True
                break
        if belittling_signal:
            _apply_belittling_caps(raw_categories, reason="dismissive/belittling language detected")

    # Point math — single source of truth.
    categories: Dict[str, CategoryResult] = {}
    total_score = 0.0
    for cat_name in REQUIRED_CATEGORIES:
        cat = raw_categories[cat_name]
        level = cat["level"]
        assessment = LEVEL_TO_ASSESSMENT[level]
        max_points = MIRubric.get_category_points(cat_name)
        multiplier = MIRubric.ASSESSMENT_MULTIPLIERS[assessment]
        points = max_points * multiplier
        if not (0.0 <= points <= max_points + 1e-9):
            raise ValueError(
                f"computed points {points} out of range for {cat_name} (max {max_points})"
            )
        categories[cat_name] = CategoryResult(
            assessment=level,
            points=points,
            max_points=max_points,
            rationale=str(cat.get("rationale", "")).strip(),
            evidence_quote=str(cat.get("evidence_quote", "")).strip(),
        )
        total_score += points

    max_total = MIRubric.get_total_possible()
    percentage = (total_score / max_total) * 100.0 if max_total else 0.0

    recs = [str(r).strip() for r in data["recommendations"] if str(r).strip()]
    lowest_name, lowest_data = min(
        categories.items(),
        key=lambda kv: (kv[1]["points"] / kv[1]["max_points"], kv[0]),
    )
    lowest_pct = lowest_data["points"] / lowest_data["max_points"]
    if lowest_pct < 1.0 and not any(lowest_name.lower() in r.lower() for r in recs):
        recs.insert(
            0,
            f"{lowest_name}: Focus on strengthening this area in your next session — it scored the lowest.",
        )

    return EvaluationResult(
        categories=categories,
        total_score=total_score,
        max_possible_score=max_total,
        percentage=percentage,
        performance_band=MIRubric.get_performance_band(total_score),
        recommendations=recs,
        partial=False,
        notes="",
    )


def _apply_belittling_caps(raw_categories: Dict[str, Any], *, reason: str) -> None:
    """Cap Compassion at Minimally Met and Acceptance at Partially Met."""
    comp = raw_categories["Compassion"]
    if LEVEL_RANK[comp["level"]] > LEVEL_RANK["Minimally Met"]:
        comp["level"] = "Minimally Met"
        comp["rationale"] = (
            comp.get("rationale", "")
            + f" [Auto-corrected: rule 5 — {reason}; Compassion capped at Minimally Met.]"
        ).strip()
    acc = raw_categories["Acceptance"]
    if LEVEL_RANK[acc["level"]] > LEVEL_RANK["Partially Met"]:
        acc["level"] = "Partially Met"
        acc["rationale"] = (
            acc.get("rationale", "")
            + f" [Auto-corrected: rule 5 — {reason}; Acceptance capped at Partially Met.]"
        ).strip()


def _build_partial_result(*, session_type: str, notes: str, raw_response: str) -> EvaluationResult:
    """Construct a partial-result placeholder when both LLM attempts failed."""
    categories: Dict[str, CategoryResult] = {}
    for cat_name in REQUIRED_CATEGORIES:
        max_points = MIRubric.get_category_points(cat_name)
        categories[cat_name] = CategoryResult(
            assessment="Not Scored",
            points=0.0,
            max_points=max_points,
            rationale="Evaluator response could not be parsed; manual review required.",
            evidence_quote="",
        )
    full_notes = notes
    if raw_response:
        full_notes = f"{notes}\n\n--- RAW EVALUATOR RESPONSE ---\n{raw_response}"
    return EvaluationResult(
        categories=categories,
        total_score=0.0,
        max_possible_score=MIRubric.get_total_possible(),
        percentage=0.0,
        performance_band="Manual review required",
        recommendations=[
            "Manual instructor review required: automated evaluation could not be completed."
        ],
        partial=True,
        notes=full_notes,
    )


# ---------------------------------------------------------------------------
# Shared helpers + display
# ---------------------------------------------------------------------------


def _context_label(session_type: str) -> str:
    context = SESSION_TYPE_TO_CONTEXT.get(_canonical_session_type(session_type), RubricContext.HPV)
    return {
        RubricContext.HPV: "HPV vaccination",
        RubricContext.OHI: "oral hygiene",
        RubricContext.TOBACCO: "tobacco cessation",
        RubricContext.PERIO: "periodontitis and gum health",
    }[context]


def _canonical_session_type(session_type: str) -> str:
    s = (session_type or "").strip().upper()
    if s.startswith("HPV"):
        return "HPV"
    if s.startswith("OHI") or s.startswith("ORAL") or s.startswith("DENTAL"):
        return "OHI"
    if s.startswith("TOBACCO") or s.startswith("SMOK") or "CESSATION" in s:
        return "Tobacco"
    if s.startswith("PERIO") or "GUM" in s:
        return "Perio"
    return "HPV"


def format_evaluation_for_display(result: EvaluationResult) -> str:
    """Render the evaluation as markdown for in-app display."""
    lines: List[str] = []
    if result["partial"]:
        lines.append("> :warning: **Partial report** — manual review required. See notes at end.")
        lines.append("")
    lines.append(f"**Total score:** {int(round(result['total_score']))} / {result['max_possible_score']}  ")
    lines.append(f"**Percentage:** {int(round(result['percentage']))}%  ")
    lines.append(f"**Performance band:** {result['performance_band']}")
    lines.append("")
    lines.append("### Category breakdown")
    for cat_name, cat in result["categories"].items():
        pts = int(round(cat["points"]))
        lines.append(f"- **{cat_name}** — {cat['assessment']} ({pts} / {cat['max_points']})")
        if cat["rationale"]:
            lines.append(f"  - {cat['rationale']}")
        if cat["evidence_quote"]:
            lines.append(f"  - _Quote:_ \"{cat['evidence_quote']}\"")
    lines.append("")
    lines.append("### Recommendations")
    for rec in result["recommendations"]:
        lines.append(f"- {rec}")
    if result["partial"] and result["notes"]:
        lines.append("")
        lines.append("### Notes")
        lines.append(result["notes"])
    return "\n".join(lines)
