import importlib.util
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_change4_heldout_validation.py"
SPEC = importlib.util.spec_from_file_location("change4_heldout_validation", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["change4_heldout_validation"] = MODULE
SPEC.loader.exec_module(MODULE)

build_change4_heldout_validation = MODULE.build_change4_heldout_validation


def test_change4_heldout_validation_reports_baselines_and_errors():
    report = build_change4_heldout_validation()

    leave_one_out = report["leave_one_out"]
    chrono = report["chronological_holdout_2026"]

    assert report["source_alignment"]["heuristic_band"] == "interesting_correlation"
    assert len(leave_one_out["targets"]) == 6
    assert leave_one_out["best_mae_baseline"] in leave_one_out["baselines"]
    assert leave_one_out["best_rmse_baseline"] in leave_one_out["baselines"]
    assert "legacy_heuristic_proxy" in leave_one_out["baselines"]
    assert "learned_calibrator_proxy" in leave_one_out["baselines"]
    assert math.isclose(
        leave_one_out["baselines"]["model_phase_proxy"]["mae"],
        0.31618895360301075,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert math.isclose(
        leave_one_out["baselines"]["legacy_heuristic_proxy"]["mae"],
        0.004874911752799094,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert leave_one_out["best_mae_baseline"] == "legacy_heuristic_proxy"
    assert leave_one_out["best_rmse_baseline"] == "learned_calibrator_proxy"
    assert leave_one_out["baselines"]["learned_calibrator_proxy"]["rmse"] < leave_one_out["baselines"]["legacy_heuristic_proxy"]["rmse"]
    assert len(chrono["train_records"]) == 4
    assert len(chrono["test_records"]) == 2
    assert chrono["best_mae_baseline"] == "learned_calibrator_proxy"
    assert chrono["best_rmse_baseline"] == "legacy_heuristic_proxy"
