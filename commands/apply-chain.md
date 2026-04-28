---
description: Run a full audio-engineering chain on a file — highpass, EQ, de-essing, compression, optional loudness normalisation — in a single ffmpeg invocation. Use a saved preset or build a chain inline.
---

Apply a full processing chain to an audio file.

## Inputs

`$ARGUMENTS`:
- First positional: input audio file. Required.
- `--preset=<name>` — load a preset from `<data-dir>/presets/<name>.json` and use its full chain. If passed, skips the inline flags below.
- `--use-case=<podcast|vocals|spoken-word|broadcast>` — load defaults for an inline chain (no saved preset needed).
- `--out=<path>` — default: input dir, with `.chain.wav` suffix.
- `--no-deess` / `--no-compress` / `--no-normalize` — skip individual stages.
- `--target=<LUFS>` — override loudness target. Default from preset, or use-case table.
- `--dry-run` — print the chain and stop.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
```

## Procedure

### 1. Build the chain

If `--preset=<name>` was passed: read `<data-dir>/presets/<name>.json` and assemble in this order:

1. `highpass=f=<highpass_hz>:p=2`
2. For each `bands[]` entry: `equalizer` / `bass` / `treble` filter (see `/audio-production:apply-preset` for the mapping).
3. De-esser proxy: `acompressor=threshold=<deesser.threshold_db>dB:ratio=<deesser.ratio>:attack=2:release=50:detection=peak,equalizer=f=<deesser.freq_hz>:t=q:w=4:g=-3` (skip if `--no-deess`).
4. Compressor: `acompressor=threshold=<compressor.threshold_db>dB:ratio=<compressor.ratio>:attack=<attack_ms>:release=<release_ms>:makeup=<makeup_db>dB` (skip if `--no-compress`).

If `--use-case=<case>` was passed: use the same defaults table that `/audio-production:suggest-eq` and `/audio-production:compress` use, without writing a preset.

### 2. Run the filter chain

```bash
ffmpeg -y -i "<input>" -af "<chain>" -c:a pcm_s16le "<intermediate>"
```

### 3. Optional loudness pass

Unless `--no-normalize` was passed, run two-pass `loudnorm` to the target LUFS (see `/audio-production:normalize` for the exact two-pass invocation). Write the result to `<out>` and remove the intermediate.

If `--no-normalize` was passed, rename the intermediate to `<out>`.

### 4. Report

- Output path.
- Full filter chain string.
- Stages run and stages skipped.
- Before/after integrated LUFS, true peak, LRA.
- Preset (if used) and source data dir.

## Safety

- Never overwrite the input.
- If `--out` already exists, ask before overwriting unless explicitly given.
- If the chain has no stages enabled (everything skipped), refuse and explain.

## Notes

- Designed for end-to-end vocal/spoken-word polish in a single command.
- For surgical EQ work or sidechain de-essing, use a DAW.
