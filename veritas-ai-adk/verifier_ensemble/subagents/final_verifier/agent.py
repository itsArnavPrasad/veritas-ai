# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from ...models import VerifierEnsembleOutput
from .prompt import FINAL_VERIFIER_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create final verifier agent (merges score combiner + final output)
final_verifier_agent = LlmAgent(
    name="final_verifier_agent",
    model=GEMINI_MODEL,
    description=(
        "Final Verifier: Combines evidence analysis results, calculates weighted scores, "
        "and produces final verification output with signal summary."
    ),
    instruction=FINAL_VERIFIER_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=VerifierEnsembleOutput,
    output_key="verifier_ensemble_result",
)

