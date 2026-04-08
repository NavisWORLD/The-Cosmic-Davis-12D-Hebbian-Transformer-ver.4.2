# PR-Ready Technical Summary

## GitHub PR Summary
- Model update: replaced the rule-only observable proxy with a deterministic learned residual-ridge calibrator layered on top of the preserved legacy heuristic in `cosmos/core/cst_critical_integration.py`.
- Locked lunar calibration bundle: `19` records from `change4_lnd_reference.json`, `artemis_i_unseen_reference.json`, and `artemis_i_m42_gcr_reference.json`.
- Learned calibrator training fit: `MAE 0.010578`, `RMSE 0.018473`.
- Legacy heuristic training fit on the same bundle: `MAE 0.021887`, `RMSE 0.031928`.
- Chang'e-4 harmonic alignment: `overall 0.641144`, `cosine 0.588829`, `phase distance 0.201910`.
- Chang'e-4 leave-one-out holdout:
  `learned MAE 0.005799`, `learned RMSE 0.007518`,
  `legacy MAE 0.004875`, `legacy RMSE 0.007565`.
- Chang'e-4 chronological 2026 holdout:
  `learned MAE 0.005183`, `learned RMSE 0.006901`,
  `legacy MAE 0.006539`, `legacy RMSE 0.006609`.
- Artemis I bundle diagnostic:
  `learned MAE 0.001548`, `learned RMSE 0.001878`,
  `legacy MAE 0.013579`, `legacy RMSE 0.018427`.
- Independent MSL/RAD external stress test:
  `alignment 0.603442`,
  `learned MAE 0.243874`, `learned RMSE 0.255642`,
  `legacy MAE 0.246836`, `legacy RMSE 0.258691`,
  `midpoint baseline MAE 0.101119`, `midpoint baseline RMSE 0.141276`.
- Final gate: `not_generalized`.

## Zenodo Summary
- Validation package now includes:
  `change4_lnd_reference.json`,
  `artemis_i_unseen_reference.json`,
  `artemis_i_m42_gcr_reference.json`,
  `msl_rad_reference.json`,
  the learned calibrator implementation,
  reproducible diagnostics,
  and the `tests/galactic_cosmic_rays` suite.
- Final empirical result:
  the learned calibrator improves the bundled lunar fit,
  but the independent MSL/RAD basket still favors simpler baselines.
- Reproducibility:
  `python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation`
  `python scripts/run_change4_heldout_validation.py --output-dir docs/validation`
  `python scripts/run_artemis_i_external_validation.py --output-dir docs/validation`
  `python scripts/run_msl_rad_external_validation.py --output-dir docs/validation`
  `python scripts/run_final_generalization_test.py --output-dir docs/validation`
  `python -m pytest tests/galactic_cosmic_rays -q`
