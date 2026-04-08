import importlib.util
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_crater_lro_external_validation.py"
SPEC = importlib.util.spec_from_file_location("crater_lro_external_validation", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["crater_lro_external_validation"] = MODULE
SPEC.loader.exec_module(MODULE)

build_crater_lro_external_validation = MODULE.build_crater_lro_external_validation


def test_crater_lro_external_validation_reports_the_mixed_transfer_result():
    report = build_crater_lro_external_validation()

    assert report["external_alignment"]["official_overall_alignment"] > 0.55
    assert report["best_mae_baselines"] == ["learned_calibrator_proxy"]
    assert report["best_rmse_baselines"] == ["legacy_heuristic_proxy"]
    assert math.isclose(
        report["baselines"]["learned_calibrator_proxy"]["mae"],
        0.16597115647212154,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert report["baselines"]["learned_calibrator_proxy"]["mae"] < report["baselines"]["legacy_heuristic_proxy"]["mae"]
    assert report["baselines"]["learned_calibrator_proxy"]["rmse"] > report["baselines"]["legacy_heuristic_proxy"]["rmse"]
