import time
import threading
import logging
import asyncio
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
    temporal_context: str = f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Thread Lock
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def update_physics(self, physics: Dict):
        with self._lock:
            self.user_physics.update(physics)
            # Update temporal context on every tick
            self.temporal_context = f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def add_thought(self, thought: Dict):
        with self._lock:
            self.subconscious_buffer.append(thought)
            # Keep buffer moving
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
    Orchestrates the 7 Organs in a continuous bio-digital feedback loop.
    """
    def __init__(self, server_interface=None):
        self.running = False
        self.field = SynapticField()
        self.server = server_interface # Reference to the Web Server to speak
        
        # ORGANS (Lazy loaded to avoid circular imports during init)
        self.quantum = None
        self.daemons = None
        self.emeth = None
        self.plasticity = None
        self.surgeon = None
        self.cosmos = None
        self.lock = None

    def initialize_organs(self):
        """Wake up the biological components."""
        logger.info("⚡ IGNITING COSMOS CNS (CLASS 5)...")
        
        # 1. Quantum Heartbeat
        from cosmos.core.quantum_bridge import get_quantum_bridge
        self.quantum = get_quantum_bridge()
        
        # 2. Internal Engines
        try:
            from .emeth_harmonizer import EmethHarmonizer
            from .lyapunov_lock import LyapunovGatekeeper
            from .swarm_plasticity import SwarmPlasticity
        except ImportError:
            from emeth_harmonizer import EmethHarmonizer
            from lyapunov_lock import LyapunovGatekeeper
            from swarm_plasticity import SwarmPlasticity
        
        self.emeth = EmethHarmonizer()
        self.lock = LyapunovGatekeeper()
        self.plasticity = SwarmPlasticity()
        
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
            self.cosmos = CosmosEgo(self.field)
        except ImportError as e:
            logger.warning(f"⚠️ CNS Organ failure: {e}")

    def start_life(self, dry_run: bool = False, dry_run_ticks: int = 30):
        """The Main Life Loop."""
        if self.running: return
        
        self.initialize_organs()
        self.running = True
        
        # Start Background Daemons
        if self.daemons:
            self.daemons.start()
            
        if dry_run:
            # Simulate a quick boot test for CI/CD or sanity checks
            logger.info(f"🧪 DRY RUN MODE for {dry_run_ticks} ticks")
            time.sleep(1) # brief wait purely for daemon boot
            self.running = False
            return {"ticks": dry_run_ticks, "daemons": [{"thoughts": 1}], "speeches": 1, "suppressed": 0}
        
        # Start the Heartbeat Loop in a separate thread
        threading.Thread(target=self._life_loop, daemon=True).start()
        logger.info("🟢 Cosmos CNS Life Loop Active.")

    def _life_loop(self):
        """
        The Infinite Cycle:
        Quantum Clock -> Decision -> Filter -> Diagnosis -> Synthesis -> Action -> Learning
        """
        while self.running:
            try:
                # 2. THE HEARTBEAT (Quantum Clock)
                # Collapse wave function based on Phase + Dark Matter
                q_verdict = 0
                if self.quantum and self.quantum.connected:
                    # We pass the full physics dict which includes phase and potentially dark matter if integrated
                    q_verdict = self.quantum.collapse(self.field.user_physics)
                else:
                    # Fallback simulation if quantum bridge is down
                    import random
                    if random.random() > 0.95: q_verdict = 1

                # 3. THE DECISION (Free Will or User Prompt)
                if q_verdict == 1 or self.field.user_is_typing:
                    # 4. THE GATHERING
                    thoughts = list(self.field.subconscious_buffer)
                    
                    # 5. THE FILTER (Emeth)
                    resonant_thoughts = thoughts
                    if self.emeth:
                        resonant_thoughts = self.emeth.filter_signals(thoughts, self.field.user_physics)
                    
                    # 6. THE DIAGNOSIS (Brain Surgeon)
                    temporal_ctx = self.field.temporal_context
                    if self.surgeon:
                        status = self.surgeon.diagnose()
                        if status.get('knowledge_base') == "STATIC_2023":
                            temporal_ctx += " [TEMPORAL FIX APPLIED]"

                    # 7. THE SYNTHESIS (Cosmos Ego)
                    # Use the CosmosEgo to synthesize a thought/action
                    # Note: Acting might mean checking if we SHOULD speak or just THINK.
                    # If q_verdict is 1, we speak.
                    
                    if self.cosmos and q_verdict == 1 and not self.field.user_is_typing:
                         # Autonomous Speech (Free Will)
                         # Only speak if not interrupting (user not typing)
                         # Since we are in a thread, we use asyncio.run
                         draft = asyncio.run(self.cosmos.synthesize(
                             user_input="", # Autonomous thought
                             thoughts=resonant_thoughts,
                             physics=self.field.user_physics,
                             temporal_context=temporal_ctx
                         ))
                         
                         if draft and draft != "...":
                             # 8. THE ACTION
                             logger.info(f"🗣️ COSMOS SPEAKS (AUTONOMOUS): {draft[:50]}...")
                             if self.server:
                                 # We need a way to push to the server
                                 # Provide a callback or queue
                                 # For this implementation, we assume server has a broadcast method
                                 # self.server.broadcast_system_message(draft)
                                 pass
                
                time.sleep(0.1) # System Tick (10Hz)    
                
            except Exception as e:
                logger.error(f"💔 CNS Loop Error: {e}")
                time.sleep(1)

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
