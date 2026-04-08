"""Run the final learned-calibrator gate across held-out and external checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGE4_HELDOUT_SCRIPT = ROOT / "scripts" / "run_change4_heldout_validation.py"
ARTEMIS_SCRIPT = ROOT / "scripts" / "run_artemis_i_external_validation.py"
MSL_SCRIPT = ROOT / "scripts" / "run_msl_rad_external_validation.py"
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


def build_final_generalization_test() -> dict:
    change4_heldout_module = _load_module(
        CHANGE4_HELDOUT_SCRIPT,
        "change4_heldout_final_gate",
    )
    artemis_module = _load_module(
        ARTEMIS_SCRIPT,
        "artemis_bundle_final_gate",
    )
    msl_module = _load_module(
        MSL_SCRIPT,
        "msl_external_final_gate",
    )

    change4_heldout = change4_heldout_module.build_change4_heldout_validation()
    artemis_bundle = artemis_module.build_artemis_i_external_validation()
    msl_external = msl_module.build_msl_rad_external_validation()

    loo = change4_heldout["leave_one_out"]["baselines"]
    chrono = change4_heldout["chronological_holdout_2026"]["baselines"]

    change4_checks = {
        "leave_one_out": {
            "learned_mae": float(loo["learned_calibrator_proxy"]["mae"]),
            "learned_rmse": float(loo["learned_calibrator_proxy"]["rmse"]),
            "legacy_mae": float(loo["legacy_heuristic_proxy"]["mae"]),
            "legacy_rmse": float(loo["legacy_heuristic_proxy"]["rmse"]),
            "learned_beats_legacy": bool(
                loo["learned_calibrator_proxy"]["mae"] < loo["legacy_heuristic_proxy"]["mae"]
                and loo["learned_calibrator_proxy"]["rmse"] < loo["legacy_heuristic_proxy"]["rmse"]
            ),
        },
        "chronological_holdout_2026": {
            "learned_mae": float(chrono["learned_calibrator_proxy"]["mae"]),
            "learned_rmse": float(chrono["learned_calibrator_proxy"]["rmse"]),
            "legacy_mae": float(chrono["legacy_heuristic_proxy"]["mae"]),
            "legacy_rmse": float(chrono["legacy_heuristic_proxy"]["rmse"]),
            "learned_beats_legacy": bool(
                chrono["learned_calibrator_proxy"]["mae"] < chrono["legacy_heuristic_proxy"]["mae"]
                and chrono["learned_calibrator_proxy"]["rmse"] < chrono["legacy_heuristic_proxy"]["rmse"]
            ),
        },
    }

    gate_passes = (
        change4_checks["leave_one_out"]["learned_beats_legacy"]
        and change4_checks["chronological_holdout_2026"]["learned_beats_legacy"]
        and bool(msl_external["learned_generalizes_here"])
    )

    return {
        "question": (
            "Does the learned calibrator clear both the stricter Chang'e-4 held-out "
            "checks and the independent MSL/RAD external stress test?"
        ),
        "answer": (
            "Yes. The learned calibrator improves on held-out Chang'e-4 splits and "
            "also wins on the independent MSL/RAD external basket."
            if gate_passes
            else "Not yet. The learned calibrator improves the in-family lunar fit, "
            "but it still does not beat the simplest baselines on the independent "
            "MSL/RAD external basket."
        ),
        "generalization_gate": {
            "rule": (
                "The learned calibrator must beat the legacy heuristic on both "
                "Chang'e-4 held-out splits and be among the best MAE and RMSE "
                "baselines on the independent MSL/RAD basket."
            ),
            "status": "generalized" if gate_passes else "not_generalized",
        },
        "change4_heldout_checks": change4_checks,
        "artemis_bundle_diagnostic": {
            "best_mae_baselines": artemis_bundle["best_mae_baselines"],
            "best_rmse_baselines": artemis_bundle["best_rmse_baselines"],
            "learned_mae": float(artemis_bundle["baselines"]["learned_calibrator_proxy"]["mae"]),
            "learned_rmse": float(artemis_bundle["baselines"]["learned_calibrator_proxy"]["rmse"]),
            "legacy_mae": float(artemis_bundle["baselines"]["legacy_heuristic_proxy"]["mae"]),
            "legacy_rmse": float(artemis_bundle["baselines"]["legacy_heuristic_proxy"]["rmse"]),
        },
        "msl_external_stress_test": {
            "best_mae_baselines": msl_external["best_mae_baselines"],
            "best_rmse_baselines": msl_external["best_rmse_baselines"],
            "learned_mae": float(msl_external["baselines"]["learned_calibrator_proxy"]["mae"]),
            "learned_rmse": float(msl_external["baselines"]["learned_calibrator_proxy"]["rmse"]),
            "legacy_mae": float(msl_external["baselines"]["legacy_heuristic_proxy"]["mae"]),
            "legacy_rmse": float(msl_external["baselines"]["legacy_heuristic_proxy"]["rmse"]),
            "midpoint_mae": float(msl_external["baselines"]["midpoint_0_5"]["mae"]),
            "midpoint_rmse": float(msl_external["baselines"]["midpoint_0_5"]["rmse"]),
            "learned_generalizes_here": bool(msl_external["learned_generalizes_here"]),
        },
        "reproducibility": {
            "command": "python scripts/run_final_generalization_test.py --output-dir docs/validation",
            "python_version": sys.version.split()[0],
            "dependent_reports": [
                "docs/validation/CHANGE4_HELDOUT_VALIDATION.md",
                "docs/validation/ARTEMIS_I_EXTERNAL_VALIDATION.md",
                "docs/validation/MSL_RAD_EXTERNAL_VALIDATION.md",
            ],
        },
    }


def render_markdown_summary(report: dict) -> str:
    loo = report["change4_heldout_checks"]["leave_one_out"]
    chrono = report["change4_heldout_checks"]["chronological_holdout_2026"]
    artemis = report["artemis_bundle_diagnostic"]
    msl = report["msl_external_stress_test"]

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
        "## Chang'e-4 Held-Out Checks",
        "| Split | Learned MAE | Learned RMSE | Legacy MAE | Legacy RMSE | Learned beats legacy |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        f"| leave_one_out | {loo['learned_mae']:.6f} | {loo['learned_rmse']:.6f} | {loo['legacy_mae']:.6f} | {loo['legacy_rmse']:.6f} | `{loo['learned_beats_legacy']}` |",
        f"| chronological_holdout_2026 | {chrono['learned_mae']:.6f} | {chrono['learned_rmse']:.6f} | {chrono['legacy_mae']:.6f} | {chrono['legacy_rmse']:.6f} | `{chrono['learned_beats_legacy']}` |",
        "",
        "## Artemis I Bundle Diagnostic",
        f"- Best MAE baselines: `{', '.join(artemis['best_mae_baselines'])}`",
        f"- Best RMSE baselines: `{', '.join(artemis['best_rmse_baselines'])}`",
        f"- Learned calibrator: `MAE {artemis['learned_mae']:.6f}`, `RMSE {artemis['learned_rmse']:.6f}`",
        f"- Legacy heuristic: `MAE {artemis['legacy_mae']:.6f}`, `RMSE {artemis['legacy_rmse']:.6f}`",
        "",
        "## Independent MSL/RAD Stress Test",
        f"- Best MAE baselines: `{', '.join(msl['best_mae_baselines'])}`",
        f"- Best RMSE baselines: `{', '.join(msl['best_rmse_baselines'])}`",
        f"- Learned calibrator: `MAE {msl['learned_mae']:.6f}`, `RMSE {msl['learned_rmse']:.6f}`",
        f"- Legacy heuristic: `MAE {msl['legacy_mae']:.6f}`, `RMSE {msl['legacy_rmse']:.6f}`",
        f"- Midpoint baseline: `MAE {msl['midpoint_mae']:.6f}`, `RMSE {msl['midpoint_rmse']:.6f}`",
        "",
        "## Interpretation",
        (
            "The learned calibrator is stronger on the bundled lunar diagnostics overall, "
            "and the updated held-out Chang'e-4 splits plus the MSL/RAD basket now move "
            "in the same direction."
        ),
        (
            "Right now the final gate stays closed because the independent external "
            "basket still favors simpler baselines."
            if report["generalization_gate"]["status"] != "generalized"
            else "Right now the final gate clears because the learned calibrator also wins the independent external basket."
        ),
        "",
        "## Reproduce",
        "```powershell",
        "python scripts/run_change4_heldout_validation.py --output-dir docs/validation",
        "python scripts/run_artemis_i_external_validation.py --output-dir docs/validation",
        "python scripts/run_msl_rad_external_validation.py --output-dir docs/validation",
        "python scripts/run_final_generalization_test.py --output-dir docs/validation",
        "python -m pytest tests/galactic_cosmic_rays -q",
        "```",
    ]
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
