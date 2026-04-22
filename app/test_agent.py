import sys
import os

# Add app to path
sys.path.append(os.path.join(os.getcwd(), "app"))

from services.main_agent import bot

try:
    print("Testing Agent...")
    res = bot("Hello")
    print(f"Response: {res}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
