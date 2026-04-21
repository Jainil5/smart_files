from pymongo import MongoClient
from datetime import datetime
import os
import uuid

# ------------------ CONFIG ------------------ #
MONGO_URI = "mongodb+srv://jainil5:8aH8MG3Pb8AUZHen@documents-cluster.lp8qt26.mongodb.net/"
DB_NAME = "files_db"
INDEX_COLLECTION_NAME = "files_collection"
UPLOADED_COLLECTION_NAME = "uploaded_files"


# ------------------ CONNECTION ------------------ #
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    index_collection = db[INDEX_COLLECTION_NAME]
    uploaded_collection = db[UPLOADED_COLLECTION_NAME]

    # indexes (important for performance)
    index_collection.create_index("file_hash")
    index_collection.create_index("file_name")
    index_collection.create_index("file_id")
    index_collection.create_index("hosted_link")

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")


# ------------------ UTILS ------------------ #
def generate_file_id():
    return str(uuid.uuid4())


# ------------------ STORE LOCAL FILE ------------------ #
def upload_local_file(local_path, file_hash):
    try:
        existing = uploaded_collection.find_one({"file_hash": file_hash})
        if existing:
            return existing["_id"]

        with open(local_path, "rb") as f:
            file_data = f.read()

        data = {
            "file_name": os.path.basename(local_path),
            "file_data": file_data,
            "file_hash": file_hash,
            "created_at": datetime.utcnow()
        }

        result = uploaded_collection.insert_one(data)
        return result.inserted_id

    except Exception as e:
        print("Upload error:", e)
        return None


# ------------------ MAIN INSERT FUNCTION ------------------ #
def add_file_to_db(file_id, file_name, file_type,
                   source_platform, local_path,
                   file_hash, hosted_link):

    try:
        # -------------------------------
        # STEP 1: HASH CHECK
        # -------------------------------
        same_hash_files = list(index_collection.find({"file_hash": file_hash}))

        if same_hash_files:
            for f in same_hash_files:
                if f["file_name"] == file_name:
                    return 2, "Duplicate file (same hash + same name)"

            # Same hash but different name → NEW FILE
            # Use passed file_id
            version = 0

        else:
            # -------------------------------
            # STEP 2: VERSION CHECK
            # -------------------------------
            existing_files = list(index_collection.find({
                "$or": [
                    {"hosted_link": hosted_link},
                    {"file_name": file_name}
                ]
            }))

            if existing_files:
                latest = max(existing_files, key=lambda x: x.get("version", 0))

                # Override file_id (IMPORTANT)
                file_id = latest["file_id"]
                version = latest["version"] + 1

                # mark old latest false
                index_collection.update_many(
                    {"file_id": file_id, "is_latest": True},
                    {"$set": {"is_latest": False}}
                )

            else:
                # completely new file
                version = 0
                # use passed file_id

        # -------------------------------
        # STEP 3: INSERT
        # -------------------------------
        data = {
            "file_id": file_id,
            "file_name": file_name,
            "version": version,
            "file_hash": file_hash,
            "hosted_link": hosted_link,
            "local_path": local_path,
            "file_type": file_type,
            "source_platform": source_platform,
            "is_latest": True,
            "file_size": os.path.getsize(local_path) if os.path.exists(local_path) else None,
            "created_at": datetime.utcnow()
        }

        index_collection.insert_one(data)

        return 1, f"Inserted (version {version})"

    except Exception as e:
        return 0, str(e)


# ------------------ FETCH ALL FILES ------------------ #
def get_all_files_from_db():
    try:
        # Fetch all documents from the correct collection (index_collection)
        files_cursor = index_collection.find({"is_latest": True})
        file_list = []
        
        for doc in files_cursor:
            # Convert MongoDB ObjectId to string for JSON compatibility
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
            # Convert datetime to string for JSON compatibility
            if "created_at" in doc and isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].isoformat()
                
            file_list.append(doc)
            
        return file_list
    except Exception as e:
        print(f"Database Error: {e}")
        return []
# ------------------ FETCH FUNCTIONS ------------------ #
def get_file_id_from_path(local_path: str):
    result = index_collection.find_one({"local_path": local_path, "is_latest": True})
    return result["file_id"] if result else None


def hosted_from_id(file_id: str):
    result = index_collection.find_one({"file_id": file_id, "is_latest": True})
    return result["hosted_link"] if result else None


def hosted_from_local(local_path: str):
    result = index_collection.find_one({"local_path": local_path, "is_latest": True})
    return result["hosted_link"] if result else None

def get_versions(file_id: str):
    files = list(index_collection.find({"file_id": file_id}).sort("version", 1))
    return files if files else []