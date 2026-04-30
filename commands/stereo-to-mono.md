---
description: Downmix stereo (or multichannel) audio to mono
argument-hint: <input-file> [--mode average|left|right|sum]
---

Downmix `$1` to mono and write `<name>_mono.<ext>`.

## Modes

- **average** (default): `0.5*L + 0.5*R` — safe, phase-aware would be better but this is simple.
- **left**: keep L only (useful when R is noisy/empty).
- **right**: keep R only.
- **sum**: `L + R` with 3 dB attenuation to avoid clipping — preserves center content energy better than average.

## Steps

1. Verify input is ≥2 channel (`ffprobe`). If mono, warn and exit.
2. Build filter:
   - average: `-ac 1`
   - left: `pan=mono|c0=c0`
   - right: `pan=mono|c0=c1`
   - sum: `pan=mono|c0=0.707*c0+0.707*c1`
3. Run:
   ```
   ffmpeg -i "$INPUT" -af "$FILTER" -ac 1 \
     -c:a <match-input-codec> -b:a <match-input-bitrate> \
     "$OUTPUT"
   ```
4. Output naming: same dir, stem + `_mono` + same extension.
5. Check for clipping in `sum` mode; if any, report and suggest `average` instead.

Mono is strongly preferred for transcription, voice archival, and any speech-only pipeline — halves file size with no intelligibility loss.
