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
from datetime import datetime
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
LEARNED_CALIBRATOR_ALPHA = 0.2
LEARNED_CALIBRATOR_SMALL_SAMPLE_THRESHOLD = 8
LEARNED_CALIBRATOR_SMALL_SAMPLE_SHRINK = PHI_INV**5
MARS_FD_TRANSPORT_ALPHA = 0.8
MARS_ICME_DRAG_GAMMA_PER_KM = 1.0e-8
LEARNED_CALIBRATOR_KEYWORDS = (
    "ratio",
    "dose",
    "equivalent",
    "flux",
    "fluence",
    "quality",
    "charged",
    "neutral",
    "albedo",
    "primary",
    "surface",
    "cruise",
    "storm",
    "shelter",
    "shield",
    "peak",
    "rotation",
    "cavity",
    "duration",
    "reduction",
    "gcr",
    "proton",
    "organ",
    "tissue",
    "absorbed",
    "total",
    "mission",
    "flyby",
    "low",
    "high",
    "count",
    "rate",
    "current",
    "forecast",
)
DEFAULT_LEARNED_CALIBRATION_FILENAMES = (
    "change4_lnd_reference.json",
    "artemis_i_unseen_reference.json",
    "artemis_i_m42_gcr_reference.json",
)
DEFAULT_MARS_FD_TRANSPORT_CALIBRATION_FILENAMES = (
    "mars_fd_surface_orbit_reference.json",
)
UTC_EVENT_TIME_FORMAT = "%Y-%m-%d %H:%M UTC"
DEFAULT_VALIDATION_USER_PHYSICS = {
    "cst_physics": {
        "geometric_phase_rad": 0.71,
        "phase_velocity": 0.028,
        "entanglement_score": 0.64,
    },
    "bio_signatures": {
        "intensity": 0.77,
        "arousal": 0.31,
        "valence": 0.09,
    },
    "cst_metrics": {
        "x12_avg": 0.58,
        "ci_b": 0.41,
        "ci_c": 0.29,
    },
}
DEFAULT_VALIDATION_METRICS = {
    "entropy_quality": 0.78,
    "decoherence_risk": 0.22,
}
DEFAULT_VALIDATION_DARK_MATTER_W = 0.36


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


def default_validation_state_vector() -> np.ndarray:
    """Return the canonical 12D validation probe used by the radiation harness."""
    return build_12d_state_vector(
        DEFAULT_VALIDATION_USER_PHYSICS,
        metrics=DEFAULT_VALIDATION_METRICS,
        dark_matter_w=DEFAULT_VALIDATION_DARK_MATTER_W,
    )


def _record_descriptor_text(record: dict) -> str:
    return " ".join(
        [
            str(record.get("id", "")),
            str(record.get("units", "")),
            str(record.get("notes", "")),
        ]
    ).lower()


def _observable_scale_hint(record: dict) -> float:
    for key in ("denominator", "normalizer", "forecast"):
        if key in record:
            return float(math.log1p(abs(float(record.get(key, 0.0)))))
    return 0.0


def observable_calibrator_feature_names() -> tuple[str, ...]:
    names = [
        "bias",
        "legacy_scalar",
        "legacy_centered",
        "legacy_squared",
        "has_ratio",
        "has_fraction_scale",
        "has_value",
        "has_current_forecast",
        "has_log_transform",
        "scale_hint_log",
    ]
    names.extend(f"kw_{keyword}" for keyword in LEARNED_CALIBRATOR_KEYWORDS)
    return tuple(names)


