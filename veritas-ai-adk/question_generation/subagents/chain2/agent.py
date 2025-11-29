# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import CHAIN2_QUESTION_GENERATION_INSTRUCTION
from .models import Chain2Output

# Create Chain 2 question generation agent
chain2_agent = LlmAgent(
    name="chain2_question_generation_agent",
    model="gemini-2.5-flash",  # Change to available model if needed
    description=(
        "Chain 2: Generates 3 context and detail queries to investigate WHO, WHAT, WHEN, WHERE, HOW, "
        "and SCOPE of the claim. Focuses on legal instruments, affected parties, timeframe, and exemptions."
    ),
    instruction=CHAIN2_QUESTION_GENERATION_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=Chain2Output,
    output_key="chain2_queries",
)

