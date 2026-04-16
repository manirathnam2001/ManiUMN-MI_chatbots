"""MI Evaluation: strict-JSON evaluator + schema validator + point math.

Single source of truth for evaluating MI sessions. Replaces the legacy chain of
``services/evaluation_service.py`` (regex parsing), ``feedback_template.py``
(prompt + display formatting), and the LLM-call portion of ``scoring_utils.py``.

Design goals:

* Evaluator returns **strict JSON**, not free-form text. Eliminates the regex
  parser that used to crash with ``NameError: cls`` and silently degrade PDFs.
* Single function ``_validate_and_normalize`` owns all point math.
* On parse / schema failure we **retry once** with a corrective system message;
  if that still fails we return ``EvaluationResult(partial=True, ...)`` instead
  of raising. Hard failures (network, auth) raise ``EvaluationError``.
* Two evaluator-prompt rules added that the old system lacked:
    - **Rule 4**: missing closing summary forces ``Summary = Not Met``.
    - **Rule 5**: dismissive/judgmental/belittling student language caps
      ``Compassion`` at Minimally Met and ``Acceptance`` at Partially Met.

Public surface:

* ``EvaluationError`` (typed exception with ``phase`` + ``raw_response``)
* ``EvaluationResult`` (TypedDict)
* ``EVALUATOR_SYSTEM_PROMPT`` (strict JSON contract)
* ``evaluate_session(transcript, session_type, student_name, *, client, model=...)``
* ``format_evaluation_for_display(result) -> str``
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict

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
# Constants — schema, level mapping, prompt
# ---------------------------------------------------------------------------


REQUIRED_CATEGORIES: List[str] = [
    "Collaboration",
    "Acceptance",
    "Compassion",
    "Evocation",
    "Summary",
    "Response Factor",
]


# Order matters for the level→multiplier ranking comparisons in rule 5.
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
    model: str = "llama-3.3-70b-versatile",
) -> EvaluationResult:
    """Evaluate one MI session and return a normalized result.

    ``client`` must expose a Groq-style ``chat.completions.create(...)`` method.
    ``transcript`` is the raw conversation text. ``session_type`` is one of
    ``"HPV"``, ``"OHI"``, ``"Tobacco"``, ``"Perio"`` (case-insensitive).

    Returns a fully-validated :class:`EvaluationResult`. On JSON / schema
    failure that survives one retry, the result is returned with
    ``partial=True`` and a ``notes`` string explaining what went wrong; the PDF
    layer renders a clearly-marked partial report in that case.

    Raises :class:`EvaluationError` only for hard failures (network, auth,
    invalid arguments).
    """
    if not transcript or not transcript.strip():
        raise EvaluationError(
            "Transcript is empty; nothing to evaluate.",
            phase="normalization",
        )

    user_prompt = _build_user_prompt(transcript, session_type, student_name)
    base_messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    raw_first = _call_llm(client, model, base_messages)
    parsed = _try_parse_and_validate(raw_first, session_type)
    if isinstance(parsed, dict) and parsed.get("__ok__"):
        return parsed["result"]  # type: ignore[return-value]

    first_error = parsed  # parsed is the error string in the failure path

    # Retry once with a corrective hint appended.
    retry_messages = base_messages + [
        {"role": "system", "content": _RETRY_CORRECTION_HINT + f" (Previous failure: {first_error})"},
    ]
    raw_second = _call_llm(client, model, retry_messages)
    parsed_second = _try_parse_and_validate(raw_second, session_type)
    if isinstance(parsed_second, dict) and parsed_second.get("__ok__"):
        return parsed_second["result"]  # type: ignore[return-value]

    # Both attempts failed: return a partial result rather than raise. The PDF
    # layer surfaces this clearly with a banner; no silent fallback.
    logger.warning(
        "Evaluator returned unparseable output twice for student=%s session=%s. "
        "Returning partial result. First error: %s. Second error: %s",
        student_name, session_type, first_error, parsed_second,
    )
    return _build_partial_result(
        session_type=session_type,
        notes=(
            f"Evaluator output could not be parsed after one retry. "
            f"First failure: {first_error}. "
            f"Second failure: {parsed_second}. "
            f"Raw final response preserved below for instructor review."
        ),
        raw_response=raw_second,
    )


# ---------------------------------------------------------------------------
# LLM call (Groq client adapter)
# ---------------------------------------------------------------------------


def _call_llm(client: Any, model: str, messages: List[Dict[str, str]]) -> str:
    """Call the Groq client. Try with json_object response_format, fall back if unsupported."""
    try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except TypeError:
            # Older client signatures may not accept response_format.
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
            )
        except Exception as exc:
            # Groq raises BadRequestError for unsupported models; fall back to
            # plain mode and let _try_parse_and_validate catch any malformed
            # JSON downstream.
            if _looks_like_unsupported_format(exc):
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
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


def _looks_like_unsupported_format(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "response_format" in msg or "json_object" in msg


# ---------------------------------------------------------------------------
# Parse + validate + normalize
# ---------------------------------------------------------------------------


def _try_parse_and_validate(raw: str, session_type: str):
    """Attempt JSON parse + schema check + normalization.

    Returns ``{"__ok__": True, "result": EvaluationResult}`` on success, or an
    error message string on failure.
    """
    if not raw or not raw.strip():
        return "empty response"

    text = raw.strip()
    # Strip accidental ```json fences if the model added them.
    if text.startswith("```"):
        text = text.strip("`")
        # Drop a leading "json" language tag if present.
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip()
        # Drop a trailing closing fence remnant.
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return f"json parse: {exc.msg} at line {exc.lineno} col {exc.colno}"

    schema_error = _check_schema(data)
    if schema_error:
        return f"schema: {schema_error}"

    try:
        result = _validate_and_normalize(data, session_type)
    except ValueError as exc:
        return f"normalization: {exc}"

    return {"__ok__": True, "result": result}


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


def _validate_and_normalize(data: Dict[str, Any], session_type: str) -> EvaluationResult:
    """Convert validated raw JSON into a fully-typed :class:`EvaluationResult`.

    This is the **single source of truth** for point math. It also enforces
    the post-hoc invariants from rules 4 and 5 in case the LLM violated them.
    """
    raw_categories = data["categories"]

    # Apply rule 4 post-hoc safety: if level claims Summary > Not Met but
    # rationale or evidence indicates no summary was given, downgrade to Not
    # Met. We cannot reliably detect that from structured fields alone, so we
    # only apply a minimal check: empty evidence_quote AND rationale containing
    # a "no summary" signal.
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

    # Apply rule 5 post-hoc safety: if any rationale flags belittling/dismissive
    # language by the student, cap Compassion at Minimally Met and Acceptance
    # at Partially Met.
    belittling_signal = False
    for cat_name, cat in raw_categories.items():
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
        comp = raw_categories["Compassion"]
        if LEVEL_RANK[comp["level"]] > LEVEL_RANK["Minimally Met"]:
            comp["level"] = "Minimally Met"
            comp["rationale"] = (
                comp.get("rationale", "")
                + " [Auto-corrected: rule 5 — dismissive/belittling language detected; Compassion capped at Minimally Met.]"
            ).strip()
        acc = raw_categories["Acceptance"]
        if LEVEL_RANK[acc["level"]] > LEVEL_RANK["Partially Met"]:
            acc["level"] = "Partially Met"
            acc["rationale"] = (
                acc.get("rationale", "")
                + " [Auto-corrected: rule 5 — dismissive/belittling language detected; Acceptance capped at Partially Met.]"
            ).strip()

    # Now compute points category-by-category.
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

    # Recommendations: ensure the lowest-scored category is referenced by name,
    # but only when there's actually room to improve. If every category is at
    # max points, leave the LLM's recommendations as-is.
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
# Prompt + display helpers
# ---------------------------------------------------------------------------


def _build_user_prompt(transcript: str, session_type: str, student_name: str) -> str:
    context = SESSION_TYPE_TO_CONTEXT.get(_canonical_session_type(session_type), RubricContext.HPV)
    context_label = {
        RubricContext.HPV: "HPV vaccination",
        RubricContext.OHI: "oral hygiene",
        RubricContext.TOBACCO: "tobacco cessation",
        RubricContext.PERIO: "periodontitis and gum health",
    }[context]
    return (
        f"## Session\n\n"
        f"- Session type: {session_type} ({context_label})\n"
        f"- Student name: {student_name}\n\n"
        f"## Transcript\n\n{transcript}\n\n"
        f"Now produce the JSON object as specified in the system prompt. "
        f"Remember rules 4 (Summary) and 5 (belittling)."
    )


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
