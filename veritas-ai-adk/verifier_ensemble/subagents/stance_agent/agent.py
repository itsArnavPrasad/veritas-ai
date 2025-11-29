# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from ...models import StanceResult
from .prompt import STANCE_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create stance detection agent
stance_agent = LlmAgent(
    name="stance_agent",
    model=GEMINI_MODEL,
    description=(
        "Stance detection agent: Classifies whether a document/passage supports, opposes, or is neutral "
        "toward a claim. Considers author intent and overall document sentiment."
    ),
    instruction=STANCE_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=StanceResult,
    output_key="stance_result",
)

