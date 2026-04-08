import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
FINAL_V5_SCRIPT = ROOT / "scripts" / "run_final_v5_validation.py"
MANIFEST_V5_SCRIPT = ROOT / "scripts" / "build_validation_manifest_v5.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

FINAL_V5_SPEC = importlib.util.spec_from_file_location("final_v5_validation", FINAL_V5_SCRIPT)
FINAL_V5_MODULE = importlib.util.module_from_spec(FINAL_V5_SPEC)
assert FINAL_V5_SPEC and FINAL_V5_SPEC.loader
sys.modules["final_v5_validation"] = FINAL_V5_MODULE
FINAL_V5_SPEC.loader.exec_module(FINAL_V5_MODULE)

MANIFEST_V5_SPEC = importlib.util.spec_from_file_location("validation_manifest_v5", MANIFEST_V5_SCRIPT)
MANIFEST_V5_MODULE = importlib.util.module_from_spec(MANIFEST_V5_SPEC)
assert MANIFEST_V5_SPEC and MANIFEST_V5_SPEC.loader
sys.modules["validation_manifest_v5"] = MANIFEST_V5_MODULE
MANIFEST_V5_SPEC.loader.exec_module(MANIFEST_V5_MODULE)


def test_final_v5_validation_promotes_the_unified_transport_router():
    report = FINAL_V5_MODULE.build_final_v5_validation()

    assert report["freeze_label"] == "cst_radiation_validation_v5"
    assert report["v4_gate_status"] == "validated_predictive_subdomain"
    assert report["v5_gate"]["status"] == "validated_unified_transport_router"
    assert "v5_transport_router_proxy" in report["direct_reports"]["msl"]["best_rmse_baselines"]
    assert "v5_transport_router_proxy" in report["direct_reports"]["crater"]["best_rmse_baselines"]
    assert "v5_transport_router_proxy" in report["direct_reports"]["chandrayaan1"]["best_rmse_baselines"]
    assert report["direct_reports"]["mars_fd"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
    assert report["blind_reports"]["mars_fd"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
    assert report["direct_reports"]["mars_icme_transit"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
    assert report["blind_reports"]["mars_icme_transit"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
    assert report["direct_reports"]["mars_fd"]["bootstrap"]["v5_vs_v4"]["rmse"]["ci_high"] < 0.0
    assert report["direct_reports"]["mars_icme_transit"]["bootstrap"]["v5_vs_v4"]["rmse"]["ci_high"] < 0.0


def test_validation_manifest_v5_freezes_five_blind_templates():
    manifest = MANIFEST_V5_MODULE.build_validation_manifest_v5()

    assert manifest["freeze_label"] == "cst_radiation_validation_v5"
    assert manifest["status"] == "validated_unified_transport_router"
    assert len(manifest["blind_protocol"]["templates_sha256"]) == 5
