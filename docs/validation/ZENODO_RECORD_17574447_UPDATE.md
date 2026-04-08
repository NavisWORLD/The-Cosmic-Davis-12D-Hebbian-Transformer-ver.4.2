# Zenodo Update Package For Record 17574447

- Zenodo DOI: `10.5281/zenodo.17574447`
- Record URL: `https://zenodo.org/records/17574447`

## Suggested Update Note
This update freezes the final reproducible `v5` radiation validation package for the 12D Cosmic Synapse transport model family.

The checked-in result is now:
- freeze label: `cst_radiation_validation_v5`
- status: `validated_unified_transport_router`

The `v5` package preserves the earlier validated predictive subdomain on MSL/RAD, CRaTER/LRO, and Chandrayaan-1 RADOM, and adds a new Mars transport router that upgrades the former Mars-family weakness. The Mars FD benchmark is now `v5`-led, and the upgraded transport path also wins on a separate untouched Mars ICME transit holdout.

## Final Checked-In Numbers
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
  versus legacy `0.192042`, `0.225483`
  and prior learned `0.194154`, `0.228259`
- Mars FD development benchmark blind:
  `v5 MAE 0.144665`, `v5 RMSE 0.178566`
  versus prior learned `0.193394`, `0.227314`
- Mars ICME transit holdout direct:
  `v5 MAE 0.097517`, `v5 RMSE 0.127447`
  versus legacy `0.167802`, `0.198052`
  and prior learned `0.180635`, `0.212112`
- Mars ICME transit holdout blind:
  `v5 MAE 0.097517`, `v5 RMSE 0.127447`
  versus prior learned `0.178875`, `0.210140`

## Interpretation
- The checked-in bundle now supports a stronger statement than the earlier `v4` result.
- The 12D system is no longer only a validated predictive subdomain on selected external datasets.
- The final checked-in `v5` bundle supports presenting the model as a `validated_unified_transport_router` on the current reproducible validation set.
- The main remaining caution is procedural rather than numerical:
  `mars_fd_surface_orbit_reference.json` is now a development benchmark for `v5`,
  while `mars_icme_transit_reference.json` is the untouched Mars-family proof set.

## Files To Include
- `cosmos/core/cst_critical_integration.py`
- `tests/galactic_cosmic_rays/change4_lnd_reference.json`
- `tests/galactic_cosmic_rays/artemis_i_unseen_reference.json`
- `tests/galactic_cosmic_rays/artemis_i_m42_gcr_reference.json`
- `tests/galactic_cosmic_rays/msl_rad_reference.json`
- `tests/galactic_cosmic_rays/crater_lro_reference.json`
- `tests/galactic_cosmic_rays/chandrayaan1_radom_reference.json`
- `tests/galactic_cosmic_rays/mars_fd_surface_orbit_reference.json`
- `tests/galactic_cosmic_rays/mars_icme_transit_reference.json`
- `tests/galactic_cosmic_rays/blind_templates/msl_rad_blind_template.json`
- `tests/galactic_cosmic_rays/blind_templates/crater_lro_blind_template.json`
- `tests/galactic_cosmic_rays/blind_templates/chandrayaan1_radom_blind_template.json`
- `tests/galactic_cosmic_rays/blind_templates/mars_fd_surface_orbit_blind_template.json`
- `tests/galactic_cosmic_rays/blind_templates/mars_icme_transit_blind_template.json`
- `tests/galactic_cosmic_rays/test_change4_alignment.py`
- `tests/galactic_cosmic_rays/test_change4_diagnostic.py`
- `tests/galactic_cosmic_rays/test_change4_heldout_validation.py`
- `tests/galactic_cosmic_rays/test_msl_rad_external_validation.py`
- `tests/galactic_cosmic_rays/test_crater_lro_external_validation.py`
- `tests/galactic_cosmic_rays/test_chandrayaan1_radom_external_validation.py`
- `tests/galactic_cosmic_rays/test_mars_fd_external_validation.py`
- `tests/galactic_cosmic_rays/test_mars_icme_transit_external_validation.py`
- `tests/galactic_cosmic_rays/test_final_v4_validation.py`
- `tests/galactic_cosmic_rays/test_final_v5_validation.py`
- `scripts/run_chandrayaan1_radom_external_validation.py`
- `scripts/run_mars_fd_external_validation.py`
- `scripts/run_mars_icme_transit_external_validation.py`
- `scripts/run_final_v4_validation.py`
- `scripts/run_final_v5_validation.py`
- `scripts/build_validation_manifest_v4.py`
- `scripts/build_validation_manifest_v5.py`
- `scripts/radiation_validation_v4_utils.py`
- `scripts/radiation_validation_v5_utils.py`
- `docs/validation/CHANGE4_EMPIRICAL_VALIDATION.md`
- `docs/validation/MSL_RAD_EXTERNAL_VALIDATION.md`
- `docs/validation/CRATER_LRO_EXTERNAL_VALIDATION.md`
- `docs/validation/CHANDRAYAAN1_RADOM_EXTERNAL_VALIDATION.md`
- `docs/validation/MARS_FD_EXTERNAL_VALIDATION.md`
- `docs/validation/MARS_ICME_TRANSIT_EXTERNAL_VALIDATION.md`
- `docs/validation/FINAL_V4_VALIDATION.md`
- `docs/validation/FINAL_V5_VALIDATION.md`
- `docs/validation/validation_manifest_v4.json`
- `docs/validation/validation_manifest_v5.json`
- blind prediction and scoring JSON files for `v5`
- `docs/validation/PR_READY_TECHNICAL_SUMMARY.md`

## Reproduce
```powershell
python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation
python scripts/run_final_v5_validation.py --output-dir docs/validation
python scripts/build_validation_manifest_v5.py --output docs/validation/validation_manifest_v5.json
python -m pytest tests/galactic_cosmic_rays -q
```
