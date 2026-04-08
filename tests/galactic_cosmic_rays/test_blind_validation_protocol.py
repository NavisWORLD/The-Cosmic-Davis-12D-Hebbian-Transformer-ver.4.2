import importlib.util
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PREDICT_SCRIPT = ROOT / "scripts" / "generate_blind_validation_predictions.py"
SCORE_SCRIPT = ROOT / "scripts" / "score_blind_validation_predictions.py"
MANIFEST_SCRIPT = ROOT / "scripts" / "build_validation_manifest.py"

PREDICT_SPEC = importlib.util.spec_from_file_location("blind_validation_predictions", PREDICT_SCRIPT)
PREDICT_MODULE = importlib.util.module_from_spec(PREDICT_SPEC)
assert PREDICT_SPEC and PREDICT_SPEC.loader
sys.modules["blind_validation_predictions"] = PREDICT_MODULE
PREDICT_SPEC.loader.exec_module(PREDICT_MODULE)

SCORE_SPEC = importlib.util.spec_from_file_location("blind_validation_scoring", SCORE_SCRIPT)
SCORE_MODULE = importlib.util.module_from_spec(SCORE_SPEC)
assert SCORE_SPEC and SCORE_SPEC.loader
sys.modules["blind_validation_scoring"] = SCORE_MODULE
SCORE_SPEC.loader.exec_module(SCORE_MODULE)

MANIFEST_SPEC = importlib.util.spec_from_file_location("validation_manifest_builder", MANIFEST_SCRIPT)
MANIFEST_MODULE = importlib.util.module_from_spec(MANIFEST_SPEC)
assert MANIFEST_SPEC and MANIFEST_SPEC.loader
sys.modules["validation_manifest_builder"] = MANIFEST_MODULE
MANIFEST_SPEC.loader.exec_module(MANIFEST_MODULE)


def test_blind_prediction_and_scoring_pipeline_is_reproducible_for_msl(tmp_path):
    template = ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "msl_rad_blind_template.json"
    revealed = ROOT / "tests" / "galactic_cosmic_rays" / "msl_rad_reference.json"

    bundle = PREDICT_MODULE.build_prediction_bundle(template, label="msl_rad_v2")
    predictions_path = tmp_path / "blind_predictions_msl_v2.json"
    PREDICT_MODULE.write_prediction_bundle(predictions_path, bundle)
    score = SCORE_MODULE.score_prediction_bundle(
        predictions_path,
        revealed,
    )

    assert bundle["label"] == "msl_rad_v2"
    assert len(bundle["predictions"]) == 6
    assert score["best_mae_baselines"] == ["learned_calibrator_proxy"]
    assert score["best_rmse_baselines"] == ["learned_calibrator_proxy"]
    assert math.isclose(
        score["baselines"]["learned_calibrator_proxy"]["mae"],
        0.011207102395483642,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )


def test_validation_manifest_freezes_the_current_status():
    manifest = MANIFEST_MODULE.build_validation_manifest()

    assert manifest["freeze_label"] == "cst_radiation_validation_v2"
    assert manifest["status"] == "generalized"
    assert len(manifest["blind_protocol"]["template_sha256"]) == 2
    assert manifest["reports"]["msl_external"]["best_mae_baselines"] == ["learned_calibrator_proxy"]
