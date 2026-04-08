"""Run held-out and baseline validation for the Chang'e-4/LND probe."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ALIGNMENT_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "change4_heldout_validation_report.json"
MARKDOWN_REPORT_NAME = "CHANGE4_HELDOUT_VALIDATION.md"


def _load_alignment_module():
    spec = importlib.util.spec_from_file_location(
        "change4_alignment_diagnostic_module",
        ALIGNMENT_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load diagnostic module from {ALIGNMENT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _error_metrics(predictions: np.ndarray, targets: np.ndarray) -> dict:
    delta = predictions - targets
    mae = float(np.mean(np.abs(delta)))
    rmse = float(np.sqrt(np.mean(delta**2)))
    max_abs_error = float(np.max(np.abs(delta)))
    return {
        "mae": mae,
        "rmse": rmse,
        "max_abs_error": max_abs_error,
    }


def _round_floats(values: list[float]) -> list[float]:
    return [float(value) for value in values]


def build_change4_heldout_validation() -> dict:
    module = _load_alignment_module()
    diagnostic = module.build_change4_alignment_diagnostic()
    records = diagnostic["records"]

    targets = np.array([record["normalized_target"] for record in records], dtype=float)
    weights = np.array([record["weight"] for record in records], dtype=float)
    model_predictions = np.array(
        [record["model_scalar_prediction"] for record in records],
        dtype=float,
    )
    observable_aware_predictions = np.array(
        [record["observable_aware_scalar_prediction"] for record in records],
        dtype=float,
    )
    midpoint_predictions = np.full_like(targets, 0.5)

    loo_mean_predictions = []
    loo_weighted_predictions = []
    for index in range(len(records)):
        mask = np.ones(len(records), dtype=bool)
        mask[index] = False
        loo_mean_predictions.append(float(np.mean(targets[mask])))
        loo_weighted_predictions.append(float(np.average(targets[mask], weights=weights[mask])))
    loo_mean_predictions = np.array(loo_mean_predictions, dtype=float)
    loo_weighted_predictions = np.array(loo_weighted_predictions, dtype=float)

    sorted_records = sorted(records, key=lambda record: (record["published_date"], record["id"]))
    sorted_targets = np.array([record["normalized_target"] for record in sorted_records], dtype=float)
    sorted_weights = np.array([record["weight"] for record in sorted_records], dtype=float)
    sorted_model_predictions = np.array(
        [record["model_scalar_prediction"] for record in sorted_records],
        dtype=float,
    )
    sorted_observable_aware_predictions = np.array(
        [record["observable_aware_scalar_prediction"] for record in sorted_records],
        dtype=float,
    )
    test_mask = np.array(
        [record["published_date"] >= "2026-01-01" for record in sorted_records],
        dtype=bool,
    )
    train_mask = ~test_mask
    if not bool(train_mask.any()) or not bool(test_mask.any()):
        raise RuntimeError("Chronological holdout requires both train and test records.")

    chronological_targets = sorted_targets[test_mask]
    chronological_model_predictions = sorted_model_predictions[test_mask]
    chronological_observable_aware_predictions = sorted_observable_aware_predictions[test_mask]
    train_mean = float(np.mean(sorted_targets[train_mask]))
    train_weighted_mean = float(
        np.average(sorted_targets[train_mask], weights=sorted_weights[train_mask])
    )
    chronological_midpoint = np.full_like(chronological_targets, 0.5)
    chronological_mean = np.full_like(chronological_targets, train_mean)
    chronological_weighted = np.full_like(chronological_targets, train_weighted_mean)

    leave_one_out = {
        "targets": _round_floats(targets.tolist()),
        "baselines": {
            "model_phase_proxy": {
                "predictions": _round_floats(model_predictions.tolist()),
                **_error_metrics(model_predictions, targets),
            },
            "observable_aware_proxy": {
                "predictions": _round_floats(observable_aware_predictions.tolist()),
                **_error_metrics(observable_aware_predictions, targets),
            },
            "midpoint_0_5": {
                "predictions": _round_floats(midpoint_predictions.tolist()),
                **_error_metrics(midpoint_predictions, targets),
            },
            "leave_one_out_mean": {
                "predictions": _round_floats(loo_mean_predictions.tolist()),
                **_error_metrics(loo_mean_predictions, targets),
            },
            "leave_one_out_weighted_mean": {
                "predictions": _round_floats(loo_weighted_predictions.tolist()),
                **_error_metrics(loo_weighted_predictions, targets),
            },
        },
    }

    chronological_holdout = {
        "train_records": [
            {
                "id": record["id"],
                "published_date": record["published_date"],
                "normalized_target": float(record["normalized_target"]),
            }
            for record in sorted_records
            if record["published_date"] < "2026-01-01"
        ],
        "test_records": [
            {
                "id": record["id"],
                "published_date": record["published_date"],
                "normalized_target": float(record["normalized_target"]),
            }
            for record in sorted_records
            if record["published_date"] >= "2026-01-01"
        ],
        "baselines": {
            "model_phase_proxy": {
                "predictions": _round_floats(chronological_model_predictions.tolist()),
                **_error_metrics(chronological_model_predictions, chronological_targets),
            },
            "observable_aware_proxy": {
                "predictions": _round_floats(chronological_observable_aware_predictions.tolist()),
                **_error_metrics(chronological_observable_aware_predictions, chronological_targets),
            },
            "midpoint_0_5": {
                "predictions": _round_floats(chronological_midpoint.tolist()),
                **_error_metrics(chronological_midpoint, chronological_targets),
            },
            "train_mean": {
                "predictions": _round_floats(chronological_mean.tolist()),
                "train_scalar": train_mean,
                **_error_metrics(chronological_mean, chronological_targets),
            },
            "train_weighted_mean": {
                "predictions": _round_floats(chronological_weighted.tolist()),
                "train_scalar": train_weighted_mean,
                **_error_metrics(chronological_weighted, chronological_targets),
            },
        },
    }

    def _best_baseline_name(section: dict, metric: str) -> str:
        return min(
            section["baselines"].items(),
            key=lambda item: item[1][metric],
        )[0]

    return {
        "reproducibility": {
            "command": "python scripts/run_change4_heldout_validation.py --output-dir docs/validation",
            "python_version": sys.version.split()[0],
            "alignment_report_dependency": "docs/validation/change4_alignment_report.json",
        },
        "source_alignment": {
            "official_overall_alignment": diagnostic["aggregate"]["official_overall_alignment"],
            "heuristic_band": diagnostic["aggregate"]["heuristic_band"],
            "fixture_sha256": diagnostic["dataset"]["fixture_sha256"],
        },
        "leave_one_out": {
            **leave_one_out,
            "best_mae_baseline": _best_baseline_name(leave_one_out, "mae"),
            "best_rmse_baseline": _best_baseline_name(leave_one_out, "rmse"),
        },
        "chronological_holdout_2026": {
            **chronological_holdout,
            "best_mae_baseline": _best_baseline_name(chronological_holdout, "mae"),
            "best_rmse_baseline": _best_baseline_name(chronological_holdout, "rmse"),
        },
    }


def render_markdown_summary(report: dict) -> str:
    loo = report["leave_one_out"]
    chrono = report["chronological_holdout_2026"]
    lines = [
        "# Chang'e-4 Held-Out Validation",
        "",
        "## Summary",
        (
            "This report asks the harder question: does the current 12D phase-proxy "
            "prediction beat simple baselines on held-out normalized Chang'e-4/LND targets?"
        ),
        (
            "Answer: the original constant phase proxy does not. A second "
            "observable-aware heuristic can reduce error sharply, but because it is "
            "a hand-authored, record-conditioned calibration, it should not be "
            "treated as independent predictive validation."
        ),
        "",
        "## Leave-One-Out Baselines",
        (
            "Each record is treated as held out while simple baselines are built from "
            "the remaining records."
        ),
        f"- Best MAE baseline: `{loo['best_mae_baseline']}`",
        f"- Best RMSE baseline: `{loo['best_rmse_baseline']}`",
        "",
        "| Baseline | MAE | RMSE | Max abs error |",
        "| --- | ---: | ---: | ---: |",
    ]

    for baseline_name, metrics in loo["baselines"].items():
        lines.append(
            f"| {baseline_name} | {metrics['mae']:.6f} | {metrics['rmse']:.6f} | {metrics['max_abs_error']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Chronological Holdout",
            (
                "Training-style baselines are fit only on the pre-2026 records "
                "and evaluated on the two 2026 cavity records."
            ),
            f"- Best MAE baseline: `{chrono['best_mae_baseline']}`",
            f"- Best RMSE baseline: `{chrono['best_rmse_baseline']}`",
            "",
            "| Baseline | MAE | RMSE | Max abs error |",
            "| --- | ---: | ---: | ---: |",
        ]
    )

    for baseline_name, metrics in chrono["baselines"].items():
        lines.append(
            f"| {baseline_name} | {metrics['mae']:.6f} | {metrics['rmse']:.6f} | {metrics['max_abs_error']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            (
                "This is the key distinction between correlation and prediction. "
                "The 12D probe still yields a nontrivial harmonic alignment score. "
                "The original constant phase proxy does not outperform simple "
                "baselines across the full dataset."
            ),
            (
                "The observable-aware proxy is useful as an engineering calibration "
                "layer, but because it is hand-shaped around observable families, it "
                "is still calibration rather than proof of prediction."
            ),
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation",
            "python scripts/run_change4_heldout_validation.py --output-dir docs/validation",
            "python -m pytest tests/galactic_cosmic_rays -q",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def write_reports(output_dir: Path, report: dict) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_REPORT_NAME
    markdown_path = output_dir / MARKDOWN_REPORT_NAME
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown_summary(report), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the JSON and Markdown reports will be written.",
    )
    args = parser.parse_args()

    report = build_change4_heldout_validation()
    json_path, markdown_path = write_reports(args.output_dir, report)
    loo = report["leave_one_out"]
    chrono = report["chronological_holdout_2026"]

    print(f"Leave-one-out best MAE baseline: {loo['best_mae_baseline']}")
    print(f"Leave-one-out best RMSE baseline: {loo['best_rmse_baseline']}")
    print(f"Chronological holdout best MAE baseline: {chrono['best_mae_baseline']}")
    print(f"Chronological holdout best RMSE baseline: {chrono['best_rmse_baseline']}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
