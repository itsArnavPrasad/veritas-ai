# agent.py
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types
from typing import List, Dict, Any
import json
from datetime import datetime

from ...models import EvidenceItem
from .prompt import WEB_SEARCH_INSTRUCTION


# Create web search agent that uses Google Search tool
web_search_agent = LlmAgent(
    name="web_search_agent",
    model="gemini-2.5-flash",  # Change to available model if needed
    description=(
        "Web search agent using Google Search to retrieve evidence for fact-checking queries. "
        "Searches for relevant web pages, articles, and documents related to the query."
    ),
    instruction=WEB_SEARCH_INSTRUCTION,
    tools=[google_search],  # ADK built-in Google Search tool
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_key="web_search_results",
)

