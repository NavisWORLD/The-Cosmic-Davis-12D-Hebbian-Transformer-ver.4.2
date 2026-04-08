import traceback
import sys

sys.path.insert(0, r"d:\Cosmos")
sys.path.insert(0, r"d:\Cosmos\Cosmos\web")

try:
    from routes.orchestrator import router
    print("Success!")
except Exception:
    traceback.print_exc()
