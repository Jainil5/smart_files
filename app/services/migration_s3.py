import os, sys
_SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_SERVICES_DIR)
_ROOT_DIR = os.path.dirname(_APP_DIR)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from services.config import DOCS_DIR
from services.main_db import get_all_files_from_db, update_file_hosted_link
from services.main_s3 import upload_file_s3


def update_db_s3_links():

    print("Starting MongoDB S3 link synchronization...")
    
    files = get_all_files_from_db()
    if not files:
        print("No files found in database to migrate.")
        return

    total_updated = 0
    
    for doc in files:
        local_path = doc.get("local_path")
        file_name = doc.get("file_name")
        current_hosted = doc.get("hosted_link", "")
        
        # Skip if already an S3 link (optional, but safer)
        # if "s3.amazonaws.com" in current_hosted:
        #     continue

        # Path Resolution Logic
        target_path = local_path
        if not target_path or not os.path.exists(target_path):
            # Try finding it in the standard data directory
            from services.config import DATA_DIR
            alt_path = os.path.join(DATA_DIR, "documents", file_name)
            if os.path.exists(alt_path):
                target_path = alt_path
            else:
                print(f"Could not locate file locally: {file_name}")
                continue
            
        # Get hosted URL using the requested function
        new_link = upload_file_s3(target_path)
        
        if new_link:
            # Update DB for all versions of this file path
            count = update_file_hosted_link(local_path, new_link, platform="aws")
            if count > 0:
                print(f"Success: Updated {file_name} with S3 link.")
                total_updated += 1
            else:
                print(f"DB update failed for: {file_name}")
        else:
            print(f"Migration failed for: {file_name}")

    print(f"Synchronization complete. Files updated: {total_updated}")

if __name__ == "__main__":
    update_db_s3_links()
