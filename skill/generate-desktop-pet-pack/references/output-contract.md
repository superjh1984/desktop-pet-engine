# Desktop-pet pack contract

Use one canonical source image and produce small, independently reviewable actions.

## Recommended first pack

| Action | Prompt intent | Loop expectation |
| --- | --- | --- |
| `idle` | Gentle breathing, centered body, fixed camera | Seamless or near-seamless |
| `walk` | Walk in place without changing scale | Loop |
| `happy` | One readable celebration and return to neutral | One-shot |
| `yawn` | Yawn, stretch slightly, return to neutral | One-shot |
| Signature action | One simple character-specific action | One-shot |

Add `dance`, `playBall`, `eat`, `drink`, `frustrated`, `crying`, `shy`, `rowing`, and `meditation` only when the base identity is stable.

## Prompt constraints

Every action prompt should request:

- the same character identity, proportions, hairstyle/fur, palette, and costume as the source;
- full body visible, centered, with feet/hands not cropped;
- fixed camera, constant distance and scale;
- one action only, then a return toward the starting pose;
- plain or transparent-compatible background;
- no text, watermark, logo, extra person, duplicate body part, or camera cut.

## Local working layout

```text
.petpack/
  plans/                  ignored model plans and private URLs
pet-pack-output/
  source/                 canonical owned/licensed reference
  generated/              raw provider results
  accepted/               human-reviewed clips
  provenance.local.json   model, prompt, source, date, review status
assets_config.json        ignored Desktop Pet Engine input mapping
```

These directories are local working data. Do not publish them unless every included source and output has an explicit redistribution basis.

## Acceptance checks

For each clip, inspect the first, middle, and final frames:

- identity and costume do not change;
- face, hands, feet, and props are anatomically consistent;
- the character remains inside frame with stable scale;
- the background is uniform enough for the preprocessing pipeline;
- there is no third-party logo, text, watermark, or unintended person;
- the motion has a usable beginning/end and matches the requested action.

Accepted clips map to the corresponding keys in `assets_config.json`. Run:

```bash
./scripts/preprocess_assets.py
./scripts/check_demo.sh
```

Keep cursor-direction idle frames synchronized with `directionTimes` when an idle source contains multiple direction poses.
