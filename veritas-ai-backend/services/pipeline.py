"""
Verification pipeline service
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session

from models.verification import Verification, VerificationStatus, InputType
from services.storage import (
    create_verification_storage,
    save_claims_json,
    save_results_json,
    append_log
)
from services.database import SessionLocal
from config import PIPELINE_STAGES

# Global dictionary to store SSE event callbacks
sse_callbacks: Dict[str, Callable] = {}


def register_sse_callback(verification_id: str, callback: Callable):
    """Register a callback for SSE events"""
    sse_callbacks[verification_id] = callback


def unregister_sse_callback(verification_id: str):
    """Unregister SSE callback"""
    sse_callbacks.pop(verification_id, None)


async def send_sse_event(verification_id: str, stage: str, progress: float, message: str, data: Optional[Dict] = None):
    """Send SSE event to registered callback"""
    if verification_id in sse_callbacks:
        callback = sse_callbacks[verification_id]
        event_data = {
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        try:
            await callback(event_data)
        except Exception as e:
            print(f"Error sending SSE event: {e}")


async def preprocess(verification_id: uuid.UUID, input_type: InputType, db: Session) -> Dict[str, Any]:
    """Preprocessing stage"""
    await send_sse_event(
        str(verification_id),
        "preprocessing",
        10.0,
        "Starting preprocessing..."
    )
    
    await append_log(verification_id, {
        "stage": "preprocessing",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Starting preprocessing"
    })
    
    await asyncio.sleep(1)  # Simulate processing
    
    result = {
        "preprocessed": True,
        "input_type": input_type.value,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await send_sse_event(
        str(verification_id),
        "preprocessing",
        20.0,
        "Preprocessing complete"
    )
    
    return result


async def extract_claims(verification_id: uuid.UUID, db: Session) -> list:
    """Extract claims from input"""
    await send_sse_event(
        str(verification_id),
        "claim_extraction",
        30.0,
        "Extracting claims..."
    )
    
    await append_log(verification_id, {
        "stage": "claim_extraction",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Extracting claims from input"
    })
    
    await asyncio.sleep(1)  # Simulate processing
    
    # Mock claims
    claims = [
        {
            "id": str(uuid.uuid4()),
            "text": "Sample claim 1: This is a test claim for verification.",
            "verdict": None,
            "confidence": None,
            "evidence": None
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Sample claim 2: Another test claim to verify.",
            "verdict": None,
            "confidence": None,
            "evidence": None
        }
    ]
    
    await save_claims_json(verification_id, claims)
    
    await send_sse_event(
        str(verification_id),
        "claim_extraction",
        40.0,
        f"Extracted {len(claims)} claims"
    )
    
    return claims


async def run_retrieval(verification_id: uuid.UUID, claims: list, db: Session) -> Dict[str, Any]:
    """Run retrieval stage"""
    await send_sse_event(
        str(verification_id),
        "retrieval",
        50.0,
        "Retrieving evidence..."
    )
    
    await append_log(verification_id, {
        "stage": "retrieval",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Retrieving evidence from knowledge base"
    })
    
    await asyncio.sleep(1)  # Simulate processing
    
    result = {
        "retrieved_sources": 5,
        "evidence_count": 10,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await send_sse_event(
        str(verification_id),
        "retrieval",
        60.0,
        f"Retrieved {result['retrieved_sources']} sources"
    )
    
    return result


async def run_forensics(verification_id: uuid.UUID, db: Session) -> Dict[str, Any]:
    """Run forensics analysis"""
    await send_sse_event(
        str(verification_id),
        "forensics",
        70.0,
        "Running forensic analysis..."
    )
    
    await append_log(verification_id, {
        "stage": "forensics",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Running forensic analysis on media"
    })
    
    await asyncio.sleep(1)  # Simulate processing
    
    result = {
        "media_analysis": {
            "authenticity": "verified",
            "manipulation_detected": False,
            "confidence": 0.95
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await send_sse_event(
        str(verification_id),
        "forensics",
        80.0,
        "Forensic analysis complete"
    )
    
    return result


async def judge(verification_id: uuid.UUID, claims: list, db: Session) -> Dict[str, Any]:
    """Final judgment stage"""
    await send_sse_event(
        str(verification_id),
        "consistency",
        85.0,
        "Analyzing consistency..."
    )
    
    await append_log(verification_id, {
        "stage": "consistency",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Analyzing claim consistency"
    })
    
    await asyncio.sleep(1)  # Simulate processing
    
    await send_sse_event(
        str(verification_id),
        "final_verdict",
        90.0,
        "Generating final verdict..."
    )
    
    await append_log(verification_id, {
        "stage": "final_verdict",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Generating final verdict"
    })
    
    await asyncio.sleep(1)  # Simulate processing
    
    # Mock verdict
    verdict = {
        "verdict": "likely_false",
        "confidence": 0.87,
        "explanation": "Multiple claims were found to be inconsistent with verified sources.",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await send_sse_event(
        str(verification_id),
        "final_verdict",
        100.0,
        "Verification complete"
    )
    
    return verdict


async def write_results_json(verification_id: uuid.UUID, results: Dict[str, Any]) -> None:
    """Write final results to JSON"""
    await save_results_json(verification_id, results)


async def run_pipeline(
    verification_id: uuid.UUID,
    input_type: InputType
) -> None:
    """Run the complete verification pipeline"""
    # Create a new database session for the background task
    db = SessionLocal()
    try:
        # Update status to processing
        verification = db.query(Verification).filter(Verification.id == verification_id).first()
        if not verification:
            raise ValueError(f"Verification {verification_id} not found")
        
        verification.status = VerificationStatus.PROCESSING
        db.commit()
        
        # Create storage directories
        create_verification_storage(verification_id)
        
        # Run pipeline stages
        preprocess_result = await preprocess(verification_id, input_type, db)
        claims = await extract_claims(verification_id, db)
        retrieval_result = await run_retrieval(verification_id, claims, db)
        forensics_result = await run_forensics(verification_id, db)
        verdict = await judge(verification_id, claims, db)
        
        # Compile final results
        final_results = {
            "verification_id": str(verification_id),
            "status": "done",
            "verdict": verdict["verdict"],
            "confidence": verdict["confidence"],
            "claims": claims,
            "media_analysis": forensics_result.get("media_analysis", {}),
            "evidence": retrieval_result,
            "explanation": verdict["explanation"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save results
        await write_results_json(verification_id, final_results)
        
        # Update verification status
        verification.status = VerificationStatus.DONE
        db.commit()
        
        await append_log(verification_id, {
            "stage": "complete",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Pipeline completed successfully"
        })
        
    except Exception as e:
        # Update status to error
        verification = db.query(Verification).filter(Verification.id == verification_id).first()
        if verification:
            verification.status = VerificationStatus.ERROR
            db.commit()
        
        await append_log(verification_id, {
            "stage": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Pipeline error: {str(e)}",
            "error": str(e)
        })
        
        await send_sse_event(
            str(verification_id),
            "error",
            0.0,
            f"Pipeline error: {str(e)}"
        )
        
        raise
    finally:
        db.close()

