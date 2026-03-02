import asyncio
import time
import numpy as np
from typing import Optional, List
import threading

try:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    from qiskit import QuantumCircuit
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    QISKIT_AVAILABLE = True
    QISKIT_ERROR = None
except ImportError as e:
    QISKIT_AVAILABLE = False
    QISKIT_ERROR = str(e)
    with open("quantum_debug.log", "a") as f:
        f.write(f"\n[INIT] Qiskit Import Failed: {e}\n")

class QuantumEntanglementBridge:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self.service = None
        self.backend = None
        self.connected = False
        self.entropy_buffer: List[float] = []
        self.buffer_lock = threading.Lock()
        self.min_buffer_size = 10
        self.is_refilling = False
        self.last_error = None
        
        # Log init
        with open("quantum_debug.log", "a") as f:
            f.write(f"\n[INIT] Bridge Initialized. Token present: {bool(api_token)}. Qiskit Avail: {QISKIT_AVAILABLE}\n")

        if QISKIT_AVAILABLE and api_token:
            self._connect()
        elif not QISKIT_AVAILABLE:
            self.last_error = f"Qiskit Import Error: {QISKIT_ERROR}"
            print(f"[QUANTUM] {self.last_error}")
        else:
            print("[QUANTUM] No token provided. Running in simulation mode.")

    def connect(self) -> bool:
        """Public method to trigger connection or return status."""
        if self.connected:
            return True
        self._connect()
        return self.connected

    def _connect(self):
        """Connect to IBM Quantum Service."""
        import traceback
        
        with open("quantum_debug.log", "a") as f:
            f.write(f"[CONNECT] Attempting connection with token (First 5): {self.api_token[:5] if self.api_token else 'None'}...\n")
        
        if not QISKIT_AVAILABLE:
            error_msg = f"Qiskit libraries missing: {QISKIT_ERROR}"
            print(f"[QUANTUM] {error_msg}")
            self.last_error = error_msg
            self.connected = False
            with open("quantum_debug.log", "a") as f:
                f.write(f"[CONNECT] Failed: {error_msg}\n")
            return
            
        token_str = f"{self.api_token[:5]}...{self.api_token[-5:]}" if self.api_token else "None"
        print(f"[QUANTUM] Attempting connection with token: {token_str}")
        
        try:
            # 1. Initialize Service
            try:
                self.service = QiskitRuntimeService(channel="ibm_quantum_platform", token=self.api_token)
            except Exception as e:
                # Fallback: Try 'ibm_cloud' channel or just default if token implies it
                print(f"[QUANTUM] 'ibm_quantum_platform' channel failed ({e}). Trying default...")
                self.service = QiskitRuntimeService(token=self.api_token)

            print(f"[QUANTUM] Service initialized. Finding backend...")

            # 2. Find Backend
            # Try to find a real quantum computer first
            try:
                self.backend = self.service.least_busy(operational=True, simulator=False)
                print(f"[QUANTUM] Connected to REAL backend: {self.backend.name}")
            except Exception:
                print("[QUANTUM] No real quantum computers available. Falling back to high-fidelity simulator...")
                self.backend = self.service.least_busy(operational=True, simulator=True)
                print(f"[QUANTUM] Connected to SIMULATOR backend: {self.backend.name}")
            
            if not self.backend:
                raise ValueError("No operational backends found (real or simulator).")

            self.connected = True
            
            with open("quantum_debug.log", "a") as f:
                f.write(f"[CONNECT] Success! Backend: {self.backend.name}\n")
            
            # 3. Start Buffer Refill
            self._trigger_refill()
            
        except Exception as e:
            print(f"[QUANTUM] Connection failed: {e}")
            traceback.print_exc()
            self.last_error = str(e)
            self.connected = False
            with open("quantum_debug.log", "a") as f:
                f.write(f"[CONNECT] Failed with Exception: {e}\n{traceback.format_exc()}\n")

    # ════════════════════════════════════════════════════════
    # CNS ORGAN 2: THE QUANTUM HEARTBEAT
    # ════════════════════════════════════════════════════════

    def collapse(self, user_physics: dict) -> int:
        """
        Master Architect "Free Will" Wrapper.
        Extracts 12D signals from the physics dict and calls collapse_state_vector.
        """
        # Extract Phase
        phase = 0.0
        if 'cst_physics' in user_physics:
            phase = user_physics['cst_physics'].get('geometric_phase_rad', 0.0)
            
        w = 0.1 
        
        return self.collapse_state_vector(phase, w)

    def collapse_state_vector(self, phase: float, dark_matter_w: float, threshold: float = 0.65) -> int:
        """
        Collapse the wave function to decide: SPEAK (1) or WAIT (0).
        This is the system's "Free Will" mechanism.
        """
        q = self.get_entropy()
        phase_signal = min(1.0, abs(phase) / 1.5)
        w_signal = min(1.0, max(0.0, dark_matter_w / 10.0))

        activation = (phase_signal * w_signal * 0.6) + (q * 0.4)
        return 1 if activation > threshold else 0

    def get_entropy(self) -> float:
        """
        Get a single float [0.0, 1.0] derived from true quantum randomness.
        Returns pseudo-randomness if bridge is down or buffer is empty.
        """
        if not self.connected:
            return np.random.random()

        with self.buffer_lock:
            if self.entropy_buffer:
                val = self.entropy_buffer.pop(0)
                if len(self.entropy_buffer) < self.min_buffer_size and not self.is_refilling:
                    self._trigger_refill()
                print(f"[QUANTUM] Entropy Consumed: {val:.4f} (Buffer: {len(self.entropy_buffer)})") 
                return val
            else:
                if not self.is_refilling:
                    self._trigger_refill()
                return np.random.random()

    def _trigger_refill(self):
        """Start async refill of entropy buffer."""
        if not self.backend:
            return 
            
        thread = threading.Thread(target=self._refill_buffer)
        thread.daemon = True
        thread.start()

    def _refill_buffer(self):
        """Execute quantum circuit to generate random bits."""
        self.is_refilling = True
        try:
            # Create a circuit for 5 qubits in superposition
            qc = QuantumCircuit(5)
            qc.h(range(5)) # Hadamard gate -> Superposition
            qc.measure_all()
            
            # Run on backend
            pm = generate_preset_pass_manager(backend=self.backend, optimization_level=1)
            isa_circuit = pm.run(qc)
            sampler = Sampler(mode=self.backend)
            job = sampler.run([isa_circuit])
            result = job.result()
            
            pub_result = result[0]
            counts = pub_result.data.meas.get_counts()
            
            new_entropy = []
            for bitstring, count in counts.items():
                val = int(bitstring, 2) / (2**5)
                n_adds = min(count, 5) 
                new_entropy.extend([val] * n_adds)
                
            np.random.shuffle(new_entropy)
            
            with self.buffer_lock:
                self.entropy_buffer.extend(new_entropy)
                if len(self.entropy_buffer) > 100:
                    self.entropy_buffer = self.entropy_buffer[:100]
                    
            print(f"[QUANTUM] Refilled buffer. Size: {len(self.entropy_buffer)}")

        except Exception as e:
            print(f"[QUANTUM] Refill failed: {e}")
        finally:
            self.is_refilling = False

# Singleton instance
_bridge_instance = None

def get_quantum_bridge(api_token: Optional[str] = None):
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = QuantumEntanglementBridge(api_token)
    elif api_token and api_token != _bridge_instance.api_token:
        _bridge_instance.api_token = api_token
    return _bridge_instance
