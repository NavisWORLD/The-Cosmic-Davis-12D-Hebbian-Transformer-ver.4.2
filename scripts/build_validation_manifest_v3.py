"""Build the frozen v3 validation manifest for the radiation model family."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
V3_SCRIPT = ROOT / "scripts" / "run_final_v3_validation.py"
DEFAULT_OUTPUT = ROOT / "docs" / "validation" / "validation_manifest_v3.json"
V3_TEMPLATE_FILENAMES = (
    "crater_lro_blind_template.json",
    "mars_fd_surface_orbit_blind_template.json",
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


def build_validation_manifest_v3() -> dict:
    change4_module = _load_module(CHANGE4_SCRIPT, "change4_alignment_manifest_v3")
    v3_module = _load_module(V3_SCRIPT, "final_v3_manifest_bundle")

    change4_report = change4_module.build_change4_alignment_diagnostic()
    v3_report = v3_module.build_final_v3_validation()

    template_dir = ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates"
    templates = {}
    for filename in V3_TEMPLATE_FILENAMES:
        path = template_dir / filename
        if path.exists():
            templates[str(path)] = _sha256(path)

    return {
        "freeze_label": "cst_radiation_validation_v3",
        "freeze_date": "2026-04-08",
        "status": v3_report["v3_gate"]["status"],
        "basis": "v2 learned-calibrator gate plus direct and blind MSL, CRaTER, and Mars FD external validation.",
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
            "v2_gate_status": v3_report["v2_gate_status"],
            "learned_calibrator_status": v3_report["learned_calibrator_status"],
            "external_baskets": v3_report["external_baskets"],
            "blind_bundle": v3_report["blind_bundle"],
            "v3_gate": v3_report["v3_gate"],
        },
        "reproducibility": {
            "python_version": sys.version.split()[0],
            "commands": [
                "python scripts/run_final_v3_validation.py --output-dir docs/validation",
                "python scripts/build_validation_manifest_v3.py --output docs/validation/validation_manifest_v3.json",
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

    manifest = build_validation_manifest_v3()
    output_path = write_manifest(args.output, manifest)
    print(f"Validation manifest: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
