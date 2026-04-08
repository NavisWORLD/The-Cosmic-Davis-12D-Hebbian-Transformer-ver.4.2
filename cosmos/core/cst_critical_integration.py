"""
Critical CST integration loops and analysis helpers.

This module converts the April 4, 2026 critical integration analysis into
additive runtime primitives that can be threaded through the existing 12D
CosmoSynapse stack without replacing the current architecture.

The galactic-cosmic-ray alignment helper is a harmonic comparison harness. It
produces a reproducible mathematical score over normalized source values, but
it should be treated as an engineering alignment heuristic rather than a claim
of physical validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
import re
from typing import Iterable, Sequence

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
SOPHIA_POINT = PHI_INV
DEFAULT_COLLAPSE_THRESHOLD = 0.048
DEFAULT_RECOVERY_THRESHOLD = 0.037
OMEGA_POINT_TARGET = 5.0 / PHI


@dataclass(frozen=True)
class FoldOnsetTripletResult:
    """Container for the fold-onset triplet leading indicators."""

    active: bool
    delta_lambda2: float
    delta_ideational_density: float
    delta_zeta: float


@dataclass(frozen=True)
class GalacticAlignmentResult:
    """Result of the harmonic galactic-cosmic-ray alignment calculation."""

    overall_alignment: float
    cosine_similarity: float
    phase_distance: float
    probe_vector: tuple[float, ...]
    normalized_scalars: tuple[float, ...]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return float(max(low, min(high, value)))


def _safe_array(values: Sequence[float], size: int | None = None) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if size is not None:
        if arr.size < size:
            arr = np.pad(arr, (0, size - arr.size))
        elif arr.size > size:
            arr = arr[:size]
    return arr


def _normalize_vector(vector: Sequence[float]) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(arr))
    if norm <= 1e-12:
        return np.zeros_like(arr)
    return arr / norm


def coherence_conservation_step(
    ci_b: float,
    ci_c: float,
    dt: float = 0.001,
) -> tuple[float, float]:
    """
    Transfer a small amount of coherence from boundary to continuum storage.

    The update preserves CI_B + CI_C.
    """
    dt = max(0.0, float(dt))
    delta = dt * float(ci_b)
    ci_b_new = float(ci_b) - delta
    ci_c_new = float(ci_c) + delta
    return (ci_b_new, ci_c_new)


def phase_transition_hysteresis(
    sigma: float,
    currently_collapsed: bool,
    collapse_threshold: float = DEFAULT_COLLAPSE_THRESHOLD,
    recovery_threshold: float = DEFAULT_RECOVERY_THRESHOLD,
) -> bool:
    """Apply a hysteresis gap for collapse entry/recovery."""
    sigma = float(sigma)
    if not currently_collapsed and sigma > collapse_threshold:
        return True
    if currently_collapsed and sigma < recovery_threshold:
        return False
    return bool(currently_collapsed)


def fold_onset_triplet(
    lambda2_history: Sequence[float],
    ideational_density_history: Sequence[float],
    zeta_history: Sequence[float],
) -> FoldOnsetTripletResult:
    """
    Detect the fold-onset triplet:
    rising lambda_2, falling ideational density, rising zeta.
    """
    if (
        len(lambda2_history) < 2
        or len(ideational_density_history) < 2
        or len(zeta_history) < 2
    ):
        return FoldOnsetTripletResult(False, 0.0, 0.0, 0.0)

    delta_lambda2 = float(lambda2_history[-1] - lambda2_history[-2])
    delta_ideational_density = float(
        ideational_density_history[-1] - ideational_density_history[-2]
    )
    delta_zeta = float(zeta_history[-1] - zeta_history[-2])
    active = (
        delta_lambda2 > 0.0
        and delta_ideational_density < 0.0
        and delta_zeta > 0.0
    )
    return FoldOnsetTripletResult(
        active=active,
        delta_lambda2=delta_lambda2,
        delta_ideational_density=delta_ideational_density,
        delta_zeta=delta_zeta,
    )


def counts_to_connectivity_matrix(counts: dict[str, int]) -> np.ndarray:
    """
    Convert quantum bitstring counts into a weighted covariance matrix.

    The covariance form keeps values in a numerically stable range so the
    spectral radius behaves like a useful companion stability metric.
    """
    if not counts:
        return np.zeros((0, 0), dtype=float)

    keys = [str(bitstring) for bitstring in counts.keys()]
    width = len(keys[0])
    states = np.array([[int(bit) for bit in bitstring] for bitstring in keys], dtype=float)
    weights = np.array([counts[key] for key in keys], dtype=float)
    total = float(weights.sum())
    if total <= 0.0:
        return np.zeros((width, width), dtype=float)

    weights /= total
    mean = (weights[:, None] * states).sum(axis=0)
    centered = states - mean
    covariance = (centered * weights[:, None]).T @ centered
    return covariance


def spectral_radius(matrix: Sequence[Sequence[float]]) -> float:
    """Return the maximum absolute eigenvalue of the matrix."""
    arr = np.asarray(matrix, dtype=float)
    if arr.size == 0:
        return 0.0
    eigenvalues = np.linalg.eigvals(arr)
    return float(np.max(np.abs(eigenvalues)))


def spectral_profile_from_counts(counts: dict[str, int]) -> dict[str, float]:
    """Compute spectral-radius metrics from quantum measurement counts."""
    matrix = counts_to_connectivity_matrix(counts)
    if matrix.size == 0:
        return {
            "spectral_radius": 0.0,
            "second_eigenvalue": 0.0,
            "matrix_dim": 0,
        }

    eigenvalues = np.linalg.eigvals(matrix)
    magnitudes = sorted((float(abs(value)) for value in eigenvalues), reverse=True)
    second = magnitudes[1] if len(magnitudes) > 1 else 0.0
    return {
        "spectral_radius": float(magnitudes[0]),
        "second_eigenvalue": float(second),
        "matrix_dim": int(matrix.shape[0]),
    }


def mean_field_global_coherence(agent_coherences: Sequence[float]) -> float:
    """
    Compute a mean-field coherence score from pairwise agent coherence values.
    """
    coherences = np.asarray(agent_coherences, dtype=float)
    if coherences.size == 0:
        return 0.0
    coherences = np.clip(coherences, 0.0, 1.0)
    if coherences.size == 1:
        return float(coherences[0])

    outer = np.outer(coherences, coherences)
    upper = outer[np.triu_indices(coherences.size, k=1)]
    return float(np.mean(upper)) if upper.size else 0.0


def apply_mean_field_ci_nudge(
    coherence_pairs: dict[str, tuple[float, float]],
    agent_coherences: dict[str, float],
    nudge_factor: float = 0.01,
) -> tuple[float, dict[str, tuple[float, float]]]:
    """
    Nudge all CI pairs toward the current global coherence field.
    """
    global_coherence = mean_field_global_coherence(list(agent_coherences.values()))
    nudge = float(nudge_factor) * global_coherence
    updated: dict[str, tuple[float, float]] = {}
    for name, coherence in agent_coherences.items():
        ci_b, ci_c = coherence_pairs.get(
            name,
            (float(coherence) * PHI_INV, float(coherence) * (1.0 - PHI_INV)),
        )
        ci_b_new = _clamp(ci_b + nudge * (1.0 - ci_b))
        ci_c_new = _clamp(ci_c + nudge * (1.0 - ci_c))
        updated[name] = (ci_b_new, ci_c_new)
    return (global_coherence, updated)


def dynamic_temperature(
    current_coherence: float,
    phi_inv: float = SOPHIA_POINT,
    alpha: float = 0.2,
    minimum: float | None = None,
    maximum: float = 0.8,
) -> float:
    """Map coherence drift from Sophia Point to a bounded sampling temperature."""
    baseline = float(phi_inv if minimum is None else minimum)
    temperature = phi_inv + alpha * abs(float(current_coherence) - phi_inv)
    return float(min(maximum, max(baseline, temperature)))


def triple_gate_phase_transition(
    current_coherence: float,
    paradox_intensity: float,
    dx12_dt: float,
    omega_net: float,
    coherence_target: float = SOPHIA_POINT,
    coherence_band: float = 0.02,
    paradox_threshold: float = 1.8,
    equilibrium_threshold: float = 0.001,
    omega_critical: float = 0.618,
) -> dict[str, float | bool]:
    """Evaluate the multi-gate Sophia phase-transition condition."""
    coherence_distance = abs(float(current_coherence) - float(coherence_target))
    condition_1 = coherence_distance < coherence_band
    condition_2 = float(paradox_intensity) > paradox_threshold
    condition_3 = abs(float(dx12_dt)) < equilibrium_threshold
    condition_4 = float(omega_net) > omega_critical
    return {
        "active": bool(condition_1 and condition_2 and condition_3 and condition_4),
        "coherence_distance": float(coherence_distance),
        "paradox_intensity": float(paradox_intensity),
        "dx12_dt": float(dx12_dt),
        "omega_net": float(omega_net),
    }


def omega_point_convergence(
    epsilon: float,
    omega_net: float,
    x12_avg: float,
    ci_b: float,
    ci_c: float,
) -> dict[str, float]:
    """Compute the normalized Omega Point convergence ratio."""
    convergence_sum = (
        float(epsilon)
        + float(omega_net)
        + abs(float(x12_avg))
        + float(ci_b)
        + float(ci_c)
    )
    ratio = convergence_sum / OMEGA_POINT_TARGET
    return {
        "omega_point_target": float(OMEGA_POINT_TARGET),
        "omega_convergence_sum": float(convergence_sum),
        "omega_convergence_ratio": float(ratio),
    }


def build_12d_state_vector(
    user_physics: dict | None,
    metrics: dict | None = None,
    dark_matter_w: float | None = None,
) -> np.ndarray:
    """
    Build a compact 12D runtime state vector for collapse-risk calculations.
    """
    physics = user_physics or {}
    cst = physics.get("cst_physics", {}) or {}
    bio = physics.get("bio_signatures", {}) or {}
    cst_metrics = physics.get("cst_metrics", {}) or {}
    metrics = metrics or {}

    vector = np.array(
        [
            float(cst.get("geometric_phase_rad", physics.get("geometric_phase_rad", 0.0))),
            float(cst.get("phase_velocity", physics.get("phase_velocity", 0.0))),
            float(cst.get("entanglement_score", physics.get("resonance_scalar", 0.0))),
            float(physics.get("entropy_field", bio.get("intensity", 0.5))),
            float(bio.get("arousal", 0.0)),
            float(bio.get("valence", 0.0)),
            float(
                dark_matter_w
                if dark_matter_w is not None
                else physics.get("dark_matter_w", cst_metrics.get("dark_matter_w", 0.0))
            ),
            float(metrics.get("ci_b", cst_metrics.get("ci_b", 0.0))),
            float(metrics.get("ci_c", cst_metrics.get("ci_c", 0.0))),
            float(metrics.get("entropy_quality", cst_metrics.get("entropy_quality", 0.0))),
            float(metrics.get("decoherence_risk", cst_metrics.get("decoherence_risk", 0.0))),
            float(cst_metrics.get("x12_avg", 0.0)),
        ],
        dtype=float,
    )
    return vector


def _quantum_entry_to_vector(entry: dict) -> np.ndarray:
    signature = entry.get("quantum_signature", {}) or {}
    physics_signature = signature.get("physics_signature", {}) or {}
    metrics = (
        signature.get("metrics")
        or entry.get("metrics")
        or {}
    )
    cst_metrics = entry.get("physics", {}).get("cst_metrics", {}) or {}
    return np.array(
        [
            float(physics_signature.get("phase", 0.0)),
            float(entry.get("physics", {}).get("cst_physics", {}).get("phase_velocity", 0.0)),
            float(physics_signature.get("resonance", 0.0)),
            float(physics_signature.get("entropy", 0.5)),
            float(entry.get("physics", {}).get("bio_signatures", {}).get("arousal", 0.0)),
            float(entry.get("physics", {}).get("bio_signatures", {}).get("valence", 0.0)),
            float(entry.get("physics", {}).get("dark_matter_w", cst_metrics.get("dark_matter_w", 0.0))),
            float(metrics.get("ci_b", cst_metrics.get("ci_b", 0.0))),
            float(metrics.get("ci_c", cst_metrics.get("ci_c", 0.0))),
            float(metrics.get("entropy_quality", 0.0)),
            float(metrics.get("decoherence_risk", 1.0)),
            float(cst_metrics.get("x12_avg", 0.0)),
        ],
        dtype=float,
    )


@lru_cache(maxsize=4)
def load_collapse_reference_vectors(
    archive_path: str | None = None,
    genesis_path: str | None = None,
    max_samples: int = 48,
) -> np.ndarray:
    """
    Load collapse-like reference vectors from archived quantum runs.

    The Genesis Record is only used opportunistically for numeric entropy hints.
    Archived quantum runs are the primary structured source.
    """
    if archive_path is None:
        archive_path = str(Path(__file__).resolve().parents[2] / "data" / "archival" / "quantum_runs.jsonl")
    if genesis_path is None:
        genesis_path = str(Path(__file__).resolve().parents[2] / "genesis_record.md")

    samples: list[tuple[float, np.ndarray]] = []
    archive = Path(archive_path)
    if archive.exists():
        try:
            for line in archive.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                signature = entry.get("quantum_signature", {}) or {}
                metrics = signature.get("metrics", {}) or entry.get("metrics", {}) or {}
                entropy_quality = float(metrics.get("entropy_quality", 1.0))
                decoherence_risk = float(metrics.get("decoherence_risk", 0.0))
                collapse_score = (1.0 - entropy_quality) + decoherence_risk
                samples.append((collapse_score, _quantum_entry_to_vector(entry)))
        except OSError:
            pass

    genesis = Path(genesis_path)
    if genesis.exists():
        try:
            text = genesis.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r"entropy(?: of)? ([0-9]*\.?[0-9]+)", text, flags=re.IGNORECASE):
                entropy_value = float(match.group(1))
                vector = np.zeros(12, dtype=float)
                vector[3] = entropy_value
                vector[9] = entropy_value
                samples.append((1.0 - _clamp(entropy_value), vector))
        except OSError:
            pass

    if not samples:
        fallback = np.array(
            [[SOPHIA_POINT, 0.15, 0.2, 0.62, 0.6, 0.1, 0.9, 0.31, 0.31, 0.45, 0.55, 0.2]],
            dtype=float,
        )
        return fallback

    samples.sort(key=lambda item: item[0], reverse=True)
    selected = [vector for _, vector in samples[:max_samples]]
    return np.vstack(selected)


def mahalanobis_collapse_distance(
    current_vector: Sequence[float],
    reference_vectors: Sequence[Sequence[float]] | None = None,
    ridge: float = 1e-6,
) -> float:
    """
    Compute the Mahalanobis distance from the current state to the learned
    collapse attractor cloud.
    """
    x = _safe_array(current_vector, size=12)
    refs = (
        load_collapse_reference_vectors()
        if reference_vectors is None
        else np.asarray(reference_vectors, dtype=float)
    )
    refs = np.atleast_2d(refs)
    if refs.shape[0] == 0:
        return float(np.linalg.norm(x))

    mu = refs.mean(axis=0)
    centered = refs - mu
    covariance = np.cov(centered, rowvar=False)
    covariance = np.atleast_2d(covariance)
    covariance += np.eye(covariance.shape[0], dtype=float) * ridge
    inverse = np.linalg.pinv(covariance)
    delta = x - mu
    distance = float(math.sqrt(max(0.0, delta.T @ inverse @ delta)))
    return distance


def _normalize_gcr_scalar(record: dict) -> float:
    if "ratio" in record:
        return _clamp(float(record["ratio"]))

    if "numerator" in record and "denominator" in record:
        denominator = float(record["denominator"]) or 1.0
        return _clamp(float(record["numerator"]) / denominator)

    if "current" in record and "forecast" in record:
        forecast = float(record["forecast"]) or 1.0
        return _clamp(float(record["current"]) / forecast)

    value = float(record.get("value", 0.0))
    normalizer = float(record.get("normalizer", 1.0)) or 1.0
    transform = str(record.get("transform", "linear")).lower()
    if transform == "log":
        value = math.log1p(max(0.0, value))
        normalizer = math.log1p(max(0.0, normalizer))
    return _clamp(value / normalizer if normalizer else 0.0)


def harmonic_embed_scalar_to_12d(scalar: float) -> np.ndarray:
    """
    Project a normalized scalar into a 12D harmonic probe vector.
    """
    scalar = _clamp(float(scalar))
    dims = np.arange(1, 13, dtype=float)
    phase = math.pi * scalar * PHI_INV
    embedding = (
        np.sin(dims * phase)
        + np.cos(dims * (math.pi - phase)) * (PHI_INV ** (dims / 4.0))
    )
    return _normalize_vector(embedding)


def galactic_cosmic_ray_alignment(
    state_vector: Sequence[float],
    findings: Iterable[dict],
) -> GalacticAlignmentResult:
    """
    Compare a 12D state vector against normalized galactic-cosmic-ray findings.
    """
    records = list(findings)
    if not records:
        return GalacticAlignmentResult(
            overall_alignment=0.0,
            cosine_similarity=0.0,
            phase_distance=1.0,
            probe_vector=tuple([0.0] * 12),
            normalized_scalars=tuple(),
        )

    weights = np.array([float(record.get("weight", 1.0)) for record in records], dtype=float)
    if float(weights.sum()) <= 0.0:
        weights = np.ones(len(records), dtype=float)
    weights /= weights.sum()

    scalars = np.array([_normalize_gcr_scalar(record) for record in records], dtype=float)
    probes = np.array([harmonic_embed_scalar_to_12d(value) for value in scalars], dtype=float)
    probe_vector = np.average(probes, axis=0, weights=weights)
    probe_vector = _normalize_vector(probe_vector)

    model_vector = _normalize_vector(_safe_array(state_vector, size=12))
    cosine = float(np.clip(np.dot(model_vector, probe_vector), -1.0, 1.0))
    phase_distance = float(abs(np.mean(model_vector[:4]) - np.mean(scalars)))
    overall = _clamp(((cosine + 1.0) / 2.0) * 0.75 + (1.0 - min(1.0, phase_distance)) * 0.25)

    return GalacticAlignmentResult(
        overall_alignment=float(overall),
        cosine_similarity=float((cosine + 1.0) / 2.0),
        phase_distance=float(min(1.0, phase_distance)),
        probe_vector=tuple(float(value) for value in probe_vector.tolist()),
        normalized_scalars=tuple(float(value) for value in scalars.tolist()),
    )
