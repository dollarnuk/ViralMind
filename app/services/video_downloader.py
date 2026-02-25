import yt_dlp
import os
import uuid
from app.core.config import settings

class VideoDownloader:
    def __init__(self, download_dir: str = settings.DOWNLOAD_DIR):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    def download(self, url: str) -> str:
        """
        Downloads a video from a URL and returns the local file path.
        """
        unique_id = str(uuid.uuid4())
        output_template = os.path.join(self.download_dir, f"{unique_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        return filename

# Global instance
downloader = VideoDownloader()
