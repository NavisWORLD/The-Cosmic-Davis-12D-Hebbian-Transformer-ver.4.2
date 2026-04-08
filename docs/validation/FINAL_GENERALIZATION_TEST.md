# Final Generalization Test

## Summary
Does the learned calibrator clear both the stricter Chang'e-4 held-out checks and the independent MSL/RAD external stress test?
Not yet. The learned calibrator improves the in-family lunar fit, but it still does not beat the simplest baselines on the independent MSL/RAD external basket.

- Gate status: `not_generalized`
- Rule: The learned calibrator must beat the legacy heuristic on both Chang'e-4 held-out splits and be among the best MAE and RMSE baselines on the independent MSL/RAD basket.

## Chang'e-4 Held-Out Checks
| Split | Learned MAE | Learned RMSE | Legacy MAE | Legacy RMSE | Learned beats legacy |
| --- | ---: | ---: | ---: | ---: | --- |
| leave_one_out | 0.005799 | 0.007518 | 0.004875 | 0.007565 | `False` |
| chronological_holdout_2026 | 0.005183 | 0.006901 | 0.006539 | 0.006609 | `False` |

## Artemis I Bundle Diagnostic
- Best MAE baselines: `learned_calibrator_proxy`
- Best RMSE baselines: `learned_calibrator_proxy`
- Learned calibrator: `MAE 0.001548`, `RMSE 0.001878`
- Legacy heuristic: `MAE 0.013579`, `RMSE 0.018427`

## Independent MSL/RAD Stress Test
- Best MAE baselines: `midpoint_0_5`
- Best RMSE baselines: `midpoint_0_5`
- Learned calibrator: `MAE 0.243874`, `RMSE 0.255642`
- Legacy heuristic: `MAE 0.246836`, `RMSE 0.258691`
- Midpoint baseline: `MAE 0.101119`, `RMSE 0.141276`

## Interpretation
The learned calibrator is stronger on the bundled lunar diagnostics overall, but mixed on the strict Chang'e-4 held-out splits, and the MSL/RAD basket remains the decisive external check.
Right now the final gate stays closed because the independent external basket still favors simpler baselines.

## Reproduce
```powershell
python scripts/run_change4_heldout_validation.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python scripts/run_msl_rad_external_validation.py --output-dir docs/validation
python scripts/run_final_generalization_test.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
