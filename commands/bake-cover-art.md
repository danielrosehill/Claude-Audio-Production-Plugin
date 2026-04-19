---
description: Embed cover art into an existing MP3 without re-encoding the audio
---

Bake cover art into an MP3 (no audio re-encode).

Inputs (from `$ARGUMENTS` or ask):
- `--audio <mp3>` (required)
- `--cover <jpg|png>` (required; defaults to latest image in `cover-art/` if omitted)
- `--out <mp3>` (optional; defaults to `<audio-basename>-tagged.mp3`)

Behavior:
1. Verify cover is square and ≥ 1400×1400 (Apple Podcasts minimum is 1400, recommended 3000). If smaller, warn and offer `/audio-production:upscale-cover-art`.
2. Run:
   ```
   ffmpeg -hide_banner -i "<audio>" -i "<cover>" \
     -map 0:a -map 1 -c:a copy -c:v mjpeg \
     -id3v2_version 3 \
     -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" \
     "<out>"
   ```
3. Verify with `ffprobe` that the attached picture stream is present.
4. Report the new file path and size.
