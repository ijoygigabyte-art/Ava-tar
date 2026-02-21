from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    filename: str
    s3_key: str
    hls_url: Optional[str] = None
    status: str = Field(default="pending") # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VideoProcessingJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id")
    job_type: str # lut, ai_style
    job_status: str = Field(default="queued")
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
