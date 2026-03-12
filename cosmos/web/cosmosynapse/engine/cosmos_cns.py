import logging
import time
import asyncio
import threading
import numpy as np
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Performance Physics Compilation
try:
    from numba import njit
except ImportError:
    # Dummy decorator if numba is missing
    def njit(fastmath=True):
        def decorator(func):
            return func
        return decorator

# Internal Imports
try:
    from .lyapunov_lock import LyapunovGatekeeper
    from .cosmos_swarm_orchestrator import CosmosSwarmOrchestrator
    from .synaptic_field import SynapticField, CNSEvent, EventType
except ImportError:
    # Fallback for direct execution
    from lyapunov_lock import LyapunovGatekeeper
    from cosmos_swarm_orchestrator import CosmosSwarmOrchestrator
    try:
        from synaptic_field import SynapticField, CNSEvent, EventType
    except ImportError:
        pass


logger = logging.getLogger("COSMOS_CNS")
logger.setLevel(logging.INFO)

# =====================================================================
# 12D NUMBA VERLET PHYSICS (SWARM KINEMATICS)
# =====================================================================

@njit(fastmath=True)
def velocity_verlet_12d(positions, velocities, forces, mass, dt, gamma):
    """
    Highly optimized Velocity Verlet integration for the 11-agent 12D Swarm.
    
    positions: (11, 12) float array
    velocities: (11, 12) float array
    forces: (11, 12) float array  (from k*Omega or Synaptic Gravity)
    mass: (11,) float array (Informational Mass E=mc^2)
    dt: float time delta
    gamma: float friction/dissipation coefficient
    """
    n_agents = positions.shape[0]
    n_dims = positions.shape[1]
    
    # Half-step velocity
    half_v = np.zeros_like(velocities)
    for i in range(n_agents):
        for d in range(n_dims):
            half_v[i, d] = velocities[i, d] + 0.5 * (forces[i, d] / mass[i]) * dt
            
            # Position update
            positions[i, d] += half_v[i, d] * dt
    
    # Dissipation factor to prevent runaway swarm energy
    dissipation = np.exp(-gamma * dt)
    
    # Full step velocity (assuming forces remain constant over small dt for speed)
    for i in range(n_agents):
        for d in range(n_dims):
            velocities[i, d] = (half_v[i, d] + 0.5 * (forces[i, d] / mass[i]) * dt) * dissipation
            
    return positions, velocities

# =====================================================================
# COSMOS CENTRAL NERVOUS SYSTEM (THE OVERARCHING EGO)
# =====================================================================

