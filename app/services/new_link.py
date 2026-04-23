import os
import sys
import re
import requests
import hashlib
import uuid
from urllib.parse import urlparse
import gdown
from fastapi import HTTPException
from migration_s3 import get_s3_hosted_url
from services.config import DOCS_DIR
from services.main_db import add_file_to_db, upload_local_file

# ------------------ CONFIG ------------------ #
LOCAL_DATA_DIR = DOCS_DIR


# ------------------ RESPONSE FORMAT ------------------ #
def success(data):
    return {
        "status": "success",
        "type": "upload",
        "data": data,
        "message": ""
    }


def fail(msg, code=500):
    raise HTTPException(status_code=code, detail=msg)


# ------------------ UTILS ------------------ #

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def get_filename(url):
    return os.path.basename(urlparse(url).path)


def get_file_type(name):
    return os.path.splitext(name)[1].replace(".", "").lower()


def file_hash(path):
    if not path or not os.path.exists(path):
        return ""

    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_file_id():
    return str(uuid.uuid4())


# ------------------ PLATFORM DETECTION ------------------ #

def detect_platform(url):
    if "drive.google.com" in url:
        return "drive"
    if url.startswith("s3://"):
        return "aws"
    if url.startswith("gs://"):
        return "gcp"
    if "blob.core.windows.net" in url:
        return "azure"
    if url.startswith("http"):
        return "http"
    return "unknown"


# ------------------ DOWNLOADERS ------------------ #

def download_s3_via_http(s3_uri, out_dir):
    try:
        ensure_dir(out_dir)

        clean_uri = s3_uri.replace("s3://", "")
        bucket, key = clean_uri.split("/", 1)

        file_name = os.path.basename(key)
        path = os.path.join(out_dir, file_name)

        urls = [
            f"https://{bucket}.s3.amazonaws.com/{key}",
            f"https://s3.amazonaws.com/{bucket}/{key}",
            f"https://{bucket}.s3.ap-south-1.amazonaws.com/{key}",
        ]

        for url in urls:
            try:
                r = requests.get(url, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                    return path
            except:
                continue

        return None

    except Exception:
        return None


def download_gcp_via_http(gs_uri, out_dir):
    try:
        ensure_dir(out_dir)

        clean_uri = gs_uri.replace("gs://", "")
        bucket, key = clean_uri.split("/", 1)

        file_name = os.path.basename(key)
        path = os.path.join(out_dir, file_name)

        urls = [
            f"https://storage.googleapis.com/{bucket}/{key}",
            f"https://{bucket}.storage.googleapis.com/{key}",
        ]

        for url in urls:
            try:
                r = requests.get(url, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                    return path
            except:
                continue

        return None

    except Exception:
        return None


def download_azure_via_http(url, out_dir):
    try:
        ensure_dir(out_dir)

        file_name = os.path.basename(urlparse(url).path)
        path = os.path.join(out_dir, file_name)

        r = requests.get(url, stream=True, timeout=30)

        if r.status_code == 200:
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            return path

        return None

    except Exception:
        return None


def download_http(url, out_dir):
    try:
        ensure_dir(out_dir)

        file_name = get_filename(url) or "file"
        path = os.path.join(out_dir, file_name)

        r = requests.get(url, stream=True, timeout=30)

        if r.status_code != 200:
            return None

        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

        return path

    except Exception:
        return None


# ------------------ GOOGLE DRIVE ------------------ #

def extract_drive_id(url):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None


def download_drive(url, out_dir):
    try:
        ensure_dir(out_dir)

        file_id = extract_drive_id(url)
        if not file_id:
            return None

        return gdown.download(
            f"https://drive.google.com/uc?id={file_id}",
            output=out_dir,
            quiet=True
        )
    except:
        return None


# ------------------ MAIN FUNCTION ------------------ #

def process_link_api(input_path: str):
    try:
        ensure_dir(LOCAL_DATA_DIR)

        # ---------- LOCAL FILE ---------- #
        if os.path.exists(input_path):

            platform = "local"

            file_name = os.path.basename(input_path)
            new_path = os.path.join(LOCAL_DATA_DIR, file_name)

            # Avoid self-copy when file is already in the target directory
            if os.path.abspath(input_path) != os.path.abspath(new_path):
                with open(input_path, "rb") as src, open(new_path, "wb") as dst:
                    dst.write(src.read())

            path = new_path

            hash_val = file_hash(path)

            mongo_id = upload_local_file(path, hash_val)
            if not mongo_id:
                fail("Mongo upload failed")

            hosted_link = f"mongo://{mongo_id}"

        # ---------- REMOTE FILE ---------- #
        else:
            platform = detect_platform(input_path)

            if platform == "aws":
                path = download_s3_via_http(input_path, LOCAL_DATA_DIR)

            elif platform == "gcp":
                path = download_gcp_via_http(input_path, LOCAL_DATA_DIR)

            elif platform == "azure":
                path = download_azure_via_http(input_path, LOCAL_DATA_DIR)

            elif platform == "drive":
                path = download_drive(input_path, LOCAL_DATA_DIR)

            elif platform == "http":
                path = download_http(input_path, LOCAL_DATA_DIR)

            else:
                fail("Unsupported platform")

            if not path:
                fail("Download failed")

            hash_val = file_hash(path)
            hosted_link = input_path

        # ---------- METADATA ---------- #
        file_name = os.path.basename(path)
        file_type = get_file_type(file_name)
        file_id = generate_file_id()
        s3_link = get_s3_hosted_url(path)
        status, message = add_file_to_db(
            file_id=file_id,
            file_name=file_name,
            file_type=file_type,
            source_platform=platform,
            local_path=path,
            file_hash=hash_val,
            hosted_link=s3_link
        )

        if not status:
            fail(message)

        # Map status codes to human-readable result
        # status=2 → exact duplicate (same hash + name)
        # status=1, version 0 → brand new file
        # status=1, version N>0 → updated/versioned file
        if status == 2:
            upload_result = "duplicate"
        elif "version 0" in message:
            upload_result = "new"
        else:
            upload_result = "versioned"

        # ---------- SUCCESS RESPONSE ---------- #
        return success({
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "platform": platform,
            "local_path": path,
            "hosted_link": hosted_link,
            "db_status": status,
            "upload_result": upload_result,
            "message": message
        })

    except HTTPException:
        raise

    except Exception as e:
        fail(str(e))
