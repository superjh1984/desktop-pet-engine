---
name: generate-desktop-pet-pack
description: Plan and produce rights-safe sticker sheets and desktop-pet action videos from an owned or licensed character image using user-selected BYOK model providers. Use when Codex needs to turn one character reference into a consistent expression/action pack, compare Wan, Seedance, Kling, OpenAI, or other model capabilities, prepare no-charge generation plans, run an explicitly approved paid model job, or feed generated clips into Desktop Pet Engine.
---

# Generate Desktop Pet Pack

Build a reproducible character pack while keeping model choice, billing, credentials, and asset rights visible.

## Workflow

1. Establish the rights boundary.
   - Confirm the user created or is licensed to use the character image, reference motion clips, names, logos, costumes, audio, and output.
   - Treat a recognizable real person, team, brand, or protected character as third-party material even if the drawing itself is original.
   - Do not treat an AI provider's output as proof that publication or redistribution is permitted.

2. Inspect the project and provider layer.
   - Locate the repository root containing `scripts/pet_pack.py` and `config/model_providers.json`.
   - Run `./scripts/pet_pack.py providers` or filter with `--capability`.
   - Read [references/provider-selection.md](references/provider-selection.md) when choosing a provider or adding an adapter.
   - Report catalog-only models honestly; do not attempt live calls through them.

3. Define the pack before generating.
   - Preserve a single canonical reference image, proportions, palette, costume, and viewpoint policy.
   - Start with `idle`, `walk`, `happy`, `yawn`, and one signature action. Expand only after the identity is stable.
   - Read [references/output-contract.md](references/output-contract.md) for names, prompts, provenance, and Desktop Pet Engine integration.

4. Create no-charge plans first.
   - Use `./scripts/pet_pack.py plan ... --output .petpack/<action>.json`.
   - Keep private or signed source URLs inside `.petpack/`; never commit them.
   - Inspect provider, capability, API model/endpoint ID, inputs, options, and the current provider pricing page.
   - Never place a raw API key in a prompt, plan, source file, issue, commit, or chat message.

5. Stop at the billing boundary unless execution is explicitly requested.
   - Ask the user to configure the documented environment variable outside the repository.
   - Use `doctor` to confirm presence; it must never display the key.
   - Execute only after the user has approved the selected plan, provider cost, and source rights.
   - A paid call requires `--execute --accept-cost --accept-rights`.

6. Validate and integrate output.
   - Download asynchronous output promptly because provider result URLs can expire.
   - Inspect first, middle, and last frames for identity drift, extra limbs, clipping, background changes, scale jumps, and unintended marks.
   - Reject unsafe or inconsistent outputs instead of silently adding them to the pack.
   - Record model entry, API model/endpoint ID, date, prompt, source provenance, and human review status locally.
   - Map accepted videos into ignored `assets_config.json`, then use `scripts/preprocess_assets.py` and `scripts/check_demo.sh`.

## Safety rules

- Planning must remain possible with no key and no network call.
- Keep the model catalog separate from live adapters; `catalog` does not mean executable.
- Never log authorization headers, raw keys, or signed output URLs.
- Do not commit `.petpack/`, `pet-pack-output/`, source assets, or outputs without an explicit redistribution license.
- If a provider changes its API or pricing, stop and review the current official documentation before modifying or executing the adapter.
