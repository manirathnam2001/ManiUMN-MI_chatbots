"""Shared Streamlit session runner for the four MI practice pages.

Replaces ``chat_utils.py``. Each of the four pages (OHI, HPV, Perio, Tobacco)
becomes a ~30-line shell that constructs a :class:`SessionConfig` and calls
:func:`run_practice_session`.

What's deliberately NOT in this runner (documented regressions per the
approved plan; see C:\\Users\\manir\\.claude\\plans\\pure-marinating-pike.md):

* Voice mode (STT/TTS) — not wired up. ``SessionConfig`` reserves the field
  for a follow-up.
* Email-to-Box backup — the page-level send loop using
  ``RobustEmailSender`` is not invoked here.
* Mutual-intent semantic ending detection — sessions end when the student
  clicks the "Generate Feedback" button, not via automatic detection. The
  ``end_control_middleware`` module that implemented this was removed during
  the MSI migration work; it had been dead code since this runner replaced
  ``chat_utils.py``.

Public surface:

* :class:`SessionConfig` — page-level configuration.
* :func:`run_practice_session(config)` — full Streamlit page lifecycle.
* :data:`PATIENT_TURN_RULES` — turn-level system message that adds the
  resistance-under-belittling instruction the legacy prompts lacked.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import streamlit as st
from groq import Groq

from mi_evaluation import (
    EvaluationError,
    EvaluationResult,
    evaluate_session,
    format_evaluation_for_display,
)
from mi_pdf import construct_feedback_filename, generate_pdf_report
from time_utils import get_formatted_utc_time
from app_env import render_environment_banner


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Patient turn rules (the resistance-under-belittling fix)
# ---------------------------------------------------------------------------


PATIENT_TURN_RULES = """Stay in character as the patient. You are NOT the provider.

RULES:
- Keep responses to 2-3 sentences. Be realistic and conversational.
- Respond with your own feelings, concerns, and reactions as a patient would.
- NEVER provide feedback, evaluation, clinical advice, or score the student.
- NEVER use provider phrases like "It was a pleasure", "You demonstrated", "Is there anything else I can help with", or "before we wrap up".
- NEVER compliment the student's MI technique mid-conversation.

CRITICAL — RESISTANCE UNDER PRESSURE:
If the clinician uses dismissive, judgmental, fixing, lecturing, or belittling language toward you AT ANY POINT — become MORE guarded, not less:
- Give shorter answers.
- Disclose less personal information.
- Show more reluctance and visible discomfort.
- Do NOT apologize for being concerned or reluctant.
- Do NOT capitulate to pressure tactics, false reassurance, or guilt-tripping.
- It is realistic and expected for patients to disengage when they feel judged. Reflect that authentically.

