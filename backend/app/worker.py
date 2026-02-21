import asyncio
import os
import shutil
from shutil import which
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
from app.db.session import Session, engine
from app.models import Video
from app.services.storage import storage_service

async def process_video(ctx, video_id: int):
    print(f"Starting processing for video {video_id}...")
    
    with Session(engine) as session:
        video = session.get(Video, video_id)
        if not video:
            print(f"Video {video_id} not found")
            return

        video.status = "processing"
        session.add(video)
        session.commit()
        session.refresh(video)
            
        temp_dir = f"temp/{video.id}"
        output_dir = f"processed/{video.id}"
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        local_input = f"{temp_dir}/input.mp4"
        
        try:
            # 1. Download from S3
            if not storage_service.download_file(video.s3_key, local_input):
                raise Exception("Failed to download video from S3")

            ffmpeg_bin = settings.FFMPEG_BIN
            if not which(ffmpeg_bin):
                raise FileNotFoundError(
                    f"FFmpeg not found. Set FFMPEG_BIN or add ffmpeg to PATH. Current FFMPEG_BIN='{ffmpeg_bin}'"
                )
            
            # 2. Extract frames (optional for now, but good for Phase 3)
            # await asyncio.create_subprocess_exec("ffmpeg", "-i", local_input, "-vf", "fps=1", f"{output_dir}/frame%04d.jpg")
            
            # 3. Generate HLS
            # ffmpeg -i input.mp4 -profile:v baseline -level 3.0 -s 640x360 -start_number 0 -hls_time 10 -hls_list_size 0 -f hls index.m3u8
            hls_output = f"{output_dir}/index.m3u8"
            process = await asyncio.create_subprocess_exec(
                ffmpeg_bin, "-i", local_input,
                "-codec:v", "libx264", "-codec:a", "aac", 
                "-map", "0", "-f", "hls", 
                "-hls_time", "10", "-hls_playlist_type", "vod", 
                hls_output,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode()}")
                video.status = "failed"
            else:
                # 4. Upload HLS segments and playlist
                for filename in os.listdir(output_dir):
                    local_file = f"{output_dir}/{filename}"
                    s3_key = f"processed/{video.id}/{filename}"
                    storage_service.upload_file(local_file, s3_key)
                
                video.status = "completed"
                video.hls_url = f"{settings.S3_PUBLIC_ENDPOINT_URL}/{settings.S3_BUCKET}/processed/{video.id}/index.m3u8"
            
            session.add(video)
            session.commit()
        except Exception as e:
            print(f"Error in worker: {e}")
            video.status = "failed"
            session.add(video)
            session.commit()
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            shutil.rmtree(output_dir, ignore_errors=True)
            
    print(f"Finished processing for video {video_id}")

class WorkerSettings:
    functions = [process_video]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
