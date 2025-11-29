# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from ...models import EvidenceEvaluation
from .prompt import SCORE_COMBINER_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create score combiner agent
score_combiner_agent = LlmAgent(
    name="score_combiner_agent",
    model=GEMINI_MODEL,
    description=(
        "Score combiner agent: Combines NLI, stance, source credibility, and temporal alignment scores "
        "into a single combined verification score with weighted contributions."
    ),
    instruction=SCORE_COMBINER_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=EvidenceEvaluation,
    output_key="combined_evaluation",
)

