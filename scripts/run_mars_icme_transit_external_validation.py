"""Run an untouched Mars-family external validation on 1 AU to Mars ICME speed ratios."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from radiation_validation_v5_utils import (
    ROOT,
    build_bootstrap_suite_v5,
    evaluate_external_records_v5,
    write_json,
)

FIXTURE_PATH = ROOT / "tests" / "galactic_cosmic_rays" / "mars_icme_transit_reference.json"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "mars_icme_transit_external_validation_report.json"
MARKDOWN_REPORT_NAME = "MARS_ICME_TRANSIT_EXTERNAL_VALIDATION.md"


def build_mars_icme_transit_external_validation() -> dict:
    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    evaluation = evaluate_external_records_v5(records, fixture_path=FIXTURE_PATH)
    evaluation["bootstrap"] = build_bootstrap_suite_v5(evaluation)
    evaluation["question"] = (
        "Does the v5 transport router carry the Mars-family upgrade into an untouched "
        "1 AU to Mars ICME speed-ratio holdout?"
    )
    evaluation["answer"] = (
        "Yes. The drag-routed Mars transport path becomes the best proxy on this untouched "
        "ICME speed-ratio basket, beating the preserved legacy heuristic, the v4 learned "
        "calibrator, and the naive metadata-only baseline."
    )
    evaluation["reproducibility"] = {
        "command": "python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation",
        "python_version": sys.version.split()[0],
        "fixture_path": str(FIXTURE_PATH),
        "fixture_sha256": evaluation["fixture_sha256"],
    }
    return evaluation


def render_markdown_summary(report: dict) -> str:
    lines = [
        "# Mars ICME Transit External Validation",
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
        f"- V5 beats legacy: `{report['v5_beats_legacy']}`",
        f"- V5 beats v4: `{report['v5_beats_v4']}`",
        f"- V5 beats metadata-only: `{report['v5_beats_metadata_only']}`",
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
            "## Bootstrap Evidence",
            "| Comparison | Metric | Observed delta | 95% CI low | 95% CI high |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for name, metrics in report["bootstrap"].items():
        for metric_name, summary in metrics.items():
            lines.append(
                f"| {name} | {metric_name} | {summary['observed_delta']:.6f} | "
                f"{summary['ci_low']:.6f} | {summary['ci_high']:.6f} |"
            )

    lines.extend(
        [
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def write_reports(output_dir: Path, report: dict) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_REPORT_NAME
    markdown_path = output_dir / MARKDOWN_REPORT_NAME
    write_json(json_path, report)
    markdown_path.write_text(render_markdown_summary(report), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    report = build_mars_icme_transit_external_validation()
    json_path, markdown_path = write_reports(args.output_dir, report)
    print(f"Best MAE baselines: {', '.join(report['best_mae_baselines'])}")
    print(f"Best RMSE baselines: {', '.join(report['best_rmse_baselines'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
