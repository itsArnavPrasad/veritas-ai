# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import SOURCE_CREDIBILITY_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create source credibility agent
source_credibility_agent = LlmAgent(
    name="source_credibility_agent",
    model=GEMINI_MODEL,
    description=(
        "Source credibility agent: Evaluates the credibility and trustworthiness of a source domain "
        "based on domain reputation, source type, and known fact-checking indicators."
    ),
    instruction=SOURCE_CREDIBILITY_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_key="source_credibility_score",
)

