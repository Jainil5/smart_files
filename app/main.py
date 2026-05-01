from fastapi import FastAPI, HTTPException, UploadFile, File
import os, shutil, logging, time, csv, sys
from datetime import datetime
from pydantic import BaseModel

# --- Path Fix (Must be BEFORE other service imports) ---
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_BASE_DIR)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from services.config import DATA_DIR, DOCS_DIR, LOGS_DIR, API_PERFORMANCE_CSV
from services.main_agent import bot
from services.file_rag import run_rag
from services.new_link import process_link_api
from services.main_db import get_all_files_from_db
from services.embedder import embed_file
from services.logger import get_logger
from fastapi.staticfiles import StaticFiles

logger = get_logger("app_main")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI File System API")

# Enable CORS for all origins (optimize as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
app.mount("/logs", StaticFiles(directory=LOGS_DIR), name="logs")

CSV_FILE = API_PERFORMANCE_CSV

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "endpoint", "status", "latency", "details"])


def log_to_csv(endpoint, status, latency, details=""):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow(),
            endpoint,
            status,
            round(latency, 3),
            details
        ])


class UploadRequest(BaseModel):
    path: str


class QueryRequest(BaseModel):
    query: str

class RAGRequest(BaseModel):
    file_path: str
    query: str

@app.post("/upload")
def upload_file(req: UploadRequest):
    start = time.time()
    try:
        logger.info(f"/upload called | path={req.path}")

        result = process_link_api(req.path)
        upload_result = result.get("data", {}).get("upload_result")
        local_path = result.get("data", {}).get("local_path")

        if local_path and upload_result != "duplicate":
            embed_file(local_path)

        latency = time.time() - start
        logger.info(f"/upload success | latency={latency}")
        log_to_csv("/upload", "success", latency, str(upload_result))

        # Response Structure:
        # {
        #   "status": "success",
        #   "type": "upload",
        #   "data": { "file_id": "...", "file_name": "...", "upload_result": "success/duplicate", ... }
        # }
        print(f"DEBUG: /upload response -> {result}")
        return result

    except Exception as e:
        latency = time.time() - start
        logger.error(f"/upload error | {str(e)}")
        log_to_csv("/upload", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-file")
async def upload_physical_file(file: UploadFile = File(...)):
    start = time.time()
    try:
        logger.info(f"/upload-file called | filename={file.filename}")

        save_path = os.path.join(DOCS_DIR, file.filename)

        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = process_link_api(save_path)
        upload_result = result.get("data", {}).get("upload_result")

        if upload_result != "duplicate":
            embed_file(save_path)

        latency = time.time() - start
        logger.info(f"/upload-file success | latency={latency}")
        log_to_csv("/upload-file", "success", latency, file.filename)

        # Response Structure: Same as /upload
        print(f"DEBUG: /upload-file response -> {result}")
        return result

    except Exception as e:
        latency = time.time() - start
        logger.error(f"/upload-file error | {str(e)}")
        log_to_csv("/upload-file", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
def query_agent(req: QueryRequest):
    start = time.time()
    try:
        logger.info(f"/query called | query={req.query}")

        res = bot(req.query)

        latency = time.time() - start
        logger.info(f"/query success | latency={latency}")
        log_to_csv("/query", "success", latency, req.query)

        # Response Structure:
        # {
        #   "status": "success",
        #   "response": "Answer from AI agent..."
        # }
        response_data = {
            "status": "success",
            "response": res
        }
        print(f"DEBUG: /query response -> {response_data}")
        return response_data

    except Exception as e:
        latency = time.time() - start
        logger.error(f"/query error | {str(e)}")
        log_to_csv("/query", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))
  
@app.post("/file-rag")
def file_rag_query(req: RAGRequest):
    start = time.time()
    try:
        logger.info(f"/file-rag called | file={req.file_path} | query={req.query}")
        result = run_rag(req.file_path, req.query)

        latency = time.time() - start
        logger.info(f"/file-rag success | latency={latency}")
        log_to_csv("/file-rag", "success", latency, req.file_path)

        response_data = {
            "status": "success",
            "response": result.get("response"),
            "file_name": result.get("file_name"),
            "file_path": result.get("file_path"),
            "hosted_link": result.get("hosted_link")
        }

        print(f"DEBUG: /file-rag response -> {response_data}")

        return response_data

    except Exception as e:
        latency = time.time() - start
        logger.error(f"/file-rag error | {str(e)}")
        log_to_csv("/file-rag", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
async def fetch_files():
    start = time.time()
    try:
        logger.info("/files called")

        result = get_all_files_from_db()

        latency = time.time() - start
        logger.info(f"/files success | latency={latency}")
        log_to_csv("/files", "success", latency)

        # Response Structure:
        # {
        #   "status": "success",
        #   "data": [ { "file_name": "...", "version": 0, ... } ]
        # }
        response_data = {
            "status": "success",
            "data": result
        }
        print(f"DEBUG: /files response -> {len(result)} files found")
        return response_data

    except Exception as e:
        latency = time.time() - start
        logger.error(f"/files error | {str(e)}")
        log_to_csv("/files", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "ok"}