import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("change4_alignment_diagnostic", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["change4_alignment_diagnostic"] = MODULE
SPEC.loader.exec_module(MODULE)

build_change4_alignment_diagnostic = MODULE.build_change4_alignment_diagnostic


def test_change4_diagnostic_is_reproducible_and_detailed():
    diagnostic = build_change4_alignment_diagnostic()
    aggregate = diagnostic["aggregate"]
    model = diagnostic["model"]
    records = diagnostic["records"]

    assert diagnostic["dataset"]["record_count"] == 6
    assert aggregate["official_overall_alignment"] == diagnostic["aggregate"]["official_overall_alignment"]
    assert 0.60 <= aggregate["official_overall_alignment"] <= 0.70
    assert aggregate["heuristic_band"] == "interesting_correlation"
    assert model["learned_calibrator"]["type"] == "residual_ridge"
    assert model["learned_calibrator"]["training_record_count"] == 19
    assert len(records) == 6
    assert records[0]["id"] == "change4_lnd_2026_cavity_low_energy_reduction"
    assert records[0]["normalized_target"] == 0.7
    assert records[0]["record_alignment_score"] > 0.5
    assert "legacy_heuristic_scalar_prediction" in records[0]
    assert "learned_calibrator_scalar_prediction" in records[0]
