# Final Generalization Test

## Summary
Does the learned calibrator clear both the stricter Chang'e-4 held-out checks and the independent MSL/RAD external stress test?
Yes. The learned calibrator improves on held-out Chang'e-4 splits and also wins on the independent MSL/RAD external basket.

- Gate status: `generalized`
- Rule: The learned calibrator must beat the legacy heuristic on both Chang'e-4 held-out splits and be among the best MAE and RMSE baselines on the independent MSL/RAD basket.

## Chang'e-4 Held-Out Checks
| Split | Learned MAE | Learned RMSE | Legacy MAE | Legacy RMSE | Learned beats legacy |
| --- | ---: | ---: | ---: | ---: | --- |
| leave_one_out | 0.004827 | 0.007471 | 0.004875 | 0.007565 | `True` |
| chronological_holdout_2026 | 0.006416 | 0.006544 | 0.006539 | 0.006609 | `True` |

## Artemis I Bundle Diagnostic
- Best MAE baselines: `learned_calibrator_proxy`
- Best RMSE baselines: `learned_calibrator_proxy`
- Learned calibrator: `MAE 0.001548`, `RMSE 0.001878`
- Legacy heuristic: `MAE 0.013579`, `RMSE 0.018427`

## Independent MSL/RAD Stress Test
- Best MAE baselines: `learned_calibrator_proxy`
- Best RMSE baselines: `learned_calibrator_proxy`
- Learned calibrator: `MAE 0.010525`, `RMSE 0.013721`
- Legacy heuristic: `MAE 0.246836`, `RMSE 0.258691`
- Midpoint baseline: `MAE 0.101119`, `RMSE 0.141276`

## Interpretation
The learned calibrator is stronger on the bundled lunar diagnostics overall, and the updated held-out Chang'e-4 splits plus the MSL/RAD basket now move in the same direction.
Right now the final gate clears because the learned calibrator also wins the independent external basket.

## Reproduce
```powershell
python scripts/run_change4_heldout_validation.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python scripts/run_msl_rad_external_validation.py --output-dir docs/validation
python scripts/run_final_generalization_test.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
