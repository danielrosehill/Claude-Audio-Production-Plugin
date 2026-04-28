---
description: Reduce sibilance ("s" / "sh" harshness) in a voice recording using a band-limited dynamic cut. ffmpeg-only proxy for a true sidechain de-esser — fast and good enough for most podcast and spoken-word material.
---

Reduce sibilance on a voice recording.

## Inputs

`$ARGUMENTS`:
- First positional: input audio file. Required.
- `--freq=<Hz>` — sibilance centre frequency. Default `6500`. If a voice analysis exists at `<data-dir>/voice/analysis.json`, use the strongest 5–9 kHz peak from it instead.
- `--threshold=<dBFS>` — default `-24`.
- `--ratio=<n>` — default `3`.
- `--depth=<dB>` — narrow-Q cut applied at the band centre after compression. Default `-3`.
- `--out=<path>` — default: input dir, with `.deessed.wav` suffix.
- `--dry-run` — print the ffmpeg command without running.

## Procedure

### 1. Optionally read voice analysis

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
ANALYSIS="$PLUGIN_DATA_DIR/voice/analysis.json"
```

If the file exists and `--freq` was not explicitly passed, prefer a frequency derived from the analysis (the bin with the highest sustained energy in 5–9 kHz). Otherwise default to 6500 Hz.

### 2. Build filter chain

```
acompressor=threshold=<threshold>dB:ratio=<ratio>:attack=2:release=50:detection=peak,equalizer=f=<freq>:t=q:w=4:g=<depth>
```

This is a proxy: the compressor reacts to the full signal, and the narrow-Q equaliser provides a static cut at the sibilance centre. True sidechain de-essing (where only the sibilance band drives compression of the whole signal) requires a more complex `asplit` + `bandpass` + `sidechaincompress` graph — out of scope for this command. Document this in the report.

### 3. Run

```bash
ffmpeg -y -i "<input>" -af "<chain>" -c:a pcm_s16le "<out>"
```

## Report

- Output path.
- Centre frequency used and whether it came from the voice analysis or the default.
- Filter chain string.
- Note that this is a proxy; suggest a DAW plugin (FabFilter Pro-DS, Waves DeEsser) for surgical work.

## Safety

- Never overwrite the input.
- If the source has very low energy in the sibilance band, the de-esser will still apply but won't do much — note this rather than warn.
