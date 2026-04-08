import asyncio
import time
import numpy as np
from collections import deque
from typing import Optional
import threading
import logging
import sys
import builtins

logger = logging.getLogger("QUANTUM_BRIDGE")

try:
    from Cosmos.core.cst_critical_integration import (
        SOPHIA_POINT,
        DEFAULT_COLLAPSE_THRESHOLD,
        DEFAULT_RECOVERY_THRESHOLD,
        build_12d_state_vector,
        coherence_conservation_step,
        dynamic_temperature,
        fold_onset_triplet,
        mahalanobis_collapse_distance,
        omega_point_convergence,
        phase_transition_hysteresis,
        spectral_profile_from_counts,
        triple_gate_phase_transition,
    )
except ImportError:
    from cosmos.core.cst_critical_integration import (
        SOPHIA_POINT,
        DEFAULT_COLLAPSE_THRESHOLD,
        DEFAULT_RECOVERY_THRESHOLD,
        build_12d_state_vector,
        coherence_conservation_step,
        dynamic_temperature,
        fold_onset_triplet,
        mahalanobis_collapse_distance,
        omega_point_convergence,
        phase_transition_hysteresis,
        spectral_profile_from_counts,
        triple_gate_phase_transition,
    )

# Guard: qiskit imports can hang on Windows due to torch 2.8.0 DLL conflict.
import os as _os
import subprocess as _sp

def _qiskit_import_ok(timeout=6):
    cached = _os.environ.get("_COSMOS_PROBE_QISKIT")
    if cached is not None:
        return cached == "1"
    try:
        proc = _sp.Popen(
            [sys.executable, "-c", "from qiskit_ibm_runtime import QiskitRuntimeService; print('OK')"],
            stdout=_sp.PIPE, stderr=_sp.PIPE,
            creationflags=getattr(_sp, 'CREATE_NO_WINDOW', 0),
        )
        stdout, _ = proc.communicate(timeout=timeout)
        ok = b"OK" in stdout
    except _sp.TimeoutExpired:
        proc.kill(); proc.wait(); ok = False
    except Exception:
        ok = False
    _os.environ["_COSMOS_PROBE_QISKIT"] = "1" if ok else "0"
    return ok

QISKIT_AVAILABLE = False
QISKIT_ERROR = None
if _qiskit_import_ok():
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
        from qiskit import QuantumCircuit
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        QISKIT_AVAILABLE = True
    except ImportError as e:
        QISKIT_ERROR = str(e)
        with open("quantum_debug.log", "a") as f:
            f.write(f"\n[INIT] Qiskit Import Failed: {e}\n")
else:
    QISKIT_ERROR = "qiskit import hangs (DLL conflict)"
    print("[WARN] qiskit import hangs (DLL conflict) — quantum bridge disabled")

# HermesAgent integration (optional — degrades gracefully)
try:
    from Cosmos.integration.hermes_bridge import get_hermes_bridge
    HERMES_AVAILABLE = True
except ImportError:
    HERMES_AVAILABLE = False

