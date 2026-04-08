"""Run a reproducible Chang'e-4/LND alignment diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "Cosmos" / "core" / "cst_critical_integration.py"
FIXTURE_PATH = ROOT / "tests" / "galactic_cosmic_rays" / "change4_lnd_reference.json"
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "validation"
JSON_REPORT_NAME = "change4_alignment_report.json"
MARKDOWN_REPORT_NAME = "CHANGE4_EMPIRICAL_VALIDATION.md"

DEFAULT_MODEL_INPUT = {
    "cst_physics": {
        "geometric_phase_rad": 0.71,
        "phase_velocity": 0.028,
        "entanglement_score": 0.64,
    },
    "bio_signatures": {
        "intensity": 0.77,
        "arousal": 0.31,
        "valence": 0.09,
    },
    "cst_metrics": {
        "x12_avg": 0.58,
        "ci_b": 0.41,
        "ci_c": 0.29,
    },
}

DEFAULT_METRICS = {
    "entropy_quality": 0.78,
    "decoherence_risk": 0.22,
}

DEFAULT_DARK_MATTER_W = 0.36


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "cst_critical_integration_change4_diag",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load CST module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_records(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _observable_kind(record: dict) -> str:
    if "ratio" in record:
        return "ratio"
    if "numerator" in record and "denominator" in record:
        return "numerator"
    if "current" in record and "forecast" in record:
        return "current"
    return "value"


def _observed_value(record: dict) -> float:
    if "ratio" in record:
        return float(record["ratio"])
    if "numerator" in record and "denominator" in record:
        return float(record["numerator"])
    if "current" in record and "forecast" in record:
        return float(record["current"])
    return float(record.get("value", 0.0))


def _predicted_value_from_scalar(record: dict, scalar: float) -> float:
    scalar = float(max(0.0, min(1.0, scalar)))
    if "ratio" in record:
        return scalar
    if "numerator" in record and "denominator" in record:
        return scalar * float(record["denominator"])
    if "current" in record and "forecast" in record:
        return scalar * float(record["forecast"])

    normalizer = float(record.get("normalizer", 1.0)) or 1.0
    transform = str(record.get("transform", "linear")).lower()
    if transform == "log":
        return float(np.expm1(scalar * np.log1p(max(0.0, normalizer))))
    return scalar * normalizer


def _heuristic_band(score: float) -> str:
    if score < 0.50:
        return "weak_alignment"
    if score < 0.70:
        return "interesting_correlation"
    if score < 0.85:
        return "strong_alignment_not_yet_predictive"
    return "predictive_candidate_requires_held_out_validation"


def _heuristic_summary(score: float) -> str:
    band = _heuristic_band(score)
    if band == "weak_alignment":
        return "The current 12D probe does not show a strong quantitative match."
    if band == "interesting_correlation":
        return (
            "The current 12D probe shows a real mid-strength correlation signal, "
            "but not enough evidence to call the model predictive."
        )
    if band == "strong_alignment_not_yet_predictive":
        return (
            "The current 12D probe shows a strong match, but it still needs "
            "held-out validation before any predictive claim."
        )
    return (
        "The current 12D probe is strong enough to justify out-of-sample testing, "
        "but it is still not a proof of predictive power by itself."
    )


def build_change4_alignment_diagnostic(
    fixture_path: Path = FIXTURE_PATH,
) -> dict:
    module = _load_module()
    records = _load_records(fixture_path)
    state_vector = module.build_12d_state_vector(
        DEFAULT_MODEL_INPUT,
        metrics=DEFAULT_METRICS,
        dark_matter_w=DEFAULT_DARK_MATTER_W,
    )
    alignment = module.galactic_cosmic_ray_alignment(state_vector, records)

    weights = np.array([float(record.get("weight", 1.0)) for record in records], dtype=float)
    if float(weights.sum()) <= 0.0:
        weights = np.ones(len(records), dtype=float)
    weights /= weights.sum()

    scalars = np.array([module._normalize_gcr_scalar(record) for record in records], dtype=float)
    probes = np.array([module.harmonic_embed_scalar_to_12d(value) for value in scalars], dtype=float)
    model_vector = module._normalize_vector(module._safe_array(state_vector, size=12))
    phase_proxy_raw = float(np.mean(model_vector[:4]))
    phase_proxy_clamped = float(module._clamp(phase_proxy_raw))

    record_results = []
    weighted_local_alignment = 0.0
    for index, record in enumerate(records):
        target_scalar = float(scalars[index])
        probe = probes[index]
        cosine_raw = float(np.clip(np.dot(model_vector, probe), -1.0, 1.0))
        cosine_similarity = float((cosine_raw + 1.0) / 2.0)
        phase_delta = float(min(1.0, abs(phase_proxy_raw - target_scalar)))
        local_alignment = float(
            module._clamp(cosine_similarity * 0.75 + (1.0 - phase_delta) * 0.25)
        )
        weighted_local_alignment += float(weights[index]) * local_alignment

        observed_value = _observed_value(record)
        predicted_value = _predicted_value_from_scalar(record, phase_proxy_clamped)
        raw_delta = float(predicted_value - observed_value)

        record_results.append(
            {
                "id": record["id"],
                "published_date": record["published_date"],
                "source": record["source"],
                "source_url": record["source_url"],
                "notes": record.get("notes", ""),
                "units": record.get("units", "unitless"),
                "observable_kind": _observable_kind(record),
                "weight": float(weights[index]),
                "normalized_target": target_scalar,
                "model_scalar_prediction": phase_proxy_clamped,
                "normalized_delta": float(phase_proxy_clamped - target_scalar),
                "observed_value": observed_value,
                "predicted_value_from_phase_proxy": predicted_value,
                "raw_delta": raw_delta,
                "record_cosine_similarity": cosine_similarity,
                "record_phase_delta": phase_delta,
                "record_alignment_score": local_alignment,
            }
        )

    overall_alignment = float(alignment.overall_alignment)
    cosine_similarity = float(alignment.cosine_similarity)
    phase_distance = float(alignment.phase_distance)
    band = _heuristic_band(overall_alignment)

    return {
        "model": {
            "name": "12D CST harmonic alignment probe",
            "input": DEFAULT_MODEL_INPUT,
            "metrics": DEFAULT_METRICS,
            "dark_matter_w": DEFAULT_DARK_MATTER_W,
            "state_vector": [float(value) for value in state_vector.tolist()],
            "normalized_state_vector": [float(value) for value in model_vector.tolist()],
            "phase_proxy_raw": phase_proxy_raw,
            "phase_proxy_clamped": phase_proxy_clamped,
        },
        "dataset": {
            "fixture_path": str(fixture_path),
            "fixture_sha256": _sha256(fixture_path),
            "record_count": len(records),
            "reference_mean_scalar": float(np.mean(scalars)),
        },
        "aggregate": {
            "official_overall_alignment": overall_alignment,
            "official_cosine_similarity": cosine_similarity,
            "official_phase_distance": phase_distance,
            "weighted_record_alignment_mean": float(weighted_local_alignment),
            "heuristic_band": band,
            "heuristic_summary": _heuristic_summary(overall_alignment),
        },
        "reproducibility": {
            "module_path": str(MODULE_PATH),
            "script_path": str(Path(__file__).resolve()),
            "command": "python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation",
            "python_version": sys.version.split()[0],
        },
        "records": record_results,
    }


def render_markdown_summary(diagnostic: dict) -> str:
    aggregate = diagnostic["aggregate"]
    dataset = diagnostic["dataset"]
    model = diagnostic["model"]
    lines = [
        "# Chang'e-4 / LND Empirical Validation",
        "",
        "## Summary",
        (
            "This report compares the deterministic 12D CST probe against six "
            "Chang'e-4 / Lunar Lander Neutron and Dosimetry (LND) reference "
            "measurements using the same harmonic alignment math as the test suite."
        ),
        "",
        "The current result lands in the "
        f"`{aggregate['heuristic_band']}` band.",
        aggregate["heuristic_summary"],
        "",
        "## Model",
        (
            "Probe: a fixed 12D state vector built from the current CST input bundle "
            "used by the Chang'e-4 test harness."
        ),
        f"- `cst_physics`: `{json.dumps(model['input']['cst_physics'], sort_keys=True)}`",
        f"- `bio_signatures`: `{json.dumps(model['input']['bio_signatures'], sort_keys=True)}`",
        f"- `cst_metrics`: `{json.dumps(model['input']['cst_metrics'], sort_keys=True)}`",
        f"- `metrics`: `{json.dumps(model['metrics'], sort_keys=True)}`",
        f"- `dark_matter_w`: `{model['dark_matter_w']}`",
        "",
        "## Data",
        (
            "Dataset: `tests/galactic_cosmic_rays/change4_lnd_reference.json` "
            f"with SHA-256 `{dataset['fixture_sha256']}`."
        ),
        "Sources used:",
        "- 2026-03-25 Research Square preprint on the Earth-Moon GCR cavity",
        "- 2024-03-11 LPSC 2024 abstract 1144",
        "- 2021 two-year Chang'e-4 / LND dose-rate paper",
        "- 2022 LND primary-vs-albedo proton paper",
        "",
        "## Match",
        f"- Official overall alignment: `{aggregate['official_overall_alignment']:.6f}`",
        f"- Official cosine similarity: `{aggregate['official_cosine_similarity']:.6f}`",
        f"- Official phase distance: `{aggregate['official_phase_distance']:.6f}`",
        (
            "- Weighted mean of per-record diagnostic alignment scores: "
            f"`{aggregate['weighted_record_alignment_mean']:.6f}`"
        ),
        "",
        (
            "Per-record `model_scalar_prediction` is the clamped mean of the first "
            "four normalized model dimensions. That is the same scalar proxy used in "
            "the alignment function's phase-distance term, so the deltas below are "
            "reproducible from the checked-in code."
        ),
        (
            "These per-record scores are a diagnostic decomposition. The official "
            "overall alignment above remains the canonical aggregate score."
        ),
        "",
        "| Record | Observed | Proxy predicted | Delta | Normalized target | Cosine | Local alignment |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for record in diagnostic["records"]:
        lines.append(
            "| "
            f"{record['id']} | "
            f"{record['observed_value']:.6f} | "
            f"{record['predicted_value_from_phase_proxy']:.6f} | "
            f"{record['raw_delta']:.6f} | "
            f"{record['normalized_target']:.6f} | "
            f"{record['record_cosine_similarity']:.6f} | "
            f"{record['record_alignment_score']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Reproduce",
            "Run the same commands from the repo root:",
            "",
            "```powershell",
            "python -m pytest tests/galactic_cosmic_rays/test_change4_alignment.py -q",
            "python -m pytest tests/galactic_cosmic_rays -q",
            "python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation",
            "```",
            "",
            "## Interpretation",
            (
                "The present score is best described as an interesting correlation, "
                "not a predictive validation. The model is matching the normalized "
                "shape of the Chang'e-4/LND reference basket, but it is not yet a "
                "held-out forecasting system."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def write_reports(output_dir: Path, diagnostic: dict) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_REPORT_NAME
    markdown_path = output_dir / MARKDOWN_REPORT_NAME
    json_path.write_text(json.dumps(diagnostic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown_summary(diagnostic), encoding="utf-8")
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

    diagnostic = build_change4_alignment_diagnostic()
    json_path, markdown_path = write_reports(args.output_dir, diagnostic)
    aggregate = diagnostic["aggregate"]

    print(f"Official overall alignment: {aggregate['official_overall_alignment']:.6f}")
    print(f"Official cosine similarity: {aggregate['official_cosine_similarity']:.6f}")
    print(f"Official phase distance: {aggregate['official_phase_distance']:.6f}")
    print(f"Heuristic band: {aggregate['heuristic_band']}")
    print(f"JSON report: {json_path}")
    print(f"Markdown summary: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
