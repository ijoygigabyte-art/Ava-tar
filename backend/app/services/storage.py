import boto3
import json
from botocore.config import Config
from app.core.config import settings

class StorageService:
    def __init__(self):
        # Configuration for better compatibility with MinIO
        s3_config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"}
        )

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
            config=s3_config
        )
        # Separate client for browser-facing presigned URLs (uses localhost, not Docker hostname)
        self.s3_public_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_PUBLIC_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
            config=s3_config
        )
        self._ensure_bucket_ready()

    def _ensure_bucket_ready(self):
        try:
            self.s3_client.head_bucket(Bucket=settings.S3_BUCKET)
        except Exception:
            self.s3_client.create_bucket(Bucket=settings.S3_BUCKET)

        # Ensure processed HLS output can be fetched by the browser player.
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{settings.S3_BUCKET}/*"],
                }
            ],
        }
        self.s3_client.put_bucket_policy(
            Bucket=settings.S3_BUCKET,
            Policy=json.dumps(policy),
        )

    def generate_presigned_url(self, key: str, content_type: str = None, expiration: int = 3600):
        try:
            params = {"Bucket": settings.S3_BUCKET, "Key": key}
            if content_type:
                params["ContentType"] = content_type
            
            url = self.s3_public_client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=expiration,
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def download_file(self, key: str, local_path: str):
        try:
            self.s3_client.download_file(settings.S3_BUCKET, key, local_path)
            return True
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

    def upload_file(self, local_path: str, key: str):
        try:
            self.s3_client.upload_file(local_path, settings.S3_BUCKET, key)
            return True
        except Exception as e:
            print(f"Error uploading file: {e}")
            return False

storage_service = StorageService()
