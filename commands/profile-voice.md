---
description: Analyse a voice sample and write a spectral profile (F0, sibilance, mud, resonant peaks) to the plugin's user-data directory. Run after /audio-production:onboard or any time the user wants to refresh the profile (new mic, new room).
---

Analyse the user's reference voice sample and persist the result.

## Inputs

`$ARGUMENTS` may contain:
- A path to an audio file. If omitted, use the canonical sample at `<data-dir>/voice/sample.wav`.

## Resolve the data directory

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
```

If `<data-dir>/voice/sample.wav` doesn't exist and no path was passed, tell the user to run `/audio-production:onboard` first.

## Procedure

### 1. Verify dependencies

```bash
python3 -c "import librosa, numpy" 2>/dev/null || {
  echo "librosa not installed. Install with: pip install --user librosa numpy"
  exit 1
}
```

### 2. If the sample is not the canonical one, copy it

If `$ARGUMENTS` provided a path, transcode/copy it to `<data-dir>/voice/sample.wav` (mono, 48 kHz, PCM 16-bit) so future runs are reproducible:

```bash
ffmpeg -y -i "<input>" -ac 1 -ar 48000 -c:a pcm_s16le "$PLUGIN_DATA_DIR/voice/sample.wav"
```

### 3. Run the analysis

Use a short Python program (write it inline via heredoc — do not require a separate script file) that:

- Loads `<data-dir>/voice/sample.wav` with `librosa.load(..., sr=48000, mono=True)`.
- Computes:
  - **F0**: `librosa.pyin` with `fmin=70, fmax=400`. Report median, 5th–95th percentile range. Strip NaNs before stats.
  - **Spectral centroid**: `librosa.feature.spectral_centroid` mean.
  - **Spectral rolloff**: `librosa.feature.spectral_rolloff` mean (rolloff=0.85).
  - **Sibilance band energy**: mean magnitude in 5000–9000 Hz from an STFT (`n_fft=4096, hop_length=1024`), expressed in dBFS.
  - **Mud band energy**: same, in 200–500 Hz, dBFS.
  - **Resonant peaks**: average the magnitude spectrum across frames; smooth with a 5-bin moving average; find the top 3 peaks below 1000 Hz with `scipy.signal.find_peaks` (or numpy if scipy isn't available — argpartition on local maxima).
- If `parselmouth` is importable, also compute median F1/F2 formants (`praat`-based). Otherwise omit those fields.

### 4. Write `analysis.json`

Schema:

```json
{
  "source_path": "<data-dir>/voice/sample.wav",
  "analysed_at": "<ISO timestamp>",
  "duration_seconds": 92.4,
  "sample_rate": 48000,
  "f0_hz": {"median": 118.2, "p05": 88.0, "p95": 168.3},
  "spectral_centroid_hz": 1842.0,
  "spectral_rolloff_hz": 3950.0,
  "band_energy_dbfs": {
    "mud_200_500": -32.1,
    "sibilance_5000_9000": -41.7
  },
  "resonant_peaks_hz": [180, 320, 540],
  "formants_hz": {"f1_median": 520, "f2_median": 1480}
}
```

Write to `<data-dir>/voice/analysis.json`, overwriting any prior version.

### 5. Report

Print a short human summary:

- Pitch range and median.
- Whether the voice trends bright or dark (centroid vs typical 1500–2500 Hz spoken-word range).
- Whether mud or sibilance bands look elevated relative to typical spoken-word baselines.
- Suggest the user run `/audio-production:suggest-eq` next.

## Notes

- All analysis is local — no MCPs, no network calls.
- If `librosa.pyin` is too slow on long samples, fall back to `librosa.yin` and note that in the output.
- Never overwrite the user's source audio file — only `<data-dir>/voice/sample.wav` is plugin-owned.
