# Artemis I External Validation

## Summary
Does the locked Chang'e-4 calibrated proxy generalize to an unseen Artemis I lunar-radiation basket?
Not yet. It improves over the constant phase proxy, but it does not beat the simplest carryover baselines on aggregate external error.

This uses an unseen external basket from the Artemis I mission, not the Chang'e-4/LND calibration basket.

## External Alignment
- Official overall alignment: `0.545110`
- Official cosine similarity: `0.478926`
- Official phase distance: `0.256336`

## Baseline Comparison
- Best MAE baselines: `midpoint_0_5, change4_reference_mean, change4_weighted_mean`
- Best RMSE baselines: `change4_weighted_mean`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.279775 | 0.317106 | 0.463461 |
| observable_aware_proxy | 0.168575 | 0.216931 | 0.434582 |
| midpoint_0_5 | 0.164630 | 0.198358 | 0.274194 |
| change4_reference_mean | 0.164630 | 0.194447 | 0.272224 |
| change4_weighted_mean | 0.164630 | 0.187727 | 0.306804 |

## Record Diagnostics
| Record | Target | Phase proxy | Obs-aware proxy | Phase delta | Obs-aware delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| artemis_i_inner_belt_peak_shield_ratio | 0.240418 | 0.310733 | 0.675000 | 0.070315 | 0.434582 |
| artemis_i_hsu1_hsu2_peak_ratio | 0.466899 | 0.310733 | 0.675000 | -0.156166 | 0.208101 |
| artemis_i_gcr_lunar_flyby_reduction_ratio | 0.666667 | 0.310733 | 0.707500 | -0.355934 | 0.040833 |
| artemis_i_gcr_dose_equivalent_rate_ratio | 0.774194 | 0.310733 | 0.700500 | -0.463461 | -0.073694 |
| artemis_i_total_mission_dose_equivalent_ratio | 0.754237 | 0.310733 | 0.700500 | -0.443505 | -0.053737 |
| artemis_i_rotation_dose_drop_ratio | 0.500000 | 0.310733 | 0.700500 | -0.189267 | 0.200500 |

## Interpretation
The external Artemis I basket is the harder test. The locked Chang'e-4 calibration carries some structure across missions, but its observable-aware proxy still does not win the aggregate error contest against the simplest carryover baselines.
That means we are not yet at a credible generalization claim.

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
