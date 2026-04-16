"""Perio MI Practice page — thin shell over mi_session.run_practice_session."""

from mi_session import SessionConfig, run_practice_session
from persona_texts import PERIO_DOMAIN_KEYWORDS, PERIO_DOMAIN_NAME, PERIO_PERSONAS


INTRO = (
    "Welcome to the **Perio MI Practice App**. This chatbot simulates a realistic "
    "patient with periodontal concerns. Practice your **Motivational Interviewing** "
    "skills by engaging in a natural conversation; you'll receive **detailed feedback** "
    "based on the official 40-point MI rubric when you finish the session."
)

PERSONA_DESCRIPTIONS = """Select a patient persona to practice with — each represents a different stage of periodontal disease:

- **Alex**: Early gingivitis — at a cleaning appointment, noticing bleeding gums
- **Bob**: Early periodontitis — new patient, recently diagnosed, nervous about treatment
- **Charles**: Disease management — maintenance appointment, struggling with consistency
- **Diana**: Advanced disease — appointment to discuss bone loss and treatment options
"""


run_practice_session(SessionConfig(
    session_type="Perio",
    page_title="Perio MI Practice",
    page_icon="🦷",
    intro_markdown=INTRO,
    personas=PERIO_PERSONAS,
    persona_descriptions_markdown=PERSONA_DESCRIPTIONS,
    domain_name=PERIO_DOMAIN_NAME,
    domain_keywords=PERIO_DOMAIN_KEYWORDS,
    rubric_dir_name="perio_rubrics",
    bot_name_short="Perio",
    evaluator_label="Perio Assessment Bot",
))
