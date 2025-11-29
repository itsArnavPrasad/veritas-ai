# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from ...models import WebSearchAnswerOutput
from .prompt import COMPREHENSIVE_ANSWER_SYNTHESIS_INSTRUCTION

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Create comprehensive answer synthesis agent
# This synthesizes answers from ALL 9 queries into one comprehensive, detailed answer
comprehensive_answer_synthesis_agent = LlmAgent(
    name="comprehensive_answer_synthesis_agent",
    model=GEMINI_MODEL,
    description=(
        "Comprehensive Answer Synthesis Agent: Synthesizes evidence from all 9 queries into a single, "
        "detailed, comprehensive answer. Combines all query results, identifies consensus, contradictions, "
        "and creates a perfect, detailed synthesis with source attribution."
    ),
    instruction=COMPREHENSIVE_ANSWER_SYNTHESIS_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=WebSearchAnswerOutput,
    output_key="comprehensive_search_results",
)

