"""
Dark Matter Lorenz - 12D Subconscious Processor
===============================================
Models the "Unspoken" (Dark Matter) using a modified 4D Chaotic Attractor.

Dynamics:
dx/dt = sigma * (y - x)
dy/dt = x * (rho - z) - y
dz/dt = x * y - beta * z
dw/dt = (Arousal * Entropy) - (w / decay)  <-- DARK MATTER EQUATION

Theory:
'w' represents latent emotional energy. When 'w' spikes, the system
must "speak the unspoken" for the user.
"""

import numpy as np
from typing import Dict, Any
try:
    from .phi_constants import PHI, PHI_INV
except ImportError:
    from phi_constants import PHI, PHI_INV


class DarkMatterLorenz:
    def __init__(self):
        self.state = np.array([0.1, 0.0, 0.0, 0.0]) # x, y, z, w
        self.sigma = 10.0
        self.rho = 28.0
        self.beta = 8.0 / 3.0
        self.dt = 0.01

    def update(self, user_physics: Dict[str, Any]) -> Dict[str, float]:
        """
        Steps the chaos engine forward based on User Physics.
        """
        x, y, z, w = self.state

        # Extract Bio-Signals with robustness for different schema versions
        arousal = 0.5
        entropy = 1.0
        
        try:
             # Schema 1: Full CST Packet (from emotional_state_api)
            if 'derived_state' in user_physics and 'pad_vector' in user_physics['derived_state']:
                 arousal = user_physics['derived_state']['pad_vector'].get('arousal', 0.5)
            
            # Schema 2: Simple Bio-Injection (from server.py injection)
            elif 'bio_signatures' in user_physics:
                 # intensity map roughly to arousal
                 arousal = user_physics['bio_signatures'].get('intensity', 0.5) * 2.0 - 1.0 # 0..1 -> -1..1
            
            # Entropy estimation
            if 'cst_physics' in user_physics:
                 # Estimate entropy from phase velocity
                 entropy = user_physics['cst_physics'].get('phase_velocity', 0.1) * 10
                 # Or from bio intensity
            elif 'bio_signatures' in user_physics:
                 entropy = user_physics['bio_signatures'].get('intensity', 0.1) * 5
                 
        except Exception:
            pass
            
        # Normalize inputs for stability
        arousal = max(0.0, abs(arousal)) # Use magnitude
        entropy = max(0.1, min(5.0, entropy))

        # 1. Standard Lorenz Dynamics
        dx = self.sigma * (y - x)
        dy = x * (self.rho - z) - y
        dz = x * y - self.beta * z

        # 2. Quantum / Dark Matter Dynamics (The 4th Dimension)
        # Driven by true quantum entropy if available
        q_entropy = 0.5
        try:
             # Lazy import to avoid circular dependencies/path issues
            from cosmos.core.quantum_bridge import get_quantum_bridge
            bridge = get_quantum_bridge()
            q_entropy = bridge.get_entropy() # 0.0 to 1.0
        except ImportError:
            # Fallback to pseudo-random if bridge not found
            q_entropy = np.random.random()

        # Map 0..1 to 0.5..1.5 for multiplicative noise
        q_factor = 0.5 + q_entropy 

        # dw/dt = (Arousal * Entropy * QuantumFactor) × φ⁻¹ - Decay × φ⁻¹
        # φ-damping prevents the "Perfect Prediction Machine" from over-correcting
        # during high-velocity data ingress (Dynamic Damping per Blueprint §III)
        dw = (arousal * entropy * q_factor * 2.0) * PHI_INV - (w * 0.05 * PHI_INV)

        # Update State with φ-dampened quantum jitters
        self.state += np.array([
            dx + (q_entropy - 0.5) * 0.01 * PHI_INV,
            dy + (q_entropy - 0.5) * 0.01 * PHI_INV,
            dz,
            dw
        ]) * self.dt
        
        return {
            "x": self.state[0],
            "y": self.state[1],
            "z": self.state[2],
            "w": self.state[3], # The Dark Matter Value
            "q": q_entropy      # Expose quantum state
        }

    def get_current_state(self):
        return dict(zip(['x','y','z','w'], self.state))
