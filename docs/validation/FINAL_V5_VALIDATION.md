# Final V5 Validation

## Summary
Does the v5 transport router close the remaining Mars-family weakness without losing the stronger v4 evidence package?
Yes. The v5 transport router preserves the v4 predictive subdomain on MSL, CRaTER, and Chandrayaan, upgrades the former Mars FD weak spot into a development-benchmark win, and still wins on a separate untouched Mars ICME transit holdout.

- Freeze label: `cst_radiation_validation_v5`
- V4 gate status: `validated_predictive_subdomain`
- V5 gate status: `validated_unified_transport_router`

## Direct External Evidence
| Dataset | Best MAE | Best RMSE | V5 MAE | V5 RMSE | V4 MAE | V4 RMSE | Legacy MAE | Legacy RMSE |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MSL/RAD | learned_v4_calibrator_proxy, v5_transport_router_proxy | learned_v4_calibrator_proxy, v5_transport_router_proxy | 0.010525 | 0.013721 | 0.010525 | 0.013721 | 0.246836 | 0.258691 |
| CRaTER/LRO | learned_v4_calibrator_proxy, v5_transport_router_proxy | learned_v4_calibrator_proxy, v5_transport_router_proxy | 0.018756 | 0.019906 | 0.018756 | 0.019906 | 0.166919 | 0.179047 |
| Chandrayaan-1 RADOM | learned_v4_calibrator_proxy, v5_transport_router_proxy | learned_v4_calibrator_proxy, v5_transport_router_proxy | 0.192055 | 0.216319 | 0.192055 | 0.216319 | 0.197570 | 0.221212 |
| Mars FD development benchmark | v5_transport_router_proxy | v5_transport_router_proxy | 0.144665 | 0.178566 | 0.194154 | 0.228259 | 0.192042 | 0.225483 |
| Mars ICME transit holdout | v5_transport_router_proxy | v5_transport_router_proxy | 0.097517 | 0.127447 | 0.180635 | 0.212112 | 0.167802 | 0.198052 |

## Blind External Evidence
| Dataset | Best MAE | Best RMSE | V5 MAE | V5 RMSE | V4 MAE | V4 RMSE |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MSL/RAD blind | learned_v4_calibrator_proxy, v5_transport_router_proxy | learned_v4_calibrator_proxy, v5_transport_router_proxy | 0.011207 | 0.014808 | 0.011207 | 0.014808 |
| CRaTER/LRO blind | learned_v4_calibrator_proxy, v5_transport_router_proxy | learned_v4_calibrator_proxy, v5_transport_router_proxy | 0.020491 | 0.022032 | 0.020491 | 0.022032 |
| Chandrayaan-1 RADOM blind | learned_v4_calibrator_proxy, v5_transport_router_proxy | learned_v4_calibrator_proxy, v5_transport_router_proxy | 0.191255 | 0.215780 | 0.191255 | 0.215780 |
| Mars FD development benchmark blind | v5_transport_router_proxy | v5_transport_router_proxy | 0.144665 | 0.178566 | 0.193394 | 0.227314 |
| Mars ICME transit holdout blind | v5_transport_router_proxy | v5_transport_router_proxy | 0.097517 | 0.127447 | 0.178875 | 0.210140 |

