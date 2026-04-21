import os
import sys

# Ensure we can import from services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_db import get_all_files_from_db, update_file_hosted_link
from main_s3 import upload_file_s3
from logger import get_logger

logger = get_logger("migration_s3")

def migrate_all_to_s3():
    """
    Finds all unique files in the database, uploads them to S3, 
    and updates their links in MongoDB.
    """
    logger.info("🚀 Starting S3 link migration...")
    
    # Get all latest files from DB
    files = get_all_files_from_db()
    
    if not files:
        logger.warning("No files found in database to migrate.")
        return

    total_updated = 0
    
    for doc in files:
        local_path = doc.get("local_path")
        file_name = doc.get("file_name")
        
        # Smart Path Resolution
        target_path = local_path
        if not target_path or not os.path.exists(target_path):
            # Try relative to the app/data/documents folder
            alt_path = os.path.join("data", "documents", file_name)
            if os.path.exists(alt_path):
                target_path = alt_path
            else:
                logger.warning(f"File not found locally, skipping: {file_name}")
                continue
            
        logger.info(f"Uploading {file_name} to S3...")
        # Upload and get new presigned URL
        new_link = upload_file_s3(target_path)
        
        if new_link:
            # Update DB for all versions of this local_path (use the original local_path from DB for the filter)
            count = update_file_hosted_link(local_path, new_link, platform="aws")
            if count > 0:
                logger.info(f"✅ Updated {count} record(s) for {file_name}")
                total_updated += 1

            else:
                logger.error(f"❌ Failed to update DB for {file_name}")
        else:
            logger.error(f"❌ S3 Upload failed for {file_name}")

    logger.info(f"✨ Migration complete. Total unique files updated: {total_updated}")

if __name__ == "__main__":
    migrate_all_to_s3()
