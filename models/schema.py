from typing import Optional, List
from pydantic import BaseModel

class CommentUpdateRequest(BaseModel):
    video_id: str
    comment_id: str
    status: str 
    suggested_reply: str = None