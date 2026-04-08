import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "Cosmos"
MODULE_PATH = PACKAGE_ROOT / "core" / "cst_critical_integration.py"
SPEC = importlib.util.spec_from_file_location("cst_critical_integration_change4", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["cst_critical_integration_change4"] = MODULE
SPEC.loader.exec_module(MODULE)

build_12d_state_vector = MODULE.build_12d_state_vector
galactic_cosmic_ray_alignment = MODULE.galactic_cosmic_ray_alignment


FIXTURE_PATH = Path(__file__).with_name("change4_lnd_reference.json")


def _load_reference_data():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_change4_lnd_alignment_runs_against_recent_and_historical_lnd_measurements():
    """
    Validate the 12D model against Chang'e-4 / LND lunar far-side radiation data.

    This uses:
    - the March 25, 2026 Chang'e-4 cavity result
    - LPSC 2024 dose-equivalent values
    - 2021 two-year dose averages
    - 2022 LND albedo-to-primary proton ratio
    """
    records = _load_reference_data()
    state_vector = build_12d_state_vector(
        {
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
        },
        metrics={
            "entropy_quality": 0.78,
            "decoherence_risk": 0.22,
        },
        dark_matter_w=0.36,
    )

    result = galactic_cosmic_ray_alignment(state_vector, records)

    assert 0.0 <= result.overall_alignment <= 1.0
    assert 0.0 <= result.cosine_similarity <= 1.0
    assert 0.0 <= result.phase_distance <= 1.0
    assert len(result.probe_vector) == 12
    assert len(result.normalized_scalars) == 6
    assert result.overall_alignment >= 0.5
