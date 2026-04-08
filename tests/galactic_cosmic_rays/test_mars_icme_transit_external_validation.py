import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
SCRIPT_PATH = ROOT / "scripts" / "run_mars_icme_transit_external_validation.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location("mars_icme_transit_external_validation", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["mars_icme_transit_external_validation"] = MODULE
SPEC.loader.exec_module(MODULE)

build_mars_icme_transit_external_validation = MODULE.build_mars_icme_transit_external_validation


def test_mars_icme_transit_external_validation_is_v5_led():
    report = build_mars_icme_transit_external_validation()

    assert report["best_mae_baselines"] == ["v5_transport_router_proxy"]
    assert report["best_rmse_baselines"] == ["v5_transport_router_proxy"]
    assert report["v5_beats_legacy"] is True
    assert report["v5_beats_v4"] is True
    assert report["v5_beats_metadata_only"] is True
    assert report["bootstrap"]["v5_vs_v4"]["rmse"]["ci_high"] < 0.0
