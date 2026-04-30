---
description: Convert a mono file to stereo (duplicate, pan, or pseudo-stereo widening)
argument-hint: <input-file> [--mode duplicate|pan|widen] [--width 0.3]
---

Upmix mono `$1` to stereo and write `<name>_stereo.<ext>`.

## Modes

- **duplicate** (default): identical L/R. Transparent, no spatial info.
- **pan**: center-panned with `-3 dB` pan law. Equivalent to duplicate at equal-power.
- **widen**: Haas-effect pseudo-stereo — tiny delay (5–20 ms × `<width>`) on one channel + mild high-shelf differential. Use sparingly; can cause phase issues when folded back to mono.

## Steps

1. Verify input is mono (`ffprobe`). If already stereo, warn and exit.
2. Build filter:
   - duplicate: `-ac 2` with `channelmap=0|0`
   - pan: `pan=stereo|c0=c0|c1=c0`
   - widen: `aecho=0.88:0.9:<width*20>:0.3,pan=stereo|c0=c0|c1=c0`
3. Run:
   ```
   ffmpeg -i "$INPUT" -af "$FILTER" -ac 2 \
     -c:a <match-input-codec> -b:a <match-input-bitrate> \
     "$OUTPUT"
   ```
4. Output naming: same dir, stem + `_stereo` + same extension.

For transcription or voice archival, prefer mono — widening adds size with no benefit.
