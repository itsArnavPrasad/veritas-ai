# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from ...models import SynthesizedAnswer
from .prompt import ANSWER_SYNTHESIS_INSTRUCTION

# Create answer synthesis agent
answer_synthesis_agent = LlmAgent(
    name="answer_synthesis_agent",
    model="gemini-2.5-flash",  # Can use a larger model if available
    description=(
        "Answer synthesis agent that combines evidence from web search, Instagram, and Twitter "
        "into a coherent, synthesized answer for a fact-checking query. Identifies key information, "
        "resolves contradictions, and provides a comprehensive response."
    ),
    instruction=ANSWER_SYNTHESIS_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=SynthesizedAnswer,
    output_key="synthesized_answer",
)

