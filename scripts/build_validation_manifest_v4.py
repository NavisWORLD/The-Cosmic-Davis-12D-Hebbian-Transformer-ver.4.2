"""Build the frozen v4 validation manifest for the radiation model family."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from radiation_validation_v4_utils import (
    ROOT,
    load_cst_module,
    load_locked_change4,
    sha256,
    write_json,
)

V4_SCRIPT = ROOT / "scripts" / "run_final_v4_validation.py"
DEFAULT_OUTPUT = ROOT / "docs" / "validation" / "validation_manifest_v4.json"
V4_TEMPLATE_FILENAMES = (
    "chandrayaan1_radom_blind_template.json",
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


def build_validation_manifest_v4() -> dict:
    v4_module = _load_module(V4_SCRIPT, "final_v4_manifest_bundle")
    change4_report = load_locked_change4()
    cst_module = load_cst_module()
    v4_report = v4_module.build_final_v4_validation()

    template_dir = ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates"
    templates = {}
    for filename in V4_TEMPLATE_FILENAMES:
        path = template_dir / filename
        if path.exists():
            templates[str(path)] = sha256(path)

    learned_calibrator = cst_module.load_learned_observable_calibrator()
    return {
        "freeze_label": "cst_radiation_validation_v4",
        "freeze_date": "2026-04-08",
        "status": v4_report["v4_gate"]["status"],
        "basis": (
            "v3 validated-model-family evidence plus stronger metadata-only baselines, "
            "12D ablations, bootstrap confidence intervals, blind scoring, and an "
            "independent Chandrayaan-1 RADOM holdout."
        ),
        "model": {
            "module_path": str(ROOT / "cosmos" / "core" / "cst_critical_integration.py"),
            "learned_calibrator": learned_calibrator,
            "default_validation_state_vector": [
                float(value) for value in cst_module.default_validation_state_vector().tolist()
            ],
        },
        "training_bundle": {
            "paths": learned_calibrator.get("calibration_paths", ()),
            "sha256": change4_report["model"]["learned_calibrator"]["calibration_sha256"],
        },
        "blind_protocol": {
            "prediction_script": str(ROOT / "scripts" / "generate_blind_validation_predictions.py"),
            "scoring_script": str(ROOT / "scripts" / "score_blind_validation_predictions.py"),
            "templates_sha256": templates,
        },
        "reports": {
            "v3_gate_status": v4_report["v3_gate_status"],
            "direct_reports": v4_report["direct_reports"],
            "blind_reports": v4_report["blind_reports"],
            "v4_gate": v4_report["v4_gate"],
        },
        "reproducibility": {
            "python_version": sys.version.split()[0],
            "commands": [
                "python scripts/run_chandrayaan1_radom_external_validation.py --output-dir docs/validation",
                "python scripts/run_final_v4_validation.py --output-dir docs/validation",
                "python scripts/build_validation_manifest_v4.py --output docs/validation/validation_manifest_v4.json",
                "python -m pytest tests/galactic_cosmic_rays -q",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    manifest = build_validation_manifest_v4()
    output_path = write_json(args.output, manifest)
    print(f"Validation manifest: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