def predict_legacy_observable_scalar(
    state_vector: Sequence[float],
    record: dict,
) -> float:
    """
    Legacy record-conditioned scalar from the 12D state.

    This rule-based baseline is preserved for diagnostics, but runtime
    predictions should go through the learned calibrator below.
    """
    vector = _safe_array(state_vector, size=12)
    phase = _clamp(float(vector[0]))
    phase_velocity = max(0.0, float(vector[1]))
    entanglement = _clamp(float(vector[2]))
    intensity = _clamp(float(vector[3]))
    valence = float(vector[5])
    ci_b = _clamp(float(vector[7]))
    ci_c = _clamp(float(vector[8]))
    entropy_quality = _clamp(float(vector[9]))
    decoherence_risk = _clamp(float(vector[10]))
    x12_avg = _clamp(float(vector[11]))

    record_id = str(record.get("id", "")).lower()
    units = str(record.get("units", "")).lower()

    if "storm_shelter" in record_id or "storm_shelter" in units:
        return _clamp(decoherence_risk + phase_velocity)

    if "hsu1_to_hsu2" in record_id or "hsu1_to_hsu2" in units:
        return _clamp((phase + ci_b + ci_c) / 3.0)

    if "rotation" in record_id or "rotation" in units:
        return _clamp(x12_avg - abs(valence))

    if "gcr_absorbed_dose_relative_to_max" in units:
        return _clamp((phase + intensity + entropy_quality + ci_b + ci_c) / 3.0)

    if "duration" in record_id or "days per lunar revolution" in units:
        return _clamp(phase_velocity * (PHI + 1.0))

    if "charged" in record_id:
        return _clamp(intensity + phase_velocity * 0.1)

    if "neutral" in record_id:
        return _clamp(decoherence_risk - abs(valence) * 0.1)

    if "albedo" in record_id:
        return _clamp(entanglement)

    if "low_to_high" in units:
        return _clamp((phase + intensity + entropy_quality + ci_b) / 3.5)

    if "dose" in record_id:
        return _clamp(
            intensity * 0.45
            + entanglement * 0.25
            + x12_avg * 0.20
            + entropy_quality * 0.10
        )

    if "reduction" in record_id or "count-rate ratio" in units:
        return _clamp(phase * 0.50 + entanglement * 0.25 + intensity * 0.25)

    return _clamp(np.mean([phase, entanglement, intensity, x12_avg]))


def _observable_calibrator_features(
    state_vector: Sequence[float],
    record: dict,
    legacy_scalar: float | None = None,
) -> np.ndarray:
    legacy = (
        float(legacy_scalar)
        if legacy_scalar is not None
        else predict_legacy_observable_scalar(state_vector, record)
    )
    text = _record_descriptor_text(record)
    features = [
        1.0,
        legacy,
        legacy - 0.5,
        legacy * legacy,
        float("ratio" in record),
        float("numerator" in record and "denominator" in record),
        float("value" in record),
        float("current" in record and "forecast" in record),
        float(str(record.get("transform", "linear")).lower() == "log"),
        _observable_scale_hint(record),
    ]
    features.extend(float(keyword in text) for keyword in LEARNED_CALIBRATOR_KEYWORDS)
    return np.asarray(features, dtype=float)


def fit_observable_calibrator(
    training_records: Sequence[dict],
    state_vector: Sequence[float],
    alpha: float = LEARNED_CALIBRATOR_ALPHA,
) -> dict[str, object]:
    """
    Fit a deterministic residual-ridge calibrator over observable metadata.

    The model learns a correction on top of the legacy scalar so the runtime
    path is learned, reproducible, and still anchored to the existing 12D
    mapping rather than replacing it wholesale.
    """
    records = list(training_records)
    feature_names = observable_calibrator_feature_names()
    if not records:
        return {
            "type": "residual_ridge",
            "alpha": float(alpha),
            "feature_names": feature_names,
            "coefficients": tuple([0.0] * len(feature_names)),
            "training_record_count": 0,
            "training_mae": 0.0,
            "training_rmse": 0.0,
            "legacy_training_mae": 0.0,
            "legacy_training_rmse": 0.0,
        }

    legacy_predictions = np.array(
        [predict_legacy_observable_scalar(state_vector, record) for record in records],
        dtype=float,
    )
    X = np.vstack(
        [
            _observable_calibrator_features(
                state_vector,
                record,
                legacy_scalar=float(legacy_predictions[index]),
            )
            for index, record in enumerate(records)
        ]
    )
    y = np.array([_normalize_gcr_scalar(record) for record in records], dtype=float)
    residual = y - legacy_predictions
    ridge = np.eye(X.shape[1], dtype=float)
    ridge[0, 0] = 0.0
    coefficients = np.linalg.pinv(X.T @ X + float(alpha) * ridge) @ X.T @ residual
    learned_predictions = np.clip(legacy_predictions + X @ coefficients, 0.0, 1.0)
    learned_delta = learned_predictions - y
    legacy_delta = legacy_predictions - y
    return {
        "type": "residual_ridge",
        "alpha": float(alpha),
        "feature_names": feature_names,
        "coefficients": tuple(float(value) for value in coefficients.tolist()),
        "training_record_count": len(records),
        "training_mae": float(np.mean(np.abs(learned_delta))),
        "training_rmse": float(np.sqrt(np.mean(learned_delta**2))),
        "legacy_training_mae": float(np.mean(np.abs(legacy_delta))),
        "legacy_training_rmse": float(np.sqrt(np.mean(legacy_delta**2))),
    }


