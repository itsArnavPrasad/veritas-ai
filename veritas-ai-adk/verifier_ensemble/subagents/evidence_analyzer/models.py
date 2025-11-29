# models.py
from pydantic import BaseModel, Field
from typing import List, Optional

from ...models import NLIResult, StanceResult, TemporalAlignment


class EvidenceAnalysisResult(BaseModel):
    """Complete analysis result for a single evidence item."""
    evidence_id: str = Field(..., description="Evidence identifier")
    cluster_id: Optional[str] = Field(None, description="Optional cluster identifier")
    nli: NLIResult = Field(..., description="Natural Language Inference result")
    stance: StanceResult = Field(..., description="Stance detection result")
    domain_credibility: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Domain credibility score [0-1]"
    )
    temporal_alignment: Optional[TemporalAlignment] = Field(
        None,
        description="Temporal alignment check result"
    )


class EvidenceAnalysisOutput(BaseModel):
    """Output schema for evidence analyzer agent - contains analysis for all evidence items."""
    claim_id: str = Field(..., description="Claim identifier")
    claim_text: str = Field(..., description="Claim text")
    comprehensive_answer: Optional[str] = Field(
        None,
        description="Comprehensive synthesized answer from all queries (preserved from comprehensive_answer_synthesis_agent for final output visibility)"
    )
    analyses: List[EvidenceAnalysisResult] = Field(
        ...,
        description="Analysis results for all evidence items"
    )

