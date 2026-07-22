# Asset pipeline

## Supported inputs

- Prefer ProRes 4444 or another source with a real alpha channel.
- Accept a uniform green or black background only when the edge quality remains usable after keying.
- Reject complex backgrounds instead of silently producing a poor mask.
- Require documented ownership or redistribution permission for the character, costume, marks, reference imagery, audio, and source clip.

## Configuration

Use `assets_config.json` with:

- `fps`: output frame rate.
- `canvas`: transparent output size.
- `contentBox`: maximum visible character bounds.
- `cropPadding`: margin around detected alpha.
- `actions.<id>.source`: local source video path.
- `background`: `auto`, `black`, `green`, or `key`.
- `scale` and `offset`: per-action alignment adjustments.
- `repairFrames`: one-based damaged frames replaced by interpolation.
- `directionTimes`: idle direction timestamps converted to frame indices.

Keep the local config ignored because it normally contains absolute paths.

## Output contract

Each action uses `Assets/<action>/frame_00001.png` naming. `Assets/manifest.json` records canvas size, FPS, frame count, and optional `directionFrames`.

## Visual acceptance checks

Inspect at least the first, middle, and last frame of every action. Reject:

- clipped hair, hands, props, or feet;
- green/black edge halos;
- character scale or identity drift;
- mismatched floor position between actions;
- broken transparency or a solid canvas;
- discontinuous first/last frames for intended loops;
- third-party marks that were not part of the approved asset scope.

