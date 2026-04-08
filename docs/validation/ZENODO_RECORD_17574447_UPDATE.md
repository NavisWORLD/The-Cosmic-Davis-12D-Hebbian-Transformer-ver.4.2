# Zenodo Update Package For Record 17574447

- Zenodo DOI: `10.5281/zenodo.17574447`
- Record URL: `https://zenodo.org/records/17574447`

## Suggested Update Note
This update adds a reproducible empirical validation bundle for the 12D Cosmic Synapse radiation-alignment work. The rule-only observable proxy has been replaced with a deterministic learned residual-ridge calibrator layered on top of the preserved legacy heuristic. The locked lunar calibration bundle contains `19` records from Chang'e-4/LND and Artemis I reference fixtures.

Final checked-in numbers:
- Chang'e-4 harmonic alignment:
  `overall 0.641144`, `cosine 0.588829`, `phase distance 0.201910`
- Learned calibrator training fit on the locked lunar bundle:
  `MAE 0.010578`, `RMSE 0.018473`
- Legacy heuristic training fit on the same bundle:
  `MAE 0.021887`, `RMSE 0.031928`
- Chang'e-4 leave-one-out holdout:
  `learned MAE 0.005799`, `learned RMSE 0.007518`,
  `legacy MAE 0.004875`, `legacy RMSE 0.007565`
- Chang'e-4 chronological 2026 holdout:
  `learned MAE 0.005183`, `learned RMSE 0.006901`,
  `legacy MAE 0.006539`, `legacy RMSE 0.006609`
- Artemis I bundle diagnostic:
  `learned MAE 0.001548`, `learned RMSE 0.001878`,
  `legacy MAE 0.013579`, `legacy RMSE 0.018427`
- Independent MSL/RAD external stress test:
  `alignment 0.603442`,
  `learned MAE 0.243874`, `learned RMSE 0.255642`,
  `legacy MAE 0.246836`, `legacy RMSE 0.258691`,
  `midpoint baseline MAE 0.101119`, `midpoint baseline RMSE 0.141276`
- Final gate:
  `not_generalized`

Interpretation:
- the learned calibrator improves the bundled lunar fit
- the independent MSL/RAD basket still favors simpler baselines
- the current result supports reproducible empirical alignment work, not a finalized cross-mission predictive claim

## Files To Include
- `cosmos/core/cst_critical_integration.py`
- `tests/galactic_cosmic_rays/change4_lnd_reference.json`
- `tests/galactic_cosmic_rays/artemis_i_unseen_reference.json`
- `tests/galactic_cosmic_rays/artemis_i_m42_gcr_reference.json`
- `tests/galactic_cosmic_rays/msl_rad_reference.json`
- `tests/galactic_cosmic_rays/test_change4_alignment.py`
- `tests/galactic_cosmic_rays/test_change4_diagnostic.py`
- `tests/galactic_cosmic_rays/test_change4_heldout_validation.py`
- `tests/galactic_cosmic_rays/test_artemis_i_external_validation.py`
- `tests/galactic_cosmic_rays/test_msl_rad_external_validation.py`
- `tests/galactic_cosmic_rays/test_final_generalization_test.py`
- `scripts/run_change4_alignment_diagnostic.py`
- `scripts/run_change4_heldout_validation.py`
- `scripts/run_artemis_i_external_validation.py`
- `scripts/run_msl_rad_external_validation.py`
- `scripts/run_final_generalization_test.py`
- `docs/validation/CHANGE4_EMPIRICAL_VALIDATION.md`
- `docs/validation/CHANGE4_HELDOUT_VALIDATION.md`
- `docs/validation/ARTEMIS_I_EXTERNAL_VALIDATION.md`
- `docs/validation/MSL_RAD_EXTERNAL_VALIDATION.md`
- `docs/validation/FINAL_GENERALIZATION_TEST.md`
- `docs/validation/change4_alignment_report.json`
- `docs/validation/change4_heldout_validation_report.json`
- `docs/validation/artemis_i_external_validation_report.json`
- `docs/validation/msl_rad_external_validation_report.json`
- `docs/validation/final_generalization_test_report.json`
- `docs/validation/PR_READY_TECHNICAL_SUMMARY.md`

## Reproduce
```powershell
python scripts/run_change4_alignment_diagnostic.py --output-dir docs/validation
python scripts/run_change4_heldout_validation.py --output-dir docs/validation
python scripts/run_artemis_i_external_validation.py --output-dir docs/validation
python scripts/run_msl_rad_external_validation.py --output-dir docs/validation
python scripts/run_final_generalization_test.py --output-dir docs/validation
python -m pytest tests/galactic_cosmic_rays -q
```
