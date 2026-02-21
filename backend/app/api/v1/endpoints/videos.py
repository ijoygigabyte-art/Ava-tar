from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session
from app.db.session import get_session
from app.models import Video
from app.services.storage import storage_service
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
import uuid
import os
import shutil

router = APIRouter()

async def get_redis():
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))

@router.get("/")
def list_videos(session: Session = Depends(get_session)):
    return session.query(Video).all()

@router.post("/upload")
async def upload_video(
    title: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    file_id = str(uuid.uuid4())
    # Try to get extension from content_type
    content_type = file.content_type
    ext = content_type.split("/")[-1] if content_type and "/" in content_type else "mp4"
    if ext == "quicktime": ext = "mov" # Common mapping
    
    filename = f"{file_id}.{ext}"
    s3_key = f"uploads/{filename}"
    
    # Save file temporarily
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Upload to Minio
        success = storage_service.upload_file(temp_path, s3_key)
        if not success:
            raise HTTPException(status_code=500, detail="Could not upload file to storage")
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Create video record
    video = Video(title=title, filename=filename, s3_key=s3_key)
    session.add(video)
    session.commit()
    session.refresh(video)
    
    # Queue background task (non-fatal if Redis is unavailable)
    queue_status = "queued"
    queue_warning = None
    try:
        redis = await get_redis()
        await redis.enqueue_job("process_video", video.id)
    except Exception as e:
        queue_status = "not_queued"
        queue_warning = f"Video uploaded, but processing queue is unavailable: {e}"
        print(queue_warning)
    
    return {
        "video_id": video.id,
        "filename": filename,
        "queue_status": queue_status,
        "warning": queue_warning,
    }
