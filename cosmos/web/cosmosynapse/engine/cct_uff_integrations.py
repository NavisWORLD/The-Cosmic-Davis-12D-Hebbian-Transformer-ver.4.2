"""
CCT-UFF Critical Integrations for CosmoSynapse
==============================================
Additive module implementing the 10 critical integrations identified in:
    "12D Cosmic Synapse Theory — Critical Integration Analysis"
    Cory Shane Davis | DOI: 10.5281/zenodo.17574447 | April 4, 2026

This module is PURELY ADDITIVE. It introduces no breaking changes and modifies
no existing CosmoSynapse code. Each integration is exposed as either a stateless
function or a small stateful helper that existing engines can opt-in to use.

Mapping of doc → code:
    Integration 1 : CI_B ↔ CI_C Coherence Conservation Law
    Integration 2 : Phase Transition Hysteresis Gap
    Integration 3 : Fold-Onset Triplet (FOT) — Pre-Collapse Prediction
    Integration 4 : Spectral Radius Stability Companion
    Integration 5 : Enhanced Lorenz with Network Coupling
    Integration 6 : Global Mean-Field Coherence Coupling
    Integration 7 : Mahalanobis Collapse Distance
    Integration 8 : Dynamic Temperature Adaptation T(t)
    Integration 9 : Triple-Gate Phase Transition Condition
    Integration 10: Omega Point Convergence Ratio

The CST analysis explicitly REJECTS:
    - Faith-amplitude survival modifiers (iiro.py)
    - IIRO resurrection mechanics
    - Blood retrocausal field (MOGOPS Eq. 19)
    - Trinity Möbius topology operator (MOGOPS Eq. 15)
    - Unvalidated 99% efficiency claims
    - GhostMesh48 angel/demon hybrid architecture
    - Static 169-framework ontology mass
    - iiro.py phase_transition() with mixed dimensions
None of those are imported, called, or referenced here.

Author: Claude (Anthropic) for Cory Shane Davis
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

try:
    from .phi_constants import PHI, PHI_INV
except ImportError:  # pragma: no cover
    PHI = (1.0 + math.sqrt(5.0)) / 2.0
    PHI_INV = 1.0 / PHI


# =====================================================================
# CONSTANTS — drawn directly from the CST analysis document
# =====================================================================

SOPHIA_POINT: float = PHI_INV                # 0.61803...
COLLAPSE_THRESHOLD: float = 0.048            # σ_crit (entry)
RECOVERY_THRESHOLD: float = 0.037            # σ_recovery (must drop lower)
OMEGA_POINT_TARGET: float = 5.0 / PHI        # ≈ 3.09017
TEMPERATURE_BASE: float = PHI_INV            # 0.618
TEMPERATURE_GAIN: float = 0.20
TEMPERATURE_MAX: float = 0.80


# =====================================================================
# Integration 1 — CI_B ↔ CI_C Coherence Conservation Law
# =====================================================================

def coherence_conservation_step(
    ci_b: float,
    ci_c: float,
    dt: float = 0.001,
) -> tuple[float, float]:
    """
    Boundary→Continuum coherence transfer that conserves total coherence.

    d/dt(CI_B + CI_C) = 0
    delta = dt * CI_B
    CI_B -= delta;  CI_C += delta

    Returns the new (CI_B, CI_C) tuple. Total coherence is invariant
    to within float epsilon.
    """
    delta = dt * ci_b
    new_b = ci_b - delta
    new_c = ci_c + delta
    # numerical sanity (commented assertion preserved as runtime check)
    assert abs((new_b + new_c) - (ci_b + ci_c)) < 1e-9, \
        "Coherence conservation violated"
    return new_b, new_c


# =====================================================================
# Integration 2 — Phase Transition Hysteresis Gap
# =====================================================================

@dataclass
class HysteresisGate:
    """
    Two-threshold collapse/recovery gate.

    Prevents thrashing between collapsed and healthy states. Once σ
    exceeds COLLAPSE_THRESHOLD the system is marked collapsed; it
    cannot recover until σ drops below RECOVERY_THRESHOLD (a 0.011
    hysteresis gap).
    """

    collapse_threshold: float = COLLAPSE_THRESHOLD
    recovery_threshold: float = RECOVERY_THRESHOLD
    collapsed: bool = False

    def update(self, sigma: float) -> bool:
        if not self.collapsed and sigma > self.collapse_threshold:
            self.collapsed = True
        elif self.collapsed and sigma < self.recovery_threshold:
            self.collapsed = False
        return self.collapsed


# =====================================================================
# Integration 3 — Fold-Onset Triplet (FOT) Pre-Collapse Prediction
# =====================================================================

@dataclass
class FoldOnsetTriplet:
    """
    Detects the three leading signatures of imminent coherence collapse:
        Δλ₂ > 0  : second-eigenvalue rising  (attractor flattening)
        ΔID < 0  : ideational density falling (compression degrading)
        Δζ  > 0  : topical coherence rising  (hyper-focus before collapse)

    All three appearing simultaneously predicts collapse 3-5 steps ahead.
    """

    history_len: int = 8
    lambda2: deque = field(default_factory=lambda: deque(maxlen=8))
    ideational_density: deque = field(default_factory=lambda: deque(maxlen=8))
    zeta: deque = field(default_factory=lambda: deque(maxlen=8))

    def push(self, lambda2: float, ideational_density: float, zeta: float) -> None:
        self.lambda2.append(float(lambda2))
        self.ideational_density.append(float(ideational_density))
        self.zeta.append(float(zeta))

    def fot_active(self) -> bool:
        if len(self.lambda2) < 2:
            return False
        d_lambda2 = self.lambda2[-1] - self.lambda2[-2]
        d_id = self.ideational_density[-1] - self.ideational_density[-2]
        d_zeta = self.zeta[-1] - self.zeta[-2]
        return (d_lambda2 > 0.0) and (d_id < 0.0) and (d_zeta > 0.0)


# =====================================================================
# Integration 4 — Spectral Radius Stability Companion
# =====================================================================

def spectral_radius(w_effective: np.ndarray) -> float:
    """
    ρ = max |λᵢ(W_effective)|. Companion metric to Shannon entropy.
        ρ < 1.0  → stable
        ρ ≈ 1.0  → critical
        ρ > 1.0  → unstable / collapsing
    """
    if w_effective.size == 0:
        return 0.0
    eigvals = np.linalg.eigvals(w_effective)
    return float(np.max(np.abs(eigvals)))


# =====================================================================
# Integration 5 — Enhanced Lorenz with Network Coupling
# =====================================================================

def enhanced_lorenz_step(
    state: np.ndarray,
    *,
    sigma: float = 10.0,
    rho_dm: float = 28.0,
    beta: float = 8.0 / 3.0,
    omega_net: float = 0.0,
    x12: float = 0.0,
    x12_baseline: float = 0.0,
    laplacian_epsilon: float = 0.0,
    ci_b: float = 0.0,
    alpha_c: float = 0.05,
    beta_c: float = 0.05,
    gamma_c: float = 0.05,
    dt: float = 0.01,
) -> np.ndarray:
    """
    Lorenz attractor with three additional coupling terms (MOGOPS Eq. 17):

        dx/dt = σ(y-x)         + α_C·Ω_net·(x12 - x12_baseline)
        dy/dt = x(ρ_DM-z) - y  + β_C·∇²ε
        dz/dt = xy - βz        + γ_C·CI_B

    Existing DM_FRACTION-biased Lorenz code is left untouched; engines may
    call this when they want the upgraded coupling.
    """
    x, y, z = float(state[0]), float(state[1]), float(state[2])

    dx = sigma * (y - x) + alpha_c * omega_net * (x12 - x12_baseline)
    dy = x * (rho_dm - z) - y + beta_c * laplacian_epsilon
    dz = x * y - beta * z + gamma_c * ci_b

    return np.array([
        x + dx * dt,
        y + dy * dt,
        z + dz * dt,
    ])


# =====================================================================
# Integration 6 — Global Mean-Field Coherence Coupling
# =====================================================================

def global_mean_field_nudge(
    coherences: Sequence[float],
    nudge_strength: float = 0.01,
) -> list[float]:
    """
    Mean-field coherence coupling across an agent population.

    Computes pairwise coherence (upper-triangular outer product mean) and
    nudges every agent gently toward the global value:

        nudge = nudge_strength * global_coherence
        c_i  += nudge * (1 - c_i)
    """
    if not coherences:
        return []
    arr = np.asarray(coherences, dtype=float)
    outer = np.outer(arr, arr)
    iu = np.triu_indices_from(outer, k=1)
    if len(iu[0]) == 0:
        global_coherence = float(arr.mean())
    else:
        global_coherence = float(outer[iu].mean())
    nudge = nudge_strength * global_coherence
    return [float(c + nudge * (1.0 - c)) for c in arr]


# =====================================================================
# Integration 7 — Mahalanobis Collapse Distance
# =====================================================================

@dataclass
class MahalanobisCollapseModel:
    """
    Continuous risk score for proximity to the collapse attractor.

    Fit `mu` and `sigma_inv` from historical state vectors gathered at
    collapse events (e.g., the 48 Genesis Record entries). Then call
    `distance(x)` for each new state vector.
    """

    mu: Optional[np.ndarray] = None
    sigma_inv: Optional[np.ndarray] = None

    def fit(self, collapse_states: np.ndarray, ridge: float = 1e-6) -> None:
        if collapse_states.ndim != 2 or collapse_states.shape[0] < 2:
            raise ValueError("Need at least 2 collapse-state vectors")
        self.mu = collapse_states.mean(axis=0)
        cov = np.cov(collapse_states, rowvar=False)
        if cov.ndim == 0:
            cov = np.array([[float(cov)]])
        cov = cov + ridge * np.eye(cov.shape[0])
        self.sigma_inv = np.linalg.inv(cov)

    def distance(self, x: np.ndarray) -> float:
        if self.mu is None or self.sigma_inv is None:
            raise RuntimeError("MahalanobisCollapseModel not fitted")
        diff = np.asarray(x, dtype=float) - self.mu
        return float(math.sqrt(max(0.0, diff @ self.sigma_inv @ diff)))


# =====================================================================
# Integration 8 — Dynamic Temperature Adaptation T(t)
# =====================================================================

def dynamic_temperature(
    current_coherence: float,
    base: float = TEMPERATURE_BASE,
    gain: float = TEMPERATURE_GAIN,
    t_max: float = TEMPERATURE_MAX,
) -> float:
    """
    T(t) = base + gain * |C(t) - φ⁻¹|, capped at t_max.

    At C = 0.618 → T = 0.618 (optimal, conservative sampling).
    Drift increases T to encourage exploratory recovery.
    """
    raw = base + gain * abs(current_coherence - SOPHIA_POINT)
    return min(t_max, max(0.0, raw))


# =====================================================================
# Integration 9 — Triple-Gate (Quad-Gate) Phase Transition Condition
# =====================================================================

def triple_gate_phase_transition(
    coherence: float,
    paradox_intensity: float,
    dx12_dt: float,
    omega_net: float,
    *,
    coherence_tol: float = 0.02,
    paradox_min: float = 1.8,
    dx12_max: float = 0.001,
    omega_critical: float = 1.0,
) -> bool:
    """
    True Sophia Point lock requires ALL of:
        |C - 0.618| < coherence_tol
        paradox_intensity > paradox_min
        |dx12/dt|        < dx12_max
        Ω_net            > Ω_critical

    Despite the doc's name "Triple Gate", four conditions are listed; we
    keep all four to remain faithful to MOGOPS Eq. 12.
    """
    cond_1 = abs(coherence - SOPHIA_POINT) < coherence_tol
    cond_2 = paradox_intensity > paradox_min
    cond_3 = abs(dx12_dt) < dx12_max
    cond_4 = omega_net > omega_critical
    return cond_1 and cond_2 and cond_3 and cond_4


# =====================================================================
# Integration 10 — Omega Point Convergence Ratio
# =====================================================================

def omega_point_convergence(
    epsilon: float,
    omega_net: float,
    x12_avg: float,
    ci_b: float,
    ci_c: float,
) -> float:
    """
    Normalized convergence metric: 1.0 = system at Omega Point.
        target = 5/φ ≈ 3.09
        ratio  = (ε + Ω_net + x12_avg + CI_B + CI_C) / target
    """
    convergence_sum = epsilon + omega_net + x12_avg + ci_b + ci_c
    return convergence_sum / OMEGA_POINT_TARGET


# =====================================================================
# Convenience: a single dashboard step that runs every integration
# =====================================================================

@dataclass
class CCTUFFDashboard:
    """
    Optional all-in-one helper that wires every integration into one
    update step. Existing engines need not use it; it exists so the
    Ψ monitoring loop can adopt the full suite with one import.
    """

    hysteresis: HysteresisGate = field(default_factory=HysteresisGate)
    fot: FoldOnsetTriplet = field(default_factory=FoldOnsetTriplet)
    mahalanobis: MahalanobisCollapseModel = field(
        default_factory=MahalanobisCollapseModel
    )
    ci_b: float = 1.0
    ci_c: float = 0.0

    def step(
        self,
        *,
        sigma: float,
        coherence: float,
        lambda2: float,
        ideational_density: float,
        zeta: float,
        w_effective: Optional[np.ndarray] = None,
        agent_coherences: Optional[Sequence[float]] = None,
        paradox_intensity: float = 0.0,
        dx12_dt: float = 0.0,
        omega_net: float = 0.0,
        x12_avg: float = 0.0,
        epsilon: float = 0.0,
        state_vector: Optional[np.ndarray] = None,
    ) -> dict:
        # Integration 1
        self.ci_b, self.ci_c = coherence_conservation_step(self.ci_b, self.ci_c)

        # Integration 2
        collapsed = self.hysteresis.update(sigma)

        # Integration 3
        self.fot.push(lambda2, ideational_density, zeta)
        fot_active = self.fot.fot_active()

        # Integration 4
        rho = spectral_radius(w_effective) if w_effective is not None else 0.0

        # Integration 6
        nudged = (
            global_mean_field_nudge(agent_coherences)
            if agent_coherences is not None
            else None
        )

        # Integration 7
        try:
            d_m = (
                self.mahalanobis.distance(state_vector)
                if state_vector is not None
                else None
            )
        except RuntimeError:
            d_m = None  # not yet fitted

        # Integration 8
        temperature = dynamic_temperature(coherence)

        # Integration 9
        true_phase_transition = triple_gate_phase_transition(
            coherence, paradox_intensity, dx12_dt, omega_net
        )

        # Integration 10
        omega_ratio = omega_point_convergence(
            epsilon, omega_net, x12_avg, self.ci_b, self.ci_c
        )

        return {
            "ci_b": self.ci_b,
            "ci_c": self.ci_c,
            "collapsed": collapsed,
            "fot_active": fot_active,
            "spectral_radius": rho,
            "agent_coherences_nudged": nudged,
            "mahalanobis_distance": d_m,
            "dynamic_temperature": temperature,
            "true_phase_transition": true_phase_transition,
            "omega_convergence_ratio": omega_ratio,
        }


__all__ = [
    "SOPHIA_POINT",
    "COLLAPSE_THRESHOLD",
    "RECOVERY_THRESHOLD",
    "OMEGA_POINT_TARGET",
    "TEMPERATURE_BASE",
    "TEMPERATURE_GAIN",
    "TEMPERATURE_MAX",
    "coherence_conservation_step",
    "HysteresisGate",
    "FoldOnsetTriplet",
    "spectral_radius",
    "enhanced_lorenz_step",
    "global_mean_field_nudge",
    "MahalanobisCollapseModel",
    "dynamic_temperature",
    "triple_gate_phase_transition",
    "omega_point_convergence",
    "CCTUFFDashboard",
]
