import pytest
from unittest.mock import patch, MagicMock
from app.services.video_downloader import VideoDownloader

@patch('yt_dlp.YoutubeDL')
def test_downloader_success(mock_yt_dlp):
    # Mock yt-dlp behavior
    mock_instance = mock_yt_dlp.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {'id': 'test_id'}
    mock_instance.prepare_filename.return_value = 'downloads/test_video.mp4'
    
    downloader = VideoDownloader(download_dir="test_downloads")
    path = downloader.download("https://youtube.com/watch?v=123")
    
    assert path == 'downloads/test_video.mp4'
    mock_instance.extract_info.assert_called_once()
