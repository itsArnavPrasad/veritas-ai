# models.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class Claim(BaseModel):
    claim_id: Optional[str] = Field(
        None, description="Unique claim id (UUID recommended). If missing, agent may supply."
    )
    claim_text: str = Field(..., description="Atomic verifiable claim text (short and concise).")
    risk_hint: Optional[str] = Field(
        None,
        description="low/medium/high based on heuristics (keywords, entity types, public-safety).",
        example="high",
    )
    source_if_any: Optional[HttpUrl] = Field(None, description="If claim is itself citing a source URL, include it.")
    merged_from: Optional[List[str]] = Field(
        None,
        description="If this claim was merged from duplicates, list claim_ids/texts it was merged from (optional)."
    )


class ClaimExtractionOutput(BaseModel):
    doc_id: Optional[str] = Field(None, description="Source document id from preprocessor.")
    extracted_by: Optional[str] = Field("claim_extractor_agent", description="Agent name/version")
    extraction_time: Optional[str] = Field(None, description="ISO-8601 timestamp when extraction completed.")
    claims: List[Claim] = Field(..., max_length=3, min_length=1, description="Array of exactly 3 most important atomic claims.")
    notes: Optional[str] = Field(None, description="Processing notes, including dedupe/heuristics summary.")
    version: Optional[str] = Field("claim-extractor-v1.0")
