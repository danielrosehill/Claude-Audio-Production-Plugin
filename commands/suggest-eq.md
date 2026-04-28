---
description: Translate a mic's voice analysis into an EQ + dynamics preset for a use case (podcast, vocals, spoken-word, broadcast). Saves the preset (mic-bound) and emits a 1-min A/B audition.
---

Generate an EQ preset tailored to the user's voice profile on a given mic.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
MICS_DIR="$PLUGIN_DATA_DIR/mics"
PRESETS_DIR="$PLUGIN_DATA_DIR/presets"
```

## Inputs

`$ARGUMENTS`:
- `--use-case=<podcast|vocals|spoken-word|broadcast>` — required.
- `--mic=<mic-id>` — defaults to `default_mic_id` from `config.json`.
- `--name=<preset-name>` — default: `<use-case>--<mic-id>`. Becomes the preset filename.
- `--overwrite` — overwrite if the preset name exists. Otherwise prompt.
- `--no-audition` — skip the audition step at the end. Default: audition.

If `<MICS_DIR>/<mic-id>/analysis.json` is missing, tell the user to run `/audio-production:profile-voice --mic=<mic-id>` first.

## Decision rules

Read `<MICS_DIR>/<mic-id>/analysis.json` and build the preset using the heuristics below. Adjust live based on what the analysis shows — these are starting points.

### Highpass

- `podcast` / `spoken-word` / `broadcast`: 80 Hz HPF (12 dB/oct).
- `vocals` (sung): 60 Hz HPF.
- If the analysis shows a strong resonant peak below 100 Hz, raise HPF to 100 Hz.

### Mud cut (200–500 Hz)

- If `band_energy_dbfs.mud_200_500` is more than 5 dB above `sibilance_5000_9000`, apply −3 to −4 dB at the strongest resonant peak in the 200–500 Hz band, Q ≈ 1.0.
- If the gap is smaller, apply a gentle −2 dB at 250 Hz, Q 1.0.
- For `vocals` (sung), be gentler: −1 to −2 dB.

### Presence boost (2.5–4 kHz)

- All use cases default: +2 dB at 3 kHz, Q 0.9.
- Centroid below 1500 Hz (dark): bump to +3 dB.
- Centroid above 2500 Hz (already bright): reduce to +1 dB or skip.

### Air shelf (10 kHz+)

- `vocals`: +2 dB high shelf at 10 kHz.
- `podcast` / `spoken-word`: +1 dB high shelf at 10 kHz only if centroid < 2000 Hz.
- `broadcast`: skip.

### Sibilance / de-essing

- Centre frequency: prefer the analysis's `sibilance_peak_hz`. Fall back to 6500 Hz.
- Threshold: −24 dBFS, ratio 3:1 for `podcast` / `spoken-word` / `broadcast`.
- `vocals`: threshold −20 dBFS, ratio 2.5:1.

### Compression

| Use case | Threshold | Ratio | Attack | Release | Makeup |
|---|---|---|---|---|---|
| podcast | −20 dBFS | 3:1 | 5 ms | 80 ms | +3 dB |
| spoken-word | −22 dBFS | 2.5:1 | 8 ms | 120 ms | +2 dB |
| vocals | −18 dBFS | 4:1 | 3 ms | 60 ms | +3 dB |
| broadcast | −18 dBFS | 4:1 | 3 ms | 50 ms | +4 dB |

### Loudness target

- `podcast`: −16 LUFS.
- `spoken-word`: −18 LUFS.
- `vocals`: null (mix-bus decision).
- `broadcast`: −23 LUFS (EBU R128).

## Write the preset

JSON schema:

```json
{
  "name": "<name>",
  "use_case": "<use-case>",
  "mic_id": "<mic-id>",
  "derived_from": "mics/<mic-id>/analysis.json",
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

Save to `<PRESETS_DIR>/<name>.json`. If the file exists and `--overwrite` was not passed, ask before replacing.

## Audition

Unless `--no-audition` was passed, immediately invoke `/audio-production:audition-preset <name>` to emit a 1-min A/B pair from the bound mic's sample. Print the audition path in the report.

## Report

- Preset path.
- Plain-English summary citing the analysis numbers (e.g. "−4 dB at 211 Hz because mud_200_500 is 28 dB above sibilance").
- Audition directory (with playback hint).
- Hint: `/audio-production:apply-preset <name> <input.wav>` to use it on real audio.

## Notes

- Heuristics are starting points — encourage A/B and edit the JSON directly to tweak.
- No external services or MCPs.
