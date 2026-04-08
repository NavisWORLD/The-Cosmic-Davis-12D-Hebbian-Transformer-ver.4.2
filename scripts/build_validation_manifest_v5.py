"""Build the frozen v5 transport-router validation manifest."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from radiation_validation_v5_utils import ROOT, load_cst_module, sha256, write_json

V5_SCRIPT = ROOT / "scripts" / "run_final_v5_validation.py"
DEFAULT_OUTPUT = ROOT / "docs" / "validation" / "validation_manifest_v5.json"
V5_TEMPLATE_FILENAMES = (
    "chandrayaan1_radom_blind_template.json",
    "crater_lro_blind_template.json",
    "mars_fd_surface_orbit_blind_template.json",
    "mars_icme_transit_blind_template.json",
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


def build_validation_manifest_v5() -> dict:
    v5_module = _load_module(V5_SCRIPT, "final_v5_manifest_bundle")
    cst_module = load_cst_module()
    v5_report = v5_module.build_final_v5_validation()

    template_dir = ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates"
    templates = {}
    for filename in V5_TEMPLATE_FILENAMES:
        path = template_dir / filename
        if path.exists():
            templates[str(path)] = sha256(path)

    learned_calibrator = cst_module.load_learned_observable_calibrator()
    mars_fd_expert = cst_module.load_mars_fd_transport_expert()
    return {
        "freeze_label": "cst_radiation_validation_v5",
        "freeze_date": "2026-04-08",
        "status": v5_report["v5_gate"]["status"],
        "basis": (
            "v4 predictive-subdomain evidence plus a v5 Mars transport router that upgrades the "
            "Mars FD benchmark and wins on a separate untouched Mars ICME transit holdout."
        ),
        "model": {
            "module_path": str(ROOT / "cosmos" / "core" / "cst_critical_integration.py"),
            "learned_calibrator": learned_calibrator,
            "mars_fd_transport_expert": mars_fd_expert,
            "default_validation_state_vector": [
                float(value) for value in cst_module.default_validation_state_vector().tolist()
            ],
            "mars_icme_drag_gamma_per_km": float(cst_module.MARS_ICME_DRAG_GAMMA_PER_KM),
        },
        "blind_protocol": {
            "prediction_script": str(ROOT / "scripts" / "generate_blind_validation_predictions.py"),
            "scoring_script": str(ROOT / "scripts" / "score_blind_validation_predictions.py"),
            "templates_sha256": templates,
        },
        "reports": {
            "v4_gate_status": v5_report["v4_gate_status"],
            "direct_reports": v5_report["direct_reports"],
            "blind_reports": v5_report["blind_reports"],
            "v5_gate": v5_report["v5_gate"],
        },
        "reproducibility": {
            "python_version": sys.version.split()[0],
            "commands": [
                "python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation",
                "python scripts/run_final_v5_validation.py --output-dir docs/validation",
                "python scripts/build_validation_manifest_v5.py --output docs/validation/validation_manifest_v5.json",
                "python -m pytest tests/galactic_cosmic_rays -q",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    manifest = build_validation_manifest_v5()
    output_path = write_json(args.output, manifest)
    print(f"Validation manifest: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
