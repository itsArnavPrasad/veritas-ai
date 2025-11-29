# agent.py
# Coordinator/Orchestration Agent for Text Verification Module
# Follows https://google.github.io/adk-docs/get-started/quickstart/ for setup details

# Configure logging BEFORE importing ADK to suppress verbose logs
import sys
import os

# Ensure the agents directory (parent of coordinator) is in sys.path
# This handles the case when ADK loads coordinator as a top-level module
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_dir = os.path.dirname(current_dir)
if agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)

# Import logging configuration to suppress verbose ADK logs
try:
    import logging_config  # This will configure logging to suppress INFO logs from ADK
except ImportError:
    # If logging_config is not found, configure logging here
    import logging
    logging.getLogger('google.adk').setLevel(logging.WARNING)
    logging.getLogger('google_llm').setLevel(logging.WARNING)

from google.adk.agents import SequentialAgent, LlmAgent
from google.genai import types

# Import all agent components
# ADK adds the agents directory to sys.path when loading, so we use absolute imports

# Now import using absolute imports (relative to agents directory)
from raw_text_preprocess.agent import preprocessing_agent
from claim_extraction.agent import claim_extractor_agent
from severity_source_suggester.agent import severity_source_suggester_agent
from question_generation.agent import question_generation_agent
from web_search_answer.agent import web_search_answer_agent
from web_search_answer.subagents.comprehensive_answer_synthesis.agent import comprehensive_answer_synthesis_agent
from verifier_ensemble.agent import verifier_ensemble_agent

# Model configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Claims combiner agent: Extracts all 3 claims and combines them for processing
# Outputs in format compatible with downstream agents (claim_id, claim_text, entities)
claims_combiner = LlmAgent(
    name="claims_combiner",
    model=GEMINI_MODEL,
    instruction="""You are a claims combiner agent. Your task is to extract all 3 claims from the claim_extraction data and combine them into a single unified claim for processing.

Your input message will contain claim_extraction data (from the previous agent in the pipeline). This data contains a "claims" array with exactly 3 claims.

Extract all 3 claims from the input and combine them:
1. Get claim_id and claim_text from each of the 3 claims in the claims array
2. Combine all claim texts into a single coherent text that represents all claims together
3. Create a combined_claim_id (e.g., "combined-c-1-2-3")
4. Extract all unique entities from all 3 claims and combine into one list

Output a JSON object with these fields (format compatible with downstream agents):
- claim_id: A single ID for the combined claims (e.g., "combined-c-1-2-3")
- claim_text: All 3 claim texts combined into one coherent text that captures all claims together
- entities: List of all unique entities extracted from all 3 claims

The combined claim_text should be a coherent representation of all 3 claims together, not just concatenated. Make it flow naturally as a single unified claim that encompasses all three original claims.

Return only the JSON object with these three fields: claim_id, claim_text, entities.
""",
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_key="combined_claims",
)

# Main claim verification orchestrator that processes all claims together
# This processes the combined claims through: severity → question generation → web search → verifier
claim_verification_orchestrator = SequentialAgent(
    name="claim_verification_orchestrator",
    description=(
        "Claim Verification Orchestrator: Processes all extracted claims together as a combined unit. "
        "Sequential execution: Claims Combination → Severity/Source Suggestion → Question Generation → "
        "Web Search → Comprehensive Answer Synthesis → Verifier Ensemble. "
        "All 3 claims are merged and processed together in a single continuous pipeline run."
    ),
    sub_agents=[
        claims_combiner,                      # Step 0: Combine all 3 claims into one
        severity_source_suggester_agent,     # Step 1: Analyze severity and suggest source pools (uses combined claim)
        question_generation_agent,           # Step 2: Generate 9 queries based on combined claims
        web_search_answer_agent,             # Step 3: Retrieve evidence for all 9 queries
        comprehensive_answer_synthesis_agent, # Step 4: Synthesize comprehensive answer from all queries
        verifier_ensemble_agent,             # Step 5: Verify combined claims vs evidence
    ],
)

# Main pipeline: Sequential orchestration of the complete workflow
fact_checking_pipeline = SequentialAgent(
    name="fact_checking_pipeline",
    description=(
        "Complete Text Verification Pipeline: End-to-end fact-checking workflow. "
        "Sequential execution: Preprocessing → Claim Extraction → Claim Verification (all claims together). "
        "All claims are processed simultaneously in a single pipeline run."
    ),
    sub_agents=[
        preprocessing_agent,              # Step 1: Preprocess raw text/document
                                          # Output: preprocess_data (stored in state)
        claim_extractor_agent,            # Step 2: Extract claims from preprocessed text
                                          # Output: claim_extraction (stored in state, contains all 3 claims)
        claim_verification_orchestrator,  # Step 3: Verify all claims together
                                          # Input: Accesses claim_extraction from state
                                          # Output: Aggregated verification results for all claims
    ],
)

# Root coordinator agent exposed for ADK usage
root_agent = fact_checking_pipeline

