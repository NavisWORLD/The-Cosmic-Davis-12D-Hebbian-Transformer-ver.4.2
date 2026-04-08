# Mars ICME Transit External Validation

## Summary
Does the v5 transport router carry the Mars-family upgrade into an untouched 1 AU to Mars ICME speed-ratio holdout?
Yes. The drag-routed Mars transport path becomes the best proxy on this untouched ICME speed-ratio basket, beating the preserved legacy heuristic, the v4 learned calibrator, and the naive metadata-only baseline.

## External Alignment
- Official overall alignment: `0.569497`
- Official cosine similarity: `0.599812`
- Official phase distance: `0.521445`

## Baseline Comparison
- Best MAE baselines: `v5_transport_router_proxy`
- Best RMSE baselines: `v5_transport_router_proxy`
- V5 beats legacy: `True`
- V5 beats v4: `True`
- V5 beats metadata-only: `True`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.521445 | 0.535186 | 0.689267 |
| legacy_heuristic_proxy | 0.167802 | 0.198052 | 0.325000 |
| learned_v4_calibrator_proxy | 0.180635 | 0.212112 | 0.342609 |
| v5_transport_router_proxy | 0.097517 | 0.127447 | 0.254938 |
| midpoint_0_5 | 0.332178 | 0.353358 | 0.500000 |
| lunar_bundle_mean | 0.319535 | 0.341500 | 0.487357 |
| lunar_bundle_weighted_mean | 0.284956 | 0.309385 | 0.452778 |
| metadata_only_ridge | 0.368554 | 0.387615 | 0.536914 |
| v5_zero_state_ablation | 0.131107 | 0.162562 | 0.328197 |
| v5_phase_only_ablation | 0.113750 | 0.145568 | 0.299229 |
| v5_reversed_state_ablation | 0.106643 | 0.137730 | 0.282926 |

## Bootstrap Evidence
| Comparison | Metric | Observed delta | 95% CI low | 95% CI high |
| --- | --- | ---: | ---: | ---: |
| v5_vs_legacy | mae | -0.070285 | -0.151371 | 0.012228 |
| v5_vs_legacy | rmse | -0.070604 | -0.148459 | 0.007956 |
| v5_vs_v4 | mae | -0.083118 | -0.167509 | 0.004136 |
| v5_vs_v4 | rmse | -0.084665 | -0.164061 | -0.004147 |
| v5_vs_metadata_only | mae | -0.271037 | -0.359586 | -0.176935 |
| v5_vs_metadata_only | rmse | -0.260168 | -0.347937 | -0.170621 |
| v5_vs_phase_only_ablation | mae | -0.016233 | -0.034244 | 0.002256 |
| v5_vs_phase_only_ablation | rmse | -0.018121 | -0.030014 | -0.002208 |

## Reproduce
```powershell
python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation
```
