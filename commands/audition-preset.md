---
description: Apply a saved preset to a 1-minute clip from the bound mic's reference sample (or any audio file) and emit before/after WAVs side-by-side for A/B listening.
---

Produce a 1-minute A/B audition pair for a saved preset.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
PRESETS_DIR="$PLUGIN_DATA_DIR/presets"
MICS_DIR="$PLUGIN_DATA_DIR/mics"
AUDITIONS_DIR="$PLUGIN_DATA_DIR/auditions"
```

## Inputs

`$ARGUMENTS`:
- First positional: preset name. Required.
- `--clip=<path>` — explicit audio file to audition with. If omitted, use the sample from the preset's bound mic (`mics/<mic_id>/sample.wav`).
- `--clip-duration=<seconds>` — default `60`.
- `--clip-start=<auto|HH:MM:SS|<seconds>>` — default `auto` (loudest 60s window in the chosen clip).
- `--out-dir=<path>` — override audition output dir. Default: `auditions/<preset>__<mic-id>__<timestamp>/`.
- `--dry-run` — print commands without executing.

## Procedure

### 1. Load the preset

Read `<PRESETS_DIR>/<preset>.json`. If missing, list available and stop.

Note the `mic_id` field — required for the default clip resolution.

### 2. Resolve the clip

If `--clip` was passed, use it.

Otherwise, the source is `<MICS_DIR>/<mic_id>/sample.wav`. If missing, tell the user to re-run `/audio-production:profile-voice --mic=<mic_id>` or `/audio-production:add-mic`.

### 3. Pick the audition window

If `--clip-start=auto`, run a quick `astats` pass (same logic as `/audio-production:extract-sample`) to find the loudest contiguous `<clip-duration>`-second window. Otherwise honour the explicit value.

### 4. Create audition dir

```bash
TS=$(date -u +%Y%m%d-%H%M%SZ)
OUT_DIR="<AUDITIONS_DIR>/<preset>__<mic-id>__$TS"
mkdir -p "$OUT_DIR"
```

### 5. Emit `before.wav`

```bash
ffmpeg -y -ss <start> -t <clip-duration> -i "<clip>" -ac 1 -ar 48000 -c:a pcm_s16le "$OUT_DIR/before.wav"
```

### 6. Build the preset's filter chain

Same translation as `/audio-production:apply-preset`:

1. `highpass=f=<highpass_hz>:p=2`
2. For each band: `equalizer` / `bass` / `treble`.
3. De-esser proxy: `acompressor=...,equalizer=f=<deesser.freq_hz>:t=q:w=4:g=-3`.
4. Compressor: `acompressor=threshold=<...>dB:ratio=<...>:attack=<...>:release=<...>:makeup=<...>dB`.

### 7. Emit `after.wav`

```bash
ffmpeg -y -i "$OUT_DIR/before.wav" -af "<filter chain>" -c:a pcm_s16le "$OUT_DIR/after.wav"
```

(Run on `before.wav` rather than re-seeking the source — guarantees byte-exact comparison windows.)

### 8. Write `diff.txt`

Plain-text record of:
- Preset name and bound mic.
- Source clip path and audition window.
- Full ffmpeg filter chain string.
- Loudness numbers (integrated LUFS, true peak, LRA) for `before.wav` and `after.wav`, measured via `loudnorm=print_format=summary` in dry pass.
- Timestamp.

### 9. Report

- Audition directory path.
- Tell the user how to listen, e.g.:
  - `mpv "$OUT_DIR/before.wav"` then `mpv "$OUT_DIR/after.wav"`
  - Or open both in Audacity / a DAW for tight A/B.
- Print loudness deltas inline for quick sanity check.

## Safety

- Never overwrite the source clip.
- Never overwrite an existing audition dir — timestamp-suffixed names guarantee uniqueness.
- If the preset's `mic_id` references a missing mic dir, refuse and explain.

## Notes

- 60 seconds is enough for ear-fatigue-free A/B; bump `--clip-duration` for longer auditions.
- All processing is local ffmpeg — no MCPs.
