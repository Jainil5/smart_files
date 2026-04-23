import os
import sys
import requests

# --- Path Optimization ---
_SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_SERVICES_DIR)
_ROOT_DIR = os.path.dirname(_APP_DIR)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from services.config import DOCS_DIR
from services.main_db import get_all_files_from_db


def download_all_from_s3():
    """
    Fetches all file records from MongoDB and downloads files from their hosted links
    into the local app/data/documents folder.
    """
    # Ensure local documents directory exists
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    files = get_all_files_from_db()
    if not files:
        return

    download_count = 0
    skipped_count = 0
    
    for doc in files:
        hosted_link = doc.get("hosted_link")
        file_name = doc.get("file_name")
        
        # Validate link
        if not hosted_link or not hosted_link.startswith("http"):
            skipped_count += 1
            continue
            
        target_path = os.path.join(DOCS_DIR, file_name)
        
        # Download the file
        response = requests.get(hosted_link, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024): # 1MB chunks
                if chunk:
                    f.write(chunk)
            
        download_count += 1

if __name__ == "__main__":
    download_all_from_s3()
