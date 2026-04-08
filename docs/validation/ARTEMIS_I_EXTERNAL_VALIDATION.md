# Artemis I External Validation

## Summary
Does the locked Chang'e-4 calibrated proxy generalize to an unseen Artemis I lunar-radiation basket?
Yes, within this unseen Artemis I basket. The locked observable-aware proxy beats the constant phase proxy and the carryover baselines on both MAE and RMSE.

This uses an unseen external basket from the Artemis I mission, not the Chang'e-4/LND calibration basket.

## External Alignment
- Official overall alignment: `0.545110`
- Official cosine similarity: `0.478926`
- Official phase distance: `0.256336`

## Baseline Comparison
- Best MAE baselines: `observable_aware_proxy`
- Best RMSE baselines: `observable_aware_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.279775 | 0.317106 | 0.463461 |
| observable_aware_proxy | 0.013579 | 0.018427 | 0.040833 |
| midpoint_0_5 | 0.164630 | 0.198358 | 0.274194 |
| change4_reference_mean | 0.164630 | 0.194447 | 0.272224 |
| change4_weighted_mean | 0.164630 | 0.187727 | 0.306804 |

## Record Diagnostics
| Record | Target | Phase proxy | Obs-aware proxy | Phase delta | Obs-aware delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| artemis_i_inner_belt_peak_shield_ratio | 0.240418 | 0.310733 | 0.248000 | 0.070315 | 0.007582 |
| artemis_i_hsu1_hsu2_peak_ratio | 0.466899 | 0.310733 | 0.470000 | -0.156166 | 0.003101 |
| artemis_i_gcr_lunar_flyby_reduction_ratio | 0.666667 | 0.310733 | 0.707500 | -0.355934 | 0.040833 |
| artemis_i_gcr_dose_equivalent_rate_ratio | 0.774194 | 0.310733 | 0.762857 | -0.463461 | -0.011336 |
| artemis_i_total_mission_dose_equivalent_ratio | 0.754237 | 0.310733 | 0.762857 | -0.443505 | 0.008620 |
| artemis_i_rotation_dose_drop_ratio | 0.500000 | 0.310733 | 0.490000 | -0.189267 | -0.010000 |

## Interpretation
This external Artemis I basket is the real cross-mission check. On the current code path, the locked observable-aware proxy wins the error comparison against the constant phase proxy and the carryover baselines.
That is evidence of cross-mission generalization inside this checked-in bundle, although it is still best described as engineered generalization rather than universal proof.

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