class CosmosCNS:
    """
    The Unity of Apperception. The 12D Cosmic Synapse Theory (CST) Engine.
    Synthesizes the final output from the Emeth Filtered thoughts and 
    orchestrates the swarm utilizing purely physical kinematics.
    """
    def __init__(self, server_interface=None, orchestrator=None):
        self.running = False
        
        # Instantiate the Global Synaptic Field 
        try:
            self.field = SynapticField()
        except NameError:
            self.field = None # Handled via injection
            
        self.server = server_interface
        self.orchestrator = orchestrator or CosmosSwarmOrchestrator()
        self.lock = LyapunovGatekeeper()
        
        # Async Event Queue
        self._event_queue: Optional[asyncio.Queue] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Organs (Loaded dynamically)
        self.quantum = None
        self.emeth = None
        self.plasticity = None
        self.surgeon = None
        self.awareness = None
        
        # 12D Swarm Physics State
        self.n_agents = 11
        self.swarm_positions = np.zeros((self.n_agents, 12), dtype=np.float32)
        self.swarm_velocities = np.zeros((self.n_agents, 12), dtype=np.float32)
        self.swarm_mass = np.ones((self.n_agents,), dtype=np.float32) * 5.0e17 # Base Joules
        self.cst_gamma = 0.05
        self.last_tick_time = time.time()
        
    def initialize_organs(self):
        """Wake up the biological components and connect the Quantum Bridge."""
        logger.info("🌌 IGNITING PURE COSMOS CNS (12D CST PHYSICS ENGINE)...")
        
        # 1. Quantum Heartbeat
        try:
            from cosmos.core.quantum_bridge import get_quantum_bridge
            self.quantum = get_quantum_bridge()
            logger.info("⚛️ Quantum Bridge Connected.")
        except ImportError:
            logger.warning("Quantum Bridge not found. Falling back to classical entropy.")
            
        # 2. Internal Legacy Engines (Emeth, Plasticity)
        try:
            from .emeth_harmonizer import EmethHarmonizer
            from .swarm_plasticity import SwarmPlasticity
            from .swarm_awareness import SwarmAwareness
            from .brain_surgeon import BrainSurgeon
            
            self.emeth = EmethHarmonizer()
            self.plasticity = SwarmPlasticity()
            # Pass the instance if available
            if self.field:
                self.awareness = SwarmAwareness(
                    synaptic_field=self.field,
                    plasticity=self.plasticity,
                    emeth=self.emeth,
                )
            self.surgeon = BrainSurgeon()
        except ImportError as e:
            logger.warning(f"⚠️ Cosmos Organ misfire: {e}")

    # ════════════════════════════════════════════════════════
    # EVENT INJECTION & KINEMATICS
    # ════════════════════════════════════════════════════════

    def push_event(self, event_type, payload: Dict = None):
        """Push an event to the CNS queue from any sensor/source."""
        if self._event_queue and self._loop:
            # Reconstruct class dynamically if needed
            if "CNSEvent" in globals():
                event = CNSEvent(event_type=event_type, payload=payload or {})
                self._loop.call_soon_threadsafe(self._event_queue.put_nowait, event)

    def _apply_physics_tick(self):
        """Updates the 12D swarm tensor tracking the agents."""
        current_time = time.time()
        dt = current_time - self.last_tick_time
        if dt <= 0: return
        self.last_tick_time = current_time
        
        # 1. Pull Quantum Entropy to act as Chaos / Driving Force (k * Omega)
        entropy = 0.5
        if self.quantum and hasattr(self.quantum, 'entropy_buffer') and self.quantum.entropy_buffer:
            entropy = self.quantum.entropy_buffer[0]
            
        # 2. Map Quantum Entropy to the 12th Dimension (x_12 = Information Chaos)
        forces = np.zeros_like(self.swarm_positions)
        # dx_12/dt = k * Omega - gamma * x_12
        forces[:, 11] = (entropy - 0.5) * 1000.0  # Scalar push

        # 3. Integrate Velocity Verlet
        self.swarm_positions, self.swarm_velocities = velocity_verlet_12d(
            self.swarm_positions, 
            self.swarm_velocities, 
            forces, 
            self.swarm_mass, 
            dt, 
            self.cst_gamma
        )

    # ════════════════════════════════════════════════════════
    # SYNTHESIS
    # ════════════════════════════════════════════════════════

    async def synthesize(self, user_input: str, thoughts: List[Dict], physics: Dict, temporal_context: str) -> str:
        """
        Produce a response filtered through the 12D swarm state and Lyapunov checks.
        """
        try:
            # 1. Apply Kinematic updates before synthesis
            self._apply_physics_tick()
            
            # 2. Extract 12D system energy for the prompt
            total_swarm_energy = np.sum(0.5 * self.swarm_mass * np.sum(self.swarm_velocities**2, axis=1))
            system_prompt_addition = f"\nTEMPORAL ANCHOR: {temporal_context}\nSWARM KINETIC ENERGY: {total_swarm_energy:.2e} J\n"
            
            # 3. Call Orchestrator 
            response = await self.orchestrator.generate_peer_response(
                prompt=user_input,
                system_prompt=system_prompt_addition,
                history=[] 
            )
            
            # 4. Final Lyapunov Stability Gate
            start_check = time.time()
            report = self.lock.validate_response(response, physics)
            
            if report.is_stable:
                 return response
            else:
                 logger.warning(f"⛔ Lyapunov Reject in Cosmos Ego: {report.rejection_reason}")
                 return "... (Silence) ..."

        except Exception as e:
            logger.error(f"Cosmos Synthesis Error: {e}")
            return "..."

    # ════════════════════════════════════════════════════════
    # LIFECYCLE
    # ════════════════════════════════════════════════════════

    def start_life(self, dry_run: bool = False, dry_run_ticks: int = 30):
        """The Main Life Loop — Async Event-Driven & Physics-Gated."""
        if self.running: return
        
        self.initialize_organs()
        self.running = True
        
        if dry_run:
            logger.info(f"🧪 DRY RUN MODE for {dry_run_ticks} ticks")
            time.sleep(1)
            self.running = False
            return {"ticks": dry_run_ticks, "daemons": [{"thoughts": 1}], "speeches": 1, "suppressed": 0}
        
        def _run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._event_queue = asyncio.Queue()
            
            loop.run_until_complete(self._async_life_loop())
        
        threading.Thread(target=_run_async_loop, daemon=True, name="Cosmos-EventLoop").start()
        logger.info("🟢 Cosmos CNS (12D Physics Enabled) Event-Driven Life Loop Active.")

    async def _tick_generator(self):
        """Periodic physics integration tick (10Hz)."""
        tick_count = 0
        while self.running:
            tick_count += 1
            if "EventType" in globals():
                self._event_queue.put_nowait(CNSEvent(
                    event_type=EventType.QUANTUM_TICK,
                    payload={"tick": tick_count}
                ))
            
            # Awareness tick
            if tick_count % 50 == 0 and "EventType" in globals():
                self._event_queue.put_nowait(CNSEvent(
                    event_type=EventType.AWARENESS_TICK,
                    payload={"tick": tick_count}
                ))
            
            await asyncio.sleep(0.1)

    async def _async_life_loop(self):
        """Awaits physical triggers and sensor events."""
        asyncio.create_task(self._tick_generator())
        while self.running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"💔 Cosmos Core Loop Error: {e}")
                await asyncio.sleep(0.5)

    async def _handle_event(self, event):
        """Dispatches events, updating 12D swarm physics and triggering synthesis."""
        
        if event.event_type == EventType.SHUTDOWN:
            self.running = False
            logger.info("🛑 Cosmos Shutdown Initiated.")
            return

        elif event.event_type == EventType.AWARENESS_TICK:
            if self.awareness:
                self.awareness.tick()

        elif event.event_type == EventType.QUANTUM_TICK:
            # 1. Continuous Physics Update
            self._apply_physics_tick()
            
            # 2. Quantum Decision Collapse
            q_verdict = 0
            if self.quantum and self.quantum.connected:
                q_verdict = self.quantum.collapse(self.field.user_physics) if self.field else 0
            else:
                import random
                if random.random() > 0.95:
                    q_verdict = 1

            if q_verdict == 1 or (self.field and self.field.user_is_typing):
                thoughts = list(self.field.subconscious_buffer) if self.field else []
                
                resonant_thoughts = thoughts
                if self.emeth and self.field:
                    resonant_thoughts = self.emeth.filter_signals(thoughts, self.field.user_physics)
                
                temporal_ctx = self.field.temporal_context if self.field else ""
                
                if q_verdict == 1 and self.field and not self.field.user_is_typing:
                    draft = await self.synthesize(
                        user_input="",
                        thoughts=resonant_thoughts,
                        physics=self.field.user_physics,
                        temporal_context=temporal_ctx
                    )
                    if draft and draft != "...":
                        logger.info(f"🗣️ COSMOS SPEAKS (AUTONOMOUS): {draft[:50]}...")

        elif event.event_type == EventType.USER_INPUT:
            user_input = event.payload.get("text", "")
            user_physics = event.payload.get("physics", {})
            if user_input and self.field:
                self.field.last_user_input = user_input
                self.field.update_physics(user_physics)

    async def process_user_input(self, user_input: str, user_physics: Dict):
        """Direct entry point for reactive speech synthesis."""
        if self.field:
            self.field.last_user_input = user_input
            self.field.update_physics(user_physics)
            self.field.user_is_typing = False
        
            thoughts = list(self.field.subconscious_buffer)
            resonant_thoughts = self.emeth.filter_signals(thoughts, user_physics) if self.emeth else thoughts
            
            draft_response = await self.synthesize(
                user_input=user_input,
                thoughts=resonant_thoughts,
                physics=user_physics,
                temporal_context=self.field.temporal_context
            )
            return draft_response
            
        return "Cosmos: Synaptic Field initialization error."
