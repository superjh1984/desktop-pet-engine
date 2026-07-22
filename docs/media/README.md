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

The programmatic Blob frames and renders generated from them remain covered by the repository's Apache-2.0 license.
