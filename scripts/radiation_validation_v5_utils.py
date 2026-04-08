"""Shared helpers for the v5 radiation transport validation stack."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from radiation_validation_v4_utils import (
    ROOT,
    best_baseline_names,
    build_ablation_states,
    error_metrics,
    fit_metadata_only_ridge,
    load_change4_module,
    load_cst_module,
    load_locked_change4,
    predict_metadata_only,
    score_extended_blind_prediction_bundle,
    sha256,
    write_json,
)


def evaluate_external_records_v5(
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
    learned_v4_batch = cst_module.predict_observable_batch_scalars(
        state_vector,
        records,
        calibrator=calibrator,
    )
    learned_v4 = np.array([float(learned_v4_batch[record["id"]]) for record in records], dtype=float)
    v5_batch = cst_module.predict_v5_observable_batch_scalars(
        state_vector,
        records,
        calibrator=calibrator,
    )
    v5 = np.array([float(v5_batch[record["id"]]) for record in records], dtype=float)
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
        "learned_v4_calibrator_proxy": {
            "predictions": [float(value) for value in learned_v4.tolist()],
            **error_metrics(learned_v4, targets),
        },
        "v5_transport_router_proxy": {
            "predictions": [float(value) for value in v5.tolist()],
            **error_metrics(v5, targets),
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
        ablated_batch = cst_module.predict_v5_observable_batch_scalars(
            ablated_state,
            records,
            calibrator=calibrator,
        )
        predictions = np.array(
            [float(ablated_batch[record["id"]]) for record in records],
            dtype=float,
        )
        baselines[name.replace("learned_", "v5_")] = {
            "predictions": [float(value) for value in predictions.tolist()],
            **error_metrics(predictions, targets),
        }

    family_names = {"legacy_heuristic_proxy", "learned_v4_calibrator_proxy", "v5_transport_router_proxy"}
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
                "learned_v4_prediction": float(learned_v4[index]),
                "v5_transport_router_prediction": float(v5[index]),
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
        "v5_beats_legacy": bool(
            baselines["v5_transport_router_proxy"]["mae"] < baselines["legacy_heuristic_proxy"]["mae"]
            and baselines["v5_transport_router_proxy"]["rmse"] < baselines["legacy_heuristic_proxy"]["rmse"]
        ),
        "v5_beats_v4": bool(
            baselines["v5_transport_router_proxy"]["mae"] < baselines["learned_v4_calibrator_proxy"]["mae"]
            and baselines["v5_transport_router_proxy"]["rmse"] < baselines["learned_v4_calibrator_proxy"]["rmse"]
        ),
        "v5_beats_midpoint": bool(
            baselines["v5_transport_router_proxy"]["mae"] < baselines["midpoint_0_5"]["mae"]
            and baselines["v5_transport_router_proxy"]["rmse"] < baselines["midpoint_0_5"]["rmse"]
        ),
        "v5_beats_metadata_only": bool(
            baselines["v5_transport_router_proxy"]["mae"] < baselines["metadata_only_ridge"]["mae"]
            and baselines["v5_transport_router_proxy"]["rmse"] < baselines["metadata_only_ridge"]["rmse"]
        ),
        "family_led": bool(set(best_mae).issubset(family_names) and set(best_rmse).issubset(family_names)),
        "family_beats_naive_and_metadata": bool(
            min(
                baselines["legacy_heuristic_proxy"]["mae"],
                baselines["learned_v4_calibrator_proxy"]["mae"],
                baselines["v5_transport_router_proxy"]["mae"],
            ) < baselines["midpoint_0_5"]["mae"]
            and min(
                baselines["legacy_heuristic_proxy"]["rmse"],
                baselines["learned_v4_calibrator_proxy"]["rmse"],
                baselines["v5_transport_router_proxy"]["rmse"],
            ) < baselines["midpoint_0_5"]["rmse"]
            and min(
                baselines["legacy_heuristic_proxy"]["mae"],
                baselines["learned_v4_calibrator_proxy"]["mae"],
                baselines["v5_transport_router_proxy"]["mae"],
            ) < baselines["metadata_only_ridge"]["mae"]
            and min(
                baselines["legacy_heuristic_proxy"]["rmse"],
                baselines["learned_v4_calibrator_proxy"]["rmse"],
                baselines["v5_transport_router_proxy"]["rmse"],
            ) < baselines["metadata_only_ridge"]["rmse"]
        ),
        "records": records_out,
    }


def build_bootstrap_suite_v5(report: dict, n_boot: int = 10000, seed: int = 12) -> dict[str, dict[str, dict[str, float]]]:
    targets = np.array(report["targets"], dtype=float)
    baselines = report["baselines"]
    rng = np.random.default_rng(seed)
    n = len(targets)
    if n == 0:
        empty = {"observed_delta": 0.0, "ci_low": 0.0, "ci_high": 0.0}
        return {
            "v5_vs_legacy": {"mae": empty, "rmse": empty},
            "v5_vs_v4": {"mae": empty, "rmse": empty},
            "v5_vs_metadata_only": {"mae": empty, "rmse": empty},
            "v5_vs_phase_only_ablation": {"mae": empty, "rmse": empty},
        }

    indices = rng.integers(0, n, size=(n_boot, n))

    def metric_delta(left_name: str, right_name: str, metric: str) -> dict[str, float]:
        left = np.array(baselines[left_name]["predictions"], dtype=float)
        right = np.array(baselines[right_name]["predictions"], dtype=float)
        boot_left = left[indices]
        boot_right = right[indices]
        boot_targets = targets[indices]
        if metric == "mae":
            boot_delta = np.mean(np.abs(boot_left - boot_targets), axis=1) - np.mean(np.abs(boot_right - boot_targets), axis=1)
            observed = float(np.mean(np.abs(left - targets)) - np.mean(np.abs(right - targets)))
        else:
            boot_delta = np.sqrt(np.mean((boot_left - boot_targets) ** 2, axis=1)) - np.sqrt(np.mean((boot_right - boot_targets) ** 2, axis=1))
            observed = float(np.sqrt(np.mean((left - targets) ** 2)) - np.sqrt(np.mean((right - targets) ** 2)))
        return {
            "observed_delta": observed,
            "ci_low": float(np.quantile(boot_delta, 0.025)),
            "ci_high": float(np.quantile(boot_delta, 0.975)),
        }

    pairs = {
        "v5_vs_legacy": ("v5_transport_router_proxy", "legacy_heuristic_proxy"),
        "v5_vs_v4": ("v5_transport_router_proxy", "learned_v4_calibrator_proxy"),
        "v5_vs_metadata_only": ("v5_transport_router_proxy", "metadata_only_ridge"),
        "v5_vs_phase_only_ablation": ("v5_transport_router_proxy", "v5_phase_only_ablation"),
    }
    suite = {}
    for key, (left, right) in pairs.items():
        suite[key] = {
            "mae": metric_delta(left, right, "mae"),
            "rmse": metric_delta(left, right, "rmse"),
        }
    return suite


def build_extended_blind_prediction_bundle_v5(template_path: Path, label: str) -> dict:
    cst_module = load_cst_module()
    locked_change4 = load_locked_change4()
    calibrator = cst_module.load_learned_observable_calibrator()
    metadata_model = fit_metadata_only_ridge()
    state_vector = cst_module.default_validation_state_vector()
    template_records = json.loads(template_path.read_text(encoding="utf-8"))

    learned_v4_batch = cst_module.predict_observable_batch_scalars(
        state_vector,
        template_records,
        calibrator=calibrator,
    )
    v5_batch = cst_module.predict_v5_observable_batch_scalars(
        state_vector,
        template_records,
        calibrator=calibrator,
    )
    metadata_predictions = predict_metadata_only(template_records, metadata_model)
    ablation_predictions = {}
    for name, ablated_state in build_ablation_states(state_vector).items():
        batch = cst_module.predict_v5_observable_batch_scalars(
            ablated_state,
            template_records,
            calibrator=calibrator,
        )
        ablation_predictions[name.replace("learned_", "v5_")] = {
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
            "learned_v4_calibrator_proxy": float(learned_v4_batch[record["id"]]),
            "v5_transport_router_proxy": float(v5_batch[record["id"]]),
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


__all__ = [
    "ROOT",
    "build_bootstrap_suite_v5",
    "build_extended_blind_prediction_bundle_v5",
    "evaluate_external_records_v5",
    "score_extended_blind_prediction_bundle",
    "sha256",
    "write_json",
]
