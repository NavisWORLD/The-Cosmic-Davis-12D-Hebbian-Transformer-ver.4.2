import json
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
galactic_cosmic_ray_alignment = MODULE.galactic_cosmic_ray_alignment


FIXTURE_PATH = Path(__file__).with_name("recent_gcr_reference.json")


def _load_reference_data():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_recent_gcr_alignment_is_mathematical_and_bounded():
    """
    Use recent, source-backed galactic-cosmic-ray records and verify the
    12D model produces a bounded alignment score over real numeric inputs.
    """
    records = _load_reference_data()
    state_vector = build_12d_state_vector(
        {
            "cst_physics": {
                "geometric_phase_rad": 0.618,
                "phase_velocity": 0.014,
                "entanglement_score": 0.84,
            },
            "bio_signatures": {
                "intensity": 0.58,
                "arousal": 0.22,
                "valence": 0.14,
            },
            "cst_metrics": {
                "x12_avg": 0.63,
                "ci_b": 0.36,
                "ci_c": 0.26,
            },
        },
        metrics={
            "entropy_quality": 0.9946,
            "decoherence_risk": 0.0146,
        },
        dark_matter_w=0.47,
    )

    result = galactic_cosmic_ray_alignment(state_vector, records)

    assert 0.0 <= result.overall_alignment <= 1.0
    assert 0.0 <= result.cosine_similarity <= 1.0
    assert 0.0 <= result.phase_distance <= 1.0
    assert len(result.probe_vector) == 12
    assert len(result.normalized_scalars) == 4
    assert result.overall_alignment >= 0.45
