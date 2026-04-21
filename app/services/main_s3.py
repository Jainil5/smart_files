import os
import mimetypes
from typing import Optional
from boto3.session import Session
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from services.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


def upload_file_s3(file_path: str, expires_in: int = 3600) -> Optional[str]:
    try:
        # AWS config
        session = Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        s3_client = session.client("s3")
        bucket_name = os.getenv("AWS_BUCKET_NAME")

        file_name = os.path.basename(file_path)

        # Detect content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"

        # Upload file with inline support
        s3_client.upload_file(
            file_path,
            bucket_name,
            file_name,
            ExtraArgs={
                "ContentType": content_type,
                "ContentDisposition": "inline"
            }
        )

        logger.info(f"Uploaded: {file_name}")

        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": file_name,
                "ResponseContentDisposition": "inline",
                "ResponseContentType": content_type
            },
            ExpiresIn=expires_in
        )

        return url

    except FileNotFoundError:
        logger.error("File not found")
    except ClientError as e:
        logger.error(f"AWS Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

    return None


# ✅ Usage
if __name__ == "__main__":
    file_path = "/Users/jainil/Documents/development/smart_files/app/test/password.txt"
    
    url = upload_file_s3(file_path)
    
    if url:
        print("File URL:", url)