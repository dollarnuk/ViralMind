from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class VideoRequest(BaseModel):
    video_url: HttpUrl
    num_shorts: Optional[int] = 3
    preferred_duration: Optional[int] = 30  # seconds
    webhook_url: Optional[HttpUrl] = None

class VideoResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None

class ShortInfo(BaseModel):
    short_id: str
    url: str
    timestamp_start: float
    timestamp_end: float
