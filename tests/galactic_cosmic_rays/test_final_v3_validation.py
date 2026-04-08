import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
FINAL_V3_SCRIPT = ROOT / "scripts" / "run_final_v3_validation.py"
MANIFEST_V3_SCRIPT = ROOT / "scripts" / "build_validation_manifest_v3.py"

FINAL_V3_SPEC = importlib.util.spec_from_file_location("final_v3_validation", FINAL_V3_SCRIPT)
FINAL_V3_MODULE = importlib.util.module_from_spec(FINAL_V3_SPEC)
assert FINAL_V3_SPEC and FINAL_V3_SPEC.loader
sys.modules["final_v3_validation"] = FINAL_V3_MODULE
FINAL_V3_SPEC.loader.exec_module(FINAL_V3_MODULE)

MANIFEST_V3_SPEC = importlib.util.spec_from_file_location("validation_manifest_v3", MANIFEST_V3_SCRIPT)
MANIFEST_V3_MODULE = importlib.util.module_from_spec(MANIFEST_V3_SPEC)
assert MANIFEST_V3_SPEC and MANIFEST_V3_SPEC.loader
sys.modules["validation_manifest_v3"] = MANIFEST_V3_MODULE
MANIFEST_V3_SPEC.loader.exec_module(MANIFEST_V3_MODULE)


def test_final_v3_validation_promotes_the_model_family_finish():
    report = FINAL_V3_MODULE.build_final_v3_validation()

    assert report["freeze_label"] == "cst_radiation_validation_v3"
    assert report["v2_gate_status"] == "generalized"
    assert report["v3_gate"]["status"] == "validated_model_family"
    assert report["external_baskets"]["msl_external"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["external_baskets"]["crater_external"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["external_baskets"]["mars_fd_external"]["best_rmse_baselines"] == ["legacy_heuristic_proxy"]
    assert report["blind_bundle"]["msl"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["blind_bundle"]["crater"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["blind_bundle"]["mars_fd"]["best_rmse_baselines"] == ["legacy_heuristic_proxy"]


def test_validation_manifest_v3_freezes_three_blind_templates():
    manifest = MANIFEST_V3_MODULE.build_validation_manifest_v3()

    assert manifest["freeze_label"] == "cst_radiation_validation_v3"
    assert manifest["status"] == "validated_model_family"
    assert len(manifest["blind_protocol"]["template_sha256"]) == 3
