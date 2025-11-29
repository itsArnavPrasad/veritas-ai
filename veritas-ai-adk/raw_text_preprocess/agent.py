# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import PREPROCESS_INSTRUCTION
from .models import PreprocessData

# Create the preprocessing LLM agent
preprocessing_agent = LlmAgent(
    name="preprocessing_agent",
    model="gemini-2.5-flash",  # change to available model in your environment if needed
    description=(
        "Preprocessing agent: extracts clean article body, metadata (title, author, published_at), "
        "entities, media references, snapshots and produces canonical JSON for downstream agents."
    ),
    instruction=PREPROCESS_INSTRUCTION,
    # deterministic config
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=PreprocessData,
    output_key="preprocess_data",
)
