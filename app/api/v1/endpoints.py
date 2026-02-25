from fastapi import APIRouter, HTTPException
from app.schemas.video_request import VideoRequest, VideoResponse
from app.tasks.worker import process_video_task

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

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status of a video processing task from Celery.
    """
    from app.tasks.celery_app import celery_app
    try:
        res = celery_app.AsyncResult(task_id)
        
        # Safely get status and result
        status = res.status
        result = res.result if res.ready() else res.info
        
        return {
            "task_id": task_id,
            "status": status,
            "result": result
        }
    except Exception as e:
        # Fallback for malformed results
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "result": {"error": f"Internal task error: {str(e)}"}
        }
