import os
import mimetypes
from typing import Optional
from boto3.session import Session
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from services.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


def upload_file_s3(file_path: str, expires_in: int = 86400) -> Optional[str]:
    try:
        session = Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        s3_client = session.client("s3")
        bucket_name = os.getenv("AWS_BUCKET_NAME")

        file_name = os.path.basename(file_path)

        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"

        s3_client.upload_file(
            file_path,
            bucket_name,
            file_name,
            ExtraArgs={
                "ContentType": content_type,
                "ContentDisposition": "inline"
            }
        )

        print(f"Uploaded: {file_name}")

        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": file_name,
                "ResponseContentType": content_type,
                "ResponseContentDisposition": f'inline; filename="{file_name}"'
            },
            ExpiresIn=expires_in
        )

        return url

    except FileNotFoundError:
        print("File not found")
    except ClientError as e:
        print(f"AWS Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None