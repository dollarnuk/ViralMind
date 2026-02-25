import logging
import os
import numpy as np
import librosa
from scenedetect import detect, ContentDetector
from app.core.exceptions import AnalysisError
from app.core.config import settings

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """
    Analyzes video files to find potential viral moments based on 
    visual scene changes and audio energy peaks.
    """

    def __init__(self, scene_threshold: float = 27.0, min_scene_len: int = 2):
        self.scene_threshold = scene_threshold
        self.min_scene_len = min_scene_len

    def find_viral_moments(
        self,
        video_path: str,
        num_moments: int = 3,
        target_duration: int = 30
    ) -> list[dict]:
        """
        Main method to rank and return top-N viral moments.
        """
        logger.info(f"Analyzing virality for: {video_path}")
        
        try:
            # 1. Detect scenes
            scenes = self._detect_scenes(video_path)
            
            # 2. Analyze audio
            audio_peaks = self._analyze_audio(video_path)
            
            # 3. Rank moments
            moments = self._combine_and_rank(scenes, audio_peaks, num_moments, target_duration)
            
            return moments
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise AnalysisError(str(e)) from e

    def _detect_scenes(self, video_path: str) -> list:
        """Uses PySceneDetect to find significant scene changes."""
        logger.info("Detecting scenes...")
        scene_list = detect(video_path, ContentDetector(threshold=self.scene_threshold))
        
        results = []
        for i, (start, end) in enumerate(scene_list):
            duration = end.get_seconds() - start.get_seconds()
            if duration >= self.min_scene_len:
                results.append({
                    "start": start.get_seconds(),
                    "end": end.get_seconds(),
                    "duration": duration
                })
        
        logger.info(f"Found {len(results)} candidate scenes")
        return results

    def _analyze_audio(self, video_path: str) -> list[dict]:
        """Uses Librosa to find audio energy peaks."""
        logger.info("Analyzing audio energy peaks...")
        
        # Load audio (downsampled for performance)
        y, sr = librosa.load(video_path, sr=22050)
        
        # Calculate RMS energy
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # Find local maxima in energy
        # Normalize RMS
        rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-6)
        
        # Simple peak detection
        peaks = []
        threshold = 0.6  # Energy threshold for a 'peak'
        
        for i in range(1, len(rms_norm) - 1):
            if rms_norm[i] > threshold and rms_norm[i] > rms_norm[i-1] and rms_norm[i] > rms_norm[i+1]:
                timestamp = librosa.frames_to_time(i, sr=sr, hop_length=hop_length)
                peaks.append({"time": float(timestamp), "intensity": float(rms_norm[i])})
                
        logger.info(f"Detected {len(peaks)} audio peaks")
        return peaks

    def _combine_and_rank(
        self, 
        scenes: list[dict], 
        audio_peaks: list[dict], 
        num_moments: int, 
        target_duration: int
    ) -> list[dict]:
        """
        Combines scene and audio data to score and select the best clips.
        """
        scored_moments = []
        
        for scene in scenes:
            scene_start = scene["start"]
            scene_end = scene["end"]
            
            # Count peaks within this scene
            scene_peaks = [p for p in audio_peaks if scene_start <= p["time"] <= scene_end]
            
            # Simple scoring: number of peaks + their intensity
            peak_score = sum(p["intensity"] for p in scene_peaks)
            
            # Scene duration score: prefer scenes closer to target_duration
            # (but don't penalize shorter scenes too much if they are intense)
            duration_score = 1.0 - abs(min(scene["duration"], target_duration) - target_duration) / target_duration
            
            total_score = (peak_score * 0.7) + (duration_score * 0.3)
            
            scored_moments.append({
                "start": scene_start,
                "end": min(scene_start + target_duration, scene_end),
                "score": float(total_score)
            })
            
        # Sort by score descending
        scored_moments.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_moments[:num_moments]

# Global instance
video_analyzer = VideoAnalyzer()
