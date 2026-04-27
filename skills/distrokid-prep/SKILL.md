---
name: distrokid-prep
description: Use when Daniel wants to prep raw audio tracks for DistroKid upload — convert to FLAC, EBU R128 normalize, and group under distrokid/to-upload/<release>/. Triggers on "distrokid prep", "prep for distrokid", "prep these tracks for upload", "normalize and FLAC for distrokid".
---

# DistroKid Release Prep

Take a set of raw input tracks and produce upload-ready FLACs grouped into a release folder under `distrokid/to-upload/<release-slug>/`. Daniel will move the folder into a processed subfolder once he's confirmed the upload.

## Inputs

- Raw tracks (any common format ffmpeg can read: WAV, MP3, M4A, FLAC, AIFF, etc.) provided by the user — usually a folder path or a list of files.
- A release slug (kebab-case, e.g. `marc-mehlman`). Ask if not given.

## Output

- `distrokid/to-upload/<release-slug>/` containing one FLAC per input track.
- Filenames preserve track order — if inputs aren't already numbered, prefix with `01_`, `02_`, etc. in the order given.

## Processing

For each input track:

1. **Two-pass loudness normalization** to **-14 LUFS integrated, -1 dBTP, 11 LU LRA** (music streaming target — DistroKid distributes to Spotify/Apple/etc. which apply their own normalization, but -14 LUFS is the safe master target).
2. **Encode to FLAC** at the source sample rate, 16-bit unless source is 24-bit (then keep 24-bit).
3. Strip any embedded artwork unless the user says otherwise — DistroKid handles artwork separately.

### ffmpeg pattern (two-pass loudnorm)

Pass 1 — measure:
```bash
ffmpeg -i "$IN" -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2> /tmp/ln.log
```
Parse `input_i`, `input_tp`, `input_lra`, `input_thresh`, `target_offset` from the JSON block at the end of the log.

Pass 2 — apply with measured values:
```bash
ffmpeg -i "$IN" -af loudnorm=I=-14:TP=-1:LRA=11:measured_I=$mi:measured_TP=$mtp:measured_LRA=$mlra:measured_thresh=$mth:offset=$off:linear=true:print_format=summary -ar 44100 -map_metadata -1 "$OUT.flac"
```
Use `-ar 44100` only if source is 44.1k or below; otherwise preserve source rate.

Verify ffmpeg is installed before starting. If not, tell the user.

## After processing

- Print a short table: input filename → output filename → measured input LUFS → final LUFS.
- Remind Daniel the folder is at `distrokid/to-upload/<release-slug>/` and he should move it into a `processed/` subfolder once uploaded.
- Do **not** delete or modify the original raw inputs.
