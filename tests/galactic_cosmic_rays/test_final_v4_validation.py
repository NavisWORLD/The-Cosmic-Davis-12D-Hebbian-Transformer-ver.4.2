import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
FINAL_V4_SCRIPT = ROOT / "scripts" / "run_final_v4_validation.py"
MANIFEST_V4_SCRIPT = ROOT / "scripts" / "build_validation_manifest_v4.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

FINAL_V4_SPEC = importlib.util.spec_from_file_location("final_v4_validation", FINAL_V4_SCRIPT)
FINAL_V4_MODULE = importlib.util.module_from_spec(FINAL_V4_SPEC)
assert FINAL_V4_SPEC and FINAL_V4_SPEC.loader
sys.modules["final_v4_validation"] = FINAL_V4_MODULE
FINAL_V4_SPEC.loader.exec_module(FINAL_V4_MODULE)

MANIFEST_V4_SPEC = importlib.util.spec_from_file_location("validation_manifest_v4", MANIFEST_V4_SCRIPT)
MANIFEST_V4_MODULE = importlib.util.module_from_spec(MANIFEST_V4_SPEC)
assert MANIFEST_V4_SPEC and MANIFEST_V4_SPEC.loader
sys.modules["validation_manifest_v4"] = MANIFEST_V4_MODULE
MANIFEST_V4_SPEC.loader.exec_module(MANIFEST_V4_MODULE)


def test_final_v4_validation_promotes_a_predictive_subdomain_claim():
    report = FINAL_V4_MODULE.build_final_v4_validation()

    assert report["freeze_label"] == "cst_radiation_validation_v4"
    assert report["v3_gate_status"] == "validated_model_family"
    assert report["v4_gate"]["status"] == "validated_predictive_subdomain"
    assert report["direct_reports"]["msl"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["direct_reports"]["crater"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["blind_reports"]["msl"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["blind_reports"]["crater"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert report["direct_reports"]["mars_fd"]["family_beats_naive_and_metadata"] is True
    assert report["direct_reports"]["chandrayaan1"]["family_beats_naive_and_metadata"] is True
    assert report["direct_reports"]["msl"]["bootstrap"]["learned_vs_metadata_only"]["mae"]["ci_high"] < 0.0
    assert report["direct_reports"]["crater"]["bootstrap"]["learned_vs_metadata_only"]["mae"]["ci_high"] < 0.0


def test_validation_manifest_v4_freezes_four_blind_templates():
    manifest = MANIFEST_V4_MODULE.build_validation_manifest_v4()

    assert manifest["freeze_label"] == "cst_radiation_validation_v4"
    assert manifest["status"] == "validated_predictive_subdomain"
    assert len(manifest["blind_protocol"]["templates_sha256"]) == 4
