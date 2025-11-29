# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class NLIResult(BaseModel):
    """Natural Language Inference result."""
    label: str = Field(
        ...,
        description="NLI label: entailment, contradiction, or neutral",
        example="contradiction"
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score [0-1] for the NLI label"
    )
    rationale: Optional[str] = Field(None, description="Brief explanation of the NLI judgment")


class StanceResult(BaseModel):
    """Stance detection result."""
    label: str = Field(
        ...,
        description="Stance label: support, oppose, or neutral",
        example="deny"
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score [0-1] for the stance label"
    )
    rationale: Optional[str] = Field(None, description="Brief explanation of the stance judgment")


class TemporalAlignment(BaseModel):
    """Temporal alignment checking result."""
    ok: bool = Field(..., description="Whether the evidence temporally aligns with the claim")
    reason: Optional[str] = Field(None, description="Explanation of temporal alignment or misalignment")
    time_difference_days: Optional[int] = Field(None, description="Time difference in days if misaligned")


class EvidenceEvaluation(BaseModel):
    """Evaluation of a single evidence item against a claim."""
    evidence_id: str = Field(..., description="Unique evidence identifier")
    cluster_id: Optional[str] = Field(None, description="Cluster identifier if evidence is clustered")
    nli: NLIResult = Field(..., description="Natural Language Inference result")
    stance: StanceResult = Field(..., description="Stance detection result")
    domain_credibility: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Domain credibility score [0-1], higher is more credible"
    )
    temporal_alignment: Optional[TemporalAlignment] = Field(None, description="Temporal alignment check result")
    combined_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Combined verification score [0-1] from weighted combination of all signals"
    )
    # Note: weight_breakdown field removed to avoid additionalProperties in Gemini API schema
    # Weight information can be included in processing_notes if needed


class SignalSummary(BaseModel):
    """Summary of verification signals across all evidence."""
    num_supporting: int = Field(..., description="Number of evidence items supporting the claim")
    num_contradicting: int = Field(..., description="Number of evidence items contradicting the claim")
    num_neutral: int = Field(default=0, description="Number of neutral evidence items")
    support_weighted: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted support score [0-1], accounting for source credibility"
    )
    contradict_weighted: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted contradiction score [0-1], accounting for source credibility"
    )
    neutral_weighted: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Weighted neutral score [0-1]"
    )
    top_credible_sources: Optional[List[str]] = Field(
        None,
        description="List of evidence IDs from most credible sources"
    )


class VerifierEnsembleInput(BaseModel):
    """Input schema for the verifier ensemble agent."""
    claim_id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., description="The claim text to verify")
    claim_type: Optional[List[str]] = Field(
        None,
        description="Claim types from claim extractor (policy, temporal, geographic, etc.)"
    )
    entities: Optional[List[str]] = Field(
        None,
        description="Entities mentioned in the claim"
    )
    # Note: clusters, evidence_items, and query_results fields removed to avoid additionalProperties in Gemini API schema
    # These should be passed as structured objects or accessed from state


class ClaimFinding(BaseModel):
    """Finding for a single claim with truth score and sources."""
    claim_text: str = Field(..., description="The claim that was verified")
    finding: str = Field(..., description="What was discovered about the claim (e.g., 'No bomb was blasted at IIT Bombay')")
    sources: List[str] = Field(..., description="List of source names where the finding came from (e.g., ['BBC', 'Reuters', 'IIT Bombay Official Statement'])")
    truth_score: float = Field(..., ge=0.0, le=1.0, description="Truth score: 0.0 = False/Misinformation, 1.0 = True, 0.5 = Unclear/Mixed")
    supporting_evidence_count: int = Field(default=0, description="Number of evidence items supporting this finding")
    contradicting_evidence_count: int = Field(default=0, description="Number of evidence items contradicting this finding")


class MisinformationAnalysis(BaseModel):
    """Overall misinformation analysis based on all individual claim findings."""
    overall_truth_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average truth score across all 3 individual claims [0-1]"
    )
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the analysis [0-1], based on source credibility and consensus"
    )
    misinformation_likelihood: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Likelihood that content contains misinformation [0-1], where 1.0 = high likelihood of misinformation"
    )
    verdict: str = Field(
        ...,
        description="Overall verdict: 'LIKELY_FALSE', 'LIKELY_TRUE', 'MIXED', or 'INCONCLUSIVE'"
    )
    primary_sources: List[str] = Field(
        ...,
        description="List of primary credible sources used in analysis across all claims"
    )


class VerifierEnsembleOutput(BaseModel):
    """Output schema for the verifier ensemble agent."""
    verification_timestamp: str = Field(
        ...,
        description="ISO-8601 timestamp when verification was completed (current date/time in UTC)"
    )
    comprehensive_answer: Optional[str] = Field(
        None,
        description="Comprehensive synthesized answer from all queries (from comprehensive_answer_synthesis_agent)"
    )
    individual_claim_findings: List[ClaimFinding] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Findings for each of the 3 individual claims, with separate truth scores and sources"
    )
    misinformation_analysis: MisinformationAnalysis = Field(
        ...,
        description="Overall misinformation analysis based on all individual claim findings"
    )
    verifier_version: str = Field(default="ensemble-v2.0", description="Agent version identifier")
    processing_notes: Optional[str] = Field(
        None,
        description="Brief notes about the verification process and key insights"
    )
    # Note: evidence_evaluations and signal_summary removed from final output to simplify
    # These are still used internally but not exposed in final schema

