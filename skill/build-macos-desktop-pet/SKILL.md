---
name: build-macos-desktop-pet
description: Build, customize, audit, and package native macOS desktop-pet apps from owned or licensed image/video assets. Use when Codex needs to create an AppKit transparent floating pet, convert transparent/green-screen/black-screen animation clips into PNG frame packs, replace pet actions, prepare a universal macOS app, separate a public open-source engine from restricted demo assets, or inspect a desktop-pet repository before public release.
---

# Build macOS Desktop Pet

Create rights-safe native macOS desktop pets from the bundled public template. Keep private or restricted character demos outside public repositories.

## Workflow

1. Inspect the workspace before copying files.
   - Locate existing source, asset manifests, animation sources, build scripts, licenses, credentials, local paths, and generated artifacts.
   - Identify who owns each visual, audio, name, logo, costume, and reference image.
   - Treat a recognizable real person, brand, team, or protected character as third-party material even when the drawing or animation itself is original.

2. Choose the distribution lane.
   - **Public/open source:** include only generic code and owned or redistributable demo assets.
   - **Restricted demo:** isolate it in a separate private directory/repository and follow [references/restricted-demo.md](references/restricted-demo.md).
   - Never present a disclaimer, noncommercial label, or "do not redistribute" notice as a substitute for consent or a license.

3. Start a clean public project.
   - Run `scripts/create_from_template.py --target <path> --app-name <name> --bundle-id <id>`.
   - Do not initialize a public repository from a private character workspace with sensitive history.
   - Keep the bundled Blob frames until the user's replacement assets pass validation.

4. Prepare animation assets.
   - Read [references/asset-pipeline.md](references/asset-pipeline.md).
   - Copy `assets_config.example.json` to `assets_config.json` in the output project.
   - Use absolute source paths only in the ignored local config.
   - Run the template's `scripts/preprocess_assets.py` for owned/authorized clips.
   - Inspect representative first, middle, and final frames for edge halos, clipping, scale drift, anatomy changes, and background leakage.

5. Adapt behavior and identity.
   - Update `PetAction.swift` when adding or removing actions.
   - Keep `AssetCatalog.validateRequiredAssets()` synchronized with the shipped actions.
   - Replace the display name, bundle ID, About text, menu labels, icon, and asset provenance.
   - Preserve transparent hit testing and click-through behavior unless the user explicitly requests another interaction model.
   - When adding system cursor themes, read [references/cursor-themes.md](references/cursor-themes.md).
   - Keep cursor artwork in the same owned/licensed asset lane as character art. Never copy restricted demo `.cape` files into the public template.
   - Treat Mousecape as an optional, separately installed dependency. Do not bundle it or imply that this project's Apache-2.0 license overrides its upstream terms.

6. Build and verify.
   - Run `scripts/check_demo.sh` in the output project.
   - Run the built executable with `--cursor-self-test` when cursor themes are configured.
   - Require x86_64 and arm64 for a general macOS release unless the user explicitly limits architectures.
   - Check idle CPU, memory growth across every action, multi-display placement, Spaces/full-screen behavior, sleep/wake, and first-run installation.

7. Audit before publication.
   - Run `scripts/audit_public_release.py <path>` and add `--deny-term <term>` for every private person, brand, project name, or internal codename that must not appear.
   - Read [references/release-checklist.md](references/release-checklist.md).
   - Do not publish when the audit finds credentials, signed URLs, authentication QR codes, local paths, restricted assets, or unclear licensing.

8. Package only within the user's requested scope.
   - Local builds may use ad-hoc signing.
   - Public binary releases should use the user's Developer ID and Apple notarization credentials; do not request or expose private keys.
   - Do not upload, publish, or create a public repository unless the user explicitly asks for that external action.

## Bundled resources

- `assets/desktop-pet-engine/`: runnable Apache-2.0 AppKit template with original programmatic Blob frames.
- `scripts/create_from_template.py`: safely copy and rename the template.
- `scripts/audit_public_release.py`: scan a release tree for sensitive content and user-specified restricted terms.
- `references/asset-pipeline.md`: frame-pack and preprocessing details.
- `references/cursor-themes.md`: configuration, validation, dependency, and rights guidance for cursor themes.
- `references/release-checklist.md`: public source/binary release checks.
- `references/restricted-demo.md`: isolation and access rules for private demos.