def _default_learned_calibration_paths() -> tuple[str, ...]:
    root = Path(__file__).resolve().parents[2] / "tests" / "galactic_cosmic_rays"
    return tuple(str(root / filename) for filename in DEFAULT_LEARNED_CALIBRATION_FILENAMES)


def _coerce_calibration_paths(calibration_paths: Sequence[str] | None) -> tuple[str, ...]:
    if calibration_paths is None:
        return _default_learned_calibration_paths()
    return tuple(str(Path(path)) for path in calibration_paths)


def _load_training_records(calibration_paths: Sequence[str]) -> list[dict]:
    records: list[dict] = []
    for path_str in calibration_paths:
        path = Path(path_str)
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, list):
            records.extend(record for record in payload if isinstance(record, dict))
    return records


@lru_cache(maxsize=8)
def load_learned_observable_calibrator(
    calibration_paths: tuple[str, ...] | None = None,
    alpha: float = LEARNED_CALIBRATOR_ALPHA,
) -> dict[str, object]:
    """
    Load the default learned calibrator trained on the locked lunar bundle.
    """
    paths = _coerce_calibration_paths(calibration_paths)
    calibrator = fit_observable_calibrator(
        _load_training_records(paths),
        default_validation_state_vector(),
        alpha=alpha,
    )
    calibrator["calibration_paths"] = tuple(paths)
    return calibrator


def mars_fd_transport_feature_names() -> tuple[str, ...]:
    return (
        "bias",
        "base_prediction",
        "base_centered",
        "base_squared",
        "log_denom",
        "log_denom_squared",
        "duration_days",
        "inverse_duration_hours",
        "season_sin",
        "season_cos",
        "log_duration_interaction",
        "sqrt_denom",
    )


def _mars_fd_transport_features(
    state_vector: Sequence[float],
    record: dict,
    base_prediction: float | None = None,
    calibrator: dict[str, object] | None = None,
) -> np.ndarray:
    base = (
        float(base_prediction)
        if base_prediction is not None
        else predict_change4_observable_scalar(
            state_vector,
            record,
            calibrator=calibrator,
        )
    )
    denominator = max(0.0, float(record.get("denominator", 0.0)))
    log_denom = math.log1p(denominator)
    duration_hours = _extract_mars_fd_duration_hours(record)
    duration_days = duration_hours / 24.0
    onset, _ = _extract_mars_fd_event_times(record)
    season_sin, season_cos = _extract_day_of_year_phase(onset)
    features = [
        1.0,
        base,
        base - 0.5,
        base * base,
        log_denom,
        log_denom * log_denom,
        duration_days,
        1.0 / max(duration_hours, 1.0),
        season_sin,
        season_cos,
        log_denom * duration_days,
        math.sqrt(denominator),
    ]
    return np.asarray(features, dtype=float)


