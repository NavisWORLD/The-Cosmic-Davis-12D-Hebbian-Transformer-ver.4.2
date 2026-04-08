# Final Generalization Test

## Summary
Does the locked observable-aware proxy generalize across all external lunar datasets in this validation bundle?
No. It improves materially over the original constant phase proxy and even wins on the Artemis I organ-dose basket, but it still fails the stricter per-dataset generalization gate because it does not beat the carryover baselines on the Artemis ratio basket.

- Gate status: `not_generalized`
- Rule: The observable-aware proxy must be among the best MAE and best RMSE baselines on every external dataset individually.

## artemis_i_external_ratios
- Best MAE baselines: `midpoint_0_5, change4_reference_mean, change4_weighted_mean`
- Best RMSE baselines: `change4_weighted_mean`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.279775 | 0.317106 | 0.463461 |
| observable_aware_proxy | 0.168575 | 0.216931 | 0.434582 |
| midpoint_0_5 | 0.164630 | 0.198358 | 0.274194 |
| change4_reference_mean | 0.164630 | 0.194447 | 0.272224 |
| change4_weighted_mean | 0.164630 | 0.187727 | 0.306804 |

## artemis_i_m42_gcr_organs
- Best MAE baselines: `observable_aware_proxy`
- Best RMSE baselines: `observable_aware_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.637153 | 0.637877 | 0.689267 |
| observable_aware_proxy | 0.272886 | 0.274572 | 0.325000 |
| midpoint_0_5 | 0.447886 | 0.448915 | 0.500000 |
| change4_reference_mean | 0.435243 | 0.436302 | 0.487357 |
| change4_weighted_mean | 0.400664 | 0.401814 | 0.452778 |

## Combined External View
- Best MAE baselines: `observable_aware_proxy`
- Best RMSE baselines: `observable_aware_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.472209 | 0.515270 | 0.689267 |
| observable_aware_proxy | 0.224742 | 0.249628 | 0.434582 |
| midpoint_0_5 | 0.317152 | 0.355911 | 0.500000 |
| change4_reference_mean | 0.310345 | 0.346341 | 0.487357 |
| change4_weighted_mean | 0.291725 | 0.321251 | 0.452778 |

## Interpretation
The combined picture is nuanced: the observable-aware proxy carries more physics than the constant phase proxy, but the final gate is deliberately conservative. Failing one external dataset means the bundle does not yet support a generalization claim.

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python scripts/run_final_generalization_test.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
