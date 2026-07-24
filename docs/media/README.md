# README media provenance and license boundary

The media generator defaults to the repository's programmatic Blob demo frames:

```bash
./scripts/generate_readme_media.py
```

The current homepage renders may instead be generated from a separately held character demo with:

```bash
python3 -m pip install pillow
./scripts/generate_readme_media.py \
  --profile character \
  --asset-root /path/to/separately-held/frame-pack
```

The character source frames, source videos, prompts, app bundle, and private project are not included in this repository. Character showcase renders are provided only to demonstrate the engine and are expressly excluded from the repository's Apache-2.0 license. No license or endorsement from any depicted person, team, brand, or other third party is claimed.

`mouse-interaction.gif` is an optimized derivative of a separately supplied preview GIF. The repository version was resized from 820×480 at approximately 15 fps to 640×375 at 10 fps for faster GitHub loading. The original file is not included. This preview follows the same showcase-only license boundary described above.

The programmatic Blob frames and renders generated from them remain covered by the repository's Apache-2.0 license.
