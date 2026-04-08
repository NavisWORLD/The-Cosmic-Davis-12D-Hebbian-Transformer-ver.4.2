# Chang'e-4 Held-Out Validation

## Summary
This report asks the harder question: does the current 12D phase-proxy prediction beat simple baselines on held-out normalized Chang'e-4/LND targets?
Answer: the original constant phase proxy does not. The new learned residual-ridge calibrator materially improves over the phase proxy and the preserved legacy heuristic, but it still needs out-of-family stress testing before it can be called predictive.

## Leave-One-Out Baselines
Each record is treated as held out while simple baselines are built from the remaining records.
- Best MAE baseline: `learned_calibrator_proxy`
- Best RMSE baseline: `learned_calibrator_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.316189 | 0.337171 | 0.461995 |
| legacy_heuristic_proxy | 0.004875 | 0.007565 | 0.016000 |
| learned_calibrator_proxy | 0.004827 | 0.007471 | 0.015889 |
| midpoint_0_5 | 0.253100 | 0.270326 | 0.432272 |
| leave_one_out_mean | 0.298663 | 0.324037 | 0.533898 |
| leave_one_out_weighted_mean | 0.280711 | 0.318004 | 0.551143 |

## Chronological Holdout
Training-style baselines are fit only on the pre-2026 records and evaluated on the two 2026 cavity records.
- Best MAE baseline: `learned_calibrator_proxy`
- Best RMSE baseline: `learned_calibrator_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.316136 | 0.324485 | 0.389267 |
| legacy_heuristic_proxy | 0.006539 | 0.006609 | 0.007500 |
| learned_calibrator_proxy | 0.006416 | 0.006544 | 0.007702 |
| midpoint_0_5 | 0.316136 | 0.336793 | 0.432272 |
| train_mean | 0.316136 | 0.370481 | 0.509304 |
| train_weighted_mean | 0.316136 | 0.379966 | 0.526925 |

## Interpretation
This is the key distinction between correlation and prediction. The 12D probe still yields a nontrivial harmonic alignment score. The original constant phase proxy does not outperform simple baselines across the full dataset.
The learned calibrator is fit by refitting a residual-ridge model on each training split, so these errors are stricter than the old in-sample heuristic report. That still makes this a calibration result, not proof of external prediction.

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_change4_heldout_validation.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
