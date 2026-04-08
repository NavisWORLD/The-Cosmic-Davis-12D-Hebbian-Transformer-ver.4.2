# CRaTER/LRO External Validation

## Summary
How does the locked learned calibrator transfer to a supplementary CRaTER/LRO lunar radiation basket that was not used in the original Chang'e-4 alignment work?
The learned calibrator slightly beats the preserved legacy heuristic on MAE, but it does not win RMSE against the simple midpoint baseline.

## External Alignment
- Official overall alignment: `0.570570`
- Official cosine similarity: `0.536520`
- Official phase distance: `0.327278`

## Baseline Comparison
- Best MAE baselines: `learned_calibrator_proxy`
- Best RMSE baselines: `legacy_heuristic_proxy`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.327278 | 0.371215 | 0.562283 |
| legacy_heuristic_proxy | 0.166919 | 0.179047 | 0.235847 |
| learned_calibrator_proxy | 0.165971 | 0.179220 | 0.237893 |
| midpoint_0_5 | 0.168434 | 0.223017 | 0.373016 |

## Record Diagnostics
| Record | Target | Legacy heuristic | Learned calibrator |
| --- | ---: | ---: | ---: |
| crater_annual_10000km_to_microdosimeter_ratio | 0.873016 | 0.675000 | 0.677046 |
| crater_annual_surface_to_10000km_ratio | 0.503030 | 0.675000 | 0.677317 |
| crater_annual_surface_to_microdosimeter_ratio | 0.439153 | 0.675000 | 0.677046 |
| crater_june7_surface_to_10000km_event_ratio | 0.736842 | 0.675000 | 0.681107 |

## Reproduce
```powershell
python scripts/run_crater_lro_external_validation.py --output-dir docs/validation
```
