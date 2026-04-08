import importlib.util
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_mars_fd_external_validation.py"
SPEC = importlib.util.spec_from_file_location("mars_fd_external_validation", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["mars_fd_external_validation"] = MODULE
SPEC.loader.exec_module(MODULE)

build_mars_fd_external_validation = MODULE.build_mars_fd_external_validation


def test_mars_fd_external_validation_beats_naive_carryover_baselines():
    report = build_mars_fd_external_validation()

    assert report["paired_event_count"] == 79
    assert report["learned_beats_naive_baselines"] is True
    assert report["legacy_beats_naive_baselines"] is True
    assert report["best_mae_baselines"] == ["legacy_heuristic_proxy"]
    assert report["best_rmse_baselines"] == ["legacy_heuristic_proxy"]
    assert math.isclose(
        report["baselines"]["legacy_heuristic_proxy"]["mae"],
        0.19204242496176088,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert math.isclose(
        report["baselines"]["learned_calibrator_proxy"]["mae"],
        0.19415361355374322,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert report["baselines"]["learned_calibrator_proxy"]["mae"] < report["baselines"]["midpoint_0_5"]["mae"]
