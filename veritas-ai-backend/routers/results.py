"""
Results endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from services.database import get_db
from models.verification import Verification
from services.storage import read_results_json, read_claims_json

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
    
    # Try to read results from storage
    results = await read_results_json(verification_id)
    
    if not results:
        # Return basic status if results not ready
        return {
            "verification_id": str(verification_id),
            "status": verification.status.value,
            "message": "Results not yet available"
        }
    
    # Return full results
    return {
        "verification_id": str(verification_id),
        "status": results.get("status", verification.status.value),
        "verdict": results.get("verdict"),
        "confidence": results.get("confidence"),
        "claims": results.get("claims", []),
        "media_analysis": results.get("media_analysis", {}),
        "evidence": results.get("evidence", {}),
        "explanation": results.get("explanation", "")
    }

