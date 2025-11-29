"""
Results endpoints
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from services.database import get_db
from models.verification import Verification
from services.storage import (
    read_results_json,
    read_text_analysis_json,
    read_image_analysis_json,
    read_video_analysis_json,
    read_fusion_results_json
)

router = APIRouter()


@router.get("/result/{verification_id}")
async def get_result(
    verification_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get verification results
    """
    # Get verification from database
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Read all analysis files (only those that exist)
    text_analysis = await read_text_analysis_json(verification_id)
    image_analysis = await read_image_analysis_json(verification_id)
    video_analysis = await read_video_analysis_json(verification_id)
    fusion_results = await read_fusion_results_json(verification_id)
    
    # Check if any results exist
    has_results = text_analysis or image_analysis or video_analysis or fusion_results
    
    if not has_results:
        # Try to read legacy results.json for backward compatibility
        legacy_results = await read_results_json(verification_id)
        if legacy_results:
            return {
                "verification_id": str(verification_id),
                "status": legacy_results.get("status", verification.status.value),
                "timestamp": legacy_results.get("timestamp"),
                "fusion_results": legacy_results.get("fusion_results", {}),
                "all_outputs": legacy_results.get("all_outputs", {})
            }
        
        # Return basic status if results not ready
        return {
            "verification_id": str(verification_id),
            "status": verification.status.value,
            "message": "Results not yet available"
        }
    
    # Get timestamp from fusion results or use current time
    timestamp = fusion_results.get("fusion_timestamp") if fusion_results else datetime.utcnow().isoformat()
    
    # Return results from separate files
    return {
        "verification_id": str(verification_id),
        "status": verification.status.value if verification.status.value == "done" else "done",
        "timestamp": timestamp,
        # Individual analysis results
        "text_analysis": text_analysis,
        "image_analysis": image_analysis,
        "video_analysis": video_analysis,
        "fusion_results": fusion_results
    }