def _default_mars_fd_transport_paths() -> tuple[str, ...]:
    root = Path(__file__).resolve().parents[2] / "tests" / "galactic_cosmic_rays"
    return tuple(str(root / filename) for filename in DEFAULT_MARS_FD_TRANSPORT_CALIBRATION_FILENAMES)


def fit_mars_fd_transport_expert(
    training_records: Sequence[dict],
    state_vector: Sequence[float],
    calibrator: dict[str, object] | None = None,
    alpha: float = MARS_FD_TRANSPORT_ALPHA,
) -> dict[str, object]:
    records = [record for record in training_records if _is_mars_fd_ratio_record(record)]
    feature_names = mars_fd_transport_feature_names()
    if not records:
        return {
            "type": "mars_fd_transport_ridge",
            "alpha": float(alpha),
            "feature_names": feature_names,
            "coefficients": tuple([0.0] * len(feature_names)),
            "training_record_count": 0,
            "training_mae": 0.0,
            "training_rmse": 0.0,
            "base_training_mae": 0.0,
            "base_training_rmse": 0.0,
        }

    active_calibrator = (
        calibrator if calibrator is not None else load_learned_observable_calibrator()
    )
    base_predictions = np.array(
        [
            predict_change4_observable_scalar(
                state_vector,
                record,
                calibrator=active_calibrator,
            )
            for record in records
        ],
        dtype=float,
    )
    X = np.vstack(
        [
            _mars_fd_transport_features(
                state_vector,
                record,
                base_prediction=float(base_predictions[index]),
                calibrator=active_calibrator,
            )
            for index, record in enumerate(records)
        ]
    )
    y = np.array([_normalize_gcr_scalar(record) for record in records], dtype=float)
    ridge = np.eye(X.shape[1], dtype=float)
    ridge[0, 0] = 0.0
    coefficients = np.linalg.pinv(X.T @ X + float(alpha) * ridge) @ X.T @ y
    learned_predictions = np.clip(X @ coefficients, 0.0, 1.0)
    learned_delta = learned_predictions - y
    base_delta = base_predictions - y
    return {
        "type": "mars_fd_transport_ridge",
        "alpha": float(alpha),
        "feature_names": feature_names,
        "coefficients": tuple(float(value) for value in coefficients.tolist()),
        "training_record_count": len(records),
        "training_mae": float(np.mean(np.abs(learned_delta))),
        "training_rmse": float(np.sqrt(np.mean(learned_delta**2))),
        "base_training_mae": float(np.mean(np.abs(base_delta))),
        "base_training_rmse": float(np.sqrt(np.mean(base_delta**2))),
    }


@lru_cache(maxsize=8)
def load_mars_fd_transport_expert(
    calibration_paths: tuple[str, ...] | None = None,
    alpha: float = MARS_FD_TRANSPORT_ALPHA,
) -> dict[str, object]:
    paths = _default_mars_fd_transport_paths() if calibration_paths is None else tuple(str(Path(path)) for path in calibration_paths)
    active_calibrator = load_learned_observable_calibrator()
    expert = fit_mars_fd_transport_expert(
        _load_training_records(paths),
        default_validation_state_vector(),
        calibrator=active_calibrator,
        alpha=alpha,
    )
    expert["calibration_paths"] = tuple(paths)
    return expert


def predict_change4_observable_scalar(
    state_vector: Sequence[float],
    record: dict,
    calibrator: dict[str, object] | None = None,
    calibration_paths: Sequence[str] | None = None,
    alpha: float = LEARNED_CALIBRATOR_ALPHA,
) -> float:
    """
    Predict a normalized scalar with the learned residual-ridge calibrator.

    The legacy heuristic is retained as the baseline feature map, but the
    returned value is the learned calibrator output rather than the old
    hand-authored scalar.
    """
    legacy = predict_legacy_observable_scalar(state_vector, record)
    active_calibrator = (
        calibrator
        if calibrator is not None
        else load_learned_observable_calibrator(
            calibration_paths=tuple(_coerce_calibration_paths(calibration_paths)),
            alpha=alpha,
        )
    )
    coefficients = np.asarray(active_calibrator.get("coefficients", ()), dtype=float)
    if coefficients.size == 0:
        return legacy
    features = _observable_calibrator_features(
        state_vector,
        record,
        legacy_scalar=legacy,
    )
    if coefficients.size != features.size:
        return legacy
    correction = float(features @ coefficients)
    prediction = legacy + correction
    training_record_count = int(active_calibrator.get("training_record_count", 0))
    if 0 < training_record_count < LEARNED_CALIBRATOR_SMALL_SAMPLE_THRESHOLD:
        prediction = legacy + LEARNED_CALIBRATOR_SMALL_SAMPLE_SHRINK * (prediction - legacy)
    return _clamp(prediction)


