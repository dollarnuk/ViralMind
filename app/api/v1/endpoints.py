from fastapi import APIRouter, HTTPException, UploadFile, File
import shutil
import os
import uuid
from app.schemas.video_request import VideoRequest, VideoResponse
from app.tasks.worker import process_video_task
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/process-video", response_model=VideoResponse)
async def process_video(request: VideoRequest) -> VideoResponse:
    """
    Endpoint to trigger video processing via Celery.
    """
    try:
        # Trigger the celery task
        task = process_video_task.delay(
            str(request.video_url), 
            request.num_shorts, 
            str(request.webhook_url) if request.webhook_url else None
        )
        
        return VideoResponse(
            task_id=task.id,
            status="queued",
            message="Processing started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-video", response_model=VideoResponse)
async def upload_video(file: UploadFile = File(...)) -> VideoResponse:
    """
    Endpoint to upload a video file and trigger processing.
    """
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    try:
        # Create a unique filename in the downloads directory
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1]
        local_filename = f"{file_id}{ext}"
        local_path = os.path.join(settings.DOWNLOAD_DIR, local_filename)
        
        # Ensure directory exists
        os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
        
        # Save the file
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Trigger the celery task with local_path instead of URL
        # We'll pass it as video_url but logic in worker will handle it
        task = process_video_task.delay(
            video_url=local_path, # Local path starts with 'downloads/'
            num_shorts=3
        )
        
        return VideoResponse(
            task_id=task.id,
            status="queued",
            message="Upload successful, processing started"
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status of a video processing task from Celery.
    """
    from app.tasks.celery_app import celery_app
    try:
        res = celery_app.AsyncResult(task_id)
        status = res.status
        result = res.result if res.ready() else res.info
        
        # If task failed, ensure 'error' field is present for frontend
        if status == "FAILURE":
            if isinstance(result, Exception):
                result = {"error": str(result)}
            elif isinstance(result, dict) and "error" not in result:
                # Celery sometimes stores exception info in different keys
                error_msg = result.get("exc_message") or str(result)
                result = {"error": error_msg}
        
        return {
            "task_id": task_id,
            "status": status,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error fetching task status: {str(e)}")
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "result": {"error": f"Internal task error: {str(e)}"}
        }
