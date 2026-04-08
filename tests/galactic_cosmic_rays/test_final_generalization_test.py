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
    datasets = report["datasets"]

    assert report["generalization_gate"]["status"] == "generalized"
    assert report["answer"].startswith("Yes, within this validation bundle.")
    assert "observable_aware_proxy" in datasets["artemis_i_external_ratios"]["best_rmse_baselines"]
    assert "observable_aware_proxy" in datasets["artemis_i_m42_gcr_organs"]["best_rmse_baselines"]
    assert "observable_aware_proxy" in report["combined_external_baselines"]["best_rmse_baselines"]
