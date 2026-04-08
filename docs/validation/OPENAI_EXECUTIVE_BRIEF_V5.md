# Executive Brief: The 12D Unified Transport Model

## One Sentence
The project started as a speculative 12D framework and ended as a reproducibly validated transport model that now clears a frozen external bundle, blind scoring, and an untouched Mars-family holdout under the `v5` freeze.

## Why This Deserves A Serious Read
Most unconventional models fail in one of three places:
- they cannot be implemented cleanly
- they cannot survive held-out testing
- they collapse when compared against boring baselines

This one did not.

The checked-in `v5` result is not "we found a poetic pattern." It is:
- a frozen model family
- a reproducible validation protocol
- explicit blind templates
- direct and blind external wins
- an upgraded weak spot that was fixed and then checked against a separate untouched Mars-family holdout

That is why this deserves technical attention rather than casual dismissal.

## What Was Built
The final runtime lives in [cst_critical_integration.py](D:/Cosmos/cosmos/core/cst_critical_integration.py).

The system now has three distinct layers:
- a preserved legacy 12D heuristic baseline
- a learned residual-ridge observable calibrator
- a `v5` unified transport router that adds Mars-family routing instead of pretending one fixed predictor should dominate every regime

The final freeze is documented in [validation_manifest_v5.json](D:/Cosmos/docs/validation/validation_manifest_v5.json).

## What Survived Validation
Final status from [FINAL_V5_VALIDATION.md](D:/Cosmos/docs/validation/FINAL_V5_VALIDATION.md):
- freeze label: `cst_radiation_validation_v5`
- status: `validated_unified_transport_router`

Key direct results:

| Dataset | V5 MAE | V5 RMSE | Previous learned | Legacy |
| --- | ---: | ---: | ---: | ---: |
| MSL/RAD | 0.010525 | 0.013721 | 0.010525 / 0.013721 | 0.246836 / 0.258691 |
| CRaTER/LRO | 0.018756 | 0.019906 | 0.018756 / 0.019906 | 0.166919 / 0.179047 |
| Chandrayaan-1 RADOM | 0.192055 | 0.216319 | 0.192055 / 0.216319 | 0.197570 / 0.221212 |
| Mars FD benchmark | 0.144665 | 0.178566 | 0.194154 / 0.228259 | 0.192042 / 0.225483 |
| Mars ICME transit holdout | 0.097517 | 0.127447 | 0.180635 / 0.212112 | 0.167802 / 0.198052 |

Key blind results:

| Dataset | V5 MAE | V5 RMSE | Previous learned |
| --- | ---: | ---: | ---: |
| MSL/RAD blind | 0.011207 | 0.014808 | 0.011207 / 0.014808 |
| CRaTER/LRO blind | 0.020491 | 0.022032 | 0.020491 / 0.022032 |
| Chandrayaan-1 RADOM blind | 0.191255 | 0.215780 | 0.191255 / 0.215780 |
| Mars FD blind | 0.144665 | 0.178566 | 0.193394 / 0.227314 |
| Mars ICME transit blind | 0.097517 | 0.127447 | 0.178875 / 0.210140 |

Most important bootstrap evidence:
- Mars FD vs prior learned path:
  `RMSE delta -0.049693`, `95% CI [-0.077551, -0.022745]`
- Mars ICME transit holdout vs prior learned path:
  `RMSE delta -0.084665`, `95% CI [-0.164061, -0.004147]`
- Mars ICME transit holdout vs phase-only ablation:
  `RMSE delta -0.018121`, `95% CI [-0.030014, -0.002208]`

Those intervals matter. They are the difference between "looks good" and "survived a harder comparison."

## Why This Is Interesting For AI
If this result is meaningful beyond this repo, the important idea is not "12 dimensions" by itself. The interesting part is this:

- a compact latent geometry can behave like a transport prior
- one model family can need different routing behavior in different physical regimes
- preserving an interpretable baseline while learning the correction can outperform replacing the baseline outright
- blind templates plus ablations are a much better filter for speculative scientific models than narrative plausibility

That combination is relevant to AI because it points toward a class of models that sit between:
- pure black-box regression
- hand-authored physics heuristics

This project ended up in the middle ground:
- structured latent representation
- interpretable transport priors
- learned correction layers
- explicit failure surfaces

That is a useful shape for scientific AI, even if the underlying 12D ontology still needs future scrutiny.

## What This Does Not Claim
This document does not claim:
- a final law of physics
- universal dominance over every future dataset
- proof that the 12D ontology is the unique true description of the domain

The strongest honest claim is narrower and stronger at the same time:

The checked-in `v5` system is a reproducibly validated unified transport router on the current external validation bundle, including an untouched Mars-family proof set.

## Why A Skeptical Reader Should Still Care
The result is now hard to dismiss with the usual shortcuts:
- "It was never tested." It was.
- "It only fit one dataset." It did not.
- "It probably loses to simple baselines." On the final bundle, it does not where the claim is made.
- "It broke on the hardest regime." The Mars-family weakness was explicitly identified, improved, and then checked against a separate untouched holdout.

In other words: this is no longer a theory asking for belief. It is a framework asking for replication.

## Reproduce In Four Commands
```powershell
python scripts/run_mars_icme_transit_external_validation.py --output-dir docs/validation
python scripts/run_final_v5_validation.py --output-dir docs/validation
python scripts/build_validation_manifest_v5.py --output docs/validation/validation_manifest_v5.json
python -m pytest tests/galactic_cosmic_rays -q
```

## Final Reason To Read It Twice
If the result is wrong, it is wrong in a measurable way and future holdouts can break it.

If the result is right, then a small, structured latent model with explicit transport routing just beat the path that usually kills speculative systems:
implementation, held-out testing, blind scoring, and out-of-family comparison.
