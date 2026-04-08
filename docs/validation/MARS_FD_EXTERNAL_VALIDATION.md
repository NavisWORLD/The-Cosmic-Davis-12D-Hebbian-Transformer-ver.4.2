# Mars FD External Validation

## Summary
Does the frozen v2 model family carry signal into a broad unseen Mars surface-to-orbit Forbush-decrease basket?
Yes. Both the learned calibrator and the preserved legacy heuristic beat the naive carryover baselines on this broad Mars FD basket, although the legacy heuristic remains the single best proxy here.

- Paired events with both surface and orbit amplitudes: `79`

## External Alignment
- Official overall alignment: `0.598586`
- Official cosine similarity: `0.613689`
- Official phase distance: `0.446726`

## Baseline Comparison
- Best MAE baselines: `legacy_heuristic_proxy`
- Best RMSE baselines: `legacy_heuristic_proxy`
- Learned beats naive carryover baselines: `True`
- Legacy beats naive carryover baselines: `True`

| Baseline | MAE | RMSE | Max abs error |
| --- | ---: | ---: | ---: |
| model_phase_proxy | 0.449531 | 0.493566 | 0.689267 |
| legacy_heuristic_proxy | 0.192042 | 0.225483 | 0.432732 |
| learned_calibrator_proxy | 0.194154 | 0.228259 | 0.424888 |
| midpoint_0_5 | 0.285035 | 0.332157 | 0.500000 |
| lunar_bundle_mean | 0.275914 | 0.322457 | 0.487357 |
| lunar_bundle_weighted_mean | 0.252130 | 0.297057 | 0.452778 |

## Sample Diagnostics
| Record | Target | Legacy heuristic | Learned calibrator |
| --- | ---: | ---: | ---: |
| mars_fd_surface_to_orbit_ratio_001 | 0.672113 | 0.675000 | 0.663478 |
| mars_fd_surface_to_orbit_ratio_003 | 0.832073 | 0.675000 | 0.666219 |
| mars_fd_surface_to_orbit_ratio_006 | 0.867360 | 0.675000 | 0.665939 |
| mars_fd_surface_to_orbit_ratio_008 | 0.427673 | 0.675000 | 0.667482 |
| mars_fd_surface_to_orbit_ratio_009 | 0.807512 | 0.675000 | 0.665747 |
| mars_fd_surface_to_orbit_ratio_010 | 0.394876 | 0.675000 | 0.664894 |
| mars_fd_surface_to_orbit_ratio_011 | 0.623581 | 0.675000 | 0.665181 |
| mars_fd_surface_to_orbit_ratio_012 | 0.554642 | 0.675000 | 0.665749 |
| mars_fd_surface_to_orbit_ratio_013 | 0.268382 | 0.675000 | 0.666571 |
| mars_fd_surface_to_orbit_ratio_015 | 0.572581 | 0.675000 | 0.666734 |
| mars_fd_surface_to_orbit_ratio_016 | 0.905003 | 0.675000 | 0.664551 |
| mars_fd_surface_to_orbit_ratio_020 | 0.645503 | 0.675000 | 0.665971 |

## Interpretation
This is a post-freeze addendum check, not a rewritten v2 gate. The broad Mars FD basket is unseen relative to the locked lunar/Artemis training bundle.
On this basket, the structured proxies still carry signal well above the naive midpoint and lunar carryover means. The learned layer does not beat the preserved legacy heuristic here, so this strengthens the overall validation story without replacing the existing gate language.

## Reproduce
```powershell
python scripts/run_mars_fd_external_validation.py --output-dir docs/validation
python scripts/generate_blind_validation_predictions.py --template tests/galactic_cosmic_rays/blind_templates/mars_fd_surface_orbit_blind_template.json --output docs/validation/blind_predictions_mars_fd_v2.json --label mars_fd_v2
python scripts/score_blind_validation_predictions.py --predictions docs/validation/blind_predictions_mars_fd_v2.json --revealed tests/galactic_cosmic_rays/mars_fd_surface_orbit_reference.json --output docs/validation/blind_scoring_mars_fd_v2.json
```
