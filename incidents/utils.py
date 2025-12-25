import boto3
from botocore.client import Config
from django.conf import settings
import uuid
import logging

logger = logging.getLogger(__name__)


class MinIOClient:
    def __init__(self):
        scheme = "https" if settings.MINIO_USE_SSL else "http"
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"{scheme}://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist and set public policy"""
        from botocore.exceptions import ClientError
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404' or error_code == 'NoSuchBucket':
                try:
                    logger.info(f"Creating bucket: {self.bucket_name}")
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                except Exception as create_error:
                    logger.exception(f"Error creating bucket: {create_error}")
                    raise
            else:
                logger.exception(f"Error checking bucket: {e}")
                raise
        except Exception as e:
            logger.exception(f"Unexpected error checking bucket: {e}")
            raise
        
        # Ensure bucket is public
        try:
            self._set_public_policy()
            logger.info(f"Set public policy for bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Could not set public policy: {e}")
    
    def _set_public_policy(self):
        """Set bucket policy to allow public read access"""
        import json
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                }
            ]
        }
        self.s3_client.put_bucket_policy(
            Bucket=self.bucket_name,
            Policy=json.dumps(policy)
        )

    def upload_file(self, file, folder='incidents'):
        """
        Upload file to MinIO
        Args:
            file: Django UploadedFile object
            folder: folder name in bucket
        Returns:
            str: Public URL of uploaded file
        """
        try:
            # Generate unique filename
            ext = file.name.split('.')[-1] if '.' in file.name else 'jpg'
            filename = f"{folder}/{uuid.uuid4()}.{ext}"
            
            # Upload to MinIO
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                filename,
                ExtraArgs={'ContentType': file.content_type}
            )
            
            # Generate public URL
            scheme = "https" if settings.MINIO_USE_SSL else "http"
            url = f"{scheme}://{settings.MINIO_PUBLIC_ENDPOINT}/{self.bucket_name}/{filename}"
            return url
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def delete_file(self, file_url):
        """Delete file from MinIO given its URL"""
        try:
            # Extract key from URL
            key = file_url.split(f"/{self.bucket_name}/")[-1]
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted file: {key}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")


# Lazy singleton instance
_minio_client = None

def get_minio_client():
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client
