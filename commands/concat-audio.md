---
description: Concatenate multiple audio files (with optional crossfade) into a single output
---

Concat or crossfade audio files into one output. Works for podcast episode assembly, interview stitching, or reassembling VAD segments.

Inputs (from `$ARGUMENTS` or ask):
- `--inputs <file1> <file2> ...` (required, 2+ files in order)
- `--crossfade <seconds>` (optional, default 0 — pure concat)
- `--out <file>` (required)

**If crossfade = 0** (simple concat):
1. Build a concat list file with entries like `file '/absolute/path.wav'`.
2. Run:
   ```
   ffmpeg -hide_banner -f concat -safe 0 -i concat.txt -c:a pcm_s24le -ar 48000 "<out>"
   ```

**If crossfade > 0**:
Use the `acrossfade` filter chained between pairs:
```
ffmpeg -hide_banner -i a.wav -i b.wav -i c.wav \
  -filter_complex "[0][1]acrossfade=d=N:c1=tri:c2=tri[ab];[ab][2]acrossfade=d=N:c1=tri:c2=tri" \
  -ar 48000 "<out>"
```

Before concatenating, verify sample rate and channel layout match across inputs via `ffprobe`. If they don't, resample inputs to 48 kHz stereo first.

Report output duration and suggest running `/audio-production:normalize` and `/audio-production:check-loudness` on the result.
