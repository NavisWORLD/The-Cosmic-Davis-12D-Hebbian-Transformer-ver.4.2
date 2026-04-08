# Artemis I Calibration-Bundle Diagnostic

## Summary
How well does the learned calibrator fit the Artemis I ratio basket that now participates in the locked lunar calibration bundle?
The learned calibrator is the best MAE and RMSE baseline on this Artemis I calibration basket.

This basket is now part of the locked lunar calibration bundle, so it is reported as a post-fit diagnostic rather than an independent holdout.

## External Alignment
- Official overall alignment: `0.545110`
- Official cosine similarity: `0.478926`
- Official phase distance: `0.256336`

## Baseline Comparison
- Best MAE baselines: `learned_calibrator_proxy`
- Best RMSE baselines: `learned_calibrator_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.279775 | 0.317106 | 0.463461 |
| legacy_heuristic_proxy | 0.013579 | 0.018427 | 0.040833 |
| learned_calibrator_proxy | 0.001548 | 0.001878 | 0.003038 |
| midpoint_0_5 | 0.164630 | 0.198358 | 0.274194 |
| change4_reference_mean | 0.164630 | 0.194447 | 0.272224 |
| change4_weighted_mean | 0.164630 | 0.187727 | 0.306804 |

## Record Diagnostics
| Record | Target | Phase proxy | Learned calibrator | Phase delta | Learned delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| artemis_i_inner_belt_peak_shield_ratio | 0.240418 | 0.310733 | 0.241117 | 0.070315 | 0.000699 |
| artemis_i_hsu1_hsu2_peak_ratio | 0.466899 | 0.310733 | 0.466714 | -0.156166 | -0.000185 |
| artemis_i_gcr_lunar_flyby_reduction_ratio | 0.666667 | 0.310733 | 0.669704 | -0.355934 | 0.003038 |
| artemis_i_gcr_dose_equivalent_rate_ratio | 0.774194 | 0.310733 | 0.771892 | -0.463461 | -0.002302 |
| artemis_i_total_mission_dose_equivalent_ratio | 0.754237 | 0.310733 | 0.754924 | -0.443505 | 0.000687 |
| artemis_i_rotation_dose_drop_ratio | 0.500000 | 0.310733 | 0.497623 | -0.189267 | -0.002377 |

## Interpretation
This Artemis I basket now measures how well the learned calibrator fits one of the locked lunar calibration sources after the heuristic was replaced by a trained residual-ridge layer.
It tells us the learned layer fits the existing lunar bundle well; the true cross-mission stress test now moves to the independent MSL/RAD basket.

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