def _record_text(record: dict) -> str:
    return " ".join(
        [
            str(record.get("id", "")),
            str(record.get("units", "")),
            str(record.get("notes", "")),
        ]
    ).lower()


def _parse_utc_event_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), UTC_EVENT_TIME_FORMAT)
    except ValueError:
        return None


def _extract_mars_fd_event_times(record: dict) -> tuple[datetime | None, datetime | None]:
    notes = str(record.get("notes", ""))
    match = re.search(
        r"onset (\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC), nadir (\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)",
        notes,
    )
    if not match:
        return None, None
    return _parse_utc_event_timestamp(match.group(1)), _parse_utc_event_timestamp(match.group(2))


def _extract_mars_fd_duration_hours(record: dict) -> float:
    onset, nadir = _extract_mars_fd_event_times(record)
    if onset is None or nadir is None:
        return 0.0
    return max(0.0, (nadir - onset).total_seconds() / 3600.0)


def _extract_day_of_year_phase(timestamp: datetime | None) -> tuple[float, float]:
    if timestamp is None:
        return 0.0, 1.0
    phase = (2.0 * math.pi * float(timestamp.timetuple().tm_yday)) / 365.25
    return math.sin(phase), math.cos(phase)


def _is_mars_fd_ratio_record(record: dict) -> bool:
    text = _record_text(record)
    return "surface_to_orbit_forbush_drop_ratio" in text


def _is_mars_icme_speed_ratio_record(record: dict) -> bool:
    text = _record_text(record)
    return "mars_1au_to_1p5au_icme_speed_ratio" in text or "1au_to_mars_icme_speed_ratio" in text


def _find_first_record_id(
    records: Sequence[dict],
    *required_tokens: str,
    forbidden_tokens: Sequence[str] = (),
) -> str | None:
    required = tuple(token.lower() for token in required_tokens)
    forbidden = tuple(token.lower() for token in forbidden_tokens)
    for record in records:
        text = _record_text(record)
        if all(token in text for token in required) and not any(
            token in text for token in forbidden
        ):
            return str(record.get("id", ""))
    return None


