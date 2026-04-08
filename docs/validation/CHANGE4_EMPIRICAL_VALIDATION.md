# Chang'e-4 / LND Empirical Validation

## Summary
This report compares the deterministic 12D CST probe against six Chang'e-4 / Lunar Lander Neutron and Dosimetry (LND) reference measurements using the same harmonic alignment math as the test suite.

The current result lands in the `interesting_correlation` band.
The current 12D probe shows a real mid-strength correlation signal, but not enough evidence to call the model predictive.

## Model
Probe: a fixed 12D state vector built from the current CST input bundle used by the Chang'e-4 test harness.
- `cst_physics`: `{"entanglement_score": 0.64, "geometric_phase_rad": 0.71, "phase_velocity": 0.028}`
- `bio_signatures`: `{"arousal": 0.31, "intensity": 0.77, "valence": 0.09}`
- `cst_metrics`: `{"ci_b": 0.41, "ci_c": 0.29, "x12_avg": 0.58}`
- `metrics`: `{"decoherence_risk": 0.22, "entropy_quality": 0.78}`
- `dark_matter_w`: `0.36`

## Data
Dataset: `tests/galactic_cosmic_rays/change4_lnd_reference.json` with SHA-256 `77e313d2901c8578eb3be6e223c0771169403043ef29800751c6fade918da798`.
Sources used:
- 2026-03-25 Research Square preprint on the Earth-Moon GCR cavity
- 2024-03-11 LPSC 2024 abstract 1144
- 2021 two-year Chang'e-4 / LND dose-rate paper
- 2022 LND primary-vs-albedo proton paper

## Match
- Official overall alignment: `0.641144`
- Official cosine similarity: `0.588829`
- Official phase distance: `0.201910`
- Weighted mean of per-record diagnostic alignment scores: `0.578953`

Per-record `model_scalar_prediction` is the clamped mean of the first four normalized model dimensions. That is the same scalar proxy used in the alignment function's phase-distance term, so the deltas below are reproducible from the checked-in code.
These per-record scores are a diagnostic decomposition. The official overall alignment above remains the canonical aggregate score.
The legacy heuristic is preserved as a baseline, and a learned residual-ridge calibrator is fit on the locked Chang'e-4 + Artemis I bundle for engineering diagnostics. That learned layer is useful, but it should not be confused with the canonical harmonic alignment score.

| Record | Observed | Phase proxy | Legacy heuristic | Learned calibrator | Phase delta | Learned delta | Normalized target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| change4_lnd_2026_cavity_low_energy_reduction | 0.700000 | 0.310733 | 0.707500 | 0.699983 | -0.389267 | -0.000017 | 0.700000 | 
| change4_lnd_2026_cavity_duration | 2.000000 | 9.175936 | 2.164695 | 2.010374 | 7.175936 | 0.010374 | 0.067728 | 
| change4_lnd_2024_dose_equivalent | 1369.000000 | 621.465343 | 1401.000000 | 1367.120845 | -747.534657 | -1.879155 | 0.684500 | 
| change4_lnd_2024_charged_fraction | 10.200000 | 4.101671 | 10.200960 | 10.198848 | -6.098329 | -0.001152 | 0.772727 | 
| change4_lnd_2021_neutral_fraction | 2.670000 | 3.933876 | 2.671260 | 2.663311 | 1.263876 | -0.006689 | 0.210900 | 
| change4_lnd_2022_albedo_primary_ratio | 0.640000 | 0.310733 | 0.640000 | 0.639815 | -0.329267 | -0.000185 | 0.640000 | 

## Reproduce
Run the same commands from the repo root:

```powershell
python -m pytest tests/galactic_cosmic_rays/test_change4_alignment.py -q
python -m pytest tests/galactic_cosmic_rays -q
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
```

## Interpretation
The present score is best described as an interesting correlation, not a predictive validation. The model is matching the normalized shape of the Chang'e-4/LND reference basket, but it is not yet a held-out forecasting system.
