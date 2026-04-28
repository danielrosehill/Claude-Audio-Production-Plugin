---
description: Extract a fixed-duration sample (default 3 minutes) from a longer audio file for profiling. Auto-picks the loudest contiguous window or accepts an explicit start time. Produces a clean WAV at 48 kHz mono PCM.
---

Extract a profiling-friendly sample from a longer recording.

## Inputs

`$ARGUMENTS`:
- First positional: input audio file. Required.
- `--duration=<seconds>` — default `180` (3 min).
- `--start=<auto|HH:MM:SS|<seconds>>` — default `auto`. `auto` picks the loudest contiguous window of the requested duration.
- `--out=<path>` — output WAV path. Required if not called from a parent skill that supplies it.
- `--dry-run` — print the chosen window and ffmpeg command without running.

## Procedure

### 1. Determine the window

If `--start` is `auto`:

- Use ffmpeg `astats` over short frames to score the file:

```bash
ffmpeg -hide_banner -i "<input>" -af "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level" -f null - 2>&1 \
  | grep "RMS_level" | awk '{print $NF}'
```

  Frame length here is the default 1s. Score each 1-second frame by RMS and find the contiguous `<duration>`-second window with the highest mean RMS, ignoring leading/trailing silence.

- A simpler-but-good-enough alternative: pick the start time as 10% into the file, capped to `total_duration - duration - 5s`. Use this if `astats` parsing is fiddly. Document which method was used.

If `--start` is a timestamp or seconds offset, use that directly.

### 2. Verify the window fits

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "<input>"
```

If `start + duration > total_duration`, clamp `start = max(0, total_duration - duration)` and warn.

### 3. Extract

```bash
ffmpeg -y -ss <start> -t <duration> -i "<input>" -ac 1 -ar 48000 -c:a pcm_s16le "<out>"
```

`-ss` before `-i` is the fast seek path; for opus or other compressed inputs accuracy may drift by up to a few ms — acceptable for profiling.

### 4. Report

- Chosen start time and method (`auto` / explicit).
- Output path and size.
- Suggest the caller continue with `/audio-production:profile-voice --sample=<out>`.

## Notes

- Pure ffmpeg + ffprobe — no MCPs, no network.
- Preserves the original file untouched.
- Designed to be called from `onboard` and `add-mic`, but useful standalone.
