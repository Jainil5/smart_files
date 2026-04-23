import mlflow
import time
import json
import os
import sys
from contextlib import contextmanager

from .config import MLFLOW_TRACKING_URI, LOGS_DIR, RAG_OUTPUT_JSON, MLFLOW_ARTIFACT_LOCATION

# ---------------- MLFLOW INIT ---------------- #
MLFLOW_ENABLED = True

try:
    # Set tracking URI using SQLite database backend
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # Ensure experiment exists with correct artifact location
    exp = mlflow.get_experiment_by_name("smart_files_agent")
    if not exp:
        mlflow.create_experiment(
            "smart_files_agent", 
            artifact_location=f"file://{MLFLOW_ARTIFACT_LOCATION}"
        )
    mlflow.set_experiment("smart_files_agent")
except Exception as e:
    print(f"⚠️ MLflow initialization failed: {e}")
    print("   -> Monitoring will be bypassed to allow the API to run.")
    MLFLOW_ENABLED = False


# ---------------- RUN CONTEXT ---------------- #

@contextmanager
def start_run(run_name: str = "rag_run"):
    if not MLFLOW_ENABLED:
        yield
        return

    try:
        with mlflow.start_run(run_name=run_name):
            start_time = time.time()
            yield
            total_time = time.time() - start_time
            mlflow.log_metric("total_time", total_time)
    except Exception as e:
        print(f"⚠️ MLflow run error: {e}")
        yield


# ---------------- CONFIG LOG ---------------- #

def log_config(embedding_model: str, top_k: int):
    if not MLFLOW_ENABLED: return
    try:
        mlflow.log_param("embedding_model", embedding_model)
        mlflow.log_param("top_k", top_k)
    except: pass


# ---------------- LATENCY ---------------- #

def log_latency(retrieval_time=None, llm_time=None):
    if not MLFLOW_ENABLED: return
    try:
        if retrieval_time is not None:
            mlflow.log_metric("retrieval_time", retrieval_time)
        if llm_time is not None:
            mlflow.log_metric("llm_time", llm_time)
    except: pass


# ---------------- FILE TRACKING ---------------- #

def log_selected_file(file_name: str):
    if not MLFLOW_ENABLED: return
    try:
        mlflow.log_param("selected_file", file_name)
    except: pass


def log_rag_output(query, response, file_name):
    """Logs RAG output as both tags for the UI and an artifact for detailed history."""
    if not MLFLOW_ENABLED: return
    try:
        # Tags appear in the MLflow Table View
        mlflow.set_tag("query", query[:250])  
        mlflow.set_tag("response_preview", response[:250])
        mlflow.set_tag("source_file", file_name)

        data = {
            "query": query,
            "response": response,
            "file": file_name,
            "timestamp": time.ctime()
        }

        # Artifact stores full content
        file_path = RAG_OUTPUT_JSON
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        mlflow.log_artifact(file_path)
    except: pass

def log_agent_query(query: str):
    if not MLFLOW_ENABLED: return
    try:
        mlflow.set_tag("user_query", query)
    except: pass

def log_agent_response(response: str):
    if not MLFLOW_ENABLED: return
    try:
        mlflow.set_tag("agent_response", response[:250])
    except: pass


# ---------------- TIMER ---------------- #

class Timer:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time