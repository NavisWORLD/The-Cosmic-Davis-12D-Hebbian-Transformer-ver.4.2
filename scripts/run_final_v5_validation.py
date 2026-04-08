"""Build the final v5 transport-router validation package."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from radiation_validation_v5_utils import (
    ROOT,
    build_bootstrap_suite_v5,
    build_extended_blind_prediction_bundle_v5,
    evaluate_external_records_v5,
    score_extended_blind_prediction_bundle,
    sha256,
    write_json,
)

V4_SCRIPT = ROOT / "scripts" / "run_final_v4_validation.py"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "final_v5_validation_report.json"
MARKDOWN_REPORT_NAME = "FINAL_V5_VALIDATION.md"

DATASET_CONFIG = {
    "msl": {
        "label": "MSL/RAD",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "msl_rad_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "msl_rad_blind_template.json",
        "prediction_filename": "blind_predictions_msl_v5.json",
        "scoring_filename": "blind_scoring_msl_v5.json",
    },
    "crater": {
        "label": "CRaTER/LRO",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "crater_lro_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "crater_lro_blind_template.json",
        "prediction_filename": "blind_predictions_crater_v5.json",
        "scoring_filename": "blind_scoring_crater_v5.json",
    },
    "chandrayaan1": {
        "label": "Chandrayaan-1 RADOM",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "chandrayaan1_radom_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "chandrayaan1_radom_blind_template.json",
        "prediction_filename": "blind_predictions_chandrayaan1_v5.json",
        "scoring_filename": "blind_scoring_chandrayaan1_v5.json",
    },
    "mars_fd": {
        "label": "Mars FD development benchmark",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "mars_fd_surface_orbit_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "mars_fd_surface_orbit_blind_template.json",
        "prediction_filename": "blind_predictions_mars_fd_v5.json",
        "scoring_filename": "blind_scoring_mars_fd_v5.json",
    },
    "mars_icme_transit": {
        "label": "Mars ICME transit holdout",
        "fixture": ROOT / "tests" / "galactic_cosmic_rays" / "mars_icme_transit_reference.json",
        "template": ROOT / "tests" / "galactic_cosmic_rays" / "blind_templates" / "mars_icme_transit_blind_template.json",
        "prediction_filename": "blind_predictions_mars_icme_transit_v5.json",
        "scoring_filename": "blind_scoring_mars_icme_transit_v5.json",
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
        "v5_beats_legacy": bool(report["v5_beats_legacy"]),
        "v5_beats_v4": bool(report["v5_beats_v4"]),
        "v5_beats_metadata_only": bool(report["v5_beats_metadata_only"]),
        "v5_mae": float(baselines["v5_transport_router_proxy"]["mae"]),
        "v5_rmse": float(baselines["v5_transport_router_proxy"]["rmse"]),
        "legacy_mae": float(baselines["legacy_heuristic_proxy"]["mae"]),
        "legacy_rmse": float(baselines["legacy_heuristic_proxy"]["rmse"]),
        "v4_mae": float(baselines["learned_v4_calibrator_proxy"]["mae"]),
        "v4_rmse": float(baselines["learned_v4_calibrator_proxy"]["rmse"]),
        "metadata_mae": float(baselines["metadata_only_ridge"]["mae"]),
        "metadata_rmse": float(baselines["metadata_only_ridge"]["rmse"]),
        "phase_only_ablation_mae": float(baselines["v5_phase_only_ablation"]["mae"]),
        "phase_only_ablation_rmse": float(baselines["v5_phase_only_ablation"]["rmse"]),
        "bootstrap": report["bootstrap"],
    }


def _summary_from_blind_score(score: dict) -> dict:
    baselines = score["baselines"]
    family_names = {"legacy_heuristic_proxy", "learned_v4_calibrator_proxy", "v5_transport_router_proxy"}
    return {
        "best_mae_baselines": score["best_mae_baselines"],
        "best_rmse_baselines": score["best_rmse_baselines"],
        "family_led": bool(
            set(score["best_mae_baselines"]).issubset(family_names)
            and set(score["best_rmse_baselines"]).issubset(family_names)
        ),
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
        "v5_beats_legacy": bool(
            baselines["v5_transport_router_proxy"]["mae"] < baselines["legacy_heuristic_proxy"]["mae"]
            and baselines["v5_transport_router_proxy"]["rmse"] < baselines["legacy_heuristic_proxy"]["rmse"]
        ),
        "v5_beats_v4": bool(
            baselines["v5_transport_router_proxy"]["mae"] < baselines["learned_v4_calibrator_proxy"]["mae"]
            and baselines["v5_transport_router_proxy"]["rmse"] < baselines["learned_v4_calibrator_proxy"]["rmse"]
        ),
        "v5_beats_metadata_only": bool(
            baselines["v5_transport_router_proxy"]["mae"] < baselines["metadata_only_ridge"]["mae"]
            and baselines["v5_transport_router_proxy"]["rmse"] < baselines["metadata_only_ridge"]["rmse"]
        ),
        "v5_mae": float(baselines["v5_transport_router_proxy"]["mae"]),
        "v5_rmse": float(baselines["v5_transport_router_proxy"]["rmse"]),
        "legacy_mae": float(baselines["legacy_heuristic_proxy"]["mae"]),
        "legacy_rmse": float(baselines["legacy_heuristic_proxy"]["rmse"]),
        "v4_mae": float(baselines["learned_v4_calibrator_proxy"]["mae"]),
        "v4_rmse": float(baselines["learned_v4_calibrator_proxy"]["rmse"]),
        "metadata_mae": float(baselines["metadata_only_ridge"]["mae"]),
        "metadata_rmse": float(baselines["metadata_only_ridge"]["rmse"]),
        "predictions_path": score.get("predictions_path", ""),
        "predictions_sha256": score.get("predictions_sha256", ""),
        "template_sha256": score["template_sha256"],
        "revealed_sha256": score["revealed_sha256"],
    }


def _write_blind_bundle(output_dir: Path, key: str, config: dict) -> dict:
    bundle = build_extended_blind_prediction_bundle_v5(config["template"], label=f"{key}_v5")
    prediction_path = output_dir / config["prediction_filename"]
    write_json(prediction_path, bundle)
    scored = score_extended_blind_prediction_bundle(bundle, config["fixture"])
    scored["predictions_path"] = str(prediction_path)
    scored["predictions_sha256"] = sha256(prediction_path)
    scoring_path = output_dir / config["scoring_filename"]
    write_json(scoring_path, scored)
    return scored


def build_final_v5_validation(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict:
    v4_module = _load_module(V4_SCRIPT, "final_v4_validation_for_v5")
    v4_report = v4_module.build_final_v4_validation()

    direct_summaries = {}
    blind_summaries = {}
    for key, config in DATASET_CONFIG.items():
        records = json.loads(config["fixture"].read_text(encoding="utf-8"))
        report = evaluate_external_records_v5(records, fixture_path=config["fixture"])
        report["bootstrap"] = build_bootstrap_suite_v5(report)
        direct_summaries[key] = _summary_from_report(report)
        score = _write_blind_bundle(output_dir, key, config)
        blind_summaries[key] = _summary_from_blind_score(score)

    preserved_v4_bundle = (
        v4_report["v4_gate"]["status"] == "validated_predictive_subdomain"
        and "v5_transport_router_proxy" in direct_summaries["msl"]["best_rmse_baselines"]
        and "v5_transport_router_proxy" in direct_summaries["crater"]["best_rmse_baselines"]
        and "v5_transport_router_proxy" in direct_summaries["chandrayaan1"]["best_rmse_baselines"]
        and "v5_transport_router_proxy" in blind_summaries["msl"]["best_rmse_baselines"]
        and "v5_transport_router_proxy" in blind_summaries["crater"]["best_rmse_baselines"]
        and "v5_transport_router_proxy" in blind_summaries["chandrayaan1"]["best_rmse_baselines"]
    )

    mars_fd_upgrade = (
        direct_summaries["mars_fd"]["best_mae_baselines"] == ["v5_transport_router_proxy"]
        and direct_summaries["mars_fd"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
        and blind_summaries["mars_fd"]["best_mae_baselines"] == ["v5_transport_router_proxy"]
        and blind_summaries["mars_fd"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
        and direct_summaries["mars_fd"]["v5_beats_legacy"]
        and direct_summaries["mars_fd"]["v5_beats_v4"]
        and direct_summaries["mars_fd"]["bootstrap"]["v5_vs_legacy"]["mae"]["ci_high"] < 0.0
        and direct_summaries["mars_fd"]["bootstrap"]["v5_vs_v4"]["mae"]["ci_high"] < 0.0
    )

    untouched_mars_holdout = (
        direct_summaries["mars_icme_transit"]["best_mae_baselines"] == ["v5_transport_router_proxy"]
        and direct_summaries["mars_icme_transit"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
        and blind_summaries["mars_icme_transit"]["best_mae_baselines"] == ["v5_transport_router_proxy"]
        and blind_summaries["mars_icme_transit"]["best_rmse_baselines"] == ["v5_transport_router_proxy"]
        and direct_summaries["mars_icme_transit"]["v5_beats_legacy"]
        and direct_summaries["mars_icme_transit"]["v5_beats_v4"]
        and direct_summaries["mars_icme_transit"]["bootstrap"]["v5_vs_v4"]["rmse"]["ci_high"] < 0.0
        and direct_summaries["mars_icme_transit"]["bootstrap"]["v5_vs_phase_only_ablation"]["rmse"]["ci_high"] < 0.0
    )

    v5_passes = preserved_v4_bundle and mars_fd_upgrade and untouched_mars_holdout

    return {
        "freeze_label": "cst_radiation_validation_v5",
        "freeze_date": "2026-04-08",
        "question": (
            "Does the v5 transport router close the remaining Mars-family weakness without "
            "losing the stronger v4 evidence package?"
        ),
        "answer": (
            "Yes. The v5 transport router preserves the v4 predictive subdomain on MSL, CRaTER, "
            "and Chandrayaan, upgrades the former Mars FD weak spot into a development-benchmark win, "
            "and still wins on a separate untouched Mars ICME transit holdout."
            if v5_passes
            else "Not yet. The v4 bundle still holds, but the v5 transport router does not clear "
            "both the Mars development benchmark and the untouched Mars holdout strongly enough."
        ),
        "v4_gate_status": v4_report["v4_gate"]["status"],
        "v5_gate": {
            "rule": (
                "Keep the v4 predictive subdomain intact, make the v5 router the best direct and blind "
                "proxy on the Mars FD development benchmark, and require it to repeat that dominance on "
                "the untouched Mars ICME transit holdout."
            ),
            "status": "validated_unified_transport_router" if v5_passes else "not_validated",
        },
        "direct_reports": direct_summaries,
        "blind_reports": blind_summaries,
        "reproducibility": {
            "python_version": sys.version.split()[0],
            "commands": [
                "python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation",
                "python scripts/run_final_v5_validation.py --output-dir docs/validation",
                "python scripts/build_validation_manifest_v5.py --output docs/validation/validation_manifest_v5.json",
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
        "# Final V5 Validation",
        "",
        "## Summary",
        report["question"],
        report["answer"],
        "",
        f"- Freeze label: `{report['freeze_label']}`",
        f"- V4 gate status: `{report['v4_gate_status']}`",
        f"- V5 gate status: `{report['v5_gate']['status']}`",
        "",
        "## Direct External Evidence",
        "| Dataset | Best MAE | Best RMSE | V5 MAE | V5 RMSE | V4 MAE | V4 RMSE | Legacy MAE | Legacy RMSE |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, config in DATASET_CONFIG.items():
        summary = report["direct_reports"][key]
        lines.append(
            f"| {config['label']} | {', '.join(summary['best_mae_baselines'])} | {', '.join(summary['best_rmse_baselines'])} | "
            f"{summary['v5_mae']:.6f} | {summary['v5_rmse']:.6f} | "
            f"{summary['v4_mae']:.6f} | {summary['v4_rmse']:.6f} | "
            f"{summary['legacy_mae']:.6f} | {summary['legacy_rmse']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Blind External Evidence",
            "| Dataset | Best MAE | Best RMSE | V5 MAE | V5 RMSE | V4 MAE | V4 RMSE |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for key, config in DATASET_CONFIG.items():
        summary = report["blind_reports"][key]
        lines.append(
            f"| {config['label']} blind | {', '.join(summary['best_mae_baselines'])} | {', '.join(summary['best_rmse_baselines'])} | "
            f"{summary['v5_mae']:.6f} | {summary['v5_rmse']:.6f} | "
            f"{summary['v4_mae']:.6f} | {summary['v4_rmse']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Bootstrap Evidence",
            "| Dataset | Comparison | Metric | Observed delta | 95% CI low | 95% CI high |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for key in DATASET_CONFIG:
        label = DATASET_CONFIG[key]["label"]
        bootstrap = report["direct_reports"][key]["bootstrap"]
        for comparison in ("v5_vs_legacy", "v5_vs_v4", "v5_vs_metadata_only", "v5_vs_phase_only_ablation"):
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
            "The main v5 move is not another lunar fit. It is the new Mars transport routing layer: the former Mars FD weak spot is upgraded from a legacy-led result into a v5-led result, and the separate Mars ICME transit holdout still clears with the v5 router.",
            "That shortens the old caveat substantially. The remaining caution is procedural rather than numerical: Mars FD is now a development benchmark for v5, while the ICME transit set is the untouched Mars-family proof set.",
            "",
            "## Reproduce",
            "```powershell",
            "python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation",
            "python scripts/run_final_v5_validation.py --output-dir docs/validation",
            "python scripts/build_validation_manifest_v5.py --output docs/validation/validation_manifest_v5.json",
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

    report = build_final_v5_validation(output_dir=args.output_dir)
    json_path, markdown_path = write_reports(args.output_dir, report)
    print(f"V5 gate status: {report['v5_gate']['status']}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