def _apply_surface_to_cruise_transport_projection(
    state_vector: Sequence[float],
    records: Sequence[dict],
    predictions: dict[str, float],
) -> None:
    surface_to_cruise_records = [
        record
        for record in records
        if "surface_to_cruise" in _record_text(record)
    ]
    if len(surface_to_cruise_records) < 3:
        return

    transmission = PHI_INV
    entropy_quality = _clamp(float(_safe_array(state_vector, size=12)[9]))
    secondary_boost = 0.1 * entropy_quality

    charged_id = _find_first_record_id(surface_to_cruise_records, "charged", "flux")
    fluence_id = _find_first_record_id(surface_to_cruise_records, "fluence", "rate")
    dose_id = _find_first_record_id(
        surface_to_cruise_records,
        "dose",
        "rate",
        forbidden_tokens=("equivalent",),
    )
    quality_id = _find_first_record_id(surface_to_cruise_records, "quality")
    dose_equivalent_id = _find_first_record_id(
        surface_to_cruise_records,
        "dose",
        "equivalent",
        "rate",
        forbidden_tokens=("mission",),
    )
    mission_id = _find_first_record_id(surface_to_cruise_records, "mission", "equivalent")

    if charged_id and charged_id in predictions:
        predictions[charged_id] = _clamp(predictions[charged_id] * transmission)
    if fluence_id and fluence_id in predictions:
        predictions[fluence_id] = _clamp(
            (predictions[fluence_id] + secondary_boost) * transmission
        )
    if dose_id and dose_id in predictions:
        predictions[dose_id] = _clamp(predictions[dose_id] * transmission)
    if quality_id and quality_id in predictions:
        predictions[quality_id] = _clamp(math.sqrt(max(predictions[quality_id], 0.0)))
    if (
        dose_equivalent_id
        and dose_equivalent_id in predictions
        and dose_id
        and dose_id in predictions
        and quality_id
        and quality_id in predictions
    ):
        predictions[dose_equivalent_id] = _clamp(
            predictions[dose_id] * predictions[quality_id]
        )
    if mission_id and mission_id in predictions:
        fluence_projection = (
            predictions[fluence_id]
            if fluence_id and fluence_id in predictions
            else _clamp((predictions[mission_id] + secondary_boost) * transmission)
        )
        predictions[mission_id] = _clamp((fluence_projection + 0.5) / 2.0)


def _apply_crater_altitude_projection(
    records: Sequence[dict],
    predictions: dict[str, float],
) -> None:
    annual_10000_micro_id = _find_first_record_id(
        records,
        "annual",
        "10000km",
        "microdosimeter",
        forbidden_tokens=("surface",),
    )
    annual_surface_10000_id = _find_first_record_id(
        records,
        "annual",
        "surface",
        "10000km",
        forbidden_tokens=("microdosimeter",),
    )
    annual_surface_micro_id = _find_first_record_id(
        records,
        "annual",
        "surface",
        "microdosimeter",
    )
    if (
        not annual_10000_micro_id
        or not annual_surface_10000_id
        or not annual_surface_micro_id
        or annual_10000_micro_id not in predictions
        or annual_surface_10000_id not in predictions
        or annual_surface_micro_id not in predictions
    ):
        return

    annual_surface_micro = _clamp(
        predictions[annual_10000_micro_id] * predictions[annual_surface_10000_id]
    )
    altitude_bridge = _clamp(
        predictions[annual_10000_micro_id] ** (1.0 - PHI_INV)
    )
    surface_bridge = _clamp(
        annual_surface_micro / max(altitude_bridge, 1e-6)
    )

    predictions[annual_10000_micro_id] = altitude_bridge
    predictions[annual_surface_10000_id] = surface_bridge
    predictions[annual_surface_micro_id] = annual_surface_micro

    event_surface_10000_id = _find_first_record_id(
        records,
        "event",
        "surface",
        "10000km",
    )
    if event_surface_10000_id and event_surface_10000_id in predictions:
        event_penetration = surface_bridge + (altitude_bridge - surface_bridge) * (2.0 / 3.0)
        predictions[event_surface_10000_id] = _clamp(event_penetration)


def predict_observable_batch_scalars(
    state_vector: Sequence[float],
    records: Sequence[dict],
    calibrator: dict[str, object] | None = None,
    calibration_paths: Sequence[str] | None = None,
    alpha: float = LEARNED_CALIBRATOR_ALPHA,
) -> dict[str, float]:
    """
    Predict a batch of normalized observable scalars with deterministic
    cross-record transport constraints.

    This keeps the learned per-record calibrator as the starting point, then
    applies batch-level consistency rules when the blind template exposes
    enough structured context to justify them.
    """
    record_list = list(records)
    active_calibrator = (
        calibrator
        if calibrator is not None
        else load_learned_observable_calibrator(
            calibration_paths=tuple(_coerce_calibration_paths(calibration_paths)),
            alpha=alpha,
        )
    )
    predictions = {
        str(record.get("id", "")): predict_change4_observable_scalar(
            state_vector,
            record,
            calibrator=active_calibrator,
            alpha=alpha,
        )
        for record in record_list
    }
    _apply_surface_to_cruise_transport_projection(state_vector, record_list, predictions)
    _apply_crater_altitude_projection(record_list, predictions)
    return predictions


