---
description: Analyse a mic's reference sample and write a spectral profile (F0, sibilance, mud, resonant peaks) into the plugin's user-data directory. Bound to a specific mic — re-run after changing mic, room, or capture chain.
---

Analyse a mic's reference sample and persist the result.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
MICS_DIR="$PLUGIN_DATA_DIR/mics"
```

## Inputs

`$ARGUMENTS`:
- `--mic=<mic-id>` — the mic to profile. Defaults to `default_mic_id` from `config.json`.
- `--sample=<path>` — optional. If given, copy/transcode this file into `<MICS_DIR>/<mic-id>/sample.wav` (overwriting) before analysing. Useful when re-profiling with a fresh recording.

If `<MICS_DIR>/<mic-id>/sample.wav` doesn't exist and no `--sample` was passed, tell the user to run `/audio-production:add-mic` first.

## Procedure

### 1. Resolve the plugin Python interpreter

```bash
PYTHON="$PLUGIN_DATA_DIR/venv/bin/python"
test -x "$PYTHON" || {
  echo "Plugin venv missing. Run /audio-production:install-deps first."
  exit 1
}
"$PYTHON" -c "import librosa, numpy" 2>/dev/null || {
  echo "librosa missing from venv. Run /audio-production:install-deps."
  exit 1
}
```

Use `$PYTHON` (not system `python3`) for every Python invocation in this command.

### 2. Refresh the canonical sample (if `--sample` was passed)

```bash
ffmpeg -y -i "<sample>" -ac 1 -ar 48000 -c:a pcm_s16le "$MICS_DIR/<mic-id>/sample.wav"
```

If the source is longer than 5 minutes, hand off to `/audio-production:extract-sample` first to pick a 3-min window — don't analyse the whole thing.

### 3. Run analysis

Inline Python (heredoc — no separate script file). Load `<MICS_DIR>/<mic-id>/sample.wav` with `librosa.load(..., sr=48000, mono=True)`. Compute:

- **F0**: `librosa.pyin(..., fmin=70, fmax=400)`. Median + 5th/95th percentiles, NaNs stripped.
- **Spectral centroid**: `librosa.feature.spectral_centroid` mean.
- **Spectral rolloff**: `librosa.feature.spectral_rolloff` mean (rolloff=0.85).
- **Band energies**: STFT (`n_fft=4096`, `hop_length=1024`); mean magnitude in 200–500 Hz (mud) and 5000–9000 Hz (sibilance), expressed in dBFS.
- **Resonant peaks**: time-averaged magnitude spectrum, smoothed with a 5-bin moving average; top 3 local maxima below 1 kHz.
- **Sibilance peak**: 5–9 kHz bin with the highest sustained energy.
- **Formants** (optional): if `parselmouth` imports, F1/F2 medians from the first 60s.

If `librosa.pyin` is too slow (long sample, slow CPU), fall back to `librosa.yin` and note that in the output JSON.

### 4. Write `analysis.json`

Schema:

```json
{
  "mic_id": "<mic-id>",
  "source_path": "<MICS_DIR>/<mic-id>/sample.wav",
  "analysed_at": "<ISO timestamp>",
  "duration_seconds": 180.0,
  "sample_rate": 48000,
  "f0_hz": {"median": 118.2, "p05": 88.0, "p95": 168.3},
  "spectral_centroid_hz": 1842.0,
  "spectral_rolloff_hz": 3950.0,
  "band_energy_dbfs": {
    "mud_200_500": -32.1,
    "sibilance_5000_9000": -41.7
  },
  "resonant_peaks_hz": [180, 320, 540],
  "sibilance_peak_hz": 6300,
  "formants_hz": {"f1_median": 520, "f2_median": 1480}
}
```

Save to `<MICS_DIR>/<mic-id>/analysis.json`, overwriting any prior version.

### 5. Report

- Pitch range and median.
- Brightness read (centroid vs typical 1500–2500 Hz spoken-word range).
- Whether mud or sibilance bands look elevated.
- Suggest `/audio-production:suggest-eq --mic=<mic-id>` next.

## Notes

- All analysis is local — no MCPs, no network calls.
- Never overwrite the user's source audio file — only `<MICS_DIR>/<mic-id>/sample.wav` is plugin-owned.
