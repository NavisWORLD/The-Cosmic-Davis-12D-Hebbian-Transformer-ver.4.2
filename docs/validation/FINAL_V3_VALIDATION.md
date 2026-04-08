# Final V3 Validation

## Summary
Does the frozen radiation model family hold up across the current full external bundle when direct reports and blind scoring are taken together?
Yes. The v2 learned-calibrator gate remains generalized on Chang'e-4, Artemis, MSL, and CRaTER, and the post-freeze Mars FD holdout confirms that the frozen model family still beats naive baselines out of family even when the legacy heuristic is the best Mars proxy.

- Freeze label: `cst_radiation_validation_v3`
- V2 gate status: `generalized`
- V3 gate status: `validated_model_family`
- Learned-calibrator status: `dominant_on_msl_and_crater_mixed_on_mars`

## External Basket
| Dataset | Best MAE | Best RMSE | Learned MAE | Learned RMSE | Legacy MAE | Legacy RMSE |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MSL/RAD | learned_calibrator_proxy | learned_calibrator_proxy | 0.010525 | 0.013721 | 0.246836 | 0.258691 |
| CRaTER/LRO | learned_calibrator_proxy | learned_calibrator_proxy | 0.018756 | 0.019906 | 0.166919 | 0.179047 |
| Mars FD | legacy_heuristic_proxy | legacy_heuristic_proxy | 0.194154 | 0.228259 | 0.192042 | 0.225483 |

## Blind Bundle
| Dataset | Best MAE | Best RMSE | Learned MAE | Learned RMSE | Legacy MAE | Legacy RMSE |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MSL/RAD blind | learned_calibrator_proxy | learned_calibrator_proxy | 0.011207 | 0.014808 | 0.246836 | 0.258691 |
| CRaTER/LRO blind | learned_calibrator_proxy | learned_calibrator_proxy | 0.020491 | 0.022032 | 0.166919 | 0.179047 |
| Mars FD blind | legacy_heuristic_proxy | legacy_heuristic_proxy | 0.193394 | 0.227314 | 0.192042 | 0.225483 |

## Interpretation
This is the strongest honest finish for the current checked-in bundle: the learned calibrator stays dominant on MSL and CRaTER, while Mars stays family-led with the legacy heuristic slightly ahead.
So the v3 claim is not that every overlay wins every mission. The v3 claim is that the frozen model family keeps beating naive baselines across the present external basket and reproduces that behavior under blind scoring.

## Reproduce
```powershell
python scripts/run_final_v3_validation.py --output-dir docs/validation
python scripts/build_validation_manifest_v3.py --output docs/validation/validation_manifest_v3.json
python -m pytest tests/galactic_cosmic_rays -q
```