If the conversation winds down naturally, give a brief patient-style farewell (e.g., "Thanks, I'll think about it.")."""


# ---------------------------------------------------------------------------
# SessionConfig
# ---------------------------------------------------------------------------


@dataclass
class SessionConfig:
    """Per-page configuration for the shared session runner."""

    # Required
    session_type: str  # "OHI" | "HPV" | "Perio" | "Tobacco"
    page_title: str
    page_icon: str
    intro_markdown: str
    personas: Dict[str, Any]  # name -> persona dict (from persona_texts)
    persona_descriptions_markdown: str  # bullet list shown above the selectbox
    domain_name: str
    domain_keywords: List[str]
    rubric_dir_name: str  # e.g. "ohi_rubrics", relative to repo root
    bot_name_short: str  # used for filename: "OHI" | "HPV" | "Perio" | "Tobacco"
    evaluator_label: str  # human-readable label for the evaluator field

    # Models
    chat_model: str = "llama-3.1-8b-instant"
    eval_model: str = "llama-3.3-70b-versatile"

    # Reserved for follow-up reintegration (not implemented in this change).
    enable_voice: bool = False
    enable_email_to_box: bool = False
    enable_end_control: bool = False

    # Filled in by run_practice_session if not provided.
    extra_state_keys: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------


_DEFAULT_STATE = {
    "selected_persona": None,
    "chat_history": None,  # initialized to [] when persona chosen
    "turn_count": 0,
    "evaluation_result": None,  # EvaluationResult dict, or None
    "evaluation_timestamp": None,
    "evaluation_error": None,  # (phase, message) tuple, or None
    "feedback_button_clicked": False,
}


def _initialize_state(config: SessionConfig) -> None:
    for key, default in _DEFAULT_STATE.items():
        st.session_state.setdefault(key, default)
    for key in config.extra_state_keys:
        st.session_state.setdefault(key, None)


def _reset_session() -> None:
    for key in _DEFAULT_STATE:
        if key == "chat_history":
            st.session_state[key] = None
        else:
            st.session_state[key] = _DEFAULT_STATE[key]


# ---------------------------------------------------------------------------
# Auth + credentials guard (matches the legacy page pattern)
# ---------------------------------------------------------------------------


def _auth_guard(expected_bot: str) -> None:
    if not st.session_state.get("authenticated", False):
        st.error(":warning: Access Denied: You must enter through the secret code portal.")
        if st.button("Return to Portal"):
            st.switch_page("secret_code_portal.py")
        st.stop()

    redirect_info = st.session_state.get("redirect_info", {})
    bot_type = redirect_info.get("bot", "").upper().strip()
    if bot_type != expected_bot.upper():
        st.error(":warning: Access Denied: You are not authorized for this chatbot.")
        st.info(f"You are assigned to the {redirect_info.get('bot', 'unknown')} chatbot.")
        if st.button("Return to Portal"):
            st.switch_page("secret_code_portal.py")
        st.stop()

    if "groq_api_key" not in st.session_state or "student_name" not in st.session_state:
        st.error(":warning: Session Error: Missing credentials.")
        if st.button("Return to Portal"):
            st.switch_page("secret_code_portal.py")
        st.stop()


# ---------------------------------------------------------------------------
# Chat input + LLM call
# ---------------------------------------------------------------------------


def _personas_to_prompt_dict(personas: Dict[str, Any]) -> Dict[str, str]:
    """Accept either ``{name: prompt_str}`` or ``{name: {"system_prompt": str, ...}}``."""
    out: Dict[str, str] = {}
    for name, value in personas.items():
        if isinstance(value, str):
            out[name] = value
        elif isinstance(value, dict) and "system_prompt" in value:
            out[name] = value["system_prompt"]
        else:
            raise ValueError(f"persona {name!r} has unsupported shape: {type(value).__name__}")
    return out


def _handle_chat_turn(
    *,
    client: Groq,
    config: SessionConfig,
    persona_prompts: Dict[str, str],
) -> None:
    if st.session_state.get("evaluation_result") is not None:
        # Evaluation already produced; freeze the chat input.
        return

    user_prompt = st.chat_input("Your response...")
    if not user_prompt:
        return

    # Block in-conversation feedback requests; the student must click the
    # explicit Finish button to lock the transcript.
    blocked = ("feedback", "evaluate", "how did i do", "rate my performance", "score", "assessment")
    if any(token in user_prompt.lower() for token in blocked):
        st.warning("Feedback is provided after the conversation ends. Continue the conversation naturally.")
        return

    # Optional persona guard (off-topic + injection detection).
    guard_message = None
    try:
        from persona_guard import apply_guardrails
        needs_intervention, guard_message = apply_guardrails(
            user_prompt,
            config.domain_name,
            config.domain_keywords,
            turn_count=st.session_state.get("turn_count", 0),
        )
        if needs_intervention:
            logger.info("Guardrail intervention for: %r", user_prompt[:60])
    except ImportError:
        pass

    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    st.chat_message("user").markdown(user_prompt)
    st.session_state.turn_count += 1

    persona_name = st.session_state.selected_persona
    persona_system = persona_prompts[persona_name]

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": persona_system},
        {"role": "system", "content": PATIENT_TURN_RULES},
    ]
    if guard_message:
        messages.append(guard_message)
    messages.extend(st.session_state.chat_history)

    try:
        response = client.chat.completions.create(
            model=config.chat_model,
            messages=messages,
            max_tokens=250,
            temperature=0.7,
        )
        assistant_text = response.choices[0].message.content or ""
    except Exception as exc:
        msg = str(exc).lower()
        if "401" in msg or "invalid api key" in msg or "authentication" in msg:
            st.error("Invalid API key. Re-enter your Groq key on the portal and reload.")
            return
        raise

    # Light response sanitization: strip end-token artifacts.
    import re
    assistant_text = re.sub(r"<{1,2}\s*(?:END)?\s*>{1,2}", "", assistant_text).strip()

    st.session_state.chat_history.append({"role": "assistant", "content": assistant_text})
    with st.chat_message("assistant"):
        st.markdown(assistant_text)


# ---------------------------------------------------------------------------
# Evaluation + PDF rendering
# ---------------------------------------------------------------------------


def _generate_feedback(client: Groq, config: SessionConfig) -> None:
    """Call the evaluator, store the result, and surface errors clearly."""
    transcript_parts = [
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in st.session_state.chat_history
    ]
    transcript = "\n".join(transcript_parts)
    student_name = st.session_state.student_name

    timestamp = get_formatted_utc_time()
    try:
        result = evaluate_session(
            transcript=transcript,
            session_type=config.session_type,
            student_name=student_name,
            client=client,
            model=config.eval_model,
        )
    except EvaluationError as exc:
        logger.error("EvaluationError phase=%s: %s", exc.phase, exc)
        st.session_state.evaluation_error = (exc.phase, str(exc))
        st.session_state.evaluation_result = None
        return

    st.session_state.evaluation_result = result
    st.session_state.evaluation_timestamp = timestamp
    st.session_state.evaluation_error = None


def _render_feedback_section(config: SessionConfig) -> None:
    err = st.session_state.get("evaluation_error")
    if err:
        phase, message = err
        st.error(f"Evaluation failed (phase: {phase}). {message}")
        st.info("You can click 'Generate Feedback' again to retry, or contact your administrator.")
        return

    result: Optional[EvaluationResult] = st.session_state.get("evaluation_result")
    if not result:
        return

    st.markdown("### Feedback")
    if result["partial"]:
        st.warning("Partial report — manual review required. See appendix in the PDF for the raw evaluator response.")
    st.markdown(format_evaluation_for_display(result))

    # PDF download.
    try:
        pdf_bytes = generate_pdf_report(
            result,
            student_name=st.session_state.student_name,
            session_type=config.session_type,
            transcript=st.session_state.chat_history,
            timestamp_cst=st.session_state.evaluation_timestamp or get_formatted_utc_time(),
        )
        filename = construct_feedback_filename(
            st.session_state.student_name,
            config.bot_name_short,
            st.session_state.selected_persona,
        )
        st.download_button(
            label=f"Download {config.bot_name_short} MI Performance Report (PDF)",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
        )
    except Exception as exc:  # PDF rendering failure is rare but should not eat the screen.
        logger.exception("PDF generation failed")
        st.error(f"Could not generate PDF: {exc}")


# ---------------------------------------------------------------------------
# Persona selection UI
# ---------------------------------------------------------------------------


def _persona_selection(config: SessionConfig, persona_prompts: Dict[str, str]) -> None:
    if st.session_state.selected_persona is not None:
        return

    st.markdown("### Choose a Patient Persona")
    st.markdown(config.persona_descriptions_markdown)
    selected = st.selectbox(
        "Select a persona:",
        list(persona_prompts.keys()),
        key="persona_selector",
    )
    if st.button("Start Conversation"):
        st.session_state.selected_persona = selected
        st.session_state.chat_history = [{
            "role": "assistant",
            "content": f"Hello! I'm {selected}, nice to meet you today.",
        }]
        st.session_state.turn_count = 0
        st.rerun()
    st.stop()


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def run_practice_session(config: SessionConfig) -> None:
    """Render the full Streamlit page for one MI practice session."""
    st.set_page_config(page_title=config.page_title, page_icon=config.page_icon, layout="centered")
    render_environment_banner()
    _auth_guard(config.session_type)

    st.title(f"{config.page_icon} {config.page_title}")
    st.markdown(config.intro_markdown, unsafe_allow_html=True)

    # Initialize Groq client from session credentials. Pass the key directly
    # rather than mutating os.environ, which is process-global and would race
    # under concurrent users.
    client = Groq(api_key=st.session_state.groq_api_key)

    _initialize_state(config)
    persona_prompts = _personas_to_prompt_dict(config.personas)

    _persona_selection(config, persona_prompts)

    # Render existing chat history.
    for msg in st.session_state.chat_history or []:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Finish-session controls.
    col_a, col_b = st.columns([3, 1])
    with col_a:
        confirmed = st.checkbox(
            "I am ready to finish this session and receive feedback.",
            key="feedback_confirm",
        )
    with col_b:
        finish_clicked = st.button("Finish Session & Get Feedback")

    if finish_clicked:
        if not confirmed:
            st.warning("Please check the confirmation box first.")
        elif not st.session_state.chat_history or len(st.session_state.chat_history) < 2:
            st.warning("Have at least one exchange before requesting feedback.")
        else:
            with st.spinner("Evaluating your MI session..."):
                _generate_feedback(client, config)

    _render_feedback_section(config)

    # Chat input (disabled once evaluation is complete).
    _handle_chat_turn(client=client, config=config, persona_prompts=persona_prompts)

    # New session button.
    if st.button("Start New Conversation"):
        _reset_session()
        st.rerun()
