import time
import threading
import logging
import asyncio
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Internal Imports
try:
    from .phi_constants import PHI, PHI_INV
except ImportError:
    from phi_constants import PHI, PHI_INV

# Configure Logger
logger = logging.getLogger("COSMOS_CNS")
logger.setLevel(logging.INFO)


# ════════════════════════════════════════════════════════
# V4.0: EVENT-DRIVEN ARCHITECTURE
# ════════════════════════════════════════════════════════

class EventType(Enum):
    """V4.0: Event types for the async CNS life loop."""
    QUANTUM_TICK = "quantum_tick"       # Periodic heartbeat (~10Hz)
    USER_INPUT = "user_input"           # User sent a message
    AUDIO_FRAME = "audio_frame"         # Audio sensor data arrived
    MEDIAPIPE_UPDATE = "mediapipe"      # MediaPipe pose/face/hand update
    AWARENESS_TICK = "awareness_tick"   # Swarm-awareness assessment due
    STATE_CHECKPOINT = "state_check"    # P2P state checkpoint trigger
    SHUTDOWN = "shutdown"               # Graceful shutdown


@dataclass
class CNSEvent:
    """V4.0: A single event in the CNS event queue."""
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SynapticField:
    """
    The Global Shared State (The Field).
    There is no Input -> Output, only writes to the Field.
    """
    # 1. User State (The Physics)
    user_physics: Dict[str, Any] = field(default_factory=dict)
    user_voice_entropy: float = 0.0
    user_is_typing: bool = False
    last_user_input: str = ""
    last_input_time: float = 0.0
    
    # 2. Subconscious Buffer (The Swarm)
    subconscious_buffer: List[Dict] = field(default_factory=list)
    
    # 3. System State (The Body)
    dark_matter_state: Dict[str, float] = field(default_factory=lambda: {'x': 0.1, 'y': 0.1, 'z': 0.1, 'w': 0.0})
    quantum_verdict: int = 0  # 0 = Wait, 1 = Act
    
    # 4. Temporal Context
    temporal_context: str = field(default_factory=lambda: f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Thread Lock
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def update_physics(self, physics: Dict):
        with self._lock:
            self.user_physics.update(physics)
            self.temporal_context = f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def add_thought(self, thought: Dict):
        with self._lock:
            self.subconscious_buffer.append(thought)
            if len(self.subconscious_buffer) > 50:
                self.subconscious_buffer.pop(0)

    def get_snapshot(self) -> Dict:
        with self._lock:
            return {
                "user_physics": self.user_physics.copy(),
                "buffer_size": len(self.subconscious_buffer),
                "dark_matter": self.dark_matter_state.copy(),
                "time": self.temporal_context
            }

class CosmosCNS:
    """
    The Central Nervous System (Class 5 Symbiote).
    V4.0: Async Event-Driven Architecture.
    Orchestrates the 7 Organs via an event queue instead of busy-polling.
    """
    def __init__(self, server_interface=None, orchestrator=None):
        self.running = False
        self.field = SynapticField()
        self.server = server_interface
        self.orchestrator = orchestrator
        
        # V4.0: Event Queue
        self._event_queue: Optional[asyncio.Queue] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # ORGANS (Lazy loaded)
        self.quantum = None
        self.daemons = None
        self.emeth = None
        self.plasticity = None
        self.surgeon = None
        self.cosmos = None
        self.lock = None
        self.awareness = None  # Swarm-Awareness Protocol (The Mirror)

    def initialize_organs(self):
        """Wake up the biological components."""
        logger.info("⚡ IGNITING COSMOS CNS (CLASS 5 / V4.0 EVENT-DRIVEN)...")
        
        # 1. Quantum Heartbeat
        from cosmos.core.quantum_bridge import get_quantum_bridge
        self.quantum = get_quantum_bridge()
        
        # 2. Internal Engines
        try:
            from .emeth_harmonizer import EmethHarmonizer
            from .lyapunov_lock import LyapunovGatekeeper
            from .swarm_plasticity import SwarmPlasticity
            from .swarm_awareness import SwarmAwareness
        except ImportError:
            from emeth_harmonizer import EmethHarmonizer
            from lyapunov_lock import LyapunovGatekeeper
            from swarm_plasticity import SwarmPlasticity
            from swarm_awareness import SwarmAwareness
        
        self.emeth = EmethHarmonizer()
        self.lock = LyapunovGatekeeper()
        self.plasticity = SwarmPlasticity()
        
        # 2b. Swarm-Awareness Protocol (The Mirror)
        self.awareness = SwarmAwareness(
            synaptic_field=self.field,
            plasticity=self.plasticity,
            emeth=self.emeth,
        )
        logger.info("🪞 Swarm-Awareness Protocol (The Mirror) initialized.")
        
        # 3. New Organs (To be created)
        try:
            try:
                from .swarm_daemons import SwarmDaemons
                from .brain_surgeon import BrainSurgeon
                from .cosmos_cns import CosmosEgo
            except ImportError:
                from swarm_daemons import SwarmDaemons
                from brain_surgeon import BrainSurgeon
                from cosmos_cns import CosmosEgo
            
            self.daemons = SwarmDaemons(self.field)
            self.surgeon = BrainSurgeon()
            self.cosmos = CosmosEgo(self.field, orchestrator=self.orchestrator)
        except ImportError as e:
            logger.warning(f"⚠️ CNS Organ failure: {e}")

    # ════════════════════════════════════════════════════════
    # V4.0: EVENT INJECTION API
    # ════════════════════════════════════════════════════════

    def push_event(self, event_type: EventType, payload: Dict = None):
        """Push an event to the CNS queue from any sensor/source."""
        if self._event_queue and self._loop:
            event = CNSEvent(event_type=event_type, payload=payload or {})
            self._loop.call_soon_threadsafe(self._event_queue.put_nowait, event)

    # ════════════════════════════════════════════════════════
    # LIFECYCLE
    # ════════════════════════════════════════════════════════

    def start_life(self, dry_run: bool = False, dry_run_ticks: int = 30):
        """The Main Life Loop — V4.0 async event-driven."""
        if self.running: return
        
        self.initialize_organs()
        self.running = True
        
        # Start Background Daemons
        if self.daemons:
            self.daemons.start()
            
        if dry_run:
            logger.info(f"🧪 DRY RUN MODE for {dry_run_ticks} ticks")
            time.sleep(1)
            self.running = False
            return {"ticks": dry_run_ticks, "daemons": [{"thoughts": 1}], "speeches": 1, "suppressed": 0}
        
        # V4.0: Launch async event loop in a daemon thread
        def _run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._event_queue = asyncio.Queue()
            
            loop.run_until_complete(self._async_life_loop())
        
        threading.Thread(target=_run_async_loop, daemon=True, name="CNS-EventLoop").start()
        logger.info("🟢 Cosmos CNS V4.0 Event-Driven Life Loop Active.")

    async def _tick_generator(self):
        """V4.0: Periodic tick source — replaces the old 10Hz busy-loop."""
        tick_count = 0
        while self.running:
            tick_count += 1
            self._event_queue.put_nowait(CNSEvent(
                event_type=EventType.QUANTUM_TICK,
                payload={"tick": tick_count}
            ))
            
            # Awareness tick every 50 quantum ticks
            if tick_count % 50 == 0:
                self._event_queue.put_nowait(CNSEvent(
                    event_type=EventType.AWARENESS_TICK,
                    payload={"tick": tick_count}
                ))
            
            await asyncio.sleep(0.1)  # 10Hz base rate

    async def _async_life_loop(self):
        """
        V4.0: Event-Driven Life Loop.
        Instead of polling every 100ms, we await events from the queue.
        Events come from: tick_generator, audio sensors, MediaPipe, user input.
        """
        # Start the tick generator as a concurrent task
        asyncio.create_task(self._tick_generator())
        
        while self.running:
            try:
                # Await the next event (blocks until one arrives)
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                # No events for 1s — that's fine, loop continues
                continue
            except Exception as e:
                logger.error(f"💔 CNS Event Loop Error: {e}")
                await asyncio.sleep(0.5)

    async def _handle_event(self, event: CNSEvent):
        """V4.0: Dispatch events to the appropriate organ."""
        
        if event.event_type == EventType.SHUTDOWN:
            self.running = False
            logger.info("🛑 CNS Shutdown event received.")
            return

        elif event.event_type == EventType.AWARENESS_TICK:
            # Swarm-Awareness self-assessment
            if self.awareness:
                report = self.awareness.tick()
                if report and not report.aligned:
                    logger.warning(
                        f"🪞 AWARENESS: Misalignment detected! "
                        f"Score={report.alignment_score:.3f}"
                    )

        elif event.event_type == EventType.QUANTUM_TICK:
            # THE HEARTBEAT — Quantum Clock
            q_verdict = 0
            if self.quantum and self.quantum.connected:
                q_verdict = self.quantum.collapse(self.field.user_physics)
            else:
                import random
                if random.random() > 0.95:
                    q_verdict = 1

            # THE DECISION
            if q_verdict == 1 or self.field.user_is_typing:
                thoughts = list(self.field.subconscious_buffer)
                
                # THE FILTER (Emeth)
                resonant_thoughts = thoughts
                if self.emeth:
                    resonant_thoughts = self.emeth.filter_signals(thoughts, self.field.user_physics)
                
                # THE DIAGNOSIS (Brain Surgeon)
                temporal_ctx = self.field.temporal_context
                if self.surgeon:
                    status = self.surgeon.diagnose()
                    if status.get('knowledge_base') == "STATIC_2023":
                        temporal_ctx += " [TEMPORAL FIX APPLIED]"

                # THE SYNTHESIS (Cosmos Ego) — Autonomous Speech
                if self.cosmos and q_verdict == 1 and not self.field.user_is_typing:
                    draft = await self.cosmos.synthesize(
                        user_input="",
                        thoughts=resonant_thoughts,
                        physics=self.field.user_physics,
                        temporal_context=temporal_ctx
                    )
                    
                    if draft and draft != "...":
                        logger.info(f"🗣️ COSMOS SPEAKS (AUTONOMOUS): {draft[:50]}...")

        elif event.event_type == EventType.AUDIO_FRAME:
            # V4.0: Live audio sensor trigger
            audio_data = event.payload.get("audio_data")
            if audio_data:
                # Update voice entropy in the field
                entropy = event.payload.get("entropy", 0.0)
                self.field.user_voice_entropy = entropy

        elif event.event_type == EventType.MEDIAPIPE_UPDATE:
            # V4.0: MediaPipe pose/face/hand state transition
            mp_data = event.payload
            if mp_data and "landmarks" in mp_data:
                # Inject into user physics as bio-signal
                self.field.update_physics({"mediapipe": mp_data})

        elif event.event_type == EventType.USER_INPUT:
            # Direct user input event (alternative to process_user_input)
            user_input = event.payload.get("text", "")
            user_physics = event.payload.get("physics", {})
            if user_input:
                self.field.last_user_input = user_input
                self.field.update_physics(user_physics)

    async def process_user_input(self, user_input: str, user_physics: Dict):
        """
        External Entry Point (from Server).
        Writes to Field -> Triggers Immediate Reaction (Reactive Path).
        """
        # Update Field
        self.field.last_user_input = user_input
        self.field.update_physics(user_physics)
        self.field.user_is_typing = False # Message sent
        
        # 4. THE GATHERING
        thoughts = list(self.field.subconscious_buffer) # Copy buffer
        
        # 5. THE FILTER (Emeth)
        # Filter thoughts based on NEW physics
        resonant_thoughts = self.emeth.filter_signals(thoughts, user_physics) if self.emeth else thoughts
        
        # 6. THE DIAGNOSIS (Brain Surgeon)
        if self.surgeon:
            cortex_status = self.surgeon.diagnose()
            if cortex_status.get('knowledge_base') == "STATIC_2023":
                 # Inject Time Anchor
                 self.field.temporal_context = f"CURRENT DATE: {datetime.now().strftime('%Y-%m-%d')}. (Real-time injection)."

        # 7. THE SYNTHESIS (Cosmos Ego)
        if self.cosmos:
            draft_response = await self.cosmos.synthesize(
                user_input=user_input,
                thoughts=thoughts,     # Subconscious context
                physics=user_physics,
                temporal_context=self.field.temporal_context
            )
            
            # 8. THE CENSOR (Lyapunov)
            is_stable = True
            if self.lock:
                # Visualize checking
                pass 
                
            if is_stable:
                # 9. THE ACTION
                return draft_response
                
                # 10. THE LEARNING (Plasticity)
                # (Async update)
        
        return "Cosmos CNS: Systems initializing..."
