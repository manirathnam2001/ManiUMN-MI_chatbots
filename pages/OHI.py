"""OHI MI Practice page — thin shell over mi_session.run_practice_session."""

from mi_session import SessionConfig, run_practice_session
from persona_texts import OHI_DOMAIN_KEYWORDS, OHI_DOMAIN_NAME, OHI_PERSONAS


INTRO = (
    "Welcome to the **OHI MI Practice App**. This chatbot simulates a realistic "
    "patient who is uncertain about oral hygiene recommendations. Practice your "
    "**Motivational Interviewing** skills by engaging in a natural conversation; "
    "you'll receive **detailed feedback** based on the official 40-point MI rubric "
    "when you finish the session."
)

PERSONA_DESCRIPTIONS = """Select a patient persona to practice with:

- **Alex**: 28-year-old marketing professional with mixed oral hygiene habits
- **Bob**: 25-year-old software developer, introverted with poor oral hygiene
- **Charles**: 35-year-old executive with good oral hygiene habits
- **Diana**: 31-year-old retail manager with average habits and resistant attitude
"""


run_practice_session(SessionConfig(
    session_type="OHI",
    page_title="OHI MI Practice",
    page_icon="🦷",
    intro_markdown=INTRO,
    personas=OHI_PERSONAS,
    persona_descriptions_markdown=PERSONA_DESCRIPTIONS,
    domain_name=OHI_DOMAIN_NAME,
    domain_keywords=OHI_DOMAIN_KEYWORDS,
    rubric_dir_name="ohi_rubrics",
    bot_name_short="OHI",
    evaluator_label="OHI Assessment Bot",
))
