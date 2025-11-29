# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from ...models import TemporalAlignment
from .prompt import TEMPORAL_ALIGNMENT_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create temporal alignment agent
temporal_agent = LlmAgent(
    name="temporal_agent",
    model=GEMINI_MODEL,
    description=(
        "Temporal alignment agent: Checks if evidence temporally aligns with claims that have time-sensitive elements. "
        "Verifies dates, timeframes, and chronological consistency."
    ),
    instruction=TEMPORAL_ALIGNMENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=TemporalAlignment,
    output_key="temporal_alignment_result",
)

