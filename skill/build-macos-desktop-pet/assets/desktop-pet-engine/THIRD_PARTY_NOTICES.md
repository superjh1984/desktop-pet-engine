# Third-party notices

- AppKit and macOS SDK components are provided by Apple and are not redistributed by this repository.
- FFmpeg is an optional external tool used during asset preprocessing and is not bundled.
- Pillow is an optional external tool used only to regenerate the original Blob demo frames and is not bundled.

Review the licenses of optional tools independently before redistributing them or their binaries.

## Optional Mousecape integration

The configurable cursor bridge can call a user-installed copy of
[Mousecape](https://github.com/alexzielenski/Mousecape). Mousecape is not
bundled, installed, copied, or modified by this template.

Mousecape's upstream documentation says that it uses private CoreGraphics APIs,
and its license limits redistribution, use, or modification to personal,
non-commercial purposes. Apache-2.0 covers the bridge code and original Blob
cursor generator only; it does not relicense Mousecape or user-supplied
`.cape` files.
