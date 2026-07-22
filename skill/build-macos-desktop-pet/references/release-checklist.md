# Public release checklist

## Rights and privacy

- Maintain a source and license record for every shipped asset.
- Remove private/restricted character packs, names, prompts, screenshots, and app icons.
- Remove authentication QR codes, personal contact handles, local paths, temporary signed URLs, tokens, certificates, and build credentials.
- State accurately whether the app collects or transmits data.
- Disclose AI-generated or synthetic media when required by the distribution context.

## Repository

- Include `LICENSE`, `NOTICE`, contribution guidance, security contact instructions, `.gitignore`, and third-party notices.
- Keep generated builds, raw videos, local configs, and credentials out of source control.
- Run the public release audit with project-specific restricted terms.
- Inspect the complete staged file list before the first commit and before every release.

## App

- Use a stable reverse-DNS bundle identifier.
- Build and test x86_64 and arm64 unless intentionally limited.
- Test mouse click-through, dragging, menus, action interruption, multi-display placement, Spaces, sleep/wake, CPU, memory, and missing assets.
- For public binaries, sign with Developer ID and notarize. Keep signing keys outside the repository.
- Publish a checksum and installation/support instructions.

