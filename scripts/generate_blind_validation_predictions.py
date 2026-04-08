"""Generate frozen model predictions from a redacted validation template."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"


def _load_change4_module():
    spec = importlib.util.spec_from_file_location(
        "change4_alignment_diagnostic_blind_predictions",
        CHANGE4_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {CHANGE4_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def build_prediction_bundle(template_path: Path, label: str | None = None) -> dict:
    change4 = _load_change4_module()
    cst_module = change4._load_module()
    template_records = json.loads(template_path.read_text(encoding="utf-8"))
    state_vector = cst_module.default_validation_state_vector()
    calibrator = cst_module.load_learned_observable_calibrator()
    phase_proxy = float(
        change4.build_change4_alignment_diagnostic()["model"]["phase_proxy_clamped"]
    )

    predictions = []
    for record in template_records:
        legacy_scalar = float(cst_module.predict_legacy_observable_scalar(state_vector, record))
        learned_scalar = float(
            cst_module.predict_change4_observable_scalar(
                state_vector,
                record,
                calibrator=calibrator,
            )
        )
        raw_predictions = {}
        for key, scalar in {
            "model_phase_proxy": phase_proxy,
            "legacy_heuristic_proxy": legacy_scalar,
            "learned_calibrator_proxy": learned_scalar,
        }.items():
            try:
                raw_predictions[key] = change4._predicted_value_from_scalar(record, scalar)
            except Exception:
                raw_predictions[key] = None

        predictions.append(
            {
                "id": record["id"],
                "published_date": record.get("published_date", ""),
                "source": record.get("source", ""),
                "source_url": record.get("source_url", ""),
                "units": record.get("units", "unitless"),
                "notes": record.get("notes", ""),
                "model_phase_proxy_scalar": phase_proxy,
                "legacy_heuristic_scalar": legacy_scalar,
                "learned_calibrator_scalar": learned_scalar,
                "model_phase_proxy_raw_prediction": raw_predictions["model_phase_proxy"],
                "legacy_heuristic_raw_prediction": raw_predictions["legacy_heuristic_proxy"],
                "learned_calibrator_raw_prediction": raw_predictions["learned_calibrator_proxy"],
            }
        )

    return {
        "label": label or template_path.stem,
        "template_path": str(template_path),
        "template_sha256": _sha256(template_path),
        "reproducibility": {
            "command": (
                "python scripts/generate_blind_validation_predictions.py "
                f"--template {template_path} --output <output>"
            ),
            "python_version": sys.version.split()[0],
            "change4_script": str(CHANGE4_SCRIPT),
        },
        "model": {
            "state_vector": [float(value) for value in state_vector.tolist()],
            "phase_proxy_clamped": phase_proxy,
            "learned_calibrator": change4.build_change4_alignment_diagnostic()["model"]["learned_calibrator"],
        },
        "predictions": predictions,
    }


def write_prediction_bundle(output_path: Path, bundle: dict) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True, help="Path to the redacted blind template JSON.")
    parser.add_argument("--output", type=Path, required=True, help="Where to write the prediction bundle JSON.")
    parser.add_argument("--label", type=str, default=None, help="Optional label for the prediction bundle.")
    args = parser.parse_args()

    bundle = build_prediction_bundle(args.template, label=args.label)
    output_path = write_prediction_bundle(args.output, bundle)
    print(f"Prediction bundle: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
