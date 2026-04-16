"""Tobacco MI Practice page — thin shell over mi_session.run_practice_session."""

from mi_session import SessionConfig, run_practice_session
from persona_texts import TOBACCO_DOMAIN_KEYWORDS, TOBACCO_DOMAIN_NAME, TOBACCO_PERSONAS


INTRO = (
    "Welcome to the **Tobacco Cessation MI Practice App**. This chatbot simulates a "
    "realistic patient considering tobacco cessation. Practice your "
    "**Motivational Interviewing** skills by engaging in a natural conversation; "
    "you'll receive **detailed feedback** based on the official 40-point MI rubric "
    "when you finish the session."
)

PERSONA_DESCRIPTIONS = """Select a patient persona to practice with:

- **Alex**: 50-year-old male smoker interested in quitting
- **Bob**: 24-year-old female vaper resistant to quitting
- **Charles**: 32-year-old social smoker who is ambivalent
- **Diana**: 45-year-old former smoker concerned about relapse
"""


run_practice_session(SessionConfig(
    session_type="Tobacco",
    page_title="Tobacco MI Practice",
    page_icon="🚭",
    intro_markdown=INTRO,
    personas=TOBACCO_PERSONAS,
    persona_descriptions_markdown=PERSONA_DESCRIPTIONS,
    domain_name=TOBACCO_DOMAIN_NAME,
    domain_keywords=TOBACCO_DOMAIN_KEYWORDS,
    rubric_dir_name="tobacco_rubrics",
    bot_name_short="Tobacco",
    evaluator_label="Tobacco Assessment Bot",
))
