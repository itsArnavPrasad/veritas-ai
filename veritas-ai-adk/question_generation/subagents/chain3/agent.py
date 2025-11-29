# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import CHAIN3_QUESTION_GENERATION_INSTRUCTION
from .models import Chain3Output

# Create Chain 3 question generation agent
chain3_agent = LlmAgent(
    name="chain3_question_generation_agent",
    model="gemini-2.5-flash",  # Change to available model if needed
    description=(
        "Chain 3: Generates 3 disambiguation and contradiction resolution queries to verify actor identity, "
        "clarify regional/local scope, check for prior similar events, and resolve ambiguities from earlier chains."
    ),
    instruction=CHAIN3_QUESTION_GENERATION_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=Chain3Output,
    output_key="chain3_queries",
)

