import mlflow
import time
import json
import os
from contextlib import contextmanager

# ---------------- CONFIG ---------------- #

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(ROOT_DIR, "models")
DB_PATH = os.path.join(MODELS_DIR, "mlflow.db")

# Set tracking URI using SQLite database backend
mlflow.set_tracking_uri(f"sqlite:///{DB_PATH}")

mlflow.set_experiment("smart_files_agent")


# ---------------- RUN CONTEXT ---------------- #

@contextmanager
def start_run(run_name: str = "rag_run"):
    with mlflow.start_run(run_name=run_name):
        start_time = time.time()
        yield
        total_time = time.time() - start_time
        mlflow.log_metric("total_time", total_time)


# ---------------- CONFIG LOG ---------------- #

def log_config(embedding_model: str, top_k: int):
    mlflow.log_param("embedding_model", embedding_model)
    mlflow.log_param("top_k", top_k)


# ---------------- LATENCY ---------------- #

def log_latency(retrieval_time=None, llm_time=None):
    if retrieval_time is not None:
        mlflow.log_metric("retrieval_time", retrieval_time)
    if llm_time is not None:
        mlflow.log_metric("llm_time", llm_time)


# ---------------- FILE TRACKING ---------------- #

def log_selected_file(file_name: str):
    mlflow.log_param("selected_file", file_name)


def log_rag_output(query, response, file_name):
    """Logs RAG output as both tags for the UI and an artifact for detailed history."""
    # Tags appear in the MLflow Table View
    mlflow.set_tag("query", query[:250])  # Tags have length limits
    mlflow.set_tag("response_preview", response[:250])
    mlflow.set_tag("source_file", file_name)

    data = {
        "query": query,
        "response": response,
        "file": file_name,
        "timestamp": time.ctime()
    }

    # Artifact stores full content
    file_path = "rag_output.json"
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    mlflow.log_artifact(file_path)

def log_agent_query(query: str):
    mlflow.set_tag("user_query", query)

def log_agent_response(response: str):
    mlflow.set_tag("agent_response", response[:250])



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