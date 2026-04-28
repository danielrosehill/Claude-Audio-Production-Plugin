---
description: Apply a saved EQ + dynamics preset to an audio file via ffmpeg. Reads the preset JSON from the plugin's user-data directory, builds a filter chain, and writes a processed copy alongside the input.
---

Apply a saved preset to an audio file.

## Inputs

`$ARGUMENTS`:
- First positional: preset name (matches `<data-dir>/presets/<name>.json`). Required.
- Second positional: input audio file. Required.
- `--out=<path>` — optional. Default: same dir as input, with `.<preset-name>.wav` suffix.
- `--normalize` — optional. After the chain, run a second pass of EBU R128 loudnorm to the preset's `loudness_target_lufs`.
- `--dry-run` — optional. Print the ffmpeg command but don't execute.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
PRESET_FILE="$PLUGIN_DATA_DIR/presets/<name>.json"
```

If the preset doesn't exist, list available ones (call the same logic as `/audio-production:list-presets`) and stop.

## Build the filter chain

Read the preset JSON. Translate each section into ffmpeg `-af` filters in this order (matters):

### 1. Highpass

```
highpass=f=<highpass_hz>:p=2
```

(`p=2` ≈ 12 dB/oct.) Skip if `highpass_hz` is null/0.

### 2. Parametric EQ bands

For each band:

- `equalizer=f=<freq_hz>:t=q:w=<q>:g=<gain_db>` for peaking bands.
- `bass=g=<gain_db>:f=<freq_hz>:t=q:w=<q>` for `type: lowshelf`.
- `treble=g=<gain_db>:f=<freq_hz>:t=q:w=<q>` for `type: highshelf`.

### 3. De-esser (band-limited compressor approach)

ffmpeg has no native de-esser. Use a sidechain-style compression on the sibilance band by combining `bandpass` + `acompressor`. A practical proxy is a narrow-Q dynamic cut:

```
acompressor=threshold=<deesser.threshold_db>dB:ratio=<deesser.ratio>:attack=2:release=50:detection=peak,equalizer=f=<deesser.freq_hz>:t=q:w=4:g=-3
```

Note this is a compromise — true sidechain de-essing requires a more complex graph. Document this limitation in the report.

### 4. Compressor

```
acompressor=threshold=<compressor.threshold_db>dB:ratio=<compressor.ratio>:attack=<compressor.attack_ms>:release=<compressor.release_ms>:makeup=<compressor.makeup_db>dB
```

### 5. Optional loudnorm pass (only if `--normalize` was passed)

Run a second ffmpeg pass with two-pass `loudnorm`:

```bash
# pass 1 — measure
ffmpeg -hide_banner -i "<intermediate>" -af loudnorm=I=<target>:TP=-1:LRA=11:print_format=json -f null - 2>&1 | tail -n 12

# pass 2 — apply with measured values
ffmpeg -y -i "<intermediate>" -af loudnorm=I=<target>:TP=-1:LRA=11:measured_I=...:measured_TP=...:measured_LRA=...:measured_thresh=...:offset=...:linear=true "<final>"
```

## Run

```bash
ffmpeg -y -i "<input>" -af "<built filter chain>" -c:a pcm_s16le "<out>"
```

For `--dry-run`, print the full command and stop.

## Report

After processing, run `/audio-production:check-loudness` (or its inline equivalent) on the output and print:

- Output path and size.
- Before/after integrated LUFS, true peak, LRA.
- The full ffmpeg filter chain string (so the user can audit/edit).
- The preset that was applied.

## Safety

- Never overwrite the input.
- If the output path already exists, ask before overwriting (unless `--out` was explicit).
- Treat the preset JSON as authoritative — don't silently substitute values; if a field is missing or invalid, report and stop.

## Notes

- Pure ffmpeg — no MCPs, no external services.
- The de-esser proxy is documented as an approximation; users wanting surgical de-essing should reach for a DAW plugin. The plugin's `/audio-production:de-ess` command is the standalone version of the same proxy.
