"""Build a frozen validation manifest for the current radiation model bundle."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
FINAL_SCRIPT = ROOT / "scripts" / "run_final_generalization_test.py"
MSL_SCRIPT = ROOT / "scripts" / "run_msl_rad_external_validation.py"
CRATER_SCRIPT = ROOT / "scripts" / "run_crater_lro_external_validation.py"
DEFAULT_OUTPUT = ROOT / "docs" / "validation" / "validation_manifest_v2.json"
V2_TEMPLATE_FILENAMES = (
    "crater_lro_blind_template.json",
    "msl_rad_blind_template.json",
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def build_validation_manifest() -> dict:
    change4 = _load_module(CHANGE4_SCRIPT, "change4_alignment_manifest")
    final_gate = _load_module(FINAL_SCRIPT, "final_gate_manifest")
    msl = _load_module(MSL_SCRIPT, "msl_manifest")
    crater = _load_module(CRATER_SCRIPT, "crater_manifest")

    change4_report = change4.build_change4_alignment_diagnostic()
    final_report = final_gate.build_final_generalization_test()
    msl_report = msl.build_msl_rad_external_validation()
    crater_report = crater.build_crater_lro_external_validation()

    template_dir = ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates"
    templates = {}
    for filename in V2_TEMPLATE_FILENAMES:
        path = template_dir / filename
        if path.exists():
            templates[str(path)] = _sha256(path)

    return {
        "freeze_label": "cst_radiation_validation_v2",
        "freeze_date": "2026-04-08",
        "status": final_report["generalization_gate"]["status"],
        "model": {
            "module_path": str(ROOT / "cosmos" / "core" / "cst_critical_integration.py"),
            "learned_calibrator": change4_report["model"]["learned_calibrator"],
        },
        "training_bundle": {
            "paths": change4_report["model"]["learned_calibrator"]["calibration_paths"],
            "sha256": change4_report["model"]["learned_calibrator"]["calibration_sha256"],
        },
        "blind_protocol": {
            "prediction_script": str(ROOT / "scripts" / "generate_blind_validation_predictions.py"),
            "scoring_script": str(ROOT / "scripts" / "score_blind_validation_predictions.py"),
            "template_sha256": templates,
        },
        "reports": {
            "change4_alignment": {
                "overall_alignment": change4_report["aggregate"]["official_overall_alignment"],
                "heuristic_band": change4_report["aggregate"]["heuristic_band"],
            },
            "msl_external": {
                "best_mae_baselines": msl_report["best_mae_baselines"],
                "best_rmse_baselines": msl_report["best_rmse_baselines"],
                "learned_mae": msl_report["baselines"]["learned_calibrator_proxy"]["mae"],
                "learned_rmse": msl_report["baselines"]["learned_calibrator_proxy"]["rmse"],
            },
            "crater_external": {
                "best_mae_baselines": crater_report["best_mae_baselines"],
                "best_rmse_baselines": crater_report["best_rmse_baselines"],
                "learned_mae": crater_report["baselines"]["learned_calibrator_proxy"]["mae"],
                "learned_rmse": crater_report["baselines"]["learned_calibrator_proxy"]["rmse"],
            },
            "final_gate": final_report["generalization_gate"],
        },
        "reproducibility": {
            "python_version": sys.version.split()[0],
            "commands": [
                "python scripts/build_validation_manifest.py --output docs/validation/validation_manifest_v2.json",
                "python scripts/generate_blind_validation_predictions.py --template tests/galactic_cosmic_rays/blind_templates/msl_rad_blind_template.json --output docs/validation/blind_predictions_msl_v2.json",
                "python scripts/score_blind_validation_predictions.py --predictions docs/validation/blind_predictions_msl_v2.json --revealed tests/galactic_cosmic_rays/msl_rad_reference.json --output docs/validation/blind_scoring_msl_v2.json",
                "python scripts/run_final_generalization_test.py --output-dir docs/validation",
                "python -m pytest tests/galactic_cosmic_rays -q",
            ],
        },
    }


def write_manifest(output_path: Path, manifest: dict) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    manifest = build_validation_manifest()
    output_path = write_manifest(args.output, manifest)
    print(f"Validation manifest: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
