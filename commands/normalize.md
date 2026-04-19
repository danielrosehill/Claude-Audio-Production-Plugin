---
description: Normalize an audio file to a target LUFS (default -16, podcast standard) using ffmpeg two-pass loudnorm
---

Normalize a file to a target integrated loudness. Defaults: -16 LUFS, -1 dBTP ceiling, 11 LU range. Override via `--target=<LUFS>` in `$ARGUMENTS` (e.g. `-14` for music, `-23` for EBU R128 broadcast).

Inputs: `$ARGUMENTS` should contain the input file path. If missing, ask.

Steps:
1. **First pass** — measure:
   ```
   ffmpeg -hide_banner -i "<input>" -af loudnorm=I=<target>:TP=-1:LRA=11:print_format=json -f null -
   ```
   Parse the JSON block at the end (`input_i`, `input_tp`, `input_lra`, `input_thresh`, `target_offset`).
2. **Second pass** — apply with measured values:
   ```
   ffmpeg -hide_banner -i "<input>" -af loudnorm=I=<target>:TP=-1:LRA=11:measured_I=<input_i>:measured_TP=<input_tp>:measured_LRA=<input_lra>:measured_thresh=<input_thresh>:offset=<target_offset>:linear=true:print_format=summary -ar 48000 "<input-basename>-normalized.wav"
   ```
3. Output goes next to the input with `-normalized` suffix unless the user specifies `--out=<path>`.
4. Report the before/after integrated loudness and true peak.
