import os
import sys

# --- Path Optimization ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_APP_DIR)

# Project Structure
ROOT_DIR = _ROOT_DIR
APP_DIR = _APP_DIR
SERVICES_DIR = _CURRENT_DIR
MODELS_DIR = os.path.join(ROOT_DIR, "models")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
DATA_DIR = os.path.join(APP_DIR, "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
DATASETS_DIR = os.path.join(DATA_DIR, "datasets")

# Dataset CSVs
SALES_CSV = os.path.join(DATASETS_DIR, "clothing_sales_combined.csv")
HEALTH_CSV = os.path.join(DATASETS_DIR, "healthcare_dataset.csv")

# Ensure critical directories exist
for d in [MODELS_DIR, LOGS_DIR, DATA_DIR, DOCS_DIR, DATASETS_DIR]:
    os.makedirs(d, exist_ok=True)

# MLflow Configuration
MLFLOW_DB_PATH = os.path.join(MODELS_DIR, "mlflow.db")
MLFLOW_TRACKING_URI = f"sqlite:///{MLFLOW_DB_PATH}"
MLFLOW_ARTIFACT_LOCATION = os.path.join(MODELS_DIR, "mlruns")

# Logging Configuration
APP_RUNTIME_LOG = os.path.join(LOGS_DIR, "app_runtime.log")
API_PERFORMANCE_CSV = os.path.join(LOGS_DIR, "api_performance.csv")

# Temporary files
RAG_OUTPUT_JSON = os.path.join(LOGS_DIR, "rag_output.json")

# Ensure the root is in sys.path for absolute imports
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
