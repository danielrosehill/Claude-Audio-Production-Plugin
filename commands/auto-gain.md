---
description: Quick peak or RMS normalization — lightweight alternative to full EBU R128 loudnorm
argument-hint: <input-file> [--mode peak|rms] [--target -1] [--headroom 1]
---

Fast-normalize `$1` and write `<name>_gain.<ext>`.

## Steps

1. `ffprobe` input. Measure current peak and RMS:
   ```
   ffmpeg -i "$INPUT" -af "volumedetect" -f null - 2>&1
   ```
2. Compute gain:
   - **peak mode** (default): raise max peak to `<target>` dBFS (default `-1`). No limiter.
   - **rms mode**: raise integrated RMS to `<target>` dBFS (default `-18`), then soft-clip any peaks above `-<headroom>` dBFS.
3. Apply:
   ```
   ffmpeg -i "$INPUT" -af "volume=<gain>dB" \
     -c:a <match-input-codec> -b:a <match-input-bitrate> \
     "$OUTPUT"
   ```
4. Verify the output with `volumedetect` and report before/after peak + RMS.

## When to use this vs loudnorm

- **`/auto-gain`**: quick leveling, preserves dynamics, no EBU pass. Use for drafts, one-off listens, transcription prep.
- **`/normalize-audio` (EBU R128)**: broadcast-ready, two-pass, adjusts loudness range. Use for final deliverables.
- **`/master-audio`**: targets a specific platform (Spotify, Apple Podcast, etc.).
