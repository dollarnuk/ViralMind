import logging
import cv2
import mediapipe as mp
import subprocess
import os
import numpy as np
from app.core.exceptions import CroppingError
from app.core.config import settings

logger = logging.getLogger(__name__)

class SmartCropper:
    """
    Crops horizontal videos (16:9) to vertical (9:16) by tracking faces
    to ensure the main subject remains in frame.
    """

    def __init__(self, sample_interval: float = 0.5):
        self.sample_interval = sample_interval
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # Full range model (better for distant faces)
            min_detection_confidence=0.5
        )

    def crop_segment(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        duration: float
    ) -> str:
        """
        Extracts and crops a segment of video to 9:16.
        """
        logger.info(f"Cropping segment from {input_path} at {start_time}s for {duration}s")
        
        try:
            # 1. Detect face positions in the segment
            face_positions = self._detect_faces_in_segment(input_path, start_time, duration)
            
            # 2. Calculate optimal smooth crop X-coordinate
            crop_x = self._calculate_smooth_crop(face_positions, input_path)
            
            # 3. Execute FFmpeg crop
            self._execute_ffmpeg_crop(input_path, output_path, start_time, duration, crop_x)
            
            return output_path
        except Exception as e:
            logger.error(f"Cropping failed: {str(e)}")
            raise CroppingError(str(e)) from e

    def _detect_faces_in_segment(self, video_path: str, start_time: float, duration: float) -> list[float]:
        """
        Samples frames from the segment and detects face X-coordinates (normalized 0-1).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise CroppingError("Could not open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        start_frame = int(start_time * fps)
        end_frame = int((start_time + duration) * fps)
        
        face_x_coords = []
        
        # Sample frames every 'sample_interval' seconds
        sample_step = int(self.sample_interval * fps)
        if sample_step < 1: sample_step = 1

        try:
            for frame_idx in range(start_frame, end_frame, sample_step):
                if frame_idx >= total_frames: break
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret: break
                
                # Convert to RGB for MediaPipe
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_detection.process(frame_rgb)
                
                if results.detections:
                    # Find the most prominent face (largest bounding box)
                    best_detection = max(results.detections, key=lambda d: d.location_data.relative_bounding_box.width)
                    bbox = best_detection.location_data.relative_bounding_box
                    center_x = bbox.xmin + (bbox.width / 2)
                    face_x_coords.append(center_x)
                else:
                    # Fallback: maintain previous position or center
                    face_x_coords.append(0.5)
        finally:
            cap.release()
            
        return face_x_coords

    def _calculate_smooth_crop(self, face_positions: list[float], video_path: str) -> int:
        """
        Calculates a stable X-coordinate for the crop window.
        Returns the X coordinate (in pixels) for the left edge of the crop.
        """
        # Get video width
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        target_width = int(height * (9/16))
        if target_width > width:
            target_width = width # Fallback if source is already narrow
            
        if not face_positions:
            # Default to center
            return max(0, (width - target_width) // 2)
            
        # Median position to avoid outliers
        avg_face_x = np.median(face_positions)
        center_x_px = int(avg_face_x * width)
        
        # Calculate left edge of crop
        left_x = center_x_px - (target_width // 2)
        
        # Clamp to video boundaries
        left_x = max(0, min(left_x, width - target_width))
        
        return left_x

    def _execute_ffmpeg_crop(self, input_path: str, output_path: str, start: float, duration: float, crop_x: int):
        """
        Runs FFmpeg to cut and crop the video.
        Uses fast seek and high quality settings.
        """
        cap = cv2.VideoCapture(input_path)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        target_width = int(height * (9/16))
        
        # Fast seeking -ss before -i
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-t', str(duration),
            '-i', input_path,
            '-vf', f'crop={target_width}:{height}:{crop_x}:0,scale=1080:1920',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            output_path
        ]
        
        logger.info(f"Running FFmpeg: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise CroppingError(f"FFmpeg failed: {result.stderr}")

# Global instance
smart_cropper = SmartCropper()
