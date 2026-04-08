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


def test_blind_prediction_and_scoring_pipeline_is_reproducible_for_msl():
    template = ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "msl_rad_blind_template.json"
    revealed = ROOT / "tests" / "galactic_cosmic_rays" / "msl_rad_reference.json"

    bundle = PREDICT_MODULE.build_prediction_bundle(template, label="msl_rad_v1")
    score = SCORE_MODULE.score_prediction_bundle(
        ROOT / "docs" / "validation" / "blind_predictions_msl_v1.json",
        revealed,
    )

    assert bundle["label"] == "msl_rad_v1"
    assert len(bundle["predictions"]) == 6
    assert score["best_mae_baselines"] == ["midpoint_0_5"]
    assert score["best_rmse_baselines"] == ["midpoint_0_5"]
    assert math.isclose(
        score["baselines"]["learned_calibrator_proxy"]["mae"],
        0.2471541684533243,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )


def test_validation_manifest_freezes_the_current_status():
    manifest = MANIFEST_MODULE.build_validation_manifest()

    assert manifest["freeze_label"] == "cst_radiation_validation_v1"
    assert manifest["status"] == "not_generalized"
    assert len(manifest["blind_protocol"]["template_sha256"]) == 2
    assert manifest["reports"]["msl_external"]["best_mae_baselines"] == ["midpoint_0_5"]
