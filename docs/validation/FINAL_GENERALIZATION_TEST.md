# Final Generalization Test

## Summary
Does the locked observable-aware proxy generalize across all external lunar datasets in this validation bundle?
Yes, within this validation bundle. The locked observable-aware proxy is now among the best MAE and RMSE baselines on every external dataset included in the final gate.

- Gate status: `generalized`
- Rule: The observable-aware proxy must be among the best MAE and best RMSE baselines on every external dataset individually.

## artemis_i_external_ratios
- Best MAE baselines: `observable_aware_proxy`
- Best RMSE baselines: `observable_aware_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.279775 | 0.317106 | 0.463461 |
| observable_aware_proxy | 0.013579 | 0.018427 | 0.040833 |
| midpoint_0_5 | 0.164630 | 0.198358 | 0.274194 |
| change4_reference_mean | 0.164630 | 0.194447 | 0.272224 |
| change4_weighted_mean | 0.164630 | 0.187727 | 0.306804 |

## artemis_i_m42_gcr_organs
- Best MAE baselines: `observable_aware_proxy`
- Best RMSE baselines: `observable_aware_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.637153 | 0.637877 | 0.689267 |
| observable_aware_proxy | 0.043590 | 0.049263 | 0.064346 |
| midpoint_0_5 | 0.447886 | 0.448915 | 0.500000 |
| change4_reference_mean | 0.435243 | 0.436302 | 0.487357 |
| change4_weighted_mean | 0.400664 | 0.401814 | 0.452778 |

## Combined External View
- Best MAE baselines: `observable_aware_proxy`
- Best RMSE baselines: `observable_aware_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.472209 | 0.515270 | 0.689267 |
| observable_aware_proxy | 0.029739 | 0.038256 | 0.064346 |
| midpoint_0_5 | 0.317152 | 0.355911 | 0.500000 |
| change4_reference_mean | 0.310345 | 0.346341 | 0.487357 |
| change4_weighted_mean | 0.291725 | 0.321251 | 0.452778 |

## Interpretation
The combined picture is now much stronger. The observable-aware proxy carries more usable structure than the constant phase proxy and clears the deliberately conservative per-dataset gate across the current external bundle.
Because the proxy is still engineered rather than learned, this is best framed as validated bundle-level generalization, not proof of universal predictive power.

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python scripts/run_final_generalization_test.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
