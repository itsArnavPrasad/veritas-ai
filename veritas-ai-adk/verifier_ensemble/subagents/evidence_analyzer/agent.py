# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .models import EvidenceAnalysisOutput
from .prompt import EVIDENCE_ANALYZER_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create evidence analyzer agent (merges NLI, Stance, Source Credibility, Temporal)
evidence_analyzer_agent = LlmAgent(
    name="evidence_analyzer_agent",
    model=GEMINI_MODEL,
    description=(
        "Evidence Analyzer: Analyzes all evidence items against claims using NLI, stance detection, "
        "source credibility, and temporal alignment in a single pass."
    ),
    instruction=EVIDENCE_ANALYZER_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=EvidenceAnalysisOutput,
    output_key="evidence_analysis",
)

