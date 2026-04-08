"""Shared helpers for the v4 radiation validation stack."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=4)
def load_change4_module():
    return _load_module(CHANGE4_SCRIPT, "change4_alignment_diagnostic_v4_utils")


@lru_cache(maxsize=4)
def load_cst_module():
    return load_change4_module()._load_module()


@lru_cache(maxsize=4)
def load_locked_change4() -> dict:
    return load_change4_module().build_change4_alignment_diagnostic()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_training_records() -> list[dict]:
    cst_module = load_cst_module()
    calibrator = cst_module.load_learned_observable_calibrator()
    records: list[dict] = []
    for path_str in calibrator.get("calibration_paths", ()):
        path = Path(path_str)
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            records.extend(record for record in payload if isinstance(record, dict))
    return records


def _record_text(record: dict) -> str:
    return " ".join(
        [
            str(record.get("id", "")),
            str(record.get("units", "")),
            str(record.get("notes", "")),
        ]
    ).lower()


def _observable_scale_hint(record: dict) -> float:
    for key in ("denominator", "normalizer", "forecast"):
        if key in record:
            return float(math.log1p(abs(float(record.get(key, 0.0)))))
    return 0.0


def metadata_only_feature_names() -> tuple[str, ...]:
    cst_module = load_cst_module()
    names = [
        "bias",
        "has_ratio",
        "has_fraction_scale",
        "has_value",
        "has_current_forecast",
        "has_log_transform",
        "scale_hint_log",
    ]
    names.extend(f"kw_{keyword}" for keyword in cst_module.LEARNED_CALIBRATOR_KEYWORDS)
    return tuple(names)


def metadata_only_features(record: dict) -> np.ndarray:
    cst_module = load_cst_module()
    text = _record_text(record)
    values = [
        1.0,
        float("ratio" in record),
        float("numerator" in record and "denominator" in record),
        float("value" in record),
        float("current" in record and "forecast" in record),
        float(str(record.get("transform", "linear")).lower() == "log"),
        _observable_scale_hint(record),
    ]
    values.extend(float(keyword in text) for keyword in cst_module.LEARNED_CALIBRATOR_KEYWORDS)
    return np.asarray(values, dtype=float)


def fit_metadata_only_ridge(
    training_records: list[dict] | None = None,
    alpha: float = 0.2,
) -> dict[str, object]:
    cst_module = load_cst_module()
    records = list(load_training_records() if training_records is None else training_records)
    feature_names = metadata_only_feature_names()
    if not records:
        return {
            "type": "metadata_only_ridge",
            "alpha": float(alpha),
            "feature_names": feature_names,
            "coefficients": tuple([0.0] * len(feature_names)),
            "training_record_count": 0,
            "training_mae": 0.0,
            "training_rmse": 0.0,
        }

    X = np.vstack([metadata_only_features(record) for record in records])
    y = np.array([cst_module._normalize_gcr_scalar(record) for record in records], dtype=float)
    ridge = np.eye(X.shape[1], dtype=float)
    ridge[0, 0] = 0.0
    coefficients = np.linalg.pinv(X.T @ X + float(alpha) * ridge) @ X.T @ y
    predictions = np.clip(X @ coefficients, 0.0, 1.0)
    delta = predictions - y
    return {
        "type": "metadata_only_ridge",
        "alpha": float(alpha),
        "feature_names": feature_names,
        "coefficients": tuple(float(value) for value in coefficients.tolist()),
        "training_record_count": len(records),
        "training_mae": float(np.mean(np.abs(delta))),
        "training_rmse": float(np.sqrt(np.mean(delta**2))),
    }


def predict_metadata_only(records: list[dict], model: dict[str, object] | None = None) -> np.ndarray:
    active_model = fit_metadata_only_ridge() if model is None else model
    coefficients = np.asarray(active_model.get("coefficients", ()), dtype=float)
    if coefficients.size == 0:
        return np.zeros(len(records), dtype=float)
    X = np.vstack([metadata_only_features(record) for record in records])
    return np.clip(X @ coefficients, 0.0, 1.0)


def error_metrics(predictions: np.ndarray, targets: np.ndarray) -> dict[str, float]:
    delta = predictions - targets
    return {
        "mae": float(np.mean(np.abs(delta))),
        "rmse": float(np.sqrt(np.mean(delta**2))),
        "max_abs_error": float(np.max(np.abs(delta))),
    }


def best_baseline_names(baselines: dict[str, dict], metric: str, tol: float = 1e-12) -> list[str]:
    best_value = min(values[metric] for values in baselines.values())
    return [
        name
        for name, values in baselines.items()
        if abs(values[metric] - best_value) <= tol
    ]


def build_ablation_states(state_vector: np.ndarray) -> dict[str, np.ndarray]:
    phase_only = np.zeros_like(state_vector)
    phase_only[:4] = state_vector[:4]
    return {
        "learned_zero_state_ablation": np.zeros_like(state_vector),
        "learned_phase_only_ablation": phase_only,
        "learned_reversed_state_ablation": state_vector[::-1].copy(),
    }


def evaluate_external_records(
    records: list[dict],
    fixture_path: Path | None = None,
) -> dict:
    change4 = load_change4_module()
    cst_module = load_cst_module()
    locked_change4 = load_locked_change4()
    calibrator = cst_module.load_learned_observable_calibrator()
    metadata_model = fit_metadata_only_ridge()
    state_vector = cst_module.default_validation_state_vector()
    model_vector = cst_module._normalize_vector(cst_module._safe_array(state_vector, size=12))
    alignment = cst_module.galactic_cosmic_ray_alignment(state_vector, records)

    targets = np.array([cst_module._normalize_gcr_scalar(record) for record in records], dtype=float)
    phase_proxy = np.full(len(records), float(locked_change4["model"]["phase_proxy_clamped"]), dtype=float)
    legacy = np.array(
        [cst_module.predict_legacy_observable_scalar(state_vector, record) for record in records],
        dtype=float,
    )
    learned_batch = cst_module.predict_observable_batch_scalars(
        state_vector,
        records,
        calibrator=calibrator,
    )
    learned = np.array([float(learned_batch[record["id"]]) for record in records], dtype=float)
    midpoint = np.full(len(records), 0.5, dtype=float)
    calibration_targets = np.array(
        [record["normalized_target"] for record in locked_change4["records"]],
        dtype=float,
    )
    calibration_weights = np.array(
        [record["weight"] for record in locked_change4["records"]],
        dtype=float,
    )
    lunar_mean = np.full(len(records), float(np.mean(calibration_targets)), dtype=float)
    lunar_weighted = np.full(
        len(records),
        float(np.average(calibration_targets, weights=calibration_weights)),
        dtype=float,
    )
    metadata_only = predict_metadata_only(records, metadata_model)

    baselines: dict[str, dict] = {
        "model_phase_proxy": {
            "predictions": [float(value) for value in phase_proxy.tolist()],
            **error_metrics(phase_proxy, targets),
        },
        "legacy_heuristic_proxy": {
            "predictions": [float(value) for value in legacy.tolist()],
            **error_metrics(legacy, targets),
        },
        "learned_calibrator_proxy": {
            "predictions": [float(value) for value in learned.tolist()],
            **error_metrics(learned, targets),
        },
        "midpoint_0_5": {
            "predictions": [float(value) for value in midpoint.tolist()],
            **error_metrics(midpoint, targets),
        },
        "lunar_bundle_mean": {
            "predictions": [float(value) for value in lunar_mean.tolist()],
            **error_metrics(lunar_mean, targets),
        },
        "lunar_bundle_weighted_mean": {
            "predictions": [float(value) for value in lunar_weighted.tolist()],
            **error_metrics(lunar_weighted, targets),
        },
        "metadata_only_ridge": {
            "predictions": [float(value) for value in metadata_only.tolist()],
            **error_metrics(metadata_only, targets),
        },
    }

    for name, ablated_state in build_ablation_states(state_vector).items():
        ablated_batch = cst_module.predict_observable_batch_scalars(
            ablated_state,
            records,
            calibrator=calibrator,
        )
        predictions = np.array(
            [float(ablated_batch[record["id"]]) for record in records],
            dtype=float,
        )
        baselines[name] = {
            "predictions": [float(value) for value in predictions.tolist()],
            **error_metrics(predictions, targets),
        }

    family_names = {"learned_calibrator_proxy", "legacy_heuristic_proxy"}
    best_mae = best_baseline_names(baselines, "mae")
    best_rmse = best_baseline_names(baselines, "rmse")

    records_out = []
    for index, record in enumerate(records):
        observed_value = change4._observed_value(record)
        records_out.append(
            {
                "id": record["id"],
                "published_date": record.get("published_date", ""),
                "source": record.get("source", ""),
                "source_url": record.get("source_url", ""),
                "units": record.get("units", "unitless"),
                "notes": record.get("notes", ""),
                "normalized_target": float(targets[index]),
                "observed_value": observed_value,
                "phase_proxy_prediction": float(phase_proxy[index]),
                "legacy_heuristic_prediction": float(legacy[index]),
                "learned_calibrator_prediction": float(learned[index]),
                "metadata_only_prediction": float(metadata_only[index]),
            }
        )

    return {
        "fixture_path": str(fixture_path) if fixture_path is not None else "",
        "fixture_sha256": sha256(fixture_path) if fixture_path is not None else "",
        "model_vector": [float(value) for value in model_vector.tolist()],
        "external_alignment": {
            "official_overall_alignment": float(alignment.overall_alignment),
            "official_cosine_similarity": float(alignment.cosine_similarity),
            "official_phase_distance": float(alignment.phase_distance),
        },
        "metadata_only_ridge": metadata_model,
        "targets": [float(value) for value in targets.tolist()],
        "baselines": baselines,
        "best_mae_baselines": best_mae,
        "best_rmse_baselines": best_rmse,
        "learned_beats_midpoint": bool(
            baselines["learned_calibrator_proxy"]["mae"] < baselines["midpoint_0_5"]["mae"]
            and baselines["learned_calibrator_proxy"]["rmse"] < baselines["midpoint_0_5"]["rmse"]
        ),
        "learned_beats_metadata_only": bool(
            baselines["learned_calibrator_proxy"]["mae"] < baselines["metadata_only_ridge"]["mae"]
            and baselines["learned_calibrator_proxy"]["rmse"] < baselines["metadata_only_ridge"]["rmse"]
        ),
        "legacy_beats_midpoint": bool(
            baselines["legacy_heuristic_proxy"]["mae"] < baselines["midpoint_0_5"]["mae"]
            and baselines["legacy_heuristic_proxy"]["rmse"] < baselines["midpoint_0_5"]["rmse"]
        ),
        "legacy_beats_metadata_only": bool(
            baselines["legacy_heuristic_proxy"]["mae"] < baselines["metadata_only_ridge"]["mae"]
            and baselines["legacy_heuristic_proxy"]["rmse"] < baselines["metadata_only_ridge"]["rmse"]
        ),
        "family_led": bool(set(best_mae).issubset(family_names) and set(best_rmse).issubset(family_names)),
        "family_beats_naive_and_metadata": bool(
            min(
                baselines["learned_calibrator_proxy"]["mae"],
                baselines["legacy_heuristic_proxy"]["mae"],
            ) < baselines["midpoint_0_5"]["mae"]
            and min(
                baselines["learned_calibrator_proxy"]["rmse"],
                baselines["legacy_heuristic_proxy"]["rmse"],
            ) < baselines["midpoint_0_5"]["rmse"]
            and min(
                baselines["learned_calibrator_proxy"]["mae"],
                baselines["legacy_heuristic_proxy"]["mae"],
            ) < baselines["metadata_only_ridge"]["mae"]
            and min(
                baselines["learned_calibrator_proxy"]["rmse"],
                baselines["legacy_heuristic_proxy"]["rmse"],
            ) < baselines["metadata_only_ridge"]["rmse"]
        ),
        "records": records_out,
    }


def bootstrap_metric_delta(
    predictions_a: np.ndarray,
    predictions_b: np.ndarray,
    targets: np.ndarray,
    metric: str,
    n_boot: int = 10000,
    seed: int = 12,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = len(targets)
    if n == 0:
        return {"observed_delta": 0.0, "ci_low": 0.0, "ci_high": 0.0}
    indices = rng.integers(0, n, size=(n_boot, n))
    boot_a = predictions_a[indices]
    boot_b = predictions_b[indices]
    boot_t = targets[indices]
    if metric == "mae":
        boot_delta = np.mean(np.abs(boot_a - boot_t), axis=1) - np.mean(np.abs(boot_b - boot_t), axis=1)
        observed = float(np.mean(np.abs(predictions_a - targets)) - np.mean(np.abs(predictions_b - targets)))
    elif metric == "rmse":
        boot_delta = np.sqrt(np.mean((boot_a - boot_t) ** 2, axis=1)) - np.sqrt(np.mean((boot_b - boot_t) ** 2, axis=1))
        observed = float(np.sqrt(np.mean((predictions_a - targets) ** 2)) - np.sqrt(np.mean((predictions_b - targets) ** 2)))
    else:
        raise ValueError(f"Unsupported metric: {metric}")
    return {
        "observed_delta": observed,
        "ci_low": float(np.quantile(boot_delta, 0.025)),
        "ci_high": float(np.quantile(boot_delta, 0.975)),
    }


def build_bootstrap_suite(report: dict) -> dict[str, dict[str, dict[str, float]]]:
    baselines = report["baselines"]
    targets = np.array(report["targets"], dtype=float)
    pairs = {
        "learned_vs_metadata_only": ("learned_calibrator_proxy", "metadata_only_ridge"),
        "learned_vs_midpoint": ("learned_calibrator_proxy", "midpoint_0_5"),
        "learned_vs_phase_only_ablation": ("learned_calibrator_proxy", "learned_phase_only_ablation"),
        "learned_vs_zero_state_ablation": ("learned_calibrator_proxy", "learned_zero_state_ablation"),
        "learned_vs_legacy": ("learned_calibrator_proxy", "legacy_heuristic_proxy"),
    }
    suite: dict[str, dict[str, dict[str, float]]] = {}
    for key, (left, right) in pairs.items():
        left_predictions = np.array(baselines[left]["predictions"], dtype=float)
        right_predictions = np.array(baselines[right]["predictions"], dtype=float)
        suite[key] = {
            "mae": bootstrap_metric_delta(left_predictions, right_predictions, targets, "mae"),
            "rmse": bootstrap_metric_delta(left_predictions, right_predictions, targets, "rmse"),
        }
    return suite


def build_extended_blind_prediction_bundle(
    template_path: Path,
    label: str,
) -> dict:
    cst_module = load_cst_module()
    locked_change4 = load_locked_change4()
    calibrator = cst_module.load_learned_observable_calibrator()
    metadata_model = fit_metadata_only_ridge()
    state_vector = cst_module.default_validation_state_vector()
    template_records = json.loads(template_path.read_text(encoding="utf-8"))

    learned_batch = cst_module.predict_observable_batch_scalars(
        state_vector,
        template_records,
        calibrator=calibrator,
    )
    metadata_predictions = predict_metadata_only(template_records, metadata_model)
    ablation_predictions = {}
    for name, ablated_state in build_ablation_states(state_vector).items():
        batch = cst_module.predict_observable_batch_scalars(
            ablated_state,
            template_records,
            calibrator=calibrator,
        )
        ablation_predictions[name] = {
            record["id"]: float(batch[record["id"]])
            for record in template_records
        }

    phase_proxy = float(locked_change4["model"]["phase_proxy_clamped"])
    lunar_mean = float(np.mean([r["normalized_target"] for r in locked_change4["records"]]))
    lunar_weighted = float(
        np.average(
            [r["normalized_target"] for r in locked_change4["records"]],
            weights=[r["weight"] for r in locked_change4["records"]],
        )
    )
    predictions = []
    for index, record in enumerate(template_records):
        entry = {
            "id": record["id"],
            "published_date": record.get("published_date", ""),
            "source": record.get("source", ""),
            "source_url": record.get("source_url", ""),
            "units": record.get("units", "unitless"),
            "notes": record.get("notes", ""),
            "model_phase_proxy": phase_proxy,
            "legacy_heuristic_proxy": float(cst_module.predict_legacy_observable_scalar(state_vector, record)),
            "learned_calibrator_proxy": float(learned_batch[record["id"]]),
            "midpoint_0_5": 0.5,
            "lunar_bundle_mean": lunar_mean,
            "lunar_bundle_weighted_mean": lunar_weighted,
            "metadata_only_ridge": float(metadata_predictions[index]),
        }
        for name, prediction_map in ablation_predictions.items():
            entry[name] = prediction_map[record["id"]]
        predictions.append(entry)

    return {
        "label": label,
        "template_path": str(template_path),
        "template_sha256": sha256(template_path),
        "predictions": predictions,
    }


def score_extended_blind_prediction_bundle(
    prediction_bundle: dict,
    revealed_path: Path,
) -> dict:
    cst_module = load_cst_module()
    revealed_records = json.loads(revealed_path.read_text(encoding="utf-8"))
    revealed_by_id = {record["id"]: record for record in revealed_records}
    first_prediction = prediction_bundle["predictions"][0] if prediction_bundle["predictions"] else {}
    baseline_names = [
        key
        for key in first_prediction.keys()
        if key not in {"id", "published_date", "source", "source_url", "units", "notes"}
    ]

    merged = []
    for prediction in prediction_bundle["predictions"]:
        record = revealed_by_id[prediction["id"]]
        merged.append(
            {
                "id": prediction["id"],
                "normalized_target": float(cst_module._normalize_gcr_scalar(record)),
                **{name: float(prediction[name]) for name in baseline_names},
            }
        )

    targets = np.array([record["normalized_target"] for record in merged], dtype=float)
    baselines = {}
    for name in baseline_names:
        values = np.array([record[name] for record in merged], dtype=float)
        baselines[name] = {
            "predictions": [float(value) for value in values.tolist()],
            **error_metrics(values, targets),
        }

    return {
        "label": prediction_bundle["label"],
        "template_path": prediction_bundle["template_path"],
        "template_sha256": prediction_bundle["template_sha256"],
        "revealed_path": str(revealed_path),
        "revealed_sha256": sha256(revealed_path),
        "targets": [float(value) for value in targets.tolist()],
        "baselines": baselines,
        "best_mae_baselines": best_baseline_names(baselines, "mae"),
        "best_rmse_baselines": best_baseline_names(baselines, "rmse"),
    }


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