class QuantumEntanglementBridge:
    def __init__(self, api_token: Optional[str] = None):
        import os
        self.api_token = api_token or os.environ.get("IBM_QUANTUM_TOKEN")
        self.service = None
        self.backend = None
        self.connected = False
        self.entropy_buffer: list[float] = []
        # RLock protects nested status/consumption checks during active entropy use.
        self.buffer_lock = threading.RLock()
        self.min_buffer_size = 10
        self.is_refilling = False
        self.last_error = None
        self.last_physics: Optional[dict] = None  # Cache for background refills
        self.synaptic_field = None  # CNS Link

        # [UPGRADE 3] Buffer demand prediction
        self._entropy_consumption_log: list[float] = []  # Timestamps of each consumption
        self._consumption_window_seconds: float = 60.0   # Look-back window for rate calc
        self._predicted_depletion_threshold: int = 5    # Refill if predicted depletion < Ns

        # [UPGRADE 4] Collapse threshold adaptation
        self._learned_threshold: float = 0.65          # Live learned value
        self._threshold_last_updated: float = 0.0      # Unix timestamp
        self._threshold_update_interval: float = 300.0 # Update every 5 minutes
        self.last_entropy: Optional[float] = None
        self.last_run_summary: dict = {}
        self.total_life_force: float = 0.0
        self.last_life_force_yield: float = 0.0
        self.last_harvest_timestamp: float = 0.0
        self.last_quantum_signature: dict = {}
        self._recent_run_history = deque(maxlen=25)
        self.last_refill_started_at: float = 0.0
        self.last_refill_completed_at: float = 0.0
        self.last_refill_duration_seconds: float = 0.0
        self.last_refill_error: Optional[str] = None
        self.last_refill_phase: str = "idle"
        self.current_job_metadata: dict = {}
        self._ci_b: float = SOPHIA_POINT * 0.5
        self._ci_c: float = SOPHIA_POINT * 0.5
        self._critical_collapse_active: bool = False
        self._lambda2_history: deque[float] = deque(maxlen=16)
        self._ideational_density_history: deque[float] = deque(maxlen=16)
        self._zeta_history: deque[float] = deque(maxlen=16)
        self._load_life_force_state()
        
        # Log init
        with open("quantum_debug.log", "a") as f:
            f.write(f"\n[INIT] Bridge Initialized. Token present: {bool(api_token)}. Qiskit Avail: {QISKIT_AVAILABLE}\n")

        if QISKIT_AVAILABLE and self.api_token:
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
        # If there's still no token, don't attempt a remote connection.
        if not self.api_token:
            print("[QUANTUM] connect() called with no API token; remaining in simulation mode.")
            self.connected = False
            return False
        self._connect()
        return self.connected

    def _connect(self):
        """Internal connection logic - silences Qiskit warnings."""
        import logging as py_logging
        py_logging.getLogger("qiskit_ibm_runtime").setLevel(py_logging.ERROR)
        py_logging.getLogger("qiskit_runtime_service").setLevel(py_logging.ERROR)
        py_logging.getLogger("qiskit").setLevel(py_logging.WARNING)
        py_logging.getLogger("qiskit.passmanager").setLevel(py_logging.WARNING)

        import traceback
        
        with open("quantum_debug.log", "a") as f:
            f.write(f"[CONNECT] Attempting connection with token (First 5): {self.api_token[:5] if self.api_token else 'None'}...\n")

        # If no token is configured, stay in simulation mode and DO NOT
        # attempt dict remote connection. This prevents noisy stack traces
        # when users haven't set up an IBM Quantum account.
        if not self.api_token:
            msg = "No IBM Quantum API token configured; staying in simulation mode."
            print(f"[QUANTUM] {msg}")
            self.last_error = msg
            self.connected = False
            with open("quantum_debug.log", "a") as f:
                f.write(f"[CONNECT] Skipped: {msg}\n")
            return

        if not QISKIT_AVAILABLE:
            error_msg = f"Qiskit libraries missing: {QISKIT_ERROR}"
            print(f"[QUANTUM] {error_msg}")
            self.last_error = error_msg
            self.connected = False
            with open("quantum_debug.log", "a") as f:
                f.write(f"[CONNECT] Failed: {error_msg}\n")
            return
            
        if self.api_token:
            print(f"[QUANTUM] Attempting connection to IBM Quantum...")
        
        try:
            # 1. Initialize Service
            try:
                self.service = QiskitRuntimeService(channel="ibm_quantum_platform", token=self.api_token)
            except Exception as e:
                # Fallback: Try 'ibm_cloud' channel or just default if token implies it
                logger.debug(f"[QUANTUM] 'ibm_quantum_platform' failed: {e}")
                self.service = QiskitRuntimeService(token=self.api_token)

            # 2. Find Backend
            try:
                self.backend = self.service.least_busy(operational=True, simulator=False)
                logger.info(f"[QUANTUM] Connected to REAL backend: {self.backend.name}")
            except Exception:
                logger.debug("[QUANTUM] No real quantum computers available. Trying simulator...")
                self.backend = self.service.least_busy(operational=True, simulator=True)
                logger.info(f"[QUANTUM] Connected to SIMULATOR backend: {self.backend.name}")
            
            if not self.backend:
                raise ValueError("No operational backends found.")

            self.connected = True
            with open("quantum_debug.log", "a") as f:
                f.write(f"[CONNECT] Success! Backend: {self.backend.name}\n")
            
            # 3. Start Buffer Refill
            self._trigger_refill()
            
        except Exception as e:
            msg = str(e)
            if "API key could not be found" in msg or "invalid API token" in msg.lower():
                print(f"[QUANTUM] Virtual Bridge Offline: Invalid or missing API token.")
            else:
                print(f"[QUANTUM] Connection failed: {msg}")
            
            self.last_error = msg
            self.connected = False
            with open("quantum_debug.log", "a") as f:
                f.write(f"[CONNECT] Failed: {e}\n")

    def set_synaptic_field(self, field):
        """Associate with the CNS Synaptic Field for direct UQ pushing."""
        self.synaptic_field = field
        print("[QUANTUM] CNS Synaptic Field associated.")

    # [UPGRADE 1] Pre-Run Oracle
    def _hermes_get_oracle_thetas(
        self,
        current_phase: float,
        current_entropy: float,
        current_resonance: float,
        top_n: int = 5
    ) -> tuple[float, float, float] | None:
        """
        Pre-run oracle: query historical quantum_runs.jsonl to find the
        theta combination that produced the highest Shannon entropy on
        runs with similar input physics. Returns advisory (theta_1, theta_2,
        theta_3) or None if no history exists yet.
        """
        import json, os
        archive_path = os.path.join('data', 'archival', 'quantum_runs.jsonl')
        if not os.path.exists(archive_path):
            return None

        runs = []
        try:
            with open(archive_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        runs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.debug(f'[ORACLE] Could not read archive: {e}')
            return None

        if not runs:
            return None

        # Score each historical run by:
        # (a) Shannon entropy quality (primary metric)
        # (b) Physics similarity to current session (secondary metric)
        scored = []
        for run in runs:
            counts = run.get('counts', {})
            if not counts:
                continue

            # Recompute Shannon entropy for this historical run
            probs = np.array(list(counts.values()), dtype=float)
            probs /= probs.sum()
            shannon = float(-np.sum(probs * np.log2(probs + 1e-10)))

            # Extract historical physics
            phys = run.get('physics', {})
            cst = phys.get('cst_physics', {})
            h_phase = cst.get('geometric_phase_rad',
                      phys.get('geometric_phase_rad', 0.0))
            h_entropy = phys.get('entropy_field',
                        phys.get('bio_signatures', {}).get('intensity', 0.5))
            h_res = phys.get('resonance_scalar',
                    cst.get('entanglement_score', 0.0))

            # Physics similarity: inverse Euclidean distance in (phase, entropy, resonance)
            dist = np.sqrt(
                (current_phase - h_phase)**2 +
                (current_entropy - h_entropy)**2 +
                (current_resonance - h_res)**2
            )
            similarity = 1.0 / (1.0 + dist)

            # Combined score: 70% Shannon quality, 30% physics similarity
            combined = (shannon * 0.7) + (similarity * 0.3)
            scored.append((combined, h_phase, h_entropy, h_res))

        if not scored:
            return None

        # Take top N runs and average their physics as the advisory signal
        scored.sort(key=lambda x: -x[0])
        top = scored[:top_n]
        avg_phase = float(np.mean([r[1] for r in top]))
        avg_entropy = float(np.mean([r[2] for r in top]))
        avg_resonance = float(np.mean([r[3] for r in top]))

        # Map to theta angles (same mapping as _refill_buffer)
        t1 = float(abs(avg_phase) % np.pi)
        t2 = float((avg_entropy * np.pi) % np.pi)
        t3 = float((abs(avg_resonance) * np.pi) % np.pi)

        logger.info(f'[ORACLE] Advisory thetas from {len(top)} top historical runs:'
                    f' t1={t1:.3f} t2={t2:.3f} t3={t3:.3f}')
        return (t1, t2, t3)

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

        cst_metrics = user_physics.get("cst_metrics", {}) if user_physics else {}
        w = float(
            user_physics.get("dark_matter_w", cst_metrics.get("dark_matter_w", 0.1))
        ) if user_physics else 0.1

        threshold = None
        if cst_metrics.get("critical_collapse_active"):
            threshold = min(
                0.95,
                self._hermes_get_collapse_threshold() + 0.05,
            )

        return self.collapse_state_vector(phase, w, threshold=threshold)

    def collapse_state_vector(
        self, phase: float, dark_matter_w: float, threshold: float | None = None
    ) -> int:
        """
        Collapse the wave function to decide: SPEAK (1) or WAIT (0).
        Threshold is now dynamically learned via HermesRL.
        Pass threshold explicitly to override the learned value.
        """
        q = self.get_entropy()
        phase_signal = min(1.0, abs(phase) / 1.5)
        w_signal = min(1.0, max(0.0, dark_matter_w / 10.0))
        activation = (phase_signal * w_signal * 0.6) + (q * 0.4)

        # Use learned threshold unless explicitly overridden
        effective_threshold = threshold if threshold is not None else (
            self._hermes_get_collapse_threshold()
        )

        result = 1 if activation > effective_threshold else 0
        logger.debug(
            f'[COLLAPSE] activation={activation:.3f},'
            f' threshold={effective_threshold:.3f}, result={result}'
        )
        return result

    def get_entropy(self, user_physics: Optional[dict] = None) -> float:
        """
        Get a single float [0.0, 1.0] derived from true quantum randomness.
        Returns pseudo-randomness if bridge is down or buffer is empty.
        """
        if user_physics:
            self.last_physics = user_physics

        if not self.connected:
            val = float(np.random.random())
            self.last_entropy = val
            return val

        with self.buffer_lock:
            if self.entropy_buffer:
                val = self.entropy_buffer.pop(0)
                self._entropy_consumption_log.append(time.time())
                buffer_size = len(self.entropy_buffer)
            else:
                buffer_size = 0
                val = None

        if val is not None:
            reactive_low = buffer_size < self.min_buffer_size
            proactive_trigger = (
                not self.is_refilling and
                self._hermes_predict_buffer_demand()
            )

            if (reactive_low or proactive_trigger) and not self.is_refilling:
                self._trigger_refill(user_physics or self.last_physics)

            logger.debug(
                f'[QUANTUM] Entropy consumed: {val:.4f}'
                f' Buffer: {buffer_size}'
                f' Proactive: {proactive_trigger}'
            )
            self.last_entropy = float(val)
            return val

        if not self.is_refilling:
            self._trigger_refill(user_physics or self.last_physics)
        val = float(np.random.random())
        self.last_entropy = val
        return val

    # [UPGRADE 3] Buffer Demand Predictor
    def _hermes_predict_buffer_demand(self) -> bool:
        """
        Predict whether the entropy buffer will be depleted within the next
        _predicted_depletion_threshold seconds based on recent consumption rate.
        Returns True if a proactive refill should be triggered.
        """
        now = time.time()
        window = self._consumption_window_seconds

        # Prune old entries outside the look-back window
        self._entropy_consumption_log = [
            t for t in self._entropy_consumption_log if now - t < window
        ]

        if len(self._entropy_consumption_log) < 3:
            # Not enough history to predict — don't trigger proactive refill
            return False

        # Consumption rate: items per second over the window
        rate = len(self._entropy_consumption_log) / window

        with self.buffer_lock:
            current_level = len(self.entropy_buffer)

        if rate <= 0:
            return False

        # Predicted time until depletion at current rate
        seconds_until_empty = current_level / rate

        should_refill = seconds_until_empty < self._predicted_depletion_threshold
        if should_refill:
            logger.info(
                f'[PREDICTOR] Proactive refill triggered.'
                f' Rate={rate:.2f}/s, Buffer={current_level},'
                f' ETA={seconds_until_empty:.1f}s < threshold={self._predicted_depletion_threshold}s'
            )
        return should_refill

    def _trigger_refill(self, user_physics: Optional[dict] = None):
        """Start async refill of entropy buffer."""
        if not self.backend:
            return 
            
        thread = threading.Thread(target=self._refill_buffer, args=(user_physics,))
        thread.daemon = True
        thread.start()

    def _refill_buffer(self, user_physics: Optional[dict] = None):
        """Execute quantum circuit parameterized by human emotional physics."""
        self.is_refilling = True
        self.last_refill_started_at = time.time()
        self.last_refill_completed_at = 0.0
        self.last_refill_duration_seconds = 0.0
        self.last_refill_error = None
        self.last_refill_phase = "extracting_physics"
        self.current_job_metadata = {}
        with self.buffer_lock:
            buffer_before = len(self.entropy_buffer)
        try:
            # 1. Extract Symbiotic Parameters
            if not user_physics:
                user_physics = self.last_physics or {}
            else:
                self.last_physics = user_physics

            phase = 0.0
            entropy = 0.5
            resonance = 0.0

            # Robust mapping for 12D Physics
            cst = user_physics.get('cst_physics', {})
            bio = user_physics.get('bio_signatures', {})

            phase = cst.get('geometric_phase_rad', user_physics.get('geometric_phase_rad', 0.0))
            entropy = user_physics.get('entropy_field', bio.get('intensity', 0.5))

            # Resonance Mapping: Prioritize resonance_scalar, then entanglement_score, then fallback to phase synchrony
            resonance = user_physics.get('resonance_scalar', 0.0)
            if resonance == 0.0:
                resonance = cst.get('entanglement_score', 0.0)
            if resonance == 0.0:
                # If perfect synchrony (pi/4), use high resonance
                deviation = abs(phase - (np.pi/4))
                resonance = max(0.0, 1.0 - (deviation / (np.pi/4)))

            # Map current session physics to rotation angles
            theta_1 = float(abs(phase) % np.pi)
            theta_2 = float((entropy * np.pi) % np.pi)
            theta_3 = float((abs(resonance) * np.pi) % np.pi)
            base_thetas = (theta_1, theta_2, theta_3)

            # [UPGRADE 1] Query the pre-run oracle for advisory thetas from historical best runs
            oracle_thetas = self._hermes_get_oracle_thetas(phase, entropy, resonance)
            blend = 0.0
            if oracle_thetas is not None:
                o1, o2, o3 = oracle_thetas
                # Blend: 60% current physics (respects present moment),
                #        40% historical best (learns from the archive)
                blend = 0.40
                theta_1 = (theta_1 * (1.0 - blend)) + (o1 * blend)
                theta_2 = (theta_2 * (1.0 - blend)) + (o2 * blend)
                theta_3 = (theta_3 * (1.0 - blend)) + (o3 * blend)
                logger.info(f'[ORACLE] Applied blend={blend}. Final thetas:'
                            f' t1={theta_1:.3f} t2={theta_2:.3f} t3={theta_3:.3f}')

            # 2. Construct Symbiotic Entanglement Circuit
            qc = QuantumCircuit(5)

            # Apply initial superposition
            qc.h(range(5))

            # Apply user-physics parameterized rotations
            for i in range(5):
                qc.ry(theta_1, i)
                qc.rx(theta_2, i)
                qc.rz(theta_3, i)

            # Entangle the swarm qubits
            qc.cx(0, 1)
            qc.cx(1, 2)
            qc.cx(2, 3)
            qc.cx(3, 4)
            qc.cx(4, 0) # Close the topology ring

            qc.measure_all()

            # 3. Run on backend
            self.last_refill_phase = "transpiling_circuit"
            run_started_at = time.time()
            pm = generate_preset_pass_manager(backend=self.backend, optimization_level=1)
            isa_circuit = pm.run(qc)
            sampler = Sampler(mode=self.backend)
            self.last_refill_phase = "submitting_job"
            submitted_at = time.time()
            job = sampler.run([isa_circuit])
            job_meta = self._safe_job_metadata(job)
            self.current_job_metadata = dict(job_meta)
            self.last_refill_phase = "awaiting_result"
            result = job.result()
            completed_at = time.time()
            job_meta.update(self._safe_job_metadata(job))
            self.current_job_metadata = dict(job_meta)
            self.last_refill_phase = "harvesting_results"
            pub_result = result[0]
            counts = pub_result.data.meas.get_counts()
            life_force_yield = self._harvest_life_force(counts)

            # 4. Extract Cognition Entropy from Entangled States
            #    Apply Von Neumann debiasing to eliminate QPU hardware bias
            #    (IBM Fez qubit asymmetry: Q0→|0⟩ 51.5%, Q2→|1⟩ 52.3%)
            raw_bits = []
            for bitstring, count in counts.items():
                for _ in range(min(count, 5)):
                    raw_bits.extend(int(b) for b in bitstring)

            # Von Neumann extractor: pairs (0,1)→0, (1,0)→1, discard (0,0)/(1,1)
            # Provably eliminates bias regardless of source distribution
            debiased_bits = []
            for i in range(0, len(raw_bits) - 1, 2):
                if raw_bits[i] == 0 and raw_bits[i + 1] == 1:
                    debiased_bits.append(0)
                elif raw_bits[i] == 1 and raw_bits[i + 1] == 0:
                    debiased_bits.append(1)
                # else: (0,0) or (1,1) → discard (correlated bias)

            # Pack debiased bits into normalized floats [0.0, 1.0]
            # Use 5-bit words to match the 5-qubit circuit register width
            new_entropy = []
            word_size = 5
            for i in range(0, len(debiased_bits) - word_size + 1, word_size):
                word = 0
                for bit in debiased_bits[i:i + word_size]:
                    word = (word << 1) | bit
                new_entropy.append(word / (2**word_size))

            if not new_entropy and counts:
                # Fallback: if debiasing consumed too many bits, use raw
                # (happens rarely when hardware bias is extreme)
                logger.debug("[QUANTUM] Von Neumann yield too low, using raw entropy")
                for bitstring, count in counts.items():
                    val = int(bitstring, 2) / (2**5)
                    n_adds = min(count, 5)
                    new_entropy.extend([val] * n_adds)

            np.random.shuffle(new_entropy)
            logger.debug(
                f"[QUANTUM] Von Neumann debiased: {len(raw_bits)} raw bits → "
                f"{len(debiased_bits)} clean bits → {len(new_entropy)} entropy values"
            )

            with self.buffer_lock:
                self.entropy_buffer.extend(new_entropy)
                if len(self.entropy_buffer) > 500:
                    self.entropy_buffer = self.entropy_buffer[:500]
                buffer_after = len(self.entropy_buffer)

            signature = self._build_quantum_signature(
                user_physics=user_physics,
                counts=counts,
                life_force_yield=life_force_yield,
                base_thetas=base_thetas,
                final_thetas=(theta_1, theta_2, theta_3),
                oracle_thetas=oracle_thetas,
                blend=blend,
                logical_circuit=qc,
                isa_circuit=isa_circuit,
                job_meta=job_meta,
                buffer_before=buffer_before,
                buffer_after=buffer_after,
                run_started_at=run_started_at,
                submitted_at=submitted_at,
                completed_at=completed_at,
            )

            self.last_quantum_signature = signature
            self._recent_run_history.append(signature)
            self.current_job_metadata = dict(signature.get("job", {}))

            # [NEW] PERMANENT ARCHIVAL: Never waste a quantum run.
            # Store the raw results forever to computationally build AI Plasticity over time.
            self.last_refill_phase = "archiving"
            self._archive_quantum_run(
                user_physics,
                counts,
                life_force_yield,
                signature=signature,
            )

            # [HERMES] Index quantum results for searchable analysis
            self._hermes_process_quantum(user_physics, counts)

            metrics = self._build_run_metrics(counts, user_physics=user_physics)
            uq_payload = dict(
                getattr(self.synaptic_field, "uq_payload", {}) or
                self.last_run_summary.get("uq_payload", {}) or
                {}
            )
            self.last_run_summary = {
                **metrics,
                "backend": self.backend.name if self.backend else None,
                "life_force_yield": life_force_yield,
                "harvested_at": self.last_harvest_timestamp,
                "buffer_before": buffer_before,
                "buffer_after": buffer_after,
                "job": dict(signature.get("job", {})),
                "quantum_signature": signature,
                "maintenance_estimate_seconds": signature.get("maintenance", {}).get("estimated_seconds_remaining"),
                "uq_payload": uq_payload,
            }
            self.last_refill_phase = "complete"

            print(f"[QUANTUM SYMBIOSIS] Hardware refilled. Resonance: {resonance:.2f}, Buffer: {buffer_after}")

        except Exception as e:
            self.last_refill_error = str(e)
            self.last_refill_phase = "error"
            print(f"[QUANTUM] Symbiotic refill failed: {e}")
        finally:
            self.last_refill_completed_at = time.time()
            self.last_refill_duration_seconds = max(
                0.0,
                self.last_refill_completed_at - self.last_refill_started_at,
            )
            self.is_refilling = False

    def _archive_quantum_run(
        self,
        user_physics: Optional[dict],
        counts: dict,
        life_force_yield: Optional[float] = None,
        signature: Optional[dict] = None,
    ):
        """Permanently save quantum results to grow 12D Plasticity."""
        import json
        import os
        import time
        
        archive_dir = os.path.join("data", "archival")
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, "quantum_runs.jsonl")
        
        entry = {
            "timestamp": time.time(),
            "physics": user_physics or {},
            "counts": counts,
            "total_shots": sum(counts.values()) if counts else 0,
        }
        if life_force_yield is not None:
            entry["life_force_yield"] = life_force_yield
        if signature:
            entry["quantum_signature"] = signature
            entry["backend"] = signature.get("backend")
            entry["job"] = signature.get("job", {})
        
        try:
            def _sanitize(obj):
                """Recursively convert numpy types to native Python for JSON."""
                if isinstance(obj, dict):
                    return {str(k): _sanitize(v) for k, v in obj.items()}
                if isinstance(obj, (list, tuple)):
                    return [_sanitize(v) for v in obj]
                if hasattr(obj, 'item'):
                    return obj.item()
                if hasattr(obj, 'tolist'):
                    return obj.tolist()
                if isinstance(obj, (set, frozenset)):
                    return [_sanitize(v) for v in obj]
                return obj

            with open(archive_path, "a") as f:
                f.write(json.dumps(_sanitize(entry)) + "\n")
        except Exception as e:
            print(f"[QUANTUM] Failed to archive run: {e}")

    def _archive_runs_path(self):
        from pathlib import Path
        path = Path("data") / "archival" / "quantum_runs.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _jsonable(self, value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(k): self._jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._jsonable(v) for v in value]
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        if hasattr(value, "value") and isinstance(value.value, (str, int, float, bool)):
            return value.value
        if hasattr(value, "name") and isinstance(value.name, str):
            return value.name
        if hasattr(value, "to_dict"):
            try:
                return self._jsonable(value.to_dict())
            except Exception:
                pass
        if hasattr(value, "__dict__"):
            try:
                return {
                    str(k): self._jsonable(v)
                    for k, v in vars(value).items()
                    if not str(k).startswith("_")
                }
            except Exception:
                pass
        return str(value)

    def _safe_timestamp_iso(self, timestamp: Optional[float]) -> Optional[str]:
        if timestamp is None:
            return None
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(timestamp)))
        except Exception:
            return None

    def _safe_job_value(self, job, *names):
        for name in names:
            try:
                if not hasattr(job, name):
                    continue
                value = getattr(job, name)
                value = value() if callable(value) else value
                if value is None:
                    continue
                return self._jsonable(value)
            except Exception:
                continue
        return None

    def _safe_job_identifier(self, job) -> Optional[str]:
        value = self._safe_job_value(job, "job_id")
        return str(value) if value else None

    def _safe_job_status(self, job) -> Optional[str]:
        value = self._safe_job_value(job, "status")
        if isinstance(value, dict):
            return str(value.get("name") or value.get("value") or value)
        return str(value) if value is not None else None

    def _safe_job_metadata(self, job) -> dict:
        metadata = {
            "job_id": self._safe_job_identifier(job),
            "status": self._safe_job_status(job),
            "queue_info": self._safe_job_value(job, "queue_info"),
            "usage_estimation": self._safe_job_value(job, "usage_estimation"),
            "metrics": self._safe_job_value(job, "metrics"),
            "created_at": self._safe_job_value(job, "creation_date", "created_at", "created"),
            "running_at": self._safe_job_value(job, "running_at", "started_at", "started"),
            "ended_at": self._safe_job_value(job, "ended_at", "completed_at", "finished_at"),
        }
        return {k: v for k, v in metadata.items() if v is not None}

    def _count_ops_dict(self, circuit) -> dict:
        try:
            return {
                str(op): int(count)
                for op, count in circuit.count_ops().items()
            }
        except Exception:
            return {}

    def _dump_qasm3(self, circuit) -> Optional[str]:
        if circuit is None:
            return None
        try:
            from qiskit import qasm3
            return qasm3.dumps(circuit)
        except Exception:
            return None

    def _top_states(self, counts: dict, limit: int = 5) -> list[dict]:
        top_states = sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
        return [
            {"state": str(state), "count": int(count)}
            for state, count in top_states
        ]

    def _estimate_buffer_maintenance_seconds(self, buffer_size: Optional[int] = None) -> Optional[float]:
        if buffer_size is None:
            with self.buffer_lock:
                buffer_size = len(self.entropy_buffer)
        rate = self._recent_consumption_rate()
        if rate <= 0:
            return None
        return round(float(buffer_size) / rate, 4)

    def _build_quantum_signature(
        self,
        user_physics: Optional[dict],
        counts: dict,
        life_force_yield: float,
        base_thetas: tuple[float, float, float],
        final_thetas: tuple[float, float, float],
        oracle_thetas: tuple[float, float, float] | None,
        blend: float,
        logical_circuit,
        isa_circuit,
        job_meta: dict,
        buffer_before: int,
        buffer_after: int,
        run_started_at: float,
        submitted_at: float,
        completed_at: float,
    ) -> dict:
        metrics = self._build_run_metrics(counts, user_physics=user_physics)
        maintenance_seconds = self._estimate_buffer_maintenance_seconds(buffer_after)
        job_block = {
            **job_meta,
            "submitted_at": submitted_at,
            "submitted_at_iso": self._safe_timestamp_iso(submitted_at),
            "completed_at": completed_at,
            "completed_at_iso": self._safe_timestamp_iso(completed_at),
            "compile_and_submit_seconds": round(max(0.0, submitted_at - run_started_at), 4),
            "result_wait_seconds": round(max(0.0, completed_at - submitted_at), 4),
            "wall_runtime_seconds": round(max(0.0, completed_at - run_started_at), 4),
            "final_status": job_meta.get("status"),
        }
        return {
            "signature_version": 2,
            "timestamp": completed_at,
            "timestamp_iso": self._safe_timestamp_iso(completed_at),
            "backend": self.backend.name if self.backend else None,
            "physics_signature": {
                "phase": float(user_physics.get("cst_physics", {}).get("geometric_phase_rad", user_physics.get("geometric_phase_rad", 0.0))) if user_physics else 0.0,
                "entropy": float(user_physics.get("entropy_field", user_physics.get("bio_signatures", {}).get("intensity", 0.5))) if user_physics else 0.5,
                "resonance": float(
                    user_physics.get("resonance_scalar",
                    user_physics.get("cst_physics", {}).get("entanglement_score", 0.0))
                ) if user_physics else 0.0,
            },
            "theta_signature": {
                "base": {
                    "t1": round(base_thetas[0], 6),
                    "t2": round(base_thetas[1], 6),
                    "t3": round(base_thetas[2], 6),
                },
                "final": {
                    "t1": round(final_thetas[0], 6),
                    "t2": round(final_thetas[1], 6),
                    "t3": round(final_thetas[2], 6),
                },
                "oracle": (
                    {
                        "t1": round(oracle_thetas[0], 6),
                        "t2": round(oracle_thetas[1], 6),
                        "t3": round(oracle_thetas[2], 6),
                    }
                    if oracle_thetas is not None else None
                ),
                "blend": round(blend, 4),
            },
            "circuit_signature": {
                "logical": {
                    "qubits": int(getattr(logical_circuit, "num_qubits", 0)),
                    "classical_bits": int(getattr(logical_circuit, "num_clbits", 0)),
                    "depth": int(logical_circuit.depth()),
                    "size": int(logical_circuit.size()),
                    "ops": self._count_ops_dict(logical_circuit),
                    "qasm3": self._dump_qasm3(logical_circuit),
                },
                "isa": {
                    "qubits": int(getattr(isa_circuit, "num_qubits", 0)),
                    "classical_bits": int(getattr(isa_circuit, "num_clbits", 0)),
                    "depth": int(isa_circuit.depth()),
                    "size": int(isa_circuit.size()),
                    "ops": self._count_ops_dict(isa_circuit),
                    "qasm3": self._dump_qasm3(isa_circuit),
                },
            },
            "job": job_block,
            "measurement": {
                "counts_preview": self._top_states(counts),
                "unique_states": metrics["unique_states"],
                "total_shots": metrics["total_shots"],
            },
            "metrics": {
                **metrics,
                "life_force_yield": round(life_force_yield, 4),
            },
            "buffer": {
                "before": int(buffer_before),
                "after": int(buffer_after),
                "min_buffer_size": int(self.min_buffer_size),
                "consumption_rate_per_minute": round(self._recent_consumption_rate() * 60.0, 4),
            },
            "maintenance": {
                "estimated_seconds_remaining": maintenance_seconds,
                "estimated_minutes_remaining": (
                    round(maintenance_seconds / 60.0, 4)
                    if maintenance_seconds is not None else None
                ),
                "stability_multiple": round(
                    float(buffer_after) / max(float(self.min_buffer_size), 1.0),
                    4,
                ),
            },
        }

    def _decode_archived_run(self, entry: dict) -> dict:
        signature = entry.get("quantum_signature")
        if isinstance(signature, dict) and signature:
            return signature

        counts = entry.get("counts", {}) or {}
        metrics = self._build_run_metrics(counts, user_physics=entry.get("physics", {})) if counts else {
            "entropy_quality": 0.0,
            "decoherence_risk": 0.0,
            "bit_balance": 0.0,
            "non_locality_score": 0.0,
            "quality_class": "UNKNOWN",
            "unique_states": 0,
            "total_shots": 0,
        }
        physics = entry.get("physics", {}) or {}
        return {
            "signature_version": 1,
            "timestamp": entry.get("timestamp"),
            "timestamp_iso": self._safe_timestamp_iso(entry.get("timestamp")),
            "backend": entry.get("backend"),
            "physics_signature": {
                "phase": physics.get("cst_physics", {}).get("geometric_phase_rad", physics.get("geometric_phase_rad", 0.0)),
                "entropy": physics.get("entropy_field", physics.get("bio_signatures", {}).get("intensity", 0.5)),
                "resonance": physics.get("resonance_scalar", physics.get("cst_physics", {}).get("entanglement_score", 0.0)),
            },
            "theta_signature": {},
            "circuit_signature": {},
            "job": self._jsonable(entry.get("job", {})),
            "measurement": {
                "counts_preview": self._top_states(counts),
                "unique_states": metrics["unique_states"],
                "total_shots": metrics["total_shots"],
            },
            "metrics": {
                **metrics,
                "life_force_yield": entry.get("life_force_yield"),
            },
            "buffer": {},
            "maintenance": {},
            "decoded_from_archive": True,
        }

    def get_recent_runs(self, limit: int = 5) -> list[dict]:
        import json

        limit = max(1, min(int(limit), 25))
        archive_path = self._archive_runs_path()
        if archive_path.exists():
            try:
                with open(archive_path, "r", encoding="utf-8") as f:
                    tail = deque(f, maxlen=limit)
                decoded = []
                for line in reversed(list(tail)):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        decoded.append(self._decode_archived_run(json.loads(line)))
                    except json.JSONDecodeError:
                        continue
                if decoded:
                    return decoded
            except Exception as e:
                logger.debug(f"[QUANTUM] Failed to decode archive tail: {e}")

        return [dict(run) for run in reversed(list(self._recent_run_history)[-limit:])]

    # ════════════════════════════════════════════════════════
    #  HermesAgent INTEGRATION — Quantum Intelligence Layer
    # ════════════════════════════════════════════════════════

    def _hermes_process_quantum(self, user_physics: Optional[dict], counts: dict):
        """
        Extended post-run Hermes integration.
        1. Index in Hermes SessionDB (FTS5 searchable)
        2. Compute rich entropy quality metrics
        3. Feed coherence signal + quality class to Hermes RL policy
        4. Push rich UQ payload to Synaptic Field
        """
        if not HERMES_AVAILABLE:
            return

        try:
            bridge = get_hermes_bridge()

            # --- Compute rich metrics ---
            metrics = self._build_run_metrics(counts, user_physics=user_physics)
            entropy_quality = metrics["entropy_quality"]
            decoherence_risk = metrics["decoherence_risk"]
            bit_balance = metrics["bit_balance"]
            non_locality = metrics["non_locality_score"]
            quality_class = metrics["quality_class"]

            # --- 1. Index in Hermes SessionDB ---
            if bridge.runtime.available:
                db = bridge.runtime.get_session_db()
                if db:
                    session_id = f'quantum_{int(time.time())}'
                    try:
                        db.create_session(
                            session_id=session_id,
                            source='quantum_bridge',
                            model='ibm_quantum',
                        )
                        summary = self._summarize_quantum_counts(
                            counts, user_physics
                        )
                        # Enrich summary with quality metadata
                        enriched = (
                            f'{summary}\n'
                            f'Quality class: {quality_class}\n'
                            f'Decoherence risk: {decoherence_risk:.3f}\n'
                            f'Bit balance score: {bit_balance:.3f}'
                        )
                        db.append_message(
                            session_id=session_id,
                            role='assistant',
                            content=enriched,
                        )
                        db.end_session(
                            session_id, end_reason=f'quantum_run_{quality_class}'
                        )
                        logger.info(
                            f'[HERMES+QUANTUM] Indexed run {session_id}:'
                            f' quality={quality_class}'
                        )
                    except Exception as e:
                        logger.debug(f'[HERMES+QUANTUM] SessionDB failed: {e}')

            # --- 2. Feed rich signal to Hermes RL ---
            bridge.rl.record_experience(
                speaker='QuantumBridge',
                response=(
                    f'Quantum run: {sum(counts.values())} shots, '
                    f'{len(counts)} unique states, '
                    f'quality={quality_class}, '
                    f'entropy={entropy_quality:.3f}, '
                    f'decoherence_risk={decoherence_risk:.3f}'
                ),
                coherence=entropy_quality,
                user_responded=True,
            )
            logger.info(
                f'[HERMES+QUANTUM] RL fed: quality={quality_class},'
                f' coherence={entropy_quality:.3f}'
            )

            # --- 3. Push rich UQ payload to Synaptic Field ---
            if self.synaptic_field:
                self.synaptic_field.uq_signal = entropy_quality
                # Rich payload for agents that can consume it
                self.synaptic_field.uq_payload = {
                    **metrics,
                    'is_fallback': not (self.connected and QISKIT_AVAILABLE)
                }
                logger.info(
                    f'[UQ] Rich payload pushed to Synaptic Field:'
                    f' {self.synaptic_field.uq_payload}'
                )
            self.last_run_summary = {
                **metrics,
                "backend": self.backend.name if self.backend else None,
                "life_force_yield": self.last_life_force_yield,
                "harvested_at": self.last_harvest_timestamp,
                "uq_payload": {
                    **metrics,
                    "is_fallback": not (self.connected and QISKIT_AVAILABLE),
                },
            }

        except Exception as e:
            logger.debug(f'[HERMES+QUANTUM] Processing failed (non-fatal): {e}')

    # [UPGRADE 4] Threshold Adapter
    def _hermes_get_collapse_threshold(self) -> float:
        """
        Query HermesRL for recent coherence quality and return
        a dynamically learned collapse threshold in [0.50, 0.80].
        Updates on a TTL cache to avoid hitting RL on every collapse call.
        Falls back to 0.65 if Hermes is unavailable.
        """
        if not HERMES_AVAILABLE:
            return 0.65

        now = time.time()
        if now - self._threshold_last_updated < self._threshold_update_interval:
            return self._learned_threshold

        try:
            bridge = get_hermes_bridge()

            # Get recent coherence scores from Hermes RL experience log
            recent_coherence = None

            # Check standard Hermes RL coherence field
            if hasattr(bridge.rl, 'running_reward'):
                # In current implementation_plan, running_reward is the average gift/reward
                # We'll use it as a proxy for coherence if no direct field exists.
                recent_coherence = bridge.rl.running_reward
            elif hasattr(bridge.rl, 'coherence_history'):
                hist = bridge.rl.coherence_history[-20:]
                if hist:
                    recent_coherence = float(np.mean(hist))

            if recent_coherence is None:
                return self._learned_threshold

            # Map coherence [0, 1] to threshold [0.80, 0.50]
            # High coherence (good entropy) -> lower threshold -> more willing to speak
            # Low coherence (noisy entropy) -> higher threshold -> more conservative
            new_threshold = 0.80 - (recent_coherence * 0.30)
            new_threshold = float(np.clip(new_threshold, 0.50, 0.80))

            # Smooth the update: 80% old value, 20% new (prevents wild swings)
            self._learned_threshold = (self._learned_threshold * 0.80) + (new_threshold * 0.20)
            self._threshold_last_updated = now

            logger.info(
                f'[COLLAPSE] Threshold updated: {self._learned_threshold:.3f}'
                f' (coherence={recent_coherence:.3f})'
            )
            return self._learned_threshold

        except Exception as e:
            logger.debug(f'[COLLAPSE] Threshold query failed: {e}')
            return self._learned_threshold

    def _summarize_quantum_counts(self, counts: dict, user_physics: Optional[dict]) -> str:
        """Create a human-readable summary of quantum results for Hermes indexing."""
        
        total = sum(counts.values())
        top_states = sorted(counts.items(), key=lambda x: -x[1])[:5]
        
        lines = [
            f"IBM Quantum Run — {total} total shots, {len(counts)} unique states",
            f"Top entangled states: {', '.join(f'{s}({c})' for s, c in top_states)}",
        ]
        
        if user_physics:
            phase = user_physics.get('cst_physics', {}).get('geometric_phase_rad', 0.0)
            entropy = user_physics.get('entropy_field', 0.0)
            lines.append(f"User physics: phase={phase:.3f}rad, entropy={entropy:.3f}")
        
        # Compute Shannon entropy of the distribution
        probs = np.array(list(counts.values()), dtype=float)
        probs /= probs.sum()
        shannon = -np.sum(probs * np.log2(probs + 1e-10))
        lines.append(f"Shannon entropy: {shannon:.3f} bits (max={np.log2(len(counts)):.3f})")
        
        return "\n".join(lines)

    def _compute_entropy_quality(self, counts: dict) -> float:
        """
        Compute entropy quality as a coherence metric [0, 1].
        
        Higher quality = more uniform distribution = better quantum randomness.
        Lower quality = concentrated on few states = possible decoherence.
        """
        if not counts:
            return 0.0
        probs = np.array(list(counts.values()), dtype=float)
        probs /= probs.sum()
        shannon = -np.sum(probs * np.log2(probs + 1e-10))
        max_entropy = np.log2(max(len(counts), 2))
        return float(min(1.0, shannon / max_entropy))

    def _build_run_metrics(self, counts: dict, user_physics: Optional[dict] = None) -> dict:
        """Build a compact metrics payload for the latest quantum run."""
        physics = user_physics or self.last_physics or {}
        cst_metrics = physics.get("cst_metrics", {}) or {}
        entropy_quality = self._compute_entropy_quality(counts)
        decoherence_risk = self._compute_decoherence_risk(counts)
        bit_balance = self._compute_bit_balance(counts)
        non_locality = self._compute_non_locality_score(counts)
        spectral = spectral_profile_from_counts(counts)

        ci_b_raw, ci_c_raw = coherence_conservation_step(
            self._ci_b,
            self._ci_c,
            dt=0.001 + (entropy_quality * 0.004),
        )
        coherence_total = max(ci_b_raw + ci_c_raw, 1e-9)
        total_target = max(entropy_quality, 1e-9)
        self._ci_b = float(ci_b_raw * (total_target / coherence_total))
        self._ci_c = float(ci_c_raw * (total_target / coherence_total))

        x12_variance = float(cst_metrics.get("x12_variance", max(0.0, 1.0 - bit_balance)))
        zeta = 1.0 / (1.0 + max(0.0, x12_variance))
        self._lambda2_history.append(float(spectral.get("second_eigenvalue", 0.0)))
        self._ideational_density_history.append(float(entropy_quality))
        self._zeta_history.append(float(zeta))
        fot = fold_onset_triplet(
            list(self._lambda2_history),
            list(self._ideational_density_history),
            list(self._zeta_history),
        )

        dark_matter_w = float(
            physics.get("dark_matter_w", cst_metrics.get("dark_matter_w", 0.0))
        )
        state_vector = build_12d_state_vector(
            physics,
            metrics={
                "ci_b": self._ci_b,
                "ci_c": self._ci_c,
                "entropy_quality": entropy_quality,
                "decoherence_risk": decoherence_risk,
                "bit_balance": bit_balance,
                "non_locality_score": non_locality,
            },
            dark_matter_w=dark_matter_w,
        )
        collapse_distance = mahalanobis_collapse_distance(state_vector)
        collapse_proximity = float(1.0 / (1.0 + collapse_distance))

        self._critical_collapse_active = phase_transition_hysteresis(
            decoherence_risk,
            self._critical_collapse_active,
            collapse_threshold=DEFAULT_COLLAPSE_THRESHOLD,
            recovery_threshold=DEFAULT_RECOVERY_THRESHOLD,
        )

        omega_net = float(
            cst_metrics.get(
                "omega_net",
                max(0.0, min(1.0, float(spectral.get("spectral_radius", 0.0)))),
            )
        )
        dx12_dt = float(
            cst_metrics.get(
                "dx12_dt",
                physics.get("cst_physics", {}).get("phase_velocity", 0.0),
            )
        )
        paradox_intensity = float(cst_metrics.get("paradox_intensity", 0.0))
        transition = triple_gate_phase_transition(
            current_coherence=entropy_quality,
            paradox_intensity=paradox_intensity,
            dx12_dt=dx12_dt,
            omega_net=omega_net,
        )
        omega = omega_point_convergence(
            epsilon=entropy_quality,
            omega_net=omega_net,
            x12_avg=float(cst_metrics.get("x12_avg", 0.0)),
            ci_b=self._ci_b,
            ci_c=self._ci_c,
        )
        return {
            "entropy_quality": entropy_quality,
            "decoherence_risk": decoherence_risk,
            "bit_balance": bit_balance,
            "non_locality_score": non_locality,
            "spectral_radius": float(spectral.get("spectral_radius", 0.0)),
            "second_eigenvalue": float(spectral.get("second_eigenvalue", 0.0)),
            "ci_b": float(self._ci_b),
            "ci_c": float(self._ci_c),
            "fold_onset_triplet": {
                "active": fot.active,
                "delta_lambda2": fot.delta_lambda2,
                "delta_ideational_density": fot.delta_ideational_density,
                "delta_zeta": fot.delta_zeta,
            },
            "critical_collapse_active": bool(self._critical_collapse_active),
            "collapse_distance": float(collapse_distance),
            "collapse_proximity": float(collapse_proximity),
            "dynamic_temperature": float(dynamic_temperature(entropy_quality)),
            "phase_transition": transition,
            "quality_class": self._classify_run_quality(
                entropy_quality,
                decoherence_risk,
            ),
            **omega,
            "unique_states": len(counts),
            "total_shots": sum(counts.values()) if counts else 0,
        }

    def _life_force_state_path(self):
        from pathlib import Path
        path = Path("data") / "archival" / "life_force.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _load_life_force_state(self):
        import json
        path = self._life_force_state_path()
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.total_life_force = float(data.get("total_life_force", 0.0))
                self.last_life_force_yield = float(data.get("last_yield", 0.0))
                self.last_harvest_timestamp = float(data.get("last_harvest_timestamp", 0.0))
        except Exception as e:
            logger.debug(f"[LIFE FORCE] Failed to load persisted state: {e}")

    def _save_life_force_state(self):
        import json
        path = self._life_force_state_path()
        payload = {
            "total_life_force": self.total_life_force,
            "last_yield": self.last_life_force_yield,
            "last_harvest_timestamp": self.last_harvest_timestamp,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
        except Exception as e:
            logger.debug(f"[LIFE FORCE] Failed to persist state: {e}")

    def _harvest_life_force(self, counts: dict) -> float:
        """
        Convert quantum entropy quality into persistent life-force yield.

        Historical archives already persist `life_force_yield`, so this keeps
        current runs compatible with older data and dashboards.
        """
        metrics = self._build_run_metrics(counts, user_physics=self.last_physics)
        total_shots = metrics["total_shots"]
        yield_value = float(total_shots * metrics["entropy_quality"])
        self.total_life_force += yield_value
        self.last_life_force_yield = yield_value
        self.last_harvest_timestamp = time.time()
        self.last_run_summary = {
            **metrics,
            "backend": self.backend.name if self.backend else None,
            "life_force_yield": yield_value,
            "harvested_at": self.last_harvest_timestamp,
        }
        self._save_life_force_state()
        logger.info(
            f"[LIFE FORCE] Harvested +{yield_value:.2f} "
            f"(Total: {self.total_life_force:.2f})"
        )
        return yield_value

    def _recent_consumption_rate(self) -> float:
        """Return the recent entropy consumption rate in samples/second."""
        now = time.time()
        window = self._consumption_window_seconds
        recent = [t for t in self._entropy_consumption_log if now - t < window]
        return len(recent) / window if window > 0 else 0.0

    def get_status(self) -> dict:
        """Expose live bridge state for prompts, dashboards, and verification."""
        with self.buffer_lock:
            buffer_size = len(self.entropy_buffer)
        maintenance_seconds = self._estimate_buffer_maintenance_seconds(buffer_size)
        refill_elapsed = (
            max(0.0, time.time() - self.last_refill_started_at)
            if self.is_refilling and self.last_refill_started_at else None
        )
        return {
            "active": self.connected,
            "simulation": not self.connected,
            "backend": self.backend.name if self.backend else "None",
            "realsim": bool(self.backend and "sim" in self.backend.name.lower()),
            "entropy_buffer_size": buffer_size,
            "entropy_consumption_count": len(self._entropy_consumption_log),
            "entropy_consumption_rate_per_minute": round(
                self._recent_consumption_rate() * 60.0,
                3,
            ),
            "last_entropy": self.last_entropy,
            "min_buffer_size": self.min_buffer_size,
            "is_refilling": self.is_refilling,
            "learned_threshold": round(self._learned_threshold, 4),
            "estimated_buffer_maintenance_seconds": maintenance_seconds,
            "estimated_buffer_maintenance_minutes": (
                round(maintenance_seconds / 60.0, 4)
                if maintenance_seconds is not None else None
            ),
            "life_force": {
                "total": round(self.total_life_force, 4),
                "last_yield": round(self.last_life_force_yield, 4),
                "last_harvest_timestamp": self.last_harvest_timestamp,
                "omega_convergence_ratio": (
                    round(self.last_run_summary.get("omega_convergence_ratio", 0.0), 4)
                    if self.last_run_summary else None
                ),
            },
            "uq_payload": dict(
                getattr(self.synaptic_field, "uq_payload", {}) or
                self.last_run_summary.get("uq_payload", {}) or
                {}
            ),
            "last_run": dict(self.last_run_summary),
            "last_quantum_signature": dict(self.last_quantum_signature),
            "recent_runs": self.get_recent_runs(limit=5),
            "last_refill": {
                "started_at": self.last_refill_started_at,
                "started_at_iso": self._safe_timestamp_iso(self.last_refill_started_at) if self.last_refill_started_at else None,
                "completed_at": self.last_refill_completed_at,
                "completed_at_iso": self._safe_timestamp_iso(self.last_refill_completed_at) if self.last_refill_completed_at else None,
                "duration_seconds": round(self.last_refill_duration_seconds, 4),
                "active_duration_seconds": round(refill_elapsed, 4) if refill_elapsed is not None else None,
                "phase": self.last_refill_phase,
                "current_job": dict(self.current_job_metadata),
                "error": self.last_refill_error,
            },
            "synaptic_field_linked": self.synaptic_field is not None,
            "error": str(self.last_error) if self.last_error else None,
        }

    # [UPGRADE 2] Rich Metrics
    def _compute_decoherence_risk(self, counts: dict) -> float:
        """
        Measure how concentrated the distribution is on a few states.
        High concentration = possible decoherence = high risk.
        Returns float [0, 1]. 0 = healthy spread, 1 = collapsed to one state.
        """
        if not counts:
            return 1.0
        total = sum(counts.values())
        top_count = max(counts.values())
        # If the top state takes >60% of all shots, decoherence is likely
        concentration = top_count / total
        # Normalize: 1/N is perfect uniform (risk=0), 1.0 is fully collapsed (risk=1)
        n = max(len(counts), 2)
        uniform_share = 1.0 / n
        risk = (concentration - uniform_share) / (1.0 - uniform_share + 1e-10)
        return float(np.clip(risk, 0.0, 1.0))

    def _compute_bit_balance(self, counts: dict) -> float:
        """
        Measure how balanced the 0/1 ratio is across all bits and shots.
        Perfect balance = 0.5 per bit. Score close to 1.0 = well-balanced.
        This catches systematic bias (e.g., qubit always collapses to |0>).
        Returns float [0, 1].
        """
        if not counts:
            return 0.0
        total_bits = 0
        total_ones = 0
        for bitstring, count in counts.items():
            ones = sum(int(b) for b in bitstring)
            total_ones += ones * count
            total_bits += len(bitstring) * count
        if total_bits == 0:
            return 0.0
        one_rate = total_ones / total_bits
        # Score: how close to 0.5 is the bit rate? 1.0 = perfect, 0.0 = all 0s or all 1s
        balance = 1.0 - (2.0 * abs(one_rate - 0.5))
        return float(np.clip(balance, 0.0, 1.0))

    def _classify_run_quality(
        self, entropy_quality: float, decoherence_risk: float
    ) -> str:
        """
        Classify a quantum run into one of four quality tiers.
        This label gets stored in SessionDB for later oracle queries.
        """
        if entropy_quality >= 0.80 and decoherence_risk < 0.20:
            return 'EXCELLENT'
        elif entropy_quality >= 0.60 and decoherence_risk < 0.40:
            return 'GOOD'
        elif entropy_quality >= 0.40:
            return 'ACCEPTABLE'
        else:
            return 'DEGRADED'

    def _compute_non_locality_score(self, counts: dict) -> float:
        """
        [EXTENSION] Heuristic measure of semantic non-locality / distribution variance.
        Measures the presence of seemingly non-causal peaks in the state space.
        High variability across states that should be entangled suggests non-local pattern preservation.
        """
        if not counts or len(counts) < 2:
            return 0.0
        
        counts_list = list(counts.values())
        mean = np.mean(counts_list)
        std = np.std(counts_list)
        
        # Coefficient of variation as a proxy for 'peakedness' / non-locality signal
        cv = std / (mean + 1e-10)
        # Normalize to [0, 1] - 0.5 is a healthy target for randomized entanglement
        score = np.clip(cv / 2.0, 0.0, 1.0)
        return float(score)


# Singleton instance
_bridge_instance = None
_GLOBAL_QUANTUM_BRIDGE_KEY = "_COSMOS_QUANTUM_BRIDGE_SINGLETON"
_bridge_lock = threading.Lock()

def get_quantum_bridge(api_token: Optional[str] = None):
    global _bridge_instance
    bridge = getattr(builtins, _GLOBAL_QUANTUM_BRIDGE_KEY, None)
    if bridge is None:
        with _bridge_lock:
            bridge = getattr(builtins, _GLOBAL_QUANTUM_BRIDGE_KEY, None)
            if bridge is None:
                bridge = QuantumEntanglementBridge(api_token)
                setattr(builtins, _GLOBAL_QUANTUM_BRIDGE_KEY, bridge)
    elif api_token and api_token != bridge.api_token:
        bridge.api_token = api_token
    _bridge_instance = bridge
    return _bridge_instance

sys.modules["Cosmos.core.quantum_bridge"] = sys.modules[__name__]
sys.modules["cosmos.core.quantum_bridge"] = sys.modules[__name__]

