# MSL/RAD External Validation

## Summary
Does the learned calibrator, trained on the locked Chang'e-4 + Artemis I bundle, generalize to an independent MSL/RAD Mars surface-to-cruise basket?
Yes. The learned calibrator is the best MAE and RMSE baseline on the independent MSL/RAD basket.

This is the independent out-of-family stress test for the learned calibrator.

## External Alignment
- Official overall alignment: `0.603442`
- Official cosine similarity: `0.533798`
- Official phase distance: `0.187625`

## Baseline Comparison
- Best MAE baselines: `learned_calibrator_proxy`
- Best RMSE baselines: `learned_calibrator_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.187625 | 0.234860 | 0.487697 |
| legacy_heuristic_proxy | 0.246836 | 0.258691 | 0.352674 |
| learned_calibrator_proxy | 0.010525 | 0.013721 | 0.026010 |
| midpoint_0_5 | 0.101119 | 0.141276 | 0.298429 |
| lunar_bundle_mean | 0.109548 | 0.141986 | 0.285787 |
| lunar_bundle_weighted_mean | 0.132601 | 0.149479 | 0.251207 |

## Record Diagnostics
| Record | Target | Legacy heuristic | Learned calibrator | Observed raw | Learned raw |
| --- | ---: | ---: | ---: | ---: | ---: |
| msl_rad_2014_surface_to_cruise_charged_flux_ratio | 0.447552 | 0.772800 | 0.473562 | 0.640000 | 0.677194 |
| msl_rad_2014_surface_to_cruise_fluence_rate_ratio | 0.475452 | 0.675000 | 0.468015 | 1.840000 | 1.811219 |
| msl_rad_2014_surface_to_cruise_dose_rate_ratio | 0.437500 | 0.700500 | 0.431111 | 0.210000 | 0.206933 |
| msl_rad_2014_surface_to_cruise_quality_factor_ratio | 0.798429 | 0.675000 | 0.816812 | 3.050000 | 3.120222 |
| msl_rad_2014_surface_to_cruise_dose_equivalent_rate_ratio | 0.347826 | 0.700500 | 0.352137 | 0.640000 | 0.647932 |
| msl_rad_2014_surface_to_cruise_mission_dose_equivalent_ratio | 0.483384 | 0.700500 | 0.484008 | 320.000000 | 320.413029 |

## Interpretation
The learned calibrator clears the independent MSL/RAD stress test.
That is a stronger cross-mission result than the lunar-only bundle can show on its own.

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_msl_rad_external_validation.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
