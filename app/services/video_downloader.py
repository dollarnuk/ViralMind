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
            'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'addheader': [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language: en-US,en;q=0.5',
            ],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }

        # Check for cookies.txt to bypass YouTube bot detection
        cookie_path = os.path.join(os.getcwd(), "cookies.txt")
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        return filename

# Global instance
downloader = VideoDownloader()
