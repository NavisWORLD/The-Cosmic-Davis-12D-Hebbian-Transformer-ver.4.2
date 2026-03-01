
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from cosmos.core.quantum_bridge import get_quantum_bridge
    print("Import successful.")
    
    qb = get_quantum_bridge()
    print(f"Bridge instance: {qb}")
    
    # Test the new connect method
    print("Testing .connect() method...")
    success = qb.connect()
    print(f"Connect result: {success}")
    
    if success:
        entropy = qb.get_entropy()
        print(f"Entropy retrieved: {entropy}")
    else:
        print("Connection failed (expected if no valid token, but method exists)")

except AttributeError as e:
    print(f"FAIL: AttributeError detected: {e}")
except Exception as e:
    print(f"ERROR: {e}")
