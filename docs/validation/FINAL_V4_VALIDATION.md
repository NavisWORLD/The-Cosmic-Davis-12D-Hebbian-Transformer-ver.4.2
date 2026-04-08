# Final V4 Validation

## Summary
Does the upgraded v4 evidence package support a stronger claim than the v3 validated model-family result?
Yes. The learned 12D calibrator now clears a predictive subdomain on MSL/RAD and CRaTER/LRO against stronger metadata-only and ablation baselines, while the broader model family remains stable on Mars FD and Chandrayaan-1 under both direct and blind evaluation.

- Freeze label: `cst_radiation_validation_v4`
- V3 gate status: `validated_model_family`
- V4 gate status: `validated_predictive_subdomain`

## Direct External Evidence
| Dataset | Best MAE | Best RMSE | Learned MAE | Learned RMSE | Metadata MAE | Metadata RMSE | Phase-only ablation MAE |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| MSL/RAD | learned_calibrator_proxy | learned_calibrator_proxy | 0.010525 | 0.013721 | 0.155396 | 0.181424 | 0.092967 |
| CRaTER/LRO | learned_calibrator_proxy | learned_calibrator_proxy | 0.018756 | 0.019906 | 0.168382 | 0.224066 | 0.117840 |
| Mars FD | legacy_heuristic_proxy | legacy_heuristic_proxy | 0.194154 | 0.228259 | 0.286157 | 0.332777 | 0.267897 |
| Chandrayaan-1 RADOM | learned_calibrator_proxy | learned_calibrator_proxy | 0.192055 | 0.216319 | 0.277039 | 0.299257 | 0.278333 |

## Blind External Evidence
| Dataset | Best MAE | Best RMSE | Learned MAE | Learned RMSE | Metadata MAE | Metadata RMSE |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MSL/RAD blind | learned_calibrator_proxy | learned_calibrator_proxy | 0.011207 | 0.014808 | 0.164641 | 0.185440 |
| CRaTER/LRO blind | learned_calibrator_proxy | learned_calibrator_proxy | 0.020491 | 0.022032 | 0.164858 | 0.219667 |
| Mars FD blind | legacy_heuristic_proxy | legacy_heuristic_proxy | 0.193394 | 0.227314 | 0.281070 | 0.327306 |
| Chandrayaan-1 RADOM blind | learned_calibrator_proxy | learned_calibrator_proxy | 0.191255 | 0.215780 | 0.272339 | 0.293660 |

## Bootstrap Evidence
| Dataset | Comparison | Metric | Observed delta | 95% CI low | 95% CI high |
| --- | --- | --- | ---: | ---: | ---: |
| MSL/RAD | learned_vs_metadata_only | mae | -0.144870 | -0.213647 | -0.074642 |
| MSL/RAD | learned_vs_metadata_only | rmse | -0.167704 | -0.224804 | -0.095373 |
| MSL/RAD | learned_vs_phase_only_ablation | mae | -0.082441 | -0.117559 | -0.042239 |
| MSL/RAD | learned_vs_phase_only_ablation | rmse | -0.087708 | -0.118410 | -0.049159 |
| MSL/RAD | learned_vs_legacy | mae | -0.236310 | -0.295801 | -0.173839 |
| MSL/RAD | learned_vs_legacy | rmse | -0.244971 | -0.299128 | -0.182294 |
| CRaTER/LRO | learned_vs_metadata_only | mae | -0.149627 | -0.292142 | -0.007111 |
| CRaTER/LRO | learned_vs_metadata_only | rmse | -0.204160 | -0.317214 | -0.013194 |
| CRaTER/LRO | learned_vs_phase_only_ablation | mae | -0.099084 | -0.122709 | -0.075459 |
| CRaTER/LRO | learned_vs_phase_only_ablation | rmse | -0.101601 | -0.122374 | -0.075380 |
| CRaTER/LRO | learned_vs_legacy | mae | -0.148163 | -0.201509 | -0.081805 |
| CRaTER/LRO | learned_vs_legacy | rmse | -0.159141 | -0.201822 | -0.098401 |
| Mars FD | learned_vs_metadata_only | mae | -0.092003 | -0.119275 | -0.063671 |
| Mars FD | learned_vs_metadata_only | rmse | -0.104518 | -0.124965 | -0.081708 |
| Mars FD | learned_vs_phase_only_ablation | mae | -0.073744 | -0.097791 | -0.048848 |
| Mars FD | learned_vs_phase_only_ablation | rmse | -0.085587 | -0.104270 | -0.064972 |
| Mars FD | learned_vs_legacy | mae | 0.002111 | 0.000326 | 0.003929 |
| Mars FD | learned_vs_legacy | rmse | 0.002776 | 0.001130 | 0.004349 |
| Chandrayaan-1 RADOM | learned_vs_metadata_only | mae | -0.084984 | -0.183916 | 0.062311 |
| Chandrayaan-1 RADOM | learned_vs_metadata_only | rmse | -0.082938 | -0.182325 | 0.066287 |
| Chandrayaan-1 RADOM | learned_vs_phase_only_ablation | mae | -0.086279 | -0.175115 | 0.033147 |
| Chandrayaan-1 RADOM | learned_vs_phase_only_ablation | rmse | -0.081760 | -0.173111 | 0.051688 |
| Chandrayaan-1 RADOM | learned_vs_legacy | mae | -0.005516 | -0.015244 | 0.003402 |
| Chandrayaan-1 RADOM | learned_vs_legacy | rmse | -0.004893 | -0.011794 | 0.003587 |

## Interpretation
The strongest new result is not just another win table. It is that the learned 12D calibrator still wins MSL and CRaTER after adding a metadata-only ridge baseline, multiple 12D ablations, bootstrap confidence intervals, and blind scoring.
Mars FD remains more mixed, but Chandrayaan-1 now also stays family-led with the learned proxy narrowly ahead while both structured 12D proxies beat the naive and metadata-only baselines.

## Reproduce
```powershell
python scripts/run_chandrayaan1_radom_external_validation.py --output-dir docs/validation
python scripts/run_final_v4_validation.py --output-dir docs/validation
python scripts/build_validation_manifest_v4.py --output docs/validation/validation_manifest_v4.json
python -m pytest tests/galactic_cosmic_rays -q
```
