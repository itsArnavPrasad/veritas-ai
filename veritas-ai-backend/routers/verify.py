"""
Verification endpoints
"""
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

from services.database import get_db
from models.verification import Verification, InputType, VerificationStatus
from services.storage import create_verification_storage, save_input_file, save_text_input
from services.pipeline import run_pipeline
from services.image_analysis import analyze_image_description, detect_ai_artifacts
from services.video_analysis import analyze_video_comprehensive
from services.cross_modal_fusion import perform_cross_modal_fusion
from services.adk_service import call_coordinator_agent
from services.storage import save_results_json
from pathlib import Path
import aiofiles

router = APIRouter()


class TextVerificationRequest(BaseModel):
    """Text verification request"""
    text: str


class ArticleVerificationRequest(BaseModel):
    """Article verification request"""
    url: Optional[HttpUrl] = None
    html_content: Optional[str] = None


class TweetVerificationRequest(BaseModel):
    """Tweet verification request"""
    tweet_text: str
    tweet_url: Optional[str] = None
    media_urls: Optional[list[str]] = []


class InitializeVerificationRequest(BaseModel):
    """Request to initialize a verification for multimodal analysis"""
    input_types: list[str]  # e.g., ["text", "image", "video"]


@router.post("/verify/initialize")
async def initialize_verification(
    request: InitializeVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Initialize a single verification record for multimodal analysis.
    This ensures all analyses (text, image, video) use the same verification_id.
    """
    try:
        # Create a single verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.TEXT,  # Default, but will handle multiple types
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        return JSONResponse(
            status_code=200,
            content={
                "verification_id": str(verification.id),
                "status": "initialized"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing verification: {str(e)}")


@router.post("/verify/text")
async def verify_text(
    request: TextVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify plain text input
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.TEXT,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Save input text
        await save_text_input(verification.id, request.text)
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.TEXT)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating verification: {str(e)}")


@router.post("/verify/image")
async def verify_image(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify image file upload with Gemini VLM analysis
    
    Returns:
        {
            "status": "success",
            "image_saved_path": "...",
            "vlm_description": { ... },
            "vlm_ai_artifact_analysis": { ... }
        }
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.IMAGE,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Read file content
        content = await file.read()
        
        # Save uploaded file
        filename = file.filename or f"image_{verification.id}.{file.content_type.split('/')[-1] if file.content_type else 'jpg'}"
        saved_path = await save_input_file(verification.id, filename, content)
        
        # Get full path to saved image
        image_path = Path(saved_path)
        
        # Perform Gemini VLM analysis
        vlm_description = {}
        vlm_artifact_analysis = {}
        
        try:
            # Task 1: Generate detailed factual description
            vlm_description = await analyze_image_description(image_path)
        except Exception as e:
            logger.error(f"Error in image description analysis: {e}")
            vlm_description = {
                "error": str(e),
                "description": "",
                "objects": [],
                "actions": [],
                "environment": "",
                "visible_text": [],
                "other_details": ""
            }
        
        try:
            # Task 2: Detect AI-generation artifacts
            vlm_artifact_analysis = await detect_ai_artifacts(image_path)
        except Exception as e:
            logger.error(f"Error in artifact detection: {e}")
            vlm_artifact_analysis = {
                "error": str(e),
                "artifact_detected": False,
                "confidence": 0.0,
                "artifacts": [],
                "explanation": ""
            }
        
        # Trigger pipeline in background (optional, for downstream processing)
        background_tasks.add_task(run_pipeline, verification.id, InputType.IMAGE)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "image_saved_path": str(saved_path),
                "verification_id": str(verification.id),
                "vlm_description": vlm_description,
                "vlm_ai_artifact_analysis": vlm_artifact_analysis
            }
        )
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


class VerifyImageByFileIdRequest(BaseModel):
    """Request to verify image by file_id"""
    file_id: str
    verification_id: Optional[str] = None  # Optional: if provided, use existing verification


class VerifyVideoByFileIdRequest(BaseModel):
    """Request to verify video by file_id"""
    file_id: str
    verification_id: Optional[str] = None  # Optional: if provided, use existing verification


class VerifyTextByContentRequest(BaseModel):
    """Request to verify text by content"""
    text: str
    verification_id: Optional[str] = None  # Optional: if provided, use existing verification


@router.post("/verify/image/by-file-id")
async def verify_image_by_file_id(
    request: VerifyImageByFileIdRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify image by file_id (for images already uploaded via /upload/image)
    
    Returns:
        {
            "status": "success",
            "image_saved_path": "...",
            "vlm_description": { ... },
            "vlm_ai_artifact_analysis": { ... }
        }
    """
    try:
        from services.storage import get_uploaded_file, get_verification_storage_path
        from pathlib import Path
        import aiofiles
        
        # Get the uploaded file path
        image_path = await get_uploaded_file(request.file_id, "image")
        if not image_path or not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image file not found for file_id: {request.file_id}")
        
        print(f"Image verification request - file_id: {request.file_id}, verification_id: {request.verification_id}")
        
        # CRITICAL: verification_id MUST be provided - raise error if not
        if not request.verification_id:
            raise HTTPException(
                status_code=400, 
                detail="verification_id is required. Please initialize verification first using /verify/initialize"
            )
        
        # Get or create verification with the provided ID
        try:
            verification_id = uuid.UUID(request.verification_id)
            verification = db.query(Verification).filter(Verification.id == verification_id).first()
            if not verification:
                print(f"WARNING: Verification {request.verification_id} not found in DB, creating it now")
                # Create verification record with the provided ID (should have been created by /verify/initialize)
                verification = Verification(
                    id=verification_id,
                    input_type=InputType.TEXT,  # Use TEXT as default since it's multimodal
                    status=VerificationStatus.PENDING
                )
                db.add(verification)
                db.commit()
                db.refresh(verification)
                print(f"Created verification record: {verification_id}")
            else:
                print(f"Using existing verification: {verification_id}")
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid verification_id format: {request.verification_id}. Error: {str(e)}"
            )
        
        # Create storage directory
        create_verification_storage(verification_id)
        
        # Read file content
        async with aiofiles.open(image_path, "rb") as f:
            file_content = await f.read()
        
        # Rename file to use verification_id and copy to verification storage
        ext = image_path.suffix
        filename = f"{verification_id}{ext}"
        saved_path = await save_input_file(verification_id, filename, file_content)
        
        # Also rename the file in uploads directory to match verification_id
        from services.storage import get_upload_type_path
        uploads_image_path = get_upload_type_path("image")
        new_uploads_path = uploads_image_path / filename
        
        # Always write the file with verification_id name in uploads directory
        async with aiofiles.open(new_uploads_path, "wb") as f:
            await f.write(file_content)
        print(f"Image file renamed in uploads: {image_path.name} -> {filename}")
        
        # Remove old file if it's different and exists
        if image_path != new_uploads_path and image_path.exists():
            try:
                image_path.unlink()
                print(f"Removed old image file: {image_path.name}")
            except Exception as e:
                print(f"Could not remove old image file {image_path.name}: {e}")
        
        # Use the renamed file for analysis
        analysis_image_path = new_uploads_path
        
        # Perform Gemini VLM analysis
        vlm_description = {}
        vlm_artifact_analysis = {}
        
        try:
            # Task 1: Generate detailed factual description
            vlm_description = await analyze_image_description(analysis_image_path)
        except Exception as e:
            logger.error(f"Error in image description analysis: {e}")
            vlm_description = {
                "error": str(e),
                "description": "",
                "objects": [],
                "actions": [],
                "environment": "",
                "visible_text": [],
                "other_details": ""
            }
        
        try:
            # Task 2: Detect AI-generation artifacts
            vlm_artifact_analysis = await detect_ai_artifacts(analysis_image_path)
        except Exception as e:
            logger.error(f"Error in artifact detection: {e}")
            vlm_artifact_analysis = {
                "error": str(e),
                "artifact_detected": False,
                "confidence": 0.0,
                "artifacts": [],
                "explanation": ""
            }
        
        # Save image analysis results to JSON file
        from services.storage import save_image_analysis_json
        image_analysis_result = {
            "verification_id": str(verification_id),
            "image_saved_path": str(saved_path),
            "vlm_description": vlm_description,
            "vlm_ai_artifact_analysis": vlm_artifact_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            await save_image_analysis_json(verification_id, image_analysis_result)
        except Exception as e:
            logger.error(f"Error saving image analysis: {e}")
        
        # Trigger pipeline in background (optional, for downstream processing)
        background_tasks.add_task(run_pipeline, verification_id, InputType.IMAGE)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "image_saved_path": str(saved_path),
                "verification_id": str(verification_id),
                "vlm_description": vlm_description,
                "vlm_ai_artifact_analysis": vlm_artifact_analysis
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image by file_id: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/verify/video/by-file-id")
async def verify_video_by_file_id(
    request: VerifyVideoByFileIdRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify video by file_id (for videos already uploaded via /upload/video)
    
    Returns:
        {
            "status": "success",
            "video_saved_path": "...",
            "video_analysis": { ... }
        }
    """
    try:
        from services.storage import get_uploaded_file, get_upload_type_path
        
        # Get the uploaded file path
        video_path = await get_uploaded_file(request.file_id, "video")
        if not video_path or not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video file not found for file_id: {request.file_id}")
        
        print(f"Video verification request - file_id: {request.file_id}, verification_id: {request.verification_id}")
        
        # CRITICAL: verification_id MUST be provided - raise error if not
        if not request.verification_id:
            raise HTTPException(
                status_code=400, 
                detail="verification_id is required. Please initialize verification first using /verify/initialize"
            )
        
        # Get or create verification with the provided ID
        try:
            verification_id = uuid.UUID(request.verification_id)
            verification = db.query(Verification).filter(Verification.id == verification_id).first()
            if not verification:
                print(f"WARNING: Verification {request.verification_id} not found in DB, creating it now")
                # Create verification record with the provided ID (should have been created by /verify/initialize)
                verification = Verification(
                    id=verification_id,
                    input_type=InputType.TEXT,  # Use TEXT as default since it's multimodal
                    status=VerificationStatus.PENDING
                )
                db.add(verification)
                db.commit()
                db.refresh(verification)
                print(f"Created verification record: {verification_id}")
            else:
                print(f"Using existing verification: {verification_id}")
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid verification_id format: {request.verification_id}. Error: {str(e)}"
            )
        
        # Create storage directory
        create_verification_storage(verification_id)
        
        # Read file content
        async with aiofiles.open(video_path, "rb") as f:
            file_content = await f.read()
        
        # Rename file to use verification_id and copy to verification storage
        ext = video_path.suffix
        filename = f"{verification_id}{ext}"
        print(f"Saving video file with verification_id name: {filename}")
        saved_path = await save_input_file(verification_id, filename, file_content)
        print(f"Video saved to verification storage: {saved_path}")
        
        # Also rename the file in uploads directory to match verification_id
        uploads_video_path = get_upload_type_path("video")
        new_uploads_path = uploads_video_path / filename
        
        # Always write the file with verification_id name in uploads directory
        async with aiofiles.open(new_uploads_path, "wb") as f:
            await f.write(file_content)
        print(f"Video file renamed in uploads: {video_path.name} -> {filename} (path: {new_uploads_path})")
        
        # Remove old file if it's different and exists (remove file_id-based name)
        if video_path != new_uploads_path and video_path.exists():
            try:
                video_path.unlink()
                print(f"Removed old video file: {video_path.name}")
            except Exception as e:
                print(f"Could not remove old video file {video_path.name}: {e}")
        
        # Verify the file was saved correctly
        if not new_uploads_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save video file with verification_id name: {filename}"
            )
        
        print(f"Video file successfully saved with verification_id: {verification_id}, filename: {filename}")
        
        # Use the renamed file for analysis
        analysis_video_path = new_uploads_path
        
        # Perform Gemini video analysis
        video_analysis = {}
        
        try:
            # Comprehensive video analysis
            video_analysis = await analyze_video_comprehensive(Path(saved_path))
        except Exception as e:
            logger.error(f"Error in video analysis: {e}")
            video_analysis = {
                "error": str(e),
                "video_description": "",
                "claims": [],
                "overall_authenticity_score": 0.0,
                "authenticity_verdict": "UNCERTAIN"
            }
        
        # Save video analysis results to JSON file
        from services.storage import save_video_analysis_json
        video_analysis_result = {
            "verification_id": str(verification_id),
            "video_saved_path": str(saved_path),
            "video_analysis": video_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            await save_video_analysis_json(verification_id, video_analysis_result)
        except Exception as e:
            logger.error(f"Error saving video analysis: {e}")
        
        # Trigger background pipeline processing
        background_tasks.add_task(run_pipeline, verification_id, InputType.VIDEO)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "verification_id": str(verification_id),
                "video_saved_path": str(saved_path),
                "video_analysis": video_analysis
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing video by file_id: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


@router.post("/verify/text/by-content")
async def verify_text_by_content(
    request: VerifyTextByContentRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify text by content using coordinator agent
    
    Returns:
        {
            "status": "success",
            "verification_id": "...",
            "coordinator_response": { ... },
            "structured_data": { ... }
        }
    """
    try:
        print(f"Text verification request - verification_id: {request.verification_id}")
        
        # Get or create verification
        if request.verification_id:
            try:
                verification_id = uuid.UUID(request.verification_id)
                verification = db.query(Verification).filter(Verification.id == verification_id).first()
                if not verification:
                    print(f"WARNING: Verification {request.verification_id} not found, creating new one")
                    # Create new verification record if not found
                    verification = Verification(
                        id=verification_id,
                        input_type=InputType.TEXT,
                        status=VerificationStatus.PENDING
                    )
                    db.add(verification)
                    db.commit()
                    db.refresh(verification)
                else:
                    print(f"Using existing verification: {verification_id}")
            except ValueError as e:
                print(f"ERROR: Invalid verification_id format: {request.verification_id}, creating new one")
                # Create new verification record
                verification = Verification(
                    id=uuid.uuid4(),
                    input_type=InputType.TEXT,
                    status=VerificationStatus.PENDING
                )
                db.add(verification)
                db.commit()
                db.refresh(verification)
                verification_id = verification.id
        else:
            print(f"WARNING: No verification_id provided, creating new verification")
            # Create new verification record
            verification = Verification(
                id=uuid.uuid4(),
                input_type=InputType.TEXT,
                status=VerificationStatus.PENDING
            )
            db.add(verification)
            db.commit()
            db.refresh(verification)
            verification_id = verification.id
        
        # Create storage directory
        create_verification_storage(verification_id)
        
        # Save input text
        await save_text_input(verification_id, request.text)
        
        # Call coordinator agent
        coordinator_response = {}
        structured_data = {}
        coordinator_output = {}
        
        try:
            result = await call_coordinator_agent(request.text)
            if result.get("status") == "success":
                coordinator_response = result.get("raw_response", {})
                structured_data = result.get("structured_data", {})
                coordinator_output = result.get("coordinator_output", {})
            else:
                coordinator_response = {
                    "error": result.get("error"),
                    "details": result.get("details")
                }
        except Exception as e:
            logger.error(f"Error calling coordinator agent: {e}")
            coordinator_response = {
                "error": str(e)
            }
        
        # Save text analysis results to JSON file
        from services.storage import save_text_analysis_json
        text_analysis_result = {
            "verification_id": str(verification_id),
            "coordinator_response": coordinator_response,
            "structured_data": structured_data,
            "coordinator_output": coordinator_output,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            await save_text_analysis_json(verification_id, text_analysis_result)
        except Exception as e:
            logger.error(f"Error saving text analysis: {e}")
        
        # Trigger pipeline in background (optional, for downstream processing)
        background_tasks.add_task(run_pipeline, verification_id, InputType.TEXT)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "verification_id": str(verification_id),
                "coordinator_response": coordinator_response,
                "structured_data": structured_data,
                "coordinator_output": coordinator_output
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing text by content: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@router.post("/verify/video")
async def verify_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify video file upload
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.VIDEO,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Read file content
        content = await file.read()
        
        # Save uploaded file
        filename = file.filename or f"video_{verification.id}.{file.content_type.split('/')[-1] if file.content_type else 'mp4'}"
        await save_input_file(verification.id, filename, content)
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.VIDEO)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


@router.post("/verify/article")
async def verify_article(
    request: ArticleVerificationRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify article (URL or HTML content)
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.ARTICLE,
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Save input
        if request.url:
            # Save URL
            url_content = f"URL: {request.url}\n"
            await save_text_input(verification.id, url_content)
        elif request.html_content:
            # Save HTML content
            await save_text_input(verification.id, request.html_content)
        else:
            raise HTTPException(status_code=400, detail="Either url or html_content must be provided")
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.ARTICLE)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing article: {str(e)}")


@router.post("/verify/tweet")
async def verify_tweet(
    request: TweetVerificationRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Verify a tweet (text and optional media)
    """
    try:
        # Create verification record
        verification = Verification(
            id=uuid.uuid4(),
            input_type=InputType.TEXT,  # Treat tweets as text for now
            status=VerificationStatus.PENDING
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        
        # Create storage directory
        create_verification_storage(verification.id)
        
        # Save tweet text
        tweet_content = f"Tweet Text: {request.tweet_text}\n"
        if request.tweet_url:
            tweet_content += f"Tweet URL: {request.tweet_url}\n"
        if request.media_urls:
            tweet_content += f"Media URLs: {', '.join(request.media_urls)}\n"
        
        await save_text_input(verification.id, tweet_content)
        
        # Trigger pipeline in background
        background_tasks.add_task(run_pipeline, verification.id, InputType.TEXT)
        
        return JSONResponse(
            status_code=202,
            content={"verification_id": str(verification.id)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing tweet: {str(e)}")


class CrossModalFusionRequest(BaseModel):
    """Request for cross-modal fusion"""
    text_analysis: Optional[Dict[str, Any]] = None
    image_analysis: Optional[Dict[str, Any]] = None
    video_analysis: Optional[Dict[str, Any]] = None
    verification_id: Optional[str] = None


@router.post("/verify/cross-modal-fusion")
async def cross_modal_fusion(
    request: CrossModalFusionRequest,
    db: Session = Depends(get_db)
):
    """
    Perform cross-modal fusion analysis combining text, image, and video results
    
    Returns:
        {
            "status": "success",
            "fusion_results": { ... },
            "saved": true/false
        }
    """
    try:
        # Perform cross-modal fusion
        fusion_results = await perform_cross_modal_fusion(
            text_analysis=request.text_analysis,
            image_analysis=request.image_analysis,
            video_analysis=request.video_analysis
        )
        
        # Save results if verification_id is provided
        saved = False
        if request.verification_id:
            try:
                verification_id = uuid.UUID(request.verification_id)
                from services.storage import create_verification_storage
                create_verification_storage(verification_id)
                
                # Save each analysis type to separate JSON files
                from services.storage import (
                    save_text_analysis_json,
                    save_image_analysis_json,
                    save_video_analysis_json,
                    save_fusion_results_json
                )
                
                # Save text analysis if present
                if request.text_analysis:
                    await save_text_analysis_json(verification_id, request.text_analysis)
                
                # Save image analysis if present
                if request.image_analysis:
                    await save_image_analysis_json(verification_id, request.image_analysis)
                
                # Save video analysis if present
                if request.video_analysis:
                    await save_video_analysis_json(verification_id, request.video_analysis)
                
                # Save fusion results
                await save_fusion_results_json(verification_id, fusion_results)
                
                saved = True
                
                # Update verification status
                verification = db.query(Verification).filter(Verification.id == verification_id).first()
                if verification:
                    verification.status = VerificationStatus.DONE
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Error saving fusion results: {e}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "fusion_results": fusion_results,
                "saved": saved
            }
        )
    except Exception as e:
        logger.error(f"Error in cross-modal fusion: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing cross-modal fusion: {str(e)}")