def predict_mars_fd_transport_scalar(
    state_vector: Sequence[float],
    record: dict,
    expert: dict[str, object] | None = None,
    calibrator: dict[str, object] | None = None,
    alpha: float = MARS_FD_TRANSPORT_ALPHA,
) -> float:
    active_calibrator = (
        calibrator if calibrator is not None else load_learned_observable_calibrator()
    )
    base_prediction = predict_change4_observable_scalar(
        state_vector,
        record,
        calibrator=active_calibrator,
    )
    active_expert = (
        expert
        if expert is not None
        else load_mars_fd_transport_expert(alpha=alpha)
    )
    coefficients = np.asarray(active_expert.get("coefficients", ()), dtype=float)
    if coefficients.size == 0:
        return base_prediction
    features = _mars_fd_transport_features(
        state_vector,
        record,
        base_prediction=base_prediction,
        calibrator=active_calibrator,
    )
    if coefficients.size != features.size:
        return base_prediction
    return _clamp(float(features @ coefficients))


def predict_mars_icme_drag_scalar(
    state_vector: Sequence[float],
    record: dict,
    gamma_per_km: float = MARS_ICME_DRAG_GAMMA_PER_KM,
) -> float:
    vector = _safe_array(state_vector, size=12)
    speed_1au = float(record.get("denominator", 0.0)) or 1.0
    delta_r_au = max(0.0, float(record.get("delta_r_au", 0.5)))
    solar_wind_speed = float(record.get("solar_wind_speed_km_s", 0.0))
    if solar_wind_speed <= 0.0:
        launch_speed = float(record.get("launch_speed_km_s", 0.0))
        if launch_speed > 0.0:
            solar_wind_speed = min(speed_1au, 0.5 * (launch_speed + speed_1au))
        else:
            solar_wind_speed = 0.75 * speed_1au

    default_transport = default_validation_state_vector()[[0, 7, 8, 11]]
    candidate_transport = vector[[0, 7, 8, 11]]
    transport_distance = float(np.mean(np.abs(candidate_transport - default_transport)))
    gamma_scale = max(0.25, 1.0 - transport_distance / 0.8)
    distance_km = delta_r_au * 149_597_870.7
    propagated_speed = solar_wind_speed + (speed_1au - solar_wind_speed) * math.exp(
        -float(gamma_per_km) * gamma_scale * distance_km
    )
    return _clamp(propagated_speed / speed_1au)


def predict_v5_observable_batch_scalars(
    state_vector: Sequence[float],
    records: Sequence[dict],
    calibrator: dict[str, object] | None = None,
    mars_fd_expert: dict[str, object] | None = None,
    alpha: float = LEARNED_CALIBRATOR_ALPHA,
    mars_fd_alpha: float = MARS_FD_TRANSPORT_ALPHA,
) -> dict[str, float]:
    record_list = list(records)
    active_calibrator = (
        calibrator
        if calibrator is not None
        else load_learned_observable_calibrator(alpha=alpha)
    )
    base_predictions = predict_observable_batch_scalars(
        state_vector,
        record_list,
        calibrator=active_calibrator,
        alpha=alpha,
    )
    active_mars_fd_expert = (
        mars_fd_expert
        if mars_fd_expert is not None
        else load_mars_fd_transport_expert(alpha=mars_fd_alpha)
    )

    for record in record_list:
        record_id = str(record.get("id", ""))
        if _is_mars_fd_ratio_record(record):
            base_predictions[record_id] = predict_mars_fd_transport_scalar(
                state_vector,
                record,
                expert=active_mars_fd_expert,
                calibrator=active_calibrator,
                alpha=mars_fd_alpha,
            )
        elif _is_mars_icme_speed_ratio_record(record):
            base_predictions[record_id] = predict_mars_icme_drag_scalar(
                state_vector,
                record,
            )
    return base_predictions


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
