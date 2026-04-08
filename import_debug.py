import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("--- STARTING IMPORT TEST ---")
try:
    from Cosmos.web.routes.orchestrator import router
    print("SUCCESS: Orchestrator Router imported successfully.")
    print(f"Prefix: {router.prefix}")
except Exception as e:
    print("FAILED: Orchestrator Router import failed.")
    traceback.print_exc()
print("--- ENDING IMPORT TEST ---")
