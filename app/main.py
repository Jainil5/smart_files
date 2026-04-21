from fastapi import FastAPI, HTTPException, UploadFile, File
import os, shutil, logging, time, csv
from datetime import datetime
from pydantic import BaseModel
from services.main_agent import bot
from services.new_link import process_link_api
from services.main_db import get_all_files_from_db
from services.embedder import embed_file
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AI File System API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
app.mount("/logs", StaticFiles(directory=LOG_DIR), name="logs")

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "app.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

CSV_FILE = os.path.join(LOG_DIR, "api_logs.csv")

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


@app.post("/upload")
def upload_file(req: UploadRequest):
    start = time.time()
    try:
        logging.info(f"/upload called | path={req.path}")

        result = process_link_api(req.path)
        upload_result = result.get("data", {}).get("upload_result")
        local_path = result.get("data", {}).get("local_path")

        if local_path and upload_result != "duplicate":
            embed_file(local_path)

        latency = time.time() - start
        logging.info(f"/upload success | latency={latency}")
        log_to_csv("/upload", "success", latency, str(upload_result))

        return result

    except Exception as e:
        latency = time.time() - start
        logging.error(f"/upload error | {str(e)}")
        log_to_csv("/upload", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-file")
async def upload_physical_file(file: UploadFile = File(...)):
    start = time.time()
    try:
        logging.info(f"/upload-file called | filename={file.filename}")

        save_path = os.path.join(DOCS_DIR, file.filename)

        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = process_link_api(save_path)
        upload_result = result.get("data", {}).get("upload_result")

        if upload_result != "duplicate":
            embed_file(save_path)

        latency = time.time() - start
        logging.info(f"/upload-file success | latency={latency}")
        log_to_csv("/upload-file", "success", latency, file.filename)

        return result

    except Exception as e:
        latency = time.time() - start
        logging.error(f"/upload-file error | {str(e)}")
        log_to_csv("/upload-file", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
def query_agent(req: QueryRequest):
    start = time.time()
    try:
        logging.info(f"/query called | query={req.query}")

        res = bot(req.query)

        latency = time.time() - start
        logging.info(f"/query success | latency={latency}")
        log_to_csv("/query", "success", latency, req.query)

        return {
            "status": "success",
            "response": res
        }

    except Exception as e:
        latency = time.time() - start
        logging.error(f"/query error | {str(e)}")
        log_to_csv("/query", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
async def fetch_files():
    start = time.time()
    try:
        logging.info("/files called")

        result = get_all_files_from_db()

        latency = time.time() - start
        logging.info(f"/files success | latency={latency}")
        log_to_csv("/files", "success", latency)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        latency = time.time() - start
        logging.error(f"/files error | {str(e)}")
        log_to_csv("/files", "error", latency, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"status": "ok"}