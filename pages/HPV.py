"""HPV MI Practice page — thin shell over mi_session.run_practice_session."""

from mi_session import SessionConfig, run_practice_session
from persona_texts import HPV_DOMAIN_KEYWORDS, HPV_DOMAIN_NAME, HPV_PERSONAS


INTRO = (
    "Welcome to the **HPV MI Practice App**. This chatbot simulates a realistic "
    "patient who is uncertain about HPV vaccination. Practice your "
    "**Motivational Interviewing** skills by engaging in a natural conversation; "
    "you'll receive **detailed feedback** based on the official 40-point MI rubric "
    "when you finish the session."
)

PERSONA_DESCRIPTIONS = """Select a patient persona to practice with:

- **Alex**: 25-year-old barista, single, urban resident
- **Bob**: 19-year-old college student studying business
- **Charlie**: 30-year-old parent and middle school teacher
- **Diana**: 22-year-old recent graduate working in retail
"""


run_practice_session(SessionConfig(
    session_type="HPV",
    page_title="HPV MI Practice",
    page_icon="💉",
    intro_markdown=INTRO,
    personas=HPV_PERSONAS,
    persona_descriptions_markdown=PERSONA_DESCRIPTIONS,
    domain_name=HPV_DOMAIN_NAME,
    domain_keywords=HPV_DOMAIN_KEYWORDS,
    rubric_dir_name="hpv_rubrics",
    bot_name_short="HPV",
    evaluator_label="HPV Assessment Bot",
))
