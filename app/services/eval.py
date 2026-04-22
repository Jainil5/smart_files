import mlflow
try:
    from main_agent import bot
except ImportError:
    from .main_agent import bot

def evaluate():
    queries = [
        "What is in the document?",
        "Summarize the report"
    ]

    with mlflow.start_run():
        for q in queries:
            res = bot(q)
            score = len(res)  # simple proxy metric

            mlflow.log_param("query", q)
            mlflow.log_metric("response_length", score)

if __name__ == "__main__":
    evaluate()