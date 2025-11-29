# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from ...models import NLIResult
from .prompt import NLI_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create NLI agent for Natural Language Inference
nli_agent = LlmAgent(
    name="nli_agent",
    model=GEMINI_MODEL,
    description=(
        "Natural Language Inference agent: Determines if a passage entails, contradicts, or is neutral "
        "with respect to a claim. Outputs label (entailment/contradiction/neutral) and confidence score."
    ),
    instruction=NLI_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=NLIResult,
    output_key="nli_result",
)