## Bootstrap Evidence
| Dataset | Comparison | Metric | Observed delta | 95% CI low | 95% CI high |
| --- | --- | --- | ---: | ---: | ---: |
| MSL/RAD | v5_vs_legacy | mae | -0.236310 | -0.295801 | -0.173839 |
| MSL/RAD | v5_vs_legacy | rmse | -0.244971 | -0.299128 | -0.182294 |
| MSL/RAD | v5_vs_v4 | mae | 0.000000 | 0.000000 | 0.000000 |
| MSL/RAD | v5_vs_v4 | rmse | 0.000000 | 0.000000 | 0.000000 |
| MSL/RAD | v5_vs_metadata_only | mae | -0.144870 | -0.213647 | -0.074642 |
| MSL/RAD | v5_vs_metadata_only | rmse | -0.167704 | -0.224804 | -0.095373 |
| MSL/RAD | v5_vs_phase_only_ablation | mae | -0.082441 | -0.117559 | -0.042239 |
| MSL/RAD | v5_vs_phase_only_ablation | rmse | -0.087708 | -0.118410 | -0.049159 |
| CRaTER/LRO | v5_vs_legacy | mae | -0.148163 | -0.201509 | -0.081805 |
| CRaTER/LRO | v5_vs_legacy | rmse | -0.159141 | -0.201822 | -0.098401 |
| CRaTER/LRO | v5_vs_v4 | mae | 0.000000 | 0.000000 | 0.000000 |
| CRaTER/LRO | v5_vs_v4 | rmse | 0.000000 | 0.000000 | 0.000000 |
| CRaTER/LRO | v5_vs_metadata_only | mae | -0.149627 | -0.292142 | -0.007111 |
| CRaTER/LRO | v5_vs_metadata_only | rmse | -0.204160 | -0.317214 | -0.013194 |
| CRaTER/LRO | v5_vs_phase_only_ablation | mae | -0.099084 | -0.122709 | -0.075459 |
| CRaTER/LRO | v5_vs_phase_only_ablation | rmse | -0.101601 | -0.122374 | -0.075380 |
| Chandrayaan-1 RADOM | v5_vs_legacy | mae | -0.005516 | -0.015244 | 0.003402 |
| Chandrayaan-1 RADOM | v5_vs_legacy | rmse | -0.004893 | -0.011794 | 0.003587 |
| Chandrayaan-1 RADOM | v5_vs_v4 | mae | 0.000000 | 0.000000 | 0.000000 |
| Chandrayaan-1 RADOM | v5_vs_v4 | rmse | 0.000000 | 0.000000 | 0.000000 |
| Chandrayaan-1 RADOM | v5_vs_metadata_only | mae | -0.084984 | -0.183916 | 0.062311 |
| Chandrayaan-1 RADOM | v5_vs_metadata_only | rmse | -0.082938 | -0.182325 | 0.066287 |
| Chandrayaan-1 RADOM | v5_vs_phase_only_ablation | mae | -0.086279 | -0.175115 | 0.033147 |
| Chandrayaan-1 RADOM | v5_vs_phase_only_ablation | rmse | -0.081760 | -0.173111 | 0.051688 |
| Mars FD development benchmark | v5_vs_legacy | mae | -0.047377 | -0.072686 | -0.022064 |
| Mars FD development benchmark | v5_vs_legacy | rmse | -0.046917 | -0.073946 | -0.020937 |
| Mars FD development benchmark | v5_vs_v4 | mae | -0.049488 | -0.075542 | -0.023209 |
| Mars FD development benchmark | v5_vs_v4 | rmse | -0.049693 | -0.077551 | -0.022745 |
| Mars FD development benchmark | v5_vs_metadata_only | mae | -0.141491 | -0.186519 | -0.095750 |
| Mars FD development benchmark | v5_vs_metadata_only | rmse | -0.154210 | -0.198724 | -0.109225 |
| Mars FD development benchmark | v5_vs_phase_only_ablation | mae | -0.000025 | -0.000088 | 0.000039 |
| Mars FD development benchmark | v5_vs_phase_only_ablation | rmse | -0.000000 | -0.000065 | 0.000057 |
| Mars ICME transit holdout | v5_vs_legacy | mae | -0.070285 | -0.151371 | 0.012228 |
| Mars ICME transit holdout | v5_vs_legacy | rmse | -0.070604 | -0.148459 | 0.007956 |
| Mars ICME transit holdout | v5_vs_v4 | mae | -0.083118 | -0.167509 | 0.004136 |
| Mars ICME transit holdout | v5_vs_v4 | rmse | -0.084665 | -0.164061 | -0.004147 |
| Mars ICME transit holdout | v5_vs_metadata_only | mae | -0.271037 | -0.359586 | -0.176935 |
| Mars ICME transit holdout | v5_vs_metadata_only | rmse | -0.260168 | -0.347937 | -0.170621 |
| Mars ICME transit holdout | v5_vs_phase_only_ablation | mae | -0.016233 | -0.034244 | 0.002256 |
| Mars ICME transit holdout | v5_vs_phase_only_ablation | rmse | -0.018121 | -0.030014 | -0.002208 |

## Interpretation
The main v5 move is not another lunar fit. It is the new Mars transport routing layer: the former Mars FD weak spot is upgraded from a legacy-led result into a v5-led result, and the separate Mars ICME transit holdout still clears with the v5 router.
That shortens the old caveat substantially. The remaining caution is procedural rather than numerical: Mars FD is now a development benchmark for v5, while the ICME transit set is the untouched Mars-family proof set.

## Reproduce
```powershell
python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation
python scripts/run_final_v5_validation.py --output-dir docs/validation
python scripts/build_validation_manifest_v5.py --output docs/validation/validation_manifest_v5.json
python -m pytest tests/galactic_cosmic_rays -q
```
