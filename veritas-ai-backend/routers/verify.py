"""
Verification endpoints
"""
import uuid
import logging
from typing import Optional
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
from pathlib import Path

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
        from services.storage import get_uploaded_file
        from pathlib import Path
        import aiofiles
        
        # Get the uploaded file path
        image_path = await get_uploaded_file(request.file_id, "image")
        if not image_path or not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image file not found for file_id: {request.file_id}")
        
        # Read file content asynchronously
        async with aiofiles.open(image_path, "rb") as f:
            file_content = await f.read()
        
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
        
        # Copy file to verification storage
        filename = image_path.name
        saved_path = await save_input_file(verification.id, filename, file_content)
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image by file_id: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


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

