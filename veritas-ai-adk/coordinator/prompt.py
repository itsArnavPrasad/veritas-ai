# prompt.py
COORDINATOR_INSTRUCTION = """
This is the main Fact-Checking Coordinator Agent that orchestrates the complete text verification pipeline.

The coordinator executes a SequentialAgent workflow with the following stages:

**MAIN PIPELINE (fact_checking_pipeline):**

1. **Preprocessing Agent**
   - Preprocesses raw text/document
   - Extracts clean article body, metadata (title, author, published_at)
   - Identifies entities and language
   - Output: preprocess_data (stored in session state)

2. **Claim Extraction Agent**
   - Extracts exactly 3 most important, atomic, verifiable claims from canonical text
   - Each claim includes: claim_text, risk_hint
   - Output: claim_extraction (stored in session state, contains all 3 claims)

3. **Claim Verification Orchestrator** (processes all 3 claims together as a combined unit):
   
   a. **Claims Combiner**
      - Combines all 3 extracted claims into a single unified claim
      - Merges claim texts and entities into one coherent representation
      - Output: combined_claims
   
   b. **Severity/Source Suggester Agent**
      - Analyzes claim severity/harm category (political, health, finance, public-safety, etc.)
      - Recommends prioritized trusted source pools (government domains, major outlets, fact-checks)
      - Suggests relevant social platforms to monitor
      - Generates Google search site filters
      - Output: severity_source_suggestion
   
   c. **Question Generation Agent** (generates 6 queries in 3 sequential chains):
      - Chain 1: 2 direct verification queries (q1, q2) - "Did this event happen?"
      - Chain 2: 2 context/detail queries (q3, q4) - "What are the details?"
      - Chain 3: 2 disambiguation queries (q5, q6) - "Are there contradictions?"
      - Output: 6 queries total (q1 through q6)
   
   d. **Web Search Answer Agent** (retrieves evidence for all 6 queries):
      - Processes all 6 queries in parallel through query processors
      - Each query processor runs: web search → Instagram search → Twitter search → answer synthesis (per query)
      - Merges all query results into structured evidence format
      - Output: web_search_results (all evidence items from all queries)
   
   e. **Comprehensive Answer Synthesis Agent**
      - Synthesizes evidence from ALL 6 queries into a single, detailed, comprehensive answer
      - Creates a perfect, detailed synthesis that covers all aspects from all queries
      - Lists source names prominently (e.g., "According to Reuters, BBC, RBI Official Site...")
      - Identifies consensus points and contradictions across all queries
      - Includes specific details: dates, locations, entities, numbers
      - Preserves all evidence items for verification
      - Output: comprehensive_search_results (with comprehensive_answer field)
   
   f. **Verifier Ensemble Agent** (verifies combined claims against all evidence):
      - Evidence Analyzer: Analyzes all evidence items using 4 signals:
        * NLI (Natural Language Inference): entailment/contradiction/neutral
        * Stance Detection: support/oppose/neutral
        * Source Credibility: domain trustworthiness score
        * Temporal Alignment: date/time consistency check
      - Final Verifier: Combines all analysis results and calculates weighted verification scores
      - Produces final verification output with evidence evaluations and signal summary
      - Output: verifier_ensemble_result

**Key Features:**
- All 3 claims are processed together in a single continuous pipeline run (no separate verification)
- Claims are merged before verification to ensure comprehensive analysis
- All 6 queries are processed in parallel for faster processing
- Comprehensive answer synthesis ensures detailed, perfect answers from all evidence
- Final verification uses advanced scoring system with strong source comparison for accurate misinformation detection

Each step passes results via shared session state using output_key values.
"""

