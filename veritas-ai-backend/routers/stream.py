"""
Server-Sent Events (SSE) streaming endpoints
"""
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import json

from services.database import get_db
from models.verification import Verification
from services.pipeline import register_sse_callback, unregister_sse_callback

router = APIRouter()


async def event_generator(verification_id: UUID, db: Session):
    """Generate SSE events for verification progress"""
    # Verify verification exists
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        yield f"data: {json.dumps({'error': 'Verification not found'})}\n\n"
        return
    
    # Queue for events
    event_queue = asyncio.Queue()
    
    # Callback to push events to queue
    async def sse_callback(event_data):
        await event_queue.put(event_data)
    
    # Register callback
    register_sse_callback(str(verification_id), sse_callback)
    
    try:
        # Send initial connection event
        yield f"data: {json.dumps({'stage': 'connected', 'message': 'Stream connected'})}\n\n"
        
        # Keep connection alive and send events
        while True:
            try:
                # Wait for event with timeout
                event_data = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                
                # Format as SSE
                event_json = json.dumps(event_data)
                yield f"data: {event_json}\n\n"
                
                # If final stage, close connection
                if event_data.get("stage") == "final_verdict" and event_data.get("progress", 0) >= 100:
                    yield f"data: {json.dumps({'stage': 'complete', 'message': 'Verification complete'})}\n\n"
                    break
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield f": heartbeat\n\n"
                continue
                
    except asyncio.CancelledError:
        pass
    finally:
        # Unregister callback
        unregister_sse_callback(str(verification_id))


@router.get("/stream/{verification_id}")
async def stream_verification(
    verification_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Stream verification progress via Server-Sent Events
    """
    # Verify verification exists
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    return StreamingResponse(
        event_generator(verification_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

