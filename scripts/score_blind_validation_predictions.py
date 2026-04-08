"""Score a prediction bundle against a revealed validation fixture."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"


def _load_change4_module():
    spec = importlib.util.spec_from_file_location(
        "change4_alignment_diagnostic_blind_scoring",
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


def _error_metrics(predictions: np.ndarray, targets: np.ndarray) -> dict:
    delta = predictions - targets
    return {
        "mae": float(np.mean(np.abs(delta))),
        "rmse": float(np.sqrt(np.mean(delta**2))),
        "max_abs_error": float(np.max(np.abs(delta))),
    }


def score_prediction_bundle(predictions_path: Path, revealed_path: Path) -> dict:
    change4 = _load_change4_module()
    cst_module = change4._load_module()
    locked_change4 = change4.build_change4_alignment_diagnostic()

    prediction_bundle = json.loads(predictions_path.read_text(encoding="utf-8"))
    revealed_records = json.loads(revealed_path.read_text(encoding="utf-8"))
    revealed_by_id = {record["id"]: record for record in revealed_records}

    merged = []
    for prediction in prediction_bundle["predictions"]:
        record = revealed_by_id[prediction["id"]]
        target_scalar = float(cst_module._normalize_gcr_scalar(record))
        merged.append(
            {
                "id": prediction["id"],
                "normalized_target": target_scalar,
                "model_phase_proxy_scalar": float(prediction["model_phase_proxy_scalar"]),
                "legacy_heuristic_scalar": float(prediction["legacy_heuristic_scalar"]),
                "learned_calibrator_scalar": float(prediction["learned_calibrator_scalar"]),
                "observed_value": change4._observed_value(record),
                "model_phase_proxy_raw_prediction": prediction["model_phase_proxy_raw_prediction"],
                "legacy_heuristic_raw_prediction": prediction["legacy_heuristic_raw_prediction"],
                "learned_calibrator_raw_prediction": prediction["learned_calibrator_raw_prediction"],
            }
        )

    targets = np.array([record["normalized_target"] for record in merged], dtype=float)
    change4_targets = np.array(
        [record["normalized_target"] for record in locked_change4["records"]],
        dtype=float,
    )
    change4_weights = np.array(
        [record["weight"] for record in locked_change4["records"]],
        dtype=float,
    )
    baselines = {}
    for name, field in {
        "model_phase_proxy": "model_phase_proxy_scalar",
        "legacy_heuristic_proxy": "legacy_heuristic_scalar",
        "learned_calibrator_proxy": "learned_calibrator_scalar",
    }.items():
        predictions = np.array([record[field] for record in merged], dtype=float)
        baselines[name] = {
            "predictions": [float(value) for value in predictions.tolist()],
            **_error_metrics(predictions, targets),
        }

    midpoint = np.full(len(merged), 0.5, dtype=float)
    lunar_mean = np.full(len(merged), float(np.mean(change4_targets)), dtype=float)
    lunar_weighted_mean = np.full(
        len(merged),
        float(np.average(change4_targets, weights=change4_weights)),
        dtype=float,
    )
    for name, predictions in {
        "midpoint_0_5": midpoint,
        "lunar_bundle_mean": lunar_mean,
        "lunar_bundle_weighted_mean": lunar_weighted_mean,
    }.items():
        baselines[name] = {
            "predictions": [float(value) for value in predictions.tolist()],
            **_error_metrics(predictions, targets),
        }

    best_mae_value = min(metrics["mae"] for metrics in baselines.values())
    best_rmse_value = min(metrics["rmse"] for metrics in baselines.values())

    return {
        "label": prediction_bundle.get("label", predictions_path.stem),
        "predictions_path": str(predictions_path),
        "predictions_sha256": _sha256(predictions_path),
        "revealed_path": str(revealed_path),
        "revealed_sha256": _sha256(revealed_path),
        "reproducibility": {
            "command": (
                "python scripts/score_blind_validation_predictions.py "
                f"--predictions {predictions_path} --revealed {revealed_path} --output <output>"
            ),
            "python_version": sys.version.split()[0],
        },
        "baselines": baselines,
        "best_mae_baselines": [
            name
            for name, metrics in baselines.items()
            if abs(metrics["mae"] - best_mae_value) <= 1e-12
        ],
        "best_rmse_baselines": [
            name
            for name, metrics in baselines.items()
            if abs(metrics["rmse"] - best_rmse_value) <= 1e-12
        ],
        "records": merged,
    }


def write_scoring_bundle(output_path: Path, bundle: dict) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True, help="Path to the prediction bundle JSON.")
    parser.add_argument("--revealed", type=Path, required=True, help="Path to the revealed reference fixture JSON.")
    parser.add_argument("--output", type=Path, required=True, help="Where to write the scoring bundle JSON.")
    args = parser.parse_args()

    bundle = score_prediction_bundle(args.predictions, args.revealed)
    output_path = write_scoring_bundle(args.output, bundle)
    print(f"Scoring bundle: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
