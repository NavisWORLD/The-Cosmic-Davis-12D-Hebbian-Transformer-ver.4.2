"""Run an independent MSL/RAD external stress test for the learned calibrator."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
FIXTURE_PATH = ROOT / "tests" / "galactic_cosmic_rays" / "msl_rad_reference.json"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "msl_rad_external_validation_report.json"
MARKDOWN_REPORT_NAME = "MSL_RAD_EXTERNAL_VALIDATION.md"


def _load_change4_module():
    spec = importlib.util.spec_from_file_location(
        "change4_alignment_diagnostic_msl",
        CHANGE4_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {CHANGE4_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _error_metrics(predictions: np.ndarray, targets: np.ndarray) -> dict:
    delta = predictions - targets
    return {
        "mae": float(np.mean(np.abs(delta))),
        "rmse": float(np.sqrt(np.mean(delta**2))),
        "max_abs_error": float(np.max(np.abs(delta))),
    }


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _best_baseline_names(baselines: dict, metric: str, tol: float = 1e-12) -> list[str]:
    best_value = min(values[metric] for values in baselines.values())
    return [
        name
        for name, values in baselines.items()
        if abs(values[metric] - best_value) <= tol
    ]


def build_msl_rad_external_validation() -> dict:
    change4 = _load_change4_module()
    cst_module = change4._load_module()
    locked_change4 = change4.build_change4_alignment_diagnostic()
    calibrator = cst_module.load_learned_observable_calibrator()

    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    state_vector = cst_module.default_validation_state_vector()
    alignment = cst_module.galactic_cosmic_ray_alignment(state_vector, records)
    learned_batch = cst_module.predict_observable_batch_scalars(
        state_vector,
        records,
        calibrator=calibrator,
    )

    targets = np.array([cst_module._normalize_gcr_scalar(record) for record in records], dtype=float)
    phase_proxy = np.full(len(records), float(locked_change4["model"]["phase_proxy_clamped"]), dtype=float)
    legacy_heuristic = np.array(
        [cst_module.predict_legacy_observable_scalar(state_vector, record) for record in records],
        dtype=float,
    )
    learned_calibrator = np.array(
        [float(learned_batch[record["id"]]) for record in records],
        dtype=float,
    )
    midpoint = np.full(len(records), 0.5, dtype=float)

    calibration_targets = np.array(
        [record["normalized_target"] for record in locked_change4["records"]],
        dtype=float,
    )
    calibration_weights = np.array(
        [record["weight"] for record in locked_change4["records"]],
        dtype=float,
    )
    calibration_mean = float(np.mean(calibration_targets))
    calibration_weighted_mean = float(np.average(calibration_targets, weights=calibration_weights))

    baselines = {
        "model_phase_proxy": {
            "predictions": [float(value) for value in phase_proxy.tolist()],
            **_error_metrics(phase_proxy, targets),
        },
        "legacy_heuristic_proxy": {
            "predictions": [float(value) for value in legacy_heuristic.tolist()],
            **_error_metrics(legacy_heuristic, targets),
        },
        "learned_calibrator_proxy": {
            "predictions": [float(value) for value in learned_calibrator.tolist()],
            **_error_metrics(learned_calibrator, targets),
        },
        "midpoint_0_5": {
            "predictions": [float(value) for value in midpoint.tolist()],
            **_error_metrics(midpoint, targets),
        },
        "lunar_bundle_mean": {
            "predictions": [calibration_mean] * len(records),
            **_error_metrics(np.full(len(records), calibration_mean, dtype=float), targets),
        },
        "lunar_bundle_weighted_mean": {
            "predictions": [calibration_weighted_mean] * len(records),
            **_error_metrics(np.full(len(records), calibration_weighted_mean, dtype=float), targets),
        },
    }

    best_mae = _best_baseline_names(baselines, "mae")
    best_rmse = _best_baseline_names(baselines, "rmse")
    learned_generalizes_here = (
        "learned_calibrator_proxy" in best_mae
        and "learned_calibrator_proxy" in best_rmse
    )

    per_record = []
    for index, record in enumerate(records):
        target = float(targets[index])
        observed_value = change4._observed_value(record)
        per_record.append(
            {
                "id": record["id"],
                "published_date": record["published_date"],
                "source": record["source"],
                "source_url": record["source_url"],
                "units": record.get("units", "unitless"),
                "notes": record.get("notes", ""),
                "normalized_target": target,
                "observed_value": observed_value,
                "phase_proxy_prediction": float(phase_proxy[index]),
                "phase_proxy_predicted_value": change4._predicted_value_from_scalar(record, phase_proxy[index]),
                "phase_proxy_delta": float(phase_proxy[index] - target),
                "legacy_heuristic_prediction": float(legacy_heuristic[index]),
                "legacy_heuristic_predicted_value": change4._predicted_value_from_scalar(record, legacy_heuristic[index]),
                "legacy_heuristic_delta": float(legacy_heuristic[index] - target),
                "learned_calibrator_prediction": float(learned_calibrator[index]),
                "learned_calibrator_predicted_value": change4._predicted_value_from_scalar(record, learned_calibrator[index]),
                "learned_calibrator_delta": float(learned_calibrator[index] - target),
            }
        )

    return {
        "reproducibility": {
            "command": "python scripts/run_msl_rad_external_validation.py --output-dir docs/validation",
            "python_version": sys.version.split()[0],
            "fixture_path": str(FIXTURE_PATH),
            "fixture_sha256": _sha256(FIXTURE_PATH),
            "learned_calibrator_bundle": locked_change4["model"]["learned_calibrator"],
        },
        "question": (
            "Does the learned calibrator, trained on the locked Chang'e-4 + Artemis I "
            "bundle, generalize to an independent MSL/RAD Mars surface-to-cruise basket?"
        ),
        "answer": (
            "Yes. The learned calibrator is the best MAE and RMSE baseline on the "
            "independent MSL/RAD basket."
            if learned_generalizes_here
            else "Not yet. The learned calibrator transfers more structure than the "
            "legacy heuristic, but simple midpoint and lunar-bundle mean baselines "
            "still win on the independent MSL/RAD basket."
        ),
        "external_alignment": {
            "official_overall_alignment": float(alignment.overall_alignment),
            "official_cosine_similarity": float(alignment.cosine_similarity),
            "official_phase_distance": float(alignment.phase_distance),
        },
        "locked_lunar_context": {
            "phase_proxy_clamped": float(locked_change4["model"]["phase_proxy_clamped"]),
            "lunar_bundle_mean": calibration_mean,
            "lunar_bundle_weighted_mean": calibration_weighted_mean,
            "change4_alignment": float(locked_change4["aggregate"]["official_overall_alignment"]),
        },
        "targets": [float(value) for value in targets.tolist()],
        "baselines": baselines,
        "best_mae_baselines": best_mae,
        "best_rmse_baselines": best_rmse,
        "learned_generalizes_here": learned_generalizes_here,
        "records": per_record,
    }


def render_markdown_summary(report: dict) -> str:
    lines = [
        "# MSL/RAD External Validation",
        "",
        "## Summary",
        report["question"],
        report["answer"],
        "",
        "This is the independent out-of-family stress test for the learned calibrator.",
        "",
        "## External Alignment",
        f"- Official overall alignment: `{report['external_alignment']['official_overall_alignment']:.6f}`",
        f"- Official cosine similarity: `{report['external_alignment']['official_cosine_similarity']:.6f}`",
        f"- Official phase distance: `{report['external_alignment']['official_phase_distance']:.6f}`",
        "",
        "## Baseline Comparison",
        f"- Best MAE baselines: `{', '.join(report['best_mae_baselines'])}`",
        f"- Best RMSE baselines: `{', '.join(report['best_rmse_baselines'])}`",
        "",
        "| Baseline | MAE | RMSE | Max abs error |",
        "| --- | ---: | ---: | ---: |",
    ]

    for name, metrics in report["baselines"].items():
        lines.append(
            f"| {name} | {metrics['mae']:.6f} | {metrics['rmse']:.6f} | {metrics['max_abs_error']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Record Diagnostics",
            "| Record | Target | Legacy heuristic | Learned calibrator | Observed raw | Learned raw |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for record in report["records"]:
        lines.append(
            "| "
            f"{record['id']} | "
            f"{record['normalized_target']:.6f} | "
            f"{record['legacy_heuristic_prediction']:.6f} | "
            f"{record['learned_calibrator_prediction']:.6f} | "
            f"{record['observed_value']:.6f} | "
            f"{record['learned_calibrator_predicted_value']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            (
                "The learned calibrator clears the independent MSL/RAD stress test."
                if report["learned_generalizes_here"]
                else "The learned calibrator does not clear the independent MSL/RAD stress test yet."
            ),
            (
                "That means the bundled lunar fit is not enough by itself to claim robust cross-mission prediction."
                if not report["learned_generalizes_here"]
                else "That is a stronger cross-mission result than the lunar-only bundle can show on its own."
            ),
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation",
            "python scripts/run_msl_rad_external_validation.py --output-dir docs/validation",
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
        help="Directory where JSON and Markdown reports will be written.",
    )
    args = parser.parse_args()

    report = build_msl_rad_external_validation()
    json_path, markdown_path = write_reports(args.output_dir, report)
    print(f"Best MAE baselines: {', '.join(report['best_mae_baselines'])}")
    print(f"Best RMSE baselines: {', '.join(report['best_rmse_baselines'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
