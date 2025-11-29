# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import CHAIN1_QUESTION_GENERATION_INSTRUCTION
from .models import Chain1Output

# Create Chain 1 question generation agent
chain1_agent = LlmAgent(
    name="chain1_question_generation_agent",
    model="gemini-2.5-flash",  # Change to available model if needed
    description=(
        "Chain 1: Generates 3 direct verification queries to check if the core factual claim occurred. "
        "Focuses on 'Did this event happen?' queries targeting official sources, exact phrase matches, "
        "and alternative phrasings."
    ),
    instruction=CHAIN1_QUESTION_GENERATION_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=Chain1Output,
    output_key="chain1_queries",
)

