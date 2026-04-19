---
description: Upscale a cover art image using Fal AI SeedVR image upscaler
---

Upscale cover art using Fal AI's SeedVR image upscaler.

Model endpoint: `fal-ai/seedvr/upscale/image` (https://fal.ai/models/fal-ai/seedvr/upscale/image)

Inputs (from `$ARGUMENTS` or ask):
- `--in <image>` (required)
- `--out <path>` (optional; defaults to `<input>-upscaled.png`)
- `--scale <2|4>` (optional; default 2)

Auth: requires `FAL_KEY` in the environment. Do NOT print it.

Steps:
1. If the input is a local file, upload it to Fal's file storage first (via `POST https://fal.run/storage/upload`) or pass it as a base64 data URI in `image_url`.
2. Submit the upscale request:
   ```
   curl -sS -X POST https://fal.run/fal-ai/seedvr/upscale/image \
     -H "Authorization: Key $FAL_KEY" \
     -H "Content-Type: application/json" \
     -d '{"image_url": "<url-or-dataURI>", "upscale_factor": <scale>}'
   ```
3. Parse the output URL from the JSON response.
4. Download the upscaled image to `--out`.
5. Report original vs new dimensions, file size, and path.

Typical podcast use: upscale a 1024×1024 generation to 3000×3000 so it meets Apple Podcasts' recommended cover art size.
