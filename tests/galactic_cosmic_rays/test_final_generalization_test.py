import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_final_generalization_test.py"
SPEC = importlib.util.spec_from_file_location("final_generalization_test", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["final_generalization_test"] = MODULE
SPEC.loader.exec_module(MODULE)

build_final_generalization_test = MODULE.build_final_generalization_test


def test_final_generalization_gate_requires_all_external_datasets_to_win():
    report = build_final_generalization_test()

    assert report["generalization_gate"]["status"] == "generalized"
    assert report["answer"].startswith("Yes.")
    assert report["artemis_bundle_diagnostic"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["msl_external_stress_test"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["msl_external_stress_test"]["learned_generalizes_here"] is True
