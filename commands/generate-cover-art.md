---
description: Generate cover art (text-to-image or image-to-image) via Fal AI Nano Banana 2
---

Generate cover art using Fal AI's Nano Banana 2.

Model endpoint: `fal-ai/nano-banana-2` (https://fal.ai/models/fal-ai/nano-banana-2)

Inputs (from `$ARGUMENTS` or ask):
- `--prompt "<text>"` (required)
- `--ref <image-path>` (optional — if provided, run image-to-image; otherwise text-to-image)
- `--out <path>` (optional; defaults to `cover-art/<slug>-<timestamp>.png`)
- `--aspect 1:1` (default — cover art is square)

Auth: requires `FAL_KEY` in the environment. Do NOT print it.

**Text-to-image** — POST to `https://fal.run/fal-ai/nano-banana-2`:
```
curl -sS -X POST https://fal.run/fal-ai/nano-banana-2 \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "<prompt>", "image_size": "square_hd", "num_images": 1}'
```

**Image-to-image** — POST to `https://fal.run/fal-ai/nano-banana-2/edit` with the ref image passed as a public URL or data URI:
```
curl -sS -X POST https://fal.run/fal-ai/nano-banana-2/edit \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "<prompt>", "image_urls": ["<ref-url-or-dataURI>"]}'
```

Behavior:
1. Submit the request, parse the returned image URL from the JSON response.
2. Download the image to the `--out` path.
3. Check dimensions with `identify` (ImageMagick) or `ffprobe`. If < 3000×3000, suggest `/audio-production:upscale-cover-art` for Apple Podcasts recommended quality.
4. Report the saved path, dimensions, and prompt used.

Alternative: if a Nano-Banana MCP is available, use its `text_to_image` / `image_to_image` tool instead — same backend.
