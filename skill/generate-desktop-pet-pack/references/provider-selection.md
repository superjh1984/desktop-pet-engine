# Provider selection

Choose by required capability, not brand name. Run:

```bash
./scripts/pet_pack.py providers --capability <capability>
```

## Current catalog

| Provider/model entry | Capabilities | Adapter state | Runtime environment |
| --- | --- | --- | --- |
| `aliyun/wan2.7-image-pro` | character sheet, sticker set, image edit | Live | `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL` |
| `aliyun/wan2.2-animate-move` | `motion-transfer` | Live | `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL` |
| `byteplus/seedance-2.0` | `image-to-video`, `text-to-video` | Live | `ARK_API_KEY`; optional `BYTEPLUS_ARK_BASE_URL` |
| `volcengine/seedance-2.0` | `image-to-video`, `text-to-video` | Live | `ARK_API_KEY`; optional `VOLCENGINE_ARK_BASE_URL` |
| `openai/gpt-image-2` | character sheet, sticker set, image edit | Catalog only | No paid call |
| `kling/kling-video-3.0-turbo` | image/text to video | Catalog only | No paid call |

`live` means the repository contains a reviewed adapter and mocked contract tests. It does not guarantee that the user's account, region, quota, or model entitlement is active. For Seedance, pass `--api-model` with the exact model or endpoint ID enabled in the user's account.

## Selection rules

- Use `motion-transfer` when a licensed reference clip contains the exact reusable motion.
- Use `image-to-video` for short action prompts with a stable camera and simple motion.
- Generate an identity/character sheet before many videos when the source is only one pose.
- Prefer short, single-action clips. Long clips increase drift and are harder to loop.
- Keep audio disabled for desktop-pet action clips unless audio is explicitly required and licensed.
- Do not choose by a hard-coded price. Pricing, quotas, duration limits, and regional endpoints can change; review the provider page at execution time.

## Credential rules

- A key is read only at execution time from its environment variable.
- Do not add `.env`, local provider JSON, signed URLs, or shell transcripts to Git.
- Do not ask the user to paste a key into chat.
- Use `./scripts/pet_pack.py doctor --provider <id>` to report only configured/not configured.

Official documentation:

- Alibaba Wan action transfer: <https://help.aliyun.com/zh/model-studio/wan-animate-move-api>
- Alibaba Wan image generation/editing: <https://help.aliyun.com/zh/model-studio/wan-image-generation-and-editing-api-reference>
- BytePlus ModelArk generation tasks: <https://docs.byteplus.com/en/docs/ModelArk/1520757>
- Volcengine Ark generation tasks: <https://www.volcengine.com/docs/82379/1520757>
- Kling developer platform: <https://kling.ai/dev>
- OpenAI image generation: <https://developers.openai.com/api/docs/guides/image-generation>
