"""Run an external generalization check on Artemis I radiation data."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
FIXTURE_PATH = ROOT / "tests" / "galactic_cosmic_rays" / "artemis_i_unseen_reference.json"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "artemis_i_external_validation_report.json"
MARKDOWN_REPORT_NAME = "ARTEMIS_I_EXTERNAL_VALIDATION.md"


def _load_change4_module():
    spec = importlib.util.spec_from_file_location(
        "change4_alignment_diagnostic_external",
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


def build_artemis_i_external_validation() -> dict:
    change4 = _load_change4_module()
    module = change4._load_module()
    locked_change4 = change4.build_change4_alignment_diagnostic()

    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    state_vector = module.build_12d_state_vector(
        change4.DEFAULT_MODEL_INPUT,
        metrics=change4.DEFAULT_METRICS,
        dark_matter_w=change4.DEFAULT_DARK_MATTER_W,
    )
    alignment = module.galactic_cosmic_ray_alignment(state_vector, records)

    targets = np.array([module._normalize_gcr_scalar(record) for record in records], dtype=float)
    phase_proxy = np.full(len(records), float(locked_change4["model"]["phase_proxy_clamped"]), dtype=float)
    observable_aware = np.array(
        [module.predict_change4_observable_scalar(state_vector, record) for record in records],
        dtype=float,
    )
    midpoint = np.full(len(records), 0.5, dtype=float)

    change4_targets = np.array(
        [record["normalized_target"] for record in locked_change4["records"]],
        dtype=float,
    )
    change4_weights = np.array(
        [record["weight"] for record in locked_change4["records"]],
        dtype=float,
    )
    change4_mean = float(np.mean(change4_targets))
    change4_weighted_mean = float(np.average(change4_targets, weights=change4_weights))

    baselines = {
        "model_phase_proxy": {
            "predictions": [float(value) for value in phase_proxy.tolist()],
            **_error_metrics(phase_proxy, targets),
        },
        "observable_aware_proxy": {
            "predictions": [float(value) for value in observable_aware.tolist()],
            **_error_metrics(observable_aware, targets),
        },
        "midpoint_0_5": {
            "predictions": [float(value) for value in midpoint.tolist()],
            **_error_metrics(midpoint, targets),
        },
        "change4_reference_mean": {
            "predictions": [change4_mean] * len(records),
            **_error_metrics(np.full(len(records), change4_mean, dtype=float), targets),
        },
        "change4_weighted_mean": {
            "predictions": [change4_weighted_mean] * len(records),
            **_error_metrics(np.full(len(records), change4_weighted_mean, dtype=float), targets),
        },
    }

    best_mae = _best_baseline_names(baselines, "mae")
    best_rmse = _best_baseline_names(baselines, "rmse")
    generalized_here = "observable_aware_proxy" in best_mae and "observable_aware_proxy" in best_rmse

    per_record = []
    for index, record in enumerate(records):
        target = float(targets[index])
        phase_prediction = float(phase_proxy[index])
        observable_prediction = float(observable_aware[index])
        per_record.append(
            {
                "id": record["id"],
                "published_date": record["published_date"],
                "source": record["source"],
                "source_url": record["source_url"],
                "units": record.get("units", "unitless"),
                "notes": record.get("notes", ""),
                "normalized_target": target,
                "phase_proxy_prediction": phase_prediction,
                "phase_proxy_delta": float(phase_prediction - target),
                "observable_aware_prediction": observable_prediction,
                "observable_aware_delta": float(observable_prediction - target),
            }
        )

    return {
        "reproducibility": {
            "command": "python scripts/run_artemis_i_external_validation.py --output-dir docs/validation",
            "python_version": sys.version.split()[0],
            "fixture_path": str(FIXTURE_PATH),
            "fixture_sha256": _sha256(FIXTURE_PATH),
            "locked_change4_report_dependency": "docs/validation/change4_alignment_report.json",
        },
        "question": (
            "Does the locked Chang'e-4 calibrated proxy generalize to an unseen "
            "Artemis I lunar-radiation basket?"
        ),
        "answer": (
            "Yes, within this unseen Artemis I basket. The locked observable-aware "
            "proxy beats the constant phase proxy and the carryover baselines on both "
            "MAE and RMSE."
            if generalized_here
            else "Not yet. It improves over the constant phase proxy, but it does not "
            "beat the simplest carryover baselines on aggregate external error."
        ),
        "external_alignment": {
            "official_overall_alignment": float(alignment.overall_alignment),
            "official_cosine_similarity": float(alignment.cosine_similarity),
            "official_phase_distance": float(alignment.phase_distance),
        },
        "locked_change4_context": {
            "phase_proxy_clamped": float(locked_change4["model"]["phase_proxy_clamped"]),
            "change4_reference_mean": change4_mean,
            "change4_weighted_mean": change4_weighted_mean,
            "change4_alignment": float(locked_change4["aggregate"]["official_overall_alignment"]),
        },
        "targets": [float(value) for value in targets.tolist()],
        "baselines": baselines,
        "best_mae_baselines": best_mae,
        "best_rmse_baselines": best_rmse,
        "generalized_here": generalized_here,
        "records": per_record,
    }


def render_markdown_summary(report: dict) -> str:
    lines = [
        "# Artemis I External Validation",
        "",
        "## Summary",
        report["question"],
        report["answer"],
        "",
        "This uses an unseen external basket from the Artemis I mission, not the Chang'e-4/LND calibration basket.",
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
            "| Record | Target | Phase proxy | Obs-aware proxy | Phase delta | Obs-aware delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for record in report["records"]:
        lines.append(
            "| "
            f"{record['id']} | "
            f"{record['normalized_target']:.6f} | "
            f"{record['phase_proxy_prediction']:.6f} | "
            f"{record['observable_aware_prediction']:.6f} | "
            f"{record['phase_proxy_delta']:.6f} | "
            f"{record['observable_aware_delta']:.6f} |"
        )

    lines.extend(
        [
            "",
        "## Interpretation",
            (
                "This external Artemis I basket is the real cross-mission check. "
                "On the current code path, the locked observable-aware proxy wins "
                "the error comparison against the constant phase proxy and the "
                "carryover baselines."
            )
            if report["generalized_here"]
            else (
                "The external Artemis I basket is the harder test. The locked "
                "Chang'e-4 calibration carries some structure across missions, but "
                "its observable-aware proxy still does not win the aggregate error "
                "contest against the simplest carryover baselines."
            ),
            (
                "That is evidence of cross-mission generalization inside this checked-in "
                "bundle, although it is still best described as engineered generalization "
                "rather than universal proof."
            )
            if report["generalized_here"]
            else "That means we are not yet at a credible generalization claim.",
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation",
            "python scripts/run_artemis_i_external_validation.py --output-dir docs/validation",
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

    report = build_artemis_i_external_validation()
    json_path, markdown_path = write_reports(args.output_dir, report)
    print(f"Best MAE baselines: {', '.join(report['best_mae_baselines'])}")
    print(f"Best RMSE baselines: {', '.join(report['best_rmse_baselines'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
