# agent.py
from google.adk.agents import LlmAgent
from google.genai import types

from .prompt import SEVERITY_SOURCE_SUGGESTER_INSTRUCTION
from .models import SeveritySourceSuggestionOutput

# Create the severity and source suggester agent
severity_source_suggester_agent = LlmAgent(
    name="severity_source_suggester_agent",
    model="gemini-2.5-flash",  # Change to available model in your environment if needed
    description=(
        "Severity and source suggester agent: analyzes claim severity/harm category "
        "(political, health, finance, public-safety, etc.) and recommends prioritized "
        "trusted source pools (government domains, major outlets, fact-checks) and "
        "social platforms (X, Reddit, Instagram, TikTok) for verification and monitoring."
    ),
    instruction=SEVERITY_SOURCE_SUGGESTER_INSTRUCTION,
    # Deterministic config
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=SeveritySourceSuggestionOutput,
    output_key="severity_source_suggestion",
)

