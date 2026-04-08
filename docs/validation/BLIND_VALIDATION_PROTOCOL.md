# Blind Validation Protocol V2

## Freeze
- Freeze label: `cst_radiation_validation_v2`
- Manifest: `docs/validation/validation_manifest_v2.json`
- Learned calibrator: residual ridge with `alpha 0.2`
- Locked lunar training bundle:
  `change4_lnd_reference.json`,
  `artemis_i_unseen_reference.json`,
  `artemis_i_m42_gcr_reference.json`

## Blind Workflow
1. Generate predictions from a redacted template:
   `python scripts/generate_blind_validation_predictions.py --template <template> --output <predictions>`
2. Reveal the held-out fixture and score the frozen predictions:
   `python scripts/score_blind_validation_predictions.py --predictions <predictions> --revealed <fixture> --output <scoring>`

## Current Frozen Outputs
- MSL blind template:
  `tests/galactic_cosmic_rays/blind_templates/msl_rad_blind_template.json`
- MSL frozen predictions:
  `docs/validation/blind_predictions_msl_v2.json`
- MSL blind scoring:
  `docs/validation/blind_scoring_msl_v2.json`
- CRaTER blind template:
  `tests/galactic_cosmic_rays/blind_templates/crater_lro_blind_template.json`

## Frozen Results
- MSL/RAD blind score:
  learned calibrator `MAE 0.011207`, `RMSE 0.014808`
  midpoint baseline `MAE 0.101119`, `RMSE 0.141276`
- CRaTER/LRO blind score:
  learned calibrator `MAE 0.018756`, `RMSE 0.019906`
  legacy heuristic `MAE 0.166919`, `RMSE 0.179047`
- Final status:
  `generalized`

## Interpretation
The protocol is now frozen and reproducible for the current `v2` bundle. This version clears the checked-in held-out and external gates, but it should still be described as a new frozen revision rather than the untouched original `v1` freeze.
