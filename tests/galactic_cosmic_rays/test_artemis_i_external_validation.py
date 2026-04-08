import importlib.util
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_artemis_i_external_validation.py"
SPEC = importlib.util.spec_from_file_location("artemis_i_external_validation", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["artemis_i_external_validation"] = MODULE
SPEC.loader.exec_module(MODULE)

build_artemis_i_external_validation = MODULE.build_artemis_i_external_validation


def test_artemis_i_external_validation_is_honest_about_generalization():
    report = build_artemis_i_external_validation()

    assert report["external_alignment"]["official_overall_alignment"] > 0.5
    assert report["generalized_here"] is True
    assert report["answer"].startswith("Yes, within this unseen Artemis I basket.")
    assert len(report["records"]) == 6
    assert "observable_aware_proxy" in report["baselines"]
    assert math.isclose(
        report["baselines"]["model_phase_proxy"]["mae"],
        0.2797746090149557,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert math.isclose(
        report["baselines"]["observable_aware_proxy"]["mae"],
        0.013578753402350869,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert report["baselines"]["observable_aware_proxy"]["mae"] < report["baselines"]["model_phase_proxy"]["mae"]
    assert "observable_aware_proxy" in report["best_rmse_baselines"]
