import math
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "Cosmos"
MODULE_PATH = PACKAGE_ROOT / "core" / "cst_critical_integration.py"
SPEC = importlib.util.spec_from_file_location("cst_critical_integration", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["cst_critical_integration"] = MODULE
SPEC.loader.exec_module(MODULE)

build_12d_state_vector = MODULE.build_12d_state_vector
coherence_conservation_step = MODULE.coherence_conservation_step
fold_onset_triplet = MODULE.fold_onset_triplet
mahalanobis_collapse_distance = MODULE.mahalanobis_collapse_distance
omega_point_convergence = MODULE.omega_point_convergence
phase_transition_hysteresis = MODULE.phase_transition_hysteresis
spectral_profile_from_counts = MODULE.spectral_profile_from_counts


def test_coherence_conservation_preserves_total():
    ci_b, ci_c = 0.42, 0.18
    new_b, new_c = coherence_conservation_step(ci_b, ci_c, dt=0.01)
    assert math.isclose(new_b + new_c, ci_b + ci_c, rel_tol=1e-12, abs_tol=1e-12)
    assert new_b < ci_b
    assert new_c > ci_c


def test_phase_transition_hysteresis_uses_entry_and_recovery_gap():
    collapsed = phase_transition_hysteresis(0.050, currently_collapsed=False)
    assert collapsed is True

    still_collapsed = phase_transition_hysteresis(0.040, currently_collapsed=True)
    assert still_collapsed is True

    recovered = phase_transition_hysteresis(0.030, currently_collapsed=True)
    assert recovered is False


def test_fold_onset_triplet_detects_pre_collapse_pattern():
    result = fold_onset_triplet(
        lambda2_history=[0.11, 0.18],
        ideational_density_history=[0.91, 0.82],
        zeta_history=[0.33, 0.41],
    )
    assert result.active is True
    assert result.delta_lambda2 > 0
    assert result.delta_ideational_density < 0
    assert result.delta_zeta > 0


def test_spectral_profile_extracts_companion_metrics():
    counts = {
        "00000": 120,
        "11111": 110,
        "10101": 80,
        "01010": 75,
    }
    profile = spectral_profile_from_counts(counts)
    assert profile["matrix_dim"] == 5
    assert profile["spectral_radius"] >= profile["second_eigenvalue"] >= 0.0


def test_mahalanobis_distance_is_finite_for_runtime_vector():
    vector = build_12d_state_vector(
        {
            "cst_physics": {
                "geometric_phase_rad": 0.618,
                "phase_velocity": 0.03,
                "entanglement_score": 0.81,
            },
            "bio_signatures": {
                "intensity": 0.57,
                "arousal": 0.24,
                "valence": 0.08,
            },
            "cst_metrics": {
                "x12_avg": 0.61,
                "ci_b": 0.36,
                "ci_c": 0.25,
            },
        },
        metrics={"entropy_quality": 0.99, "decoherence_risk": 0.02},
        dark_matter_w=0.44,
    )
    distance = mahalanobis_collapse_distance(vector)
    assert math.isfinite(distance)
    assert distance >= 0.0


def test_omega_point_convergence_reports_ratio():
    result = omega_point_convergence(
        epsilon=0.99,
        omega_net=0.64,
        x12_avg=0.61,
        ci_b=0.34,
        ci_c=0.28,
    )
    assert result["omega_point_target"] > 0.0
    assert result["omega_convergence_sum"] > 0.0
    assert result["omega_convergence_ratio"] > 0.0
