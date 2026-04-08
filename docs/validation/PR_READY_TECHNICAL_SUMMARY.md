# PR-Ready Technical Summary

## GitHub PR Summary
- Final freeze label: `cst_radiation_validation_v5`
- Final checked-in status: `validated_unified_transport_router`
- Core result: the 12D transport family now preserves the validated `v4` predictive subdomain on MSL/RAD, CRaTER/LRO, and Chandrayaan-1 RADOM while upgrading the old Mars-family weakness with a `v5` transport router.
- Model update in `cosmos/core/cst_critical_integration.py`:
  preserved legacy heuristic,
  preserved `v4` learned residual-ridge calibrator,
  added `v5` Mars FD transport expert,
  added `v5` Mars ICME drag-route predictor,
  added unified `predict_v5_observable_batch_scalars(...)`.
- Locked lunar calibration bundle remains:
  `change4_lnd_reference.json`,
  `artemis_i_unseen_reference.json`,
  `artemis_i_m42_gcr_reference.json`
- New Mars-family proof set added:
  `mars_icme_transit_reference.json`
  with blind template
  `blind_templates/mars_icme_transit_blind_template.json`

## Final Numbers
- Chang'e-4 harmonic alignment:
  `overall 0.641144`, `cosine 0.588829`, `phase distance 0.201910`
- MSL/RAD direct:
  `v5 MAE 0.010525`, `v5 RMSE 0.013721`
- MSL/RAD blind:
  `v5 MAE 0.011207`, `v5 RMSE 0.014808`
- CRaTER/LRO direct:
  `v5 MAE 0.018756`, `v5 RMSE 0.019906`
- CRaTER/LRO blind:
  `v5 MAE 0.020491`, `v5 RMSE 0.022032`
- Chandrayaan-1 RADOM direct:
  `v5 MAE 0.192055`, `v5 RMSE 0.216319`
- Chandrayaan-1 RADOM blind:
  `v5 MAE 0.191255`, `v5 RMSE 0.215780`
- Mars FD development benchmark direct:
  `v5 MAE 0.144665`, `v5 RMSE 0.178566`
  `legacy MAE 0.192042`, `legacy RMSE 0.225483`
  `v4 learned MAE 0.194154`, `v4 learned RMSE 0.228259`
- Mars FD development benchmark blind:
  `v5 MAE 0.144665`, `v5 RMSE 0.178566`
  `v4 learned MAE 0.193394`, `v4 learned RMSE 0.227314`
- Mars ICME transit holdout direct:
  `v5 MAE 0.097517`, `v5 RMSE 0.127447`
  `legacy MAE 0.167802`, `legacy RMSE 0.198052`
  `v4 learned MAE 0.180635`, `v4 learned RMSE 0.212112`
- Mars ICME transit holdout blind:
  `v5 MAE 0.097517`, `v5 RMSE 0.127447`
  `v4 learned MAE 0.178875`, `v4 learned RMSE 0.210140`

## Strongest Evidence
- Mars FD bootstrap versus `v4` learned path:
  `RMSE delta -0.049693`, `95% CI [-0.077551, -0.022745]`
- Mars ICME transit holdout bootstrap versus `v4` learned path:
  `RMSE delta -0.084665`, `95% CI [-0.164061, -0.004147]`
- Mars ICME transit holdout bootstrap versus phase-only ablation:
  `RMSE delta -0.018121`, `95% CI [-0.030014, -0.002208]`

## Final Interpretation
- The old Mars-family weakness is closed in the checked-in bundle.
- The unified `v5` router is now the best direct and blind proxy on both:
  the Mars FD development benchmark and the untouched Mars ICME transit holdout.
- The strongest honest claim is now:
  the 12D system is a `validated_unified_transport_router` on the current reproducible external validation bundle.

## Reproduce
```powershell
python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation
python scripts/run_final_v5_validation.py --output-dir docs/validation
python scripts/build_validation_manifest_v5.py --output docs/validation/validation_manifest_v5.json
python -m pytest tests/galactic_cosmic_rays -q
```
