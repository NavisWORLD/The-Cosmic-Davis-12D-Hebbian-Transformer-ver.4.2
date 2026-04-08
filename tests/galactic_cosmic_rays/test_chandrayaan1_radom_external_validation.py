import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
SCRIPT_PATH = ROOT / "scripts" / "run_chandrayaan1_radom_external_validation.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location("chandrayaan1_radom_external_validation", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["chandrayaan1_radom_external_validation"] = MODULE
SPEC.loader.exec_module(MODULE)

build_chandrayaan1_radom_external_validation = MODULE.build_chandrayaan1_radom_external_validation


def test_chandrayaan1_radom_external_validation_stays_family_led():
    report = build_chandrayaan1_radom_external_validation()

    assert report["family_led"] is True
    assert report["family_beats_naive_and_metadata"] is True
    assert report["learned_beats_metadata_only"] is True
    assert report["legacy_beats_metadata_only"] is True
    assert report["best_mae_baselines"] == ["learned_calibrator_proxy"]
    assert report["best_rmse_baselines"] == ["learned_calibrator_proxy"]
