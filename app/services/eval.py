import mlflow
from .config import MLFLOW_TRACKING_URI, MLFLOW_ARTIFACT_LOCATION

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
exp = mlflow.get_experiment_by_name("smart_files_agent")
if not exp:
    mlflow.create_experiment("smart_files_agent", artifact_location=f"file://{MLFLOW_ARTIFACT_LOCATION}")
mlflow.set_experiment("smart_files_agent")

try:
    from main_agent import bot
except ImportError:
    from .main_agent import bot

def evaluate():
    queries = [
        "Find me a file on h20gpt?",
        "How many sick leaves do i get?"
    ]

    with mlflow.start_run():
        for q in queries:
            res = bot(q)
            score = len(res)  # simple proxy metric

            mlflow.log_param("query", q)
            mlflow.log_metric("response_length", score)

if __name__ == "__main__":
    evaluate()