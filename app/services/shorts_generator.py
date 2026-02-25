import logging
import os
import uuid
from app.services.video_analyzer import video_analyzer
from app.services.smart_cropper import smart_cropper
from app.core.config import settings
from app.core.exceptions import ViralMindError

logger = logging.getLogger(__name__)

class ShortsGenerator:
    """
    Orchestrates the full pipeline:
    Analyzes a video for moments -> Crops each moment into a short -> Returns results.
    """

    def __init__(self, output_dir: str = settings.OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_shorts(
        self,
        video_path: str,
        num_shorts: int = 3,
        target_duration: int = 30,
        task_update_callback=None
    ) -> list[dict]:
        """
        Runs the full generation pipeline.
        
        Args:
            video_path: Path to the downloaded source video.
            num_shorts: Number of shorts to generate.
            target_duration: Max duration for each short.
            task_update_callback: Optional function to call for status updates.
        """
        logger.info(f"Starting shorts generation for: {video_path}")
        
        try:
            # 1. Analyze video for viral moments
            if task_update_callback:
                task_update_callback("ANALYZING", 30)
            
            moments = video_analyzer.find_viral_moments(
                video_path, 
                num_moments=num_shorts, 
                target_duration=target_duration
            )
            
            if not moments:
                logger.warning("No viral moments found")
                return []

            results = []
            
            # 2. Process each moment
            for i, moment in enumerate(moments):
                if task_update_callback:
                    progress = 30 + (int((i / len(moments)) * 60))
                    task_update_callback("CROPPING", progress)
                
                short_id = str(uuid.uuid4())
                output_filename = f"short_{short_id}.mp4"
                output_path = os.path.join(self.output_dir, output_filename)
                
                logger.info(f"Generating short {i+1}/{len(moments)}: {output_path}")
                
                try:
                    smart_cropper.crop_segment(
                        video_path,
                        output_path,
                        moment["start"],
                        moment["end"] - moment["start"]
                    )
                    
                    results.append({
                        "short_id": short_id,
                        "file_path": output_path,
                        "timestamp_start": moment["start"],
                        "timestamp_end": moment["end"],
                        "score": moment["score"]
                    })
                except Exception as e:
                    logger.error(f"Failed to generate short {i+1}: {str(e)}")
                    continue
            
            if task_update_callback:
                task_update_callback("COMPLETED", 100)
                
            return results
            
        except Exception as e:
            logger.error(f"Generation pipeline failed: {str(e)}")
            raise ViralMindError(f"Generation failed: {str(e)}")

# Global instance
shorts_generator = ShortsGenerator()
