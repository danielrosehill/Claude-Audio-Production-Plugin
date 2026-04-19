---
description: Concatenate intro + body + outro (with optional crossfade) into a single episode master (podcast workspace)
---

Assemble an episode from its parts. For the generic case, use `/audio-production:concat-audio` — this command just layers on the intro/body/outro convention.

Inputs (from `$ARGUMENTS` or ask):
- `--intro <file>` (optional)
- `--body <file>` (required)
- `--outro <file>` (optional)
- `--crossfade <seconds>` (optional, default 0 — pure concat)
- `--out <file>` (required)

**If crossfade = 0** (simple concat):
1. Build a concat list file with entries like `file '/absolute/path.wav'`.
2. Run:
   ```
   ffmpeg -hide_banner -f concat -safe 0 -i concat.txt -c:a pcm_s24le -ar 48000 "<out>"
   ```

**If crossfade > 0**:
```
ffmpeg -hide_banner -i intro.wav -i body.wav -i outro.wav \
  -filter_complex "[0][1]acrossfade=d=N:c1=tri:c2=tri[ab];[ab][2]acrossfade=d=N:c1=tri:c2=tri" \
  -ar 48000 "<out>"
```

Before concatenating, verify sample rate and channel layout match across inputs via `ffprobe`. If they don't, resample inputs to 48 kHz stereo first.

Report output duration and suggest `/audio-production:normalize` followed by `/audio-production:check-loudness` on the result.
