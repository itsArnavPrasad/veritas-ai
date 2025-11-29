"""
Server-Sent Events (SSE) streaming endpoints
"""
import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import json
from pydantic import BaseModel

from services.database import get_db
from models.verification import Verification
from services.pipeline import register_sse_callback, unregister_sse_callback
from services.stream_manager import stream_manager

router = APIRouter()


class StartStreamRequest(BaseModel):
    """Request to start a new stream"""
    query: str


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


@router.post("/start_stream")
async def start_stream(request: StartStreamRequest):
    """
    Start a new real-time tweet stream for the given query
    
    Returns:
        { stream_id: "<uuid>" }
    """
    try:
        print(f"\n🌐 API REQUEST: /start_stream")
        print(f"   Query: '{request.query}'")
        stream_id = stream_manager.create_stream(request.query)
        print(f"   ✅ Stream started successfully")
        return {"stream_id": stream_id}
    except Exception as e:
        print(f"   ❌ Error starting stream: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting stream: {str(e)}")


class StopStreamRequest(BaseModel):
    """Request to stop a stream"""
    stream_id: str


@router.post("/stop_stream")
async def stop_stream(request: StopStreamRequest):
    """
    Stop an active stream
    
    Returns:
        { "status": "stopped", "stream_id": "<uuid>" }
    """
    try:
        print(f"\n🛑 API REQUEST: /stop_stream")
        print(f"   Stream ID: '{request.stream_id}'")
        
        if not stream_manager.is_stream_active(request.stream_id):
            raise HTTPException(status_code=404, detail="Stream not found or already stopped")
        
        stream_manager.stop_stream(request.stream_id)
        print(f"   ✅ Stream stopped successfully")
        return {"status": "stopped", "stream_id": request.stream_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error stopping stream: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping stream: {str(e)}")


@router.get("/stream/{stream_id}")
async def stream_clusters(stream_id: str):
    """
    Stream cluster updates via Server-Sent Events for a given stream_id
    """
    if not stream_manager.is_stream_active(stream_id):
        raise HTTPException(status_code=404, detail="Stream not found")
    
    cluster_queue = stream_manager.get_cluster_queue(stream_id)
    if not cluster_queue:
        raise HTTPException(status_code=404, detail="Stream queue not found")
    
    async def cluster_event_generator():
        """Generate SSE events for cluster updates"""
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'stream_id': stream_id})}\n\n"
            
            while stream_manager.is_stream_active(stream_id):
                try:
                    # Poll thread-safe queue (non-blocking with timeout)
                    try:
                        cluster = cluster_queue.get(timeout=1.0)
                        
                        # Format as SSE
                        event_data = {
                            "type": "cluster_update",
                            "stream_id": stream_id,
                            "cluster": cluster
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"
                    except:
                        # Timeout or empty queue - send heartbeat
                        await asyncio.sleep(1)
                        yield f": heartbeat\n\n"
                        continue
                    
                except Exception as e:
                    print(f"Error in cluster event generator: {e}")
                    await asyncio.sleep(1)
                    continue
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        cluster_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/_clusters/{stream_id}")
async def receive_clusters(stream_id: str, cluster: dict):
    """
    Internal endpoint to receive cluster updates from Pathway
    This endpoint is called by Pathway's HTTP output connector
    """
    if not stream_manager.is_stream_active(stream_id):
        return {"status": "stream_not_found"}
    
    cluster_queue = stream_manager.get_cluster_queue(stream_id)
    if cluster_queue:
        cluster_queue.put(cluster)  # Thread-safe queue, no await needed
    
    return {"status": "ok"}


@router.get("/verification/{verification_id}/stream")
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

