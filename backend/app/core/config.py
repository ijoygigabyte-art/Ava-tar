import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Video Stylization API"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    
    S3_BUCKET: str = os.getenv("S3_BUCKET")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY")
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL")
    S3_PUBLIC_ENDPOINT_URL: str = os.getenv("S3_PUBLIC_ENDPOINT_URL", "http://localhost:9000")
    FFMPEG_BIN: str = os.getenv("FFMPEG_BIN", "ffmpeg")
    
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN")

settings = Settings()
