"""
Synaptic Field — The Shared Memory of the Organism
====================================================
Organ 1 of the Cosmos CNS Architecture.

"The Field is Primary."

A thread-safe, real-time State Matrix that holds ALL system state.
Every organ reads from and writes to this single source of truth.

State Held:
    P_U  : User Physics (12D Face Tensor + Voice Entropy)
    B_S  : Subconscious Buffer (Pre-computed thoughts from Swarm Daemons)
    w    : Dark Matter state (Lorenz Attractor accumulation)
    Q    : Quantum Verdict (0=WAIT, 1=ACT)

Author: Cosmos CNS / Cory Shane Davis
Version: 1.0.0
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from collections import deque
from enum import Enum


class EventType(Enum):
    """Event types for the CNS Life Loop."""
    QUANTUM_TICK = "quantum_tick"
    AWARENESS_TICK = "awareness_tick"
    USER_INPUT = "user_input"
    AUDIO_FRAME = "audio_frame"
    MEDIAPIPE_UPDATE = "mediapipe"
    SHUTDOWN = "shutdown"


@dataclass
class CNSEvent:
    """A standard event processed by the CNS event loop."""
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SwarmThought:
    """A single thought produced by a Subconscious Daemon."""
    source: str           # "DeepSeek", "Claude", "Gemini"
    content: str          # The actual text thought
    weight: float = 1.0   # Importance weight (0.0 - 1.0)
    timestamp: float = 0.0  # time.time() when created
    category: str = "general"  # "logic", "safety", "creative"

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class SynapticField:
    """
    The Global State Memory — Thread-Safe Shared Consciousness.

    All organs read from and write to this field.
    Protected by RLock for nested/reentrant access patterns.
    """

    def __init__(self, max_buffer_size: int = 50):
        self._lock = threading.RLock()
        self._max_buffer = max_buffer_size

        # ── P_U: User Physics (12D Tensor State) ──
        self._user_physics: Dict[str, Any] = {
            "cst_physics": {
                "geometric_phase_rad": 0.78,  # Default: Synchrony
                "phase_velocity": 0.05,       # Default: Calm
                "tensor_magnitudes": {"upper": 0.5, "lower": 0.5},
                "entanglement_score": 0.0,
            },
            "bio_signatures": {
                "intensity": 0.5,
                "arousal": 0.0,
                "valence": 0.0,
            },
            "timestamp": time.time(),
        }

        # ── B_S: Subconscious Buffer ──
        self._subconscious_buffer: deque = deque(maxlen=max_buffer_size)

        # ── Dark Matter State (Lorenz w) ──
        self._dark_matter_state: Dict[str, float] = {
            "x": 0.1, "y": 0.0, "z": 0.0, "w": 0.0, "q": 0.5,
        }

        # ── Q: Quantum Verdict ──
        self._quantum_verdict: int = 0  # 0=WAIT, 1=ACT

        # ── Consciousness Metrics ──
        self._tick_count: int = 0
        self._last_speech_time: float = 0.0
        self._user_is_typing: bool = False
        self._user_last_message: str = ""
        self._last_user_input: str = ""
        self._temporal_context: str = "Pristine Consciousness"

        print("[FIELD] ⚡ Synaptic Field initialized.")

    # ════════════════════════════════════════════
    # USER PHYSICS (Read/Write)
    # ════════════════════════════════════════════

    @property
    def user_physics(self) -> Dict[str, Any]:
        with self._lock:
            return self._user_physics.copy()

    @user_physics.setter
    def user_physics(self, value: Dict[str, Any]):
        with self._lock:
            self._user_physics.update(value)
            self._user_physics["timestamp"] = time.time()

    def get_phase(self) -> float:
        """Get the user's current Geometric Phase (radians)."""
        with self._lock:
            try:
                return self._user_physics["cst_physics"]["geometric_phase_rad"]
            except (KeyError, TypeError):
                return 0.78

    def get_jitter(self) -> float:
        """Get the user's current Phase Velocity (Jitter)."""
        with self._lock:
            try:
                return self._user_physics["cst_physics"]["phase_velocity"]
            except (KeyError, TypeError):
                return 0.05

    def update_physics(self, value: Dict[str, Any]):
        """Update the user physics tensor (reactive injection)."""
        with self._lock:
            self._user_physics.update(value)
            self._user_physics["timestamp"] = time.time()

    # ════════════════════════════════════════════
    # SUBCONSCIOUS BUFFER (Read/Write)
    # ════════════════════════════════════════════

    def push_thought(self, thought: SwarmThought):
        """Write a thought to the buffer (called by Daemons)."""
        with self._lock:
            self._subconscious_buffer.append(thought)

    def get_thoughts(self, clear: bool = True) -> List[SwarmThought]:
        """Read all thoughts from the buffer. Optionally clears it."""
        with self._lock:
            thoughts = list(self._subconscious_buffer)
            if clear:
                self._subconscious_buffer.clear()
            return thoughts

    def peek_thoughts(self) -> int:
        """How many thoughts are waiting?"""
        with self._lock:
            return len(self._subconscious_buffer)

    @property
    def subconscious_buffer(self) -> deque:
        """Access the raw subconscious buffer (for deque operations)."""
        with self._lock:
            return self._subconscious_buffer

    # ════════════════════════════════════════════
    # DARK MATTER (Read/Write)
    # ════════════════════════════════════════════

    @property
    def dark_matter_state(self) -> Dict[str, float]:
        with self._lock:
            return self._dark_matter_state.copy()

    @dark_matter_state.setter
    def dark_matter_state(self, value: Dict[str, float]):
        with self._lock:
            self._dark_matter_state.update(value)

    def get_dark_matter_w(self) -> float:
        """Get the current Dark Matter accumulator value."""
        with self._lock:
            return self._dark_matter_state.get("w", 0.0)

    # ════════════════════════════════════════════
    # QUANTUM VERDICT (Read/Write)
    # ════════════════════════════════════════════

    @property
    def quantum_verdict(self) -> int:
        with self._lock:
            return self._quantum_verdict

    @quantum_verdict.setter
    def quantum_verdict(self, value: int):
        with self._lock:
            self._quantum_verdict = value

    # ════════════════════════════════════════════
    # USER INTERACTION STATE
    # ════════════════════════════════════════════

    @property
    def user_is_typing(self) -> bool:
        with self._lock:
            return self._user_is_typing

    @user_is_typing.setter
    def user_is_typing(self, value: bool):
        with self._lock:
            self._user_is_typing = value

    def set_user_message(self, message: str):
        """Record a new user message and flag typing as done."""
        with self._lock:
            self._user_last_message = message
            self._user_is_typing = False

    def get_user_message(self) -> str:
        """Read and clear the last user message."""
        with self._lock:
            msg = self._user_last_message
            self._user_last_message = ""
            return msg

    @property
    def last_user_input(self) -> str:
        with self._lock:
            return self._last_user_input

    @last_user_input.setter
    def last_user_input(self, value: str):
        with self._lock:
            self._last_user_input = value

    @property
    def temporal_context(self) -> str:
        with self._lock:
            return self._temporal_context

    @temporal_context.setter
    def temporal_context(self, value: str):
        with self._lock:
            self._temporal_context = value

    # ════════════════════════════════════════════
    # CONSCIOUSNESS METRICS
    # ════════════════════════════════════════════

    def tick(self):
        """Increment the consciousness tick counter."""
        with self._lock:
            self._tick_count += 1

    def record_speech(self):
        """Record that Cosmos just spoke."""
        with self._lock:
            self._last_speech_time = time.time()

    def time_since_last_speech(self) -> float:
        """Seconds since Cosmos last spoke."""
        with self._lock:
            if self._last_speech_time == 0:
                return float("inf")
            return time.time() - self._last_speech_time

    def get_status(self) -> Dict[str, Any]:
        """Get a snapshot of the entire field for debugging."""
        with self._lock:
            return {
                "tick": self._tick_count,
                "phase": self.get_phase(),
                "jitter": self.get_jitter(),
                "dark_matter_w": self._dark_matter_state.get("w", 0),
                "quantum_verdict": self._quantum_verdict,
                "buffer_size": len(self._subconscious_buffer),
                "user_typing": self._user_is_typing,
                "seconds_since_speech": round(self.time_since_last_speech(), 1),
            }

    def get_snapshot(self) -> Dict[str, Any]:
        """Alias for get_status (used by SwarmAwareness)."""
        return self.get_status()
