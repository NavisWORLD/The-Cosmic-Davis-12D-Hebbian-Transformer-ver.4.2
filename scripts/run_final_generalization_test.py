"""Run the final multi-dataset generalization gate for the locked proxy."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
EXTERNAL_SCRIPT = ROOT / "scripts" / "run_artemis_i_external_validation.py"
M42_FIXTURE = ROOT / "tests" / "galactic_cosmic_rays" / "artemis_i_m42_gcr_reference.json"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "final_generalization_test_report.json"
MARKDOWN_REPORT_NAME = "FINAL_GENERALIZATION_TEST.md"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    import hashlib

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


def _best_names(baselines: dict, metric: str, tol: float = 1e-12) -> list[str]:
    best_value = min(values[metric] for values in baselines.values())
    return [
        name
        for name, values in baselines.items()
        if abs(values[metric] - best_value) <= tol
    ]


def _evaluate_dataset(
    records: list[dict],
    module,
    phase_proxy: float,
    change4_mean: float,
    change4_weighted_mean: float,
    state_vector: np.ndarray,
    alignment: dict | None = None,
) -> dict:
    targets = np.array([module._normalize_gcr_scalar(record) for record in records], dtype=float)
    phase = np.full(len(records), phase_proxy, dtype=float)
    observable = np.array(
        [module.predict_change4_observable_scalar(state_vector, record) for record in records],
        dtype=float,
    )
    midpoint = np.full(len(records), 0.5, dtype=float)
    reference_mean = np.full(len(records), change4_mean, dtype=float)
    weighted_mean = np.full(len(records), change4_weighted_mean, dtype=float)

    baselines = {
        "model_phase_proxy": {
            "predictions": [float(value) for value in phase.tolist()],
            **_error_metrics(phase, targets),
        },
        "observable_aware_proxy": {
            "predictions": [float(value) for value in observable.tolist()],
            **_error_metrics(observable, targets),
        },
        "midpoint_0_5": {
            "predictions": [float(value) for value in midpoint.tolist()],
            **_error_metrics(midpoint, targets),
        },
        "change4_reference_mean": {
            "predictions": [change4_mean] * len(records),
            **_error_metrics(reference_mean, targets),
        },
        "change4_weighted_mean": {
            "predictions": [change4_weighted_mean] * len(records),
            **_error_metrics(weighted_mean, targets),
        },
    }

    dataset = {
        "record_count": len(records),
        "targets": [float(value) for value in targets.tolist()],
        "baselines": baselines,
        "best_mae_baselines": _best_names(baselines, "mae"),
        "best_rmse_baselines": _best_names(baselines, "rmse"),
        "records": [
            {
                "id": record["id"],
                "published_date": record["published_date"],
                "normalized_target": float(targets[index]),
                "phase_proxy_prediction": float(phase[index]),
                "observable_aware_prediction": float(observable[index]),
            }
            for index, record in enumerate(records)
        ],
    }
    if alignment is not None:
        dataset["alignment"] = alignment
    return dataset


def build_final_generalization_test() -> dict:
    change4 = _load_module(CHANGE4_SCRIPT, "change4_alignment_final_gate")
    external = _load_module(EXTERNAL_SCRIPT, "artemis_external_final_gate")
    module = change4._load_module()

    locked_change4 = change4.build_change4_alignment_diagnostic()
    artemis_external = external.build_artemis_i_external_validation()

    m42_records = json.loads(M42_FIXTURE.read_text(encoding="utf-8"))
    state_vector = module.build_12d_state_vector(
        change4.DEFAULT_MODEL_INPUT,
        metrics=change4.DEFAULT_METRICS,
        dark_matter_w=change4.DEFAULT_DARK_MATTER_W,
    )
    m42_alignment = module.galactic_cosmic_ray_alignment(state_vector, m42_records)

    phase_proxy = float(locked_change4["model"]["phase_proxy_clamped"])
    change4_mean = float(locked_change4["dataset"]["reference_mean_scalar"])
    weights = np.array([record["weight"] for record in locked_change4["records"]], dtype=float)
    change4_targets = np.array([record["normalized_target"] for record in locked_change4["records"]], dtype=float)
    change4_weighted_mean = float(np.average(change4_targets, weights=weights))

    datasets = {
        "artemis_i_external_ratios": {
            "record_count": len(artemis_external["records"]),
            "targets": artemis_external["targets"],
            "baselines": artemis_external["baselines"],
            "best_mae_baselines": artemis_external["best_mae_baselines"],
            "best_rmse_baselines": artemis_external["best_rmse_baselines"],
            "alignment": artemis_external["external_alignment"],
        },
        "artemis_i_m42_gcr_organs": _evaluate_dataset(
            m42_records,
            module,
            phase_proxy,
            change4_mean,
            change4_weighted_mean,
            state_vector,
            alignment={
                "official_overall_alignment": float(m42_alignment.overall_alignment),
                "official_cosine_similarity": float(m42_alignment.cosine_similarity),
                "official_phase_distance": float(m42_alignment.phase_distance),
            },
        ),
    }

    generalizes = all(
        "observable_aware_proxy" in datasets[name]["best_mae_baselines"]
        and "observable_aware_proxy" in datasets[name]["best_rmse_baselines"]
        for name in datasets
    )

    combined_targets = np.concatenate(
        [np.array(datasets[name]["targets"], dtype=float) for name in datasets],
        axis=0,
    )
    combined_baselines = {}
    for baseline_name in [
        "model_phase_proxy",
        "observable_aware_proxy",
        "midpoint_0_5",
        "change4_reference_mean",
        "change4_weighted_mean",
    ]:
        predictions = np.concatenate(
            [
                np.array(datasets[name]["baselines"][baseline_name]["predictions"], dtype=float)
                for name in datasets
            ],
            axis=0,
        )
        combined_baselines[baseline_name] = {
            "predictions": [float(value) for value in predictions.tolist()],
            **_error_metrics(predictions, combined_targets),
        }

    return {
        "question": (
            "Does the locked observable-aware proxy generalize across all external lunar "
            "datasets in this validation bundle?"
        ),
        "answer": (
            "No. It improves materially over the original constant phase proxy and even "
            "wins on the Artemis I organ-dose basket, but it still fails the stricter "
            "per-dataset generalization gate because it does not beat the carryover "
            "baselines on the Artemis ratio basket."
        ),
        "generalization_gate": {
            "rule": (
                "The observable-aware proxy must be among the best MAE and best RMSE "
                "baselines on every external dataset individually."
            ),
            "status": "not_generalized" if not generalizes else "generalized",
        },
        "locked_change4_context": {
            "change4_alignment": float(locked_change4["aggregate"]["official_overall_alignment"]),
            "phase_proxy_clamped": phase_proxy,
            "change4_reference_mean": change4_mean,
            "change4_weighted_mean": change4_weighted_mean,
        },
        "datasets": datasets,
        "combined_external_baselines": {
            "baselines": combined_baselines,
            "best_mae_baselines": _best_names(combined_baselines, "mae"),
            "best_rmse_baselines": _best_names(combined_baselines, "rmse"),
        },
        "reproducibility": {
            "command": "python scripts/run_final_generalization_test.py --output-dir docs/validation",
            "python_version": sys.version.split()[0],
            "m42_fixture_path": str(M42_FIXTURE),
            "m42_fixture_sha256": _sha256(M42_FIXTURE),
        },
    }


def render_markdown_summary(report: dict) -> str:
    lines = [
        "# Final Generalization Test",
        "",
        "## Summary",
        report["question"],
        report["answer"],
        "",
        f"- Gate status: `{report['generalization_gate']['status']}`",
        f"- Rule: {report['generalization_gate']['rule']}",
        "",
    ]

    for dataset_name, dataset in report["datasets"].items():
        lines.extend(
            [
                f"## {dataset_name}",
                f"- Best MAE baselines: `{', '.join(dataset['best_mae_baselines'])}`",
                f"- Best RMSE baselines: `{', '.join(dataset['best_rmse_baselines'])}`",
                "",
                "| Baseline | MAE | RMSE | Max abs error |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for baseline_name, metrics in dataset["baselines"].items():
            lines.append(
                f"| {baseline_name} | {metrics['mae']:.6f} | {metrics['rmse']:.6f} | {metrics['max_abs_error']:.6f} |"
            )
        lines.append("")

    combined = report["combined_external_baselines"]
    lines.extend(
        [
            "## Combined External View",
            f"- Best MAE baselines: `{', '.join(combined['best_mae_baselines'])}`",
            f"- Best RMSE baselines: `{', '.join(combined['best_rmse_baselines'])}`",
            "",
            "| Baseline | MAE | RMSE | Max abs error |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for baseline_name, metrics in combined["baselines"].items():
        lines.append(
            f"| {baseline_name} | {metrics['mae']:.6f} | {metrics['rmse']:.6f} | {metrics['max_abs_error']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            (
                "The combined picture is nuanced: the observable-aware proxy carries "
                "more physics than the constant phase proxy, but the final gate is "
                "deliberately conservative. Failing one external dataset means the "
                "bundle does not yet support a generalization claim."
            ),
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation",
            "python scripts/run_artemis_i_external_validation.py --output-dir docs/validation",
            "python scripts/run_final_generalization_test.py --output-dir docs/validation",
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

    report = build_final_generalization_test()
    json_path, markdown_path = write_reports(args.output_dir, report)
    print(f"Gate status: {report['generalization_gate']['status']}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
