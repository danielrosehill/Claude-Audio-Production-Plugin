---
description: Apply dynamic range compression to an audio file via ffmpeg's acompressor. Use for taming peaks and increasing perceived loudness on spoken-word, vocal, or podcast material. Standalone — does not require a saved preset.
---

Apply a single-band compressor to an audio file.

## Inputs

`$ARGUMENTS`:
- First positional: input audio file. Required.
- `--threshold=<dBFS>` — default `-20`.
- `--ratio=<n>` — default `3` (3:1).
- `--attack=<ms>` — default `5`.
- `--release=<ms>` — default `80`.
- `--makeup=<dB>` — default `3`.
- `--out=<path>` — default: input dir, with `.compressed.wav` suffix.
- `--use-case=<podcast|vocals|spoken-word|broadcast>` — preset shortcut. Sets defaults per the same table as `/audio-production:suggest-eq`. Explicit flags override.
- `--dry-run` — print the ffmpeg command without running.

## Use-case shortcuts

| Use case | Threshold | Ratio | Attack | Release | Makeup |
|---|---|---|---|---|---|
| podcast | −20 | 3:1 | 5 | 80 | +3 |
| spoken-word | −22 | 2.5:1 | 8 | 120 | +2 |
| vocals | −18 | 4:1 | 3 | 60 | +3 |
| broadcast | −18 | 4:1 | 3 | 50 | +4 |

## Run

```bash
ffmpeg -y -i "<input>" \
  -af "acompressor=threshold=<threshold>dB:ratio=<ratio>:attack=<attack>:release=<release>:makeup=<makeup>dB" \
  -c:a pcm_s16le "<out>"
```

## Report

- Output path.
- Filter string used (for auditability).
- Before/after integrated LUFS via `loudnorm=print_format=summary` measurement (read-only).

## Safety

- Never overwrite the input.
- Warn if the makeup gain pushes true peak above −1 dBTP.
