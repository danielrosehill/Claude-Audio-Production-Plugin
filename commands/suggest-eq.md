---
description: Translate the user's saved voice analysis into an EQ + dynamics preset for a given use case (podcast, vocals, spoken-word, broadcast). Saves the preset to the plugin's user-data directory.
---

Generate an EQ preset tailored to the user's voice profile.

## Inputs

`$ARGUMENTS`:
- `--use-case=<podcast|vocals|spoken-word|broadcast>` — required. Determines targets and dynamics shape.
- `--name=<preset-name>` — optional. Default: same as `--use-case`. Used as the preset filename.
- `--overwrite` — optional. If a preset with the same name exists, overwrite it. Otherwise, prompt.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
ANALYSIS="$PLUGIN_DATA_DIR/voice/analysis.json"
PRESET="$PLUGIN_DATA_DIR/presets/<name>.json"
```

If `analysis.json` is missing, tell the user to run `/audio-production:profile-voice` first. (Or, if they explicitly want a generic preset, proceed without it and set `derived_from: null`.)

## Decision rules

Read the analysis. Build the preset using these heuristics — adjust live based on what the analysis shows.

### Highpass

- `podcast` / `spoken-word` / `broadcast`: 80 Hz HPF (12 dB/oct).
- `vocals` (sung): 60 Hz HPF.
- If the analysis shows a strong resonant peak below 100 Hz, raise HPF to 100 Hz.

### Mud cut (200–500 Hz)

- If `band_energy_dbfs.mud_200_500` is more than 5 dB above `sibilance_5000_9000` (i.e. mud-heavy), apply −3 to −4 dB at the strongest resonant peak in that band, Q ≈ 1.0.
- If roughly balanced, apply −2 dB at 250 Hz, Q 1.0 as a gentle clean-up.
- For `vocals` (sung), be gentler: −1 to −2 dB.

### Presence boost (2.5–4 kHz)

- All use cases: +2 dB at 3 kHz, Q 0.9 by default.
- If centroid is below 1500 Hz (dark voice), bump to +3 dB.
- If centroid is above 2500 Hz (already bright), reduce to +1 dB or skip.

### Air shelf (10 kHz+)

- `vocals`: +2 dB high shelf at 10 kHz.
- `podcast` / `spoken-word`: +1 dB high shelf at 10 kHz only if centroid < 2000 Hz.
- `broadcast`: skip (broadcast chains usually limit air).

### Sibilance / de-essing

- Pick a de-ess centre frequency: scan the analysis's STFT in 5–9 kHz; place the de-esser at the bin with the highest sustained energy. Default 6500 Hz if data is unclear.
- Threshold: −24 dBFS, ratio 3:1, for `podcast` / `spoken-word`.
- For `vocals` (sung): threshold −20 dBFS, ratio 2.5:1 (less aggressive — preserve consonant character).

### Compression

| Use case | Threshold | Ratio | Attack | Release | Makeup |
|---|---|---|---|---|---|
| podcast | −20 dBFS | 3:1 | 5 ms | 80 ms | +3 dB |
| spoken-word | −22 dBFS | 2.5:1 | 8 ms | 120 ms | +2 dB |
| vocals | −18 dBFS | 4:1 | 3 ms | 60 ms | +3 dB |
| broadcast | −18 dBFS | 4:1 | 3 ms | 50 ms | +4 dB |

### Loudness target

- `podcast`: −16 LUFS (Spotify/Apple Podcasts norm).
- `spoken-word`: −18 LUFS.
- `vocals`: skip (mix-bus decision).
- `broadcast`: −23 LUFS (EBU R128).

## Write the preset

JSON schema:

```json
{
  "name": "<name>",
  "use_case": "<use-case>",
  "derived_from": "voice/analysis.json",
  "created_at": "<ISO timestamp>",
  "filters": {
    "highpass_hz": 80,
    "bands": [
      {"freq_hz": 250, "gain_db": -3, "q": 1.0, "reason": "tame mud"},
      {"freq_hz": 3000, "gain_db": 2, "q": 0.9, "reason": "presence"},
      {"freq_hz": 10000, "gain_db": 1, "q": 0.7, "type": "highshelf", "reason": "air"}
    ],
    "deesser": {"freq_hz": 6500, "threshold_db": -24, "ratio": 3.0},
    "compressor": {"threshold_db": -20, "ratio": 3.0, "attack_ms": 5, "release_ms": 80, "makeup_db": 3}
  },
  "loudness_target_lufs": -16
}
```

Save to `<data-dir>/presets/<name>.json`. If the file exists and `--overwrite` was not passed, ask before replacing.

## Report

Print:
- Preset path.
- A plain-English summary of what each filter does for *this* voice (cite the analysis numbers).
- Suggest `/audio-production:apply-preset <name> <input.wav>` to try it.

## Notes

- This command is read-mostly: it never modifies audio. It only writes a JSON preset.
- Heuristics are starting points — encourage the user to A/B and tweak.
- No external services or MCPs — pure local logic over a local JSON file.
