# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import CLAIM_EXTRACTION_INSTRUCTION
from .models import ClaimExtractionOutput

# create the claim extractor agent
claim_extractor_agent = LlmAgent(
    name="claim_extractor_agent",
    model="gemini-2.5-flash",  # swap if another model is required/available
    description=(
        "Extracts exactly 3 most important, atomic, verifiable claims from canonical article text. "
        "Selects the top claims that best represent core content. Outputs structured JSON with claim text, risk_hint."
    ),
    instruction=CLAIM_EXTRACTION_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=ClaimExtractionOutput,
    output_key="claim_extraction",
)
