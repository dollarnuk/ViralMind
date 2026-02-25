import logging
import os
import aiohttp
import asyncio
from app.tasks.celery_app import celery_app
from app.services.video_downloader import downloader

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_video")
def process_video_task(self, video_url: str, num_shorts: int = 3, webhook_url: str = None) -> dict:
    """
    Orchestrates the video processing pipeline.
    """
    logger.info(f"Starting process_video_task for: {video_url}")
    
    async def notify_webhook(url, payload):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    logger.info(f"Webhook notified: {url}, status: {response.status}")
            except Exception as e:
                logger.error(f"Webhook notification failed: {str(e)}")

    def update_progress(state, progress):
        self.update_state(state=state, meta={'progress': progress})

    try:
        # Step 1: Download or Use local file
        if os.path.exists(video_url):
            logger.info(f"Using local file: {video_url}")
            file_path = video_url
        else:
            update_progress("DOWNLOADING", 10)
            logger.info("Downloading video...")
            file_path = downloader.download(video_url)
        
        # Step 2-4: Analysis, Cropping, Generation via ShortsGenerator
        from app.services.shorts_generator import shorts_generator
        
        shorts = shorts_generator.generate_shorts(
            video_path=file_path,
            num_shorts=num_shorts,
            task_update_callback=update_progress
        )
        
        # Cleanup source video to save space
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up source video: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup source video: {str(e)}")
        
        result = {
            "status": "completed", 
            "shorts": shorts
        }
        
        # Notify webhook if provided
        if webhook_url:
            asyncio.run(notify_webhook(webhook_url, {
                "task_id": self.request.id,
                "status": "completed",
                "shorts": shorts
            }))
            
        return result
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        # Let Celery handle the failure state automatically to avoid malformed metadata
        raise e

@celery_app.task(name="cleanup_old_files")
def cleanup_old_files():
    """
    Cleans up files older than FILE_RETENTION_HOURS.
    """
    import time
    from app.core.config import settings
    
    current_time = time.time()
    retention_sec = settings.FILE_RETENTION_HOURS * 3600
    
    for dir_path in [settings.DOWNLOAD_DIR, settings.OUTPUT_DIR]:
        if not os.path.exists(dir_path):
            continue
            
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > retention_sec:
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {str(e)}")
