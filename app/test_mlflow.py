import mlflow
import os
import sys

# Add app to path
sys.path.append(os.path.join(os.getcwd(), "app"))

from services.monitoring import start_run, log_agent_query, log_agent_response

def test_mlflow():
    print("Testing MLflow connection...")
    print(f"Tracking URI: {mlflow.get_tracking_uri()}")
    
    try:
        with start_run("test_manual_run"):
            log_agent_query("Hello test query")
            log_agent_response("This is a test response to verify MLflow UI")
        print("✅ Run completed successfully!")
        
        experiments = mlflow.search_experiments()
        print("\nExisting Experiments:")
        for exp in experiments:
            print(f" - {exp.name} (ID: {exp.experiment_id})")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_mlflow()
