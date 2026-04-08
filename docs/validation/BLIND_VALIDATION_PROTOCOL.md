# Blind Validation Protocol V1

## Freeze
- Freeze label: `cst_radiation_validation_v1`
- Manifest: `docs/validation/validation_manifest_v1.json`
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
  `docs/validation/blind_predictions_msl_v1.json`
- MSL blind scoring:
  `docs/validation/blind_scoring_msl_v1.json`
- CRaTER blind template:
  `tests/galactic_cosmic_rays/blind_templates/crater_lro_blind_template.json`
- CRaTER frozen predictions:
  `docs/validation/blind_predictions_crater_v1.json`
- CRaTER blind scoring:
  `docs/validation/blind_scoring_crater_v1.json`

## Frozen Results
- MSL/RAD blind score:
  learned calibrator `MAE 0.247154`, `RMSE 0.259264`
  midpoint baseline `MAE 0.101119`, `RMSE 0.141276`
- CRaTER/LRO blind score:
  learned calibrator `MAE 0.165971`, `RMSE 0.179220`
  legacy heuristic `MAE 0.166919`, `RMSE 0.179047`
- Final status:
  `not_generalized`

## Interpretation
The protocol is now frozen and reproducible. The model is stronger than the original phase proxy and stronger than the legacy heuristic on some bundled and supplementary checks, but the independent MSL/RAD blind score still blocks a full predictive-validation claim.
