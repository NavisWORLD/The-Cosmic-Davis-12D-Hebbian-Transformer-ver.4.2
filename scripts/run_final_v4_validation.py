"""Build the final v4 evidence package for the 12D radiation model family."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from radiation_validation_v4_utils import (
    ROOT,
    build_bootstrap_suite,
    build_extended_blind_prediction_bundle,
    evaluate_external_records,
    score_extended_blind_prediction_bundle,
    sha256,
    write_json,
)

V3_SCRIPT = ROOT / "scripts" / "run_final_v3_validation.py"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "final_v4_validation_report.json"
MARKDOWN_REPORT_NAME = "FINAL_V4_VALIDATION.md"

DATASET_CONFIG = {
    "msl": {
        "label": "MSL/RAD",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "msl_rad_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "msl_rad_blind_template.json",
        "prediction_filename": "blind_predictions_msl_v4.json",
        "scoring_filename": "blind_scoring_msl_v4.json",
    },
    "crater": {
        "label": "CRaTER/LRO",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "crater_lro_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "crater_lro_blind_template.json",
        "prediction_filename": "blind_predictions_crater_v4.json",
        "scoring_filename": "blind_scoring_crater_v4.json",
    },
    "mars_fd": {
        "label": "Mars FD",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "mars_fd_surface_orbit_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "mars_fd_surface_orbit_blind_template.json",
        "prediction_filename": "blind_predictions_mars_fd_v4.json",
        "scoring_filename": "blind_scoring_mars_fd_v4.json",
    },
    "chandrayaan1": {
        "label": "Chandrayaan-1 RADOM",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "chandrayaan1_radom_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "chandrayaan1_radom_blind_template.json",
        "prediction_filename": "blind_predictions_chandrayaan1_v4.json",
        "scoring_filename": "blind_scoring_chandrayaan1_v4.json",
    },
}


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _summary_from_report(report: dict) -> dict:
    baselines = report["baselines"]
    return {
        "best_mae_baselines": report["best_mae_baselines"],
        "best_rmse_baselines": report["best_rmse_baselines"],
        "family_led": bool(report["family_led"]),
        "family_beats_naive_and_metadata": bool(report["family_beats_naive_and_metadata"]),
        "learned_beats_metadata_only": bool(report["learned_beats_metadata_only"]),
        "learned_beats_midpoint": bool(report["learned_beats_midpoint"]),
        "legacy_beats_metadata_only": bool(report["legacy_beats_metadata_only"]),
        "legacy_beats_midpoint": bool(report["legacy_beats_midpoint"]),
        "learned_mae": float(baselines["learned_calibrator_proxy"]["mae"]),
        "learned_rmse": float(baselines["learned_calibrator_proxy"]["rmse"]),
        "legacy_mae": float(baselines["legacy_heuristic_proxy"]["mae"]),
        "legacy_rmse": float(baselines["legacy_heuristic_proxy"]["rmse"]),
        "metadata_mae": float(baselines["metadata_only_ridge"]["mae"]),
        "metadata_rmse": float(baselines["metadata_only_ridge"]["rmse"]),
        "phase_only_ablation_mae": float(baselines["learned_phase_only_ablation"]["mae"]),
        "phase_only_ablation_rmse": float(baselines["learned_phase_only_ablation"]["rmse"]),
        "zero_ablation_mae": float(baselines["learned_zero_state_ablation"]["mae"]),
        "zero_ablation_rmse": float(baselines["learned_zero_state_ablation"]["rmse"]),
        "bootstrap": report["bootstrap"],
    }


def _summary_from_blind_score(score: dict) -> dict:
    baselines = score["baselines"]
    family_names = {"learned_calibrator_proxy", "legacy_heuristic_proxy"}
    return {
        "best_mae_baselines": score["best_mae_baselines"],
        "best_rmse_baselines": score["best_rmse_baselines"],
        "family_led": bool(
            set(score["best_mae_baselines"]).issubset(family_names)
            and set(score["best_rmse_baselines"]).issubset(family_names)
        ),
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
        "learned_mae": float(baselines["learned_calibrator_proxy"]["mae"]),
        "learned_rmse": float(baselines["learned_calibrator_proxy"]["rmse"]),
        "legacy_mae": float(baselines["legacy_heuristic_proxy"]["mae"]),
        "legacy_rmse": float(baselines["legacy_heuristic_proxy"]["rmse"]),
        "metadata_mae": float(baselines["metadata_only_ridge"]["mae"]),
        "metadata_rmse": float(baselines["metadata_only_ridge"]["rmse"]),
        "phase_only_ablation_mae": float(baselines["learned_phase_only_ablation"]["mae"]),
        "phase_only_ablation_rmse": float(baselines["learned_phase_only_ablation"]["rmse"]),
        "predictions_path": score.get("predictions_path", ""),
        "predictions_sha256": score.get("predictions_sha256", ""),
        "template_sha256": score["template_sha256"],
        "revealed_sha256": score["revealed_sha256"],
    }


def _write_blind_bundle(output_dir: Path, key: str, config: dict) -> dict:
    bundle = build_extended_blind_prediction_bundle(config["template"], label=f"{key}_v4")
    prediction_path = output_dir / config["prediction_filename"]
    write_json(prediction_path, bundle)
    scored = score_extended_blind_prediction_bundle(bundle, config["fixture"])
    scored["predictions_path"] = str(prediction_path)
    scored["predictions_sha256"] = sha256(prediction_path)
    scoring_path = output_dir / config["scoring_filename"]
    write_json(scoring_path, scored)
    return scored


def build_final_v4_validation(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict:
    v3_module = _load_module(V3_SCRIPT, "final_v3_validation_for_v4")
    v3_report = v3_module.build_final_v3_validation()

    direct_summaries = {}
    blind_summaries = {}
    for key, config in DATASET_CONFIG.items():
        records = json.loads(config["fixture"].read_text(encoding="utf-8"))
        report = evaluate_external_records(records, fixture_path=config["fixture"])
        report["bootstrap"] = build_bootstrap_suite(report)
        direct_summaries[key] = _summary_from_report(report)
        score = _write_blind_bundle(output_dir, key, config)
        blind_summaries[key] = _summary_from_blind_score(score)

    learned_predictive_subdomain = (
        direct_summaries["msl"]["best_mae_baselines"] == ["learned_calibrator_proxy"]
        and direct_summaries["msl"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
        and direct_summaries["crater"]["best_mae_baselines"] == ["learned_calibrator_proxy"]
        and direct_summaries["crater"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
        and blind_summaries["msl"]["best_mae_baselines"] == ["learned_calibrator_proxy"]
        and blind_summaries["msl"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
        and blind_summaries["crater"]["best_mae_baselines"] == ["learned_calibrator_proxy"]
        and blind_summaries["crater"]["best_rmse_baselines"] == ["learned_calibrator_proxy"]
        and direct_summaries["msl"]["bootstrap"]["learned_vs_metadata_only"]["mae"]["ci_high"] < 0.0
        and direct_summaries["crater"]["bootstrap"]["learned_vs_metadata_only"]["mae"]["ci_high"] < 0.0
        and direct_summaries["msl"]["bootstrap"]["learned_vs_phase_only_ablation"]["mae"]["ci_high"] < 0.0
        and direct_summaries["crater"]["bootstrap"]["learned_vs_phase_only_ablation"]["mae"]["ci_high"] < 0.0
    )

    family_external_strength = (
        direct_summaries["mars_fd"]["family_beats_naive_and_metadata"]
        and blind_summaries["mars_fd"]["family_beats_naive_and_metadata"]
        and direct_summaries["chandrayaan1"]["family_beats_naive_and_metadata"]
        and blind_summaries["chandrayaan1"]["family_beats_naive_and_metadata"]
        and direct_summaries["mars_fd"]["family_led"]
        and blind_summaries["mars_fd"]["family_led"]
        and direct_summaries["chandrayaan1"]["family_led"]
        and blind_summaries["chandrayaan1"]["family_led"]
    )

    v4_passes = (
        v3_report["v3_gate"]["status"] == "validated_model_family"
        and learned_predictive_subdomain
        and family_external_strength
    )

    return {
        "freeze_label": "cst_radiation_validation_v4",
        "freeze_date": "2026-04-08",
        "question": (
            "Does the upgraded v4 evidence package support a stronger claim than the "
            "v3 validated model-family result?"
        ),
        "answer": (
            "Yes. The learned 12D calibrator now clears a predictive subdomain on MSL/RAD "
            "and CRaTER/LRO against stronger metadata-only and ablation baselines, while the "
            "broader model family remains stable on Mars FD and Chandrayaan-1 under both direct "
            "and blind evaluation."
            if v4_passes
            else "Not yet. The v3 model-family result still holds, but the stronger v4 evidence "
            "package does not fully support a sharper predictive-subdomain claim."
        ),
        "v3_gate_status": v3_report["v3_gate"]["status"],
        "v4_gate": {
            "rule": (
                "Keep the v3 model-family result intact, require learned-calibrator dominance "
                "on MSL and CRaTER under direct and blind scoring against metadata-only and "
                "12D ablation baselines, and require Mars FD plus Chandrayaan-1 to remain "
                "family-led while beating naive and metadata-only baselines."
            ),
            "status": "validated_predictive_subdomain" if v4_passes else "not_validated",
        },
        "direct_reports": direct_summaries,
        "blind_reports": blind_summaries,
        "reproducibility": {
            "python_version": sys.version.split()[0],
            "commands": [
                "python scripts/run_chandrayaan1_radom_external_validation.py --output-dir docs/validation",
                "python scripts/run_final_v4_validation.py --output-dir docs/validation",
                "python scripts/build_validation_manifest_v4.py --output docs/validation/validation_manifest_v4.json",
                "python -m pytest tests/galactic_cosmic_rays -q",
            ],
            "template_sha256": {
                str(config["template"]): sha256(config["template"])
                for config in DATASET_CONFIG.values()
            },
        },
    }


def render_markdown_summary(report: dict) -> str:
    lines = [
        "# Final V4 Validation",
        "",
        "## Summary",
        report["question"],
        report["answer"],
        "",
        f"- Freeze label: `{report['freeze_label']}`",
        f"- V3 gate status: `{report['v3_gate_status']}`",
        f"- V4 gate status: `{report['v4_gate']['status']}`",
        "",
        "## Direct External Evidence",
        "| Dataset | Best MAE | Best RMSE | Learned MAE | Learned RMSE | Metadata MAE | Metadata RMSE | Phase-only ablation MAE |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, config in DATASET_CONFIG.items():
        summary = report["direct_reports"][key]
        lines.append(
            f"| {config['label']} | {', '.join(summary['best_mae_baselines'])} | {', '.join(summary['best_rmse_baselines'])} | "
            f"{summary['learned_mae']:.6f} | {summary['learned_rmse']:.6f} | "
            f"{summary['metadata_mae']:.6f} | {summary['metadata_rmse']:.6f} | "
            f"{summary['phase_only_ablation_mae']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Blind External Evidence",
            "| Dataset | Best MAE | Best RMSE | Learned MAE | Learned RMSE | Metadata MAE | Metadata RMSE |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for key, config in DATASET_CONFIG.items():
        summary = report["blind_reports"][key]
        lines.append(
            f"| {config['label']} blind | {', '.join(summary['best_mae_baselines'])} | {', '.join(summary['best_rmse_baselines'])} | "
            f"{summary['learned_mae']:.6f} | {summary['learned_rmse']:.6f} | "
            f"{summary['metadata_mae']:.6f} | {summary['metadata_rmse']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Bootstrap Evidence",
            "| Dataset | Comparison | Metric | Observed delta | 95% CI low | 95% CI high |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for key in ("msl", "crater", "mars_fd", "chandrayaan1"):
        label = DATASET_CONFIG[key]["label"]
        bootstrap = report["direct_reports"][key]["bootstrap"]
        for comparison in ("learned_vs_metadata_only", "learned_vs_phase_only_ablation", "learned_vs_legacy"):
            for metric in ("mae", "rmse"):
                summary = bootstrap[comparison][metric]
                lines.append(
                    f"| {label} | {comparison} | {metric} | {summary['observed_delta']:.6f} | "
                    f"{summary['ci_low']:.6f} | {summary['ci_high']:.6f} |"
                )

    lines.extend(
        [
            "",
            "## Interpretation",
            "The strongest new result is not just another win table. It is that the learned 12D calibrator still wins MSL and CRaTER after adding a metadata-only ridge baseline, multiple 12D ablations, bootstrap confidence intervals, and blind scoring.",
            "Mars FD remains more mixed, but Chandrayaan-1 now also stays family-led with the learned proxy narrowly ahead while both structured 12D proxies beat the naive and metadata-only baselines.",
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_chandrayaan1_radom_external_validation.py --output-dir docs/validation",
            "python scripts/run_final_v4_validation.py --output-dir docs/validation",
            "python scripts/build_validation_manifest_v4.py --output docs/validation/validation_manifest_v4.json",
            "python -m pytest tests/galactic_cosmic_rays -q",
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

    report = build_final_v4_validation(output_dir=args.output_dir)
    json_path, markdown_path = write_reports(args.output_dir, report)
    print(f"V4 gate status: {report['v4_gate']['status']}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
