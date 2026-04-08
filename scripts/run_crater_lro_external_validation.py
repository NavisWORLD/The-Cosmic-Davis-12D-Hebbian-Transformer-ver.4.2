"""Run a supplementary external validation on the CRaTER/LRO lunar radiation basket."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_SCRIPT = ROOT / "scripts" / "run_change4_alignment_diagnostic.py"
FIXTURE_PATH = ROOT / "tests" / "galactic_cosmic_rays" / "crater_lro_reference.json"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "crater_lro_external_validation_report.json"
MARKDOWN_REPORT_NAME = "CRATER_LRO_EXTERNAL_VALIDATION.md"


def _load_change4_module():
    spec = importlib.util.spec_from_file_location(
        "change4_alignment_diagnostic_crater",
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


def build_crater_lro_external_validation() -> dict:
    change4 = _load_change4_module()
    cst_module = change4._load_module()
    locked_change4 = change4.build_change4_alignment_diagnostic()
    calibrator = cst_module.load_learned_observable_calibrator()

    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    state_vector = cst_module.default_validation_state_vector()
    alignment = cst_module.galactic_cosmic_ray_alignment(state_vector, records)

    targets = np.array([cst_module._normalize_gcr_scalar(record) for record in records], dtype=float)
    phase_proxy = np.full(len(records), float(locked_change4["model"]["phase_proxy_clamped"]), dtype=float)
    legacy = np.array(
        [cst_module.predict_legacy_observable_scalar(state_vector, record) for record in records],
        dtype=float,
    )
    learned = np.array(
        [
            cst_module.predict_change4_observable_scalar(
                state_vector,
                record,
                calibrator=calibrator,
            )
            for record in records
        ],
        dtype=float,
    )
    midpoint = np.full(len(records), 0.5, dtype=float)

    baselines = {
        "model_phase_proxy": {
            "predictions": [float(value) for value in phase_proxy.tolist()],
            **_error_metrics(phase_proxy, targets),
        },
        "legacy_heuristic_proxy": {
            "predictions": [float(value) for value in legacy.tolist()],
            **_error_metrics(legacy, targets),
        },
        "learned_calibrator_proxy": {
            "predictions": [float(value) for value in learned.tolist()],
            **_error_metrics(learned, targets),
        },
        "midpoint_0_5": {
            "predictions": [float(value) for value in midpoint.tolist()],
            **_error_metrics(midpoint, targets),
        },
    }

    records_out = []
    for index, record in enumerate(records):
        records_out.append(
            {
                "id": record["id"],
                "published_date": record["published_date"],
                "source": record["source"],
                "source_url": record["source_url"],
                "units": record.get("units", "unitless"),
                "notes": record.get("notes", ""),
                "normalized_target": float(targets[index]),
                "observed_value": change4._observed_value(record),
                "legacy_heuristic_prediction": float(legacy[index]),
                "learned_calibrator_prediction": float(learned[index]),
                "legacy_heuristic_raw_prediction": change4._predicted_value_from_scalar(record, legacy[index]),
                "learned_calibrator_raw_prediction": change4._predicted_value_from_scalar(record, learned[index]),
            }
        )

    return {
        "question": (
            "How does the locked learned calibrator transfer to a supplementary "
            "CRaTER/LRO lunar radiation basket that was not used in the original "
            "Chang'e-4 alignment work?"
        ),
        "answer": (
            "The learned calibrator slightly beats the preserved legacy heuristic on "
            "MAE, but it does not win RMSE against the simple midpoint baseline."
        ),
        "external_alignment": {
            "official_overall_alignment": float(alignment.overall_alignment),
            "official_cosine_similarity": float(alignment.cosine_similarity),
            "official_phase_distance": float(alignment.phase_distance),
        },
        "baselines": baselines,
        "best_mae_baselines": _best_baseline_names(baselines, "mae"),
        "best_rmse_baselines": _best_baseline_names(baselines, "rmse"),
        "records": records_out,
        "reproducibility": {
            "command": "python scripts/run_crater_lro_external_validation.py --output-dir docs/validation",
            "python_version": sys.version.split()[0],
            "fixture_path": str(FIXTURE_PATH),
            "fixture_sha256": _sha256(FIXTURE_PATH),
        },
    }


def render_markdown_summary(report: dict) -> str:
    lines = [
        "# CRaTER/LRO External Validation",
        "",
        "## Summary",
        report["question"],
        report["answer"],
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
            "| Record | Target | Legacy heuristic | Learned calibrator |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for record in report["records"]:
        lines.append(
            f"| {record['id']} | {record['normalized_target']:.6f} | "
            f"{record['legacy_heuristic_prediction']:.6f} | {record['learned_calibrator_prediction']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_crater_lro_external_validation.py --output-dir docs/validation",
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
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    report = build_crater_lro_external_validation()
    json_path, markdown_path = write_reports(args.output_dir, report)
    print(f"Best MAE baselines: {', '.join(report['best_mae_baselines'])}")
    print(f"Best RMSE baselines: {', '.join(report['best_rmse_baselines'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
