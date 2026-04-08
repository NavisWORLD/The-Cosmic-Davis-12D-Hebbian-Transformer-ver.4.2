import importlib.util
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_msl_rad_external_validation.py"
SPEC = importlib.util.spec_from_file_location("msl_rad_external_validation", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["msl_rad_external_validation"] = MODULE
SPEC.loader.exec_module(MODULE)

build_msl_rad_external_validation = MODULE.build_msl_rad_external_validation


def test_msl_rad_external_validation_clears_the_independent_stress_test():
    report = build_msl_rad_external_validation()

    assert report["external_alignment"]["official_overall_alignment"] > 0.6
    assert report["learned_generalizes_here"] is True
    assert report["best_mae_baselines"] == ["learned_calibrator_proxy"]
    assert report["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert math.isclose(
        report["baselines"]["learned_calibrator_proxy"]["mae"],
        0.010525463648841762,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert report["baselines"]["learned_calibrator_proxy"]["mae"] < report["baselines"]["legacy_heuristic_proxy"]["mae"]
    assert report["baselines"]["learned_calibrator_proxy"]["mae"] < report["baselines"]["midpoint_0_5"]["mae"]
