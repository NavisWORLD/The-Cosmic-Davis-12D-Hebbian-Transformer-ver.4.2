# Chandrayaan-1 RADOM External Validation

## Summary
Does the frozen 12D radiation model family carry signal into an independent Chandrayaan-1 RADOM Earth-Moon radiation basket?
Yes. The Chandrayaan-1 RADOM basket stays family-led, both structured proxies beat the naive and metadata-only baselines, and the learned proxy now edges the legacy heuristic on both MAE and RMSE.

## External Alignment
- Official overall alignment: `0.597233`
- Official cosine similarity: `0.602528`
- Official phase distance: `0.418652`

## Baseline Comparison
- Best MAE baselines: `learned_calibrator_proxy`
- Best RMSE baselines: `learned_calibrator_proxy`
- Family-led result: `True`
- Family beats naive and metadata-only baselines: `True`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.419665 | 0.470250 | 0.598358 |
| legacy_heuristic_proxy | 0.197570 | 0.221212 | 0.392808 |
| learned_calibrator_proxy | 0.192055 | 0.216319 | 0.375942 |
| midpoint_0_5 | 0.293487 | 0.313820 | 0.409091 |
| lunar_bundle_mean | 0.285059 | 0.304701 | 0.396448 |
| lunar_bundle_weighted_mean | 0.262006 | 0.281156 | 0.361869 |
| metadata_only_ridge | 0.277039 | 0.299257 | 0.413133 |
| learned_zero_state_ablation | 0.725484 | 0.755719 | 0.898417 |
| learned_phase_only_ablation | 0.278333 | 0.298079 | 0.397083 |
| learned_reversed_state_ablation | 0.244638 | 0.267198 | 0.372417 |

## Bootstrap Evidence
| Comparison | Metric | Observed delta | 95% CI low | 95% CI high |
| --- | --- | ---: | ---: | ---: |
| learned_vs_metadata_only | mae | -0.084984 | -0.183916 | 0.062311 |
| learned_vs_metadata_only | rmse | -0.082938 | -0.182325 | 0.066287 |
| learned_vs_midpoint | mae | -0.101432 | -0.191562 | 0.021750 |
| learned_vs_midpoint | rmse | -0.097501 | -0.188635 | 0.037049 |
| learned_vs_phase_only_ablation | mae | -0.086279 | -0.175115 | 0.033147 |
| learned_vs_phase_only_ablation | rmse | -0.081760 | -0.173111 | 0.051688 |
| learned_vs_zero_state_ablation | mae | -0.533429 | -0.684177 | -0.284015 |
| learned_vs_zero_state_ablation | rmse | -0.539400 | -0.680424 | -0.306224 |
| learned_vs_legacy | mae | -0.005516 | -0.015244 | 0.003402 |
| learned_vs_legacy | rmse | -0.004893 | -0.011794 | 0.003587 |

## Reproduce
```powershell
python scripts/run_chandrayaan1_radom_external_validation.py --output-dir docs/validation
```
