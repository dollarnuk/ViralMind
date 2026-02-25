from pydantic import BaseModel
from typing import Optional, Any, Dict

class TaskStatusSchema(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = 0
    result: Optional[Any] = None
    error: Optional[str] = None
