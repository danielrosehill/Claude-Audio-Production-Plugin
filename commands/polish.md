---
description: Full production chain orchestrator — runs (optional denoise) → truncate-silence → EQ preset chain → loudnorm in one invocation. Two modes: clean (default, source is already clean) and noisy (adds DeepFilterNet denoise). Designed as the one-shot finisher for podcast and spoken-word recordings.
---

Polish a recording into a publishable file.

## Inputs

`$ARGUMENTS`:
- First positional: input audio file. Required.
- `--mode=<clean|noisy>` — default `clean`. `noisy` prepends a DeepFilterNet denoise step.
- `--preset=<name>` — default: `podcast--<default_mic_id>` from `config.json`. The EQ + dynamics preset to apply.
- `--mic=<id>` — default: `default_mic_id` from `config.json`. Used only as the fallback for resolving the default preset name.
- `--out=<path>` — default: `<input-dir>/<stem>.polished.wav`.
- `--no-truncate` — skip the silence-truncation stage.
- `--no-eq` — skip the EQ preset chain (just denoise + truncate, if applicable).
- `--no-normalize` — skip the final loudnorm pass.
- `--threshold-db=<dB>` — silence threshold for truncate. Default `-40`.
- `--min-silence=<seconds>` — minimum silence to collapse. Default `1.0`.
- `--keep-pad=<seconds>` — silence to retain at each gap. Default `0.3`.
- `--dry-run` — print the planned chain and stop.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
```

Read `config.json` for `default_mic_id` and `loudness_target_lufs`. Read the chosen preset from `<PLUGIN_DATA_DIR>/presets/<preset>.json`. If either is missing, refuse and explain — do not silently substitute defaults beyond the documented fallbacks.

## Procedure

Each stage writes to a temp file in the same directory as the input; the final stage produces the user-facing `<out>`. Clean up intermediates at the end unless `--dry-run` was passed.

### Stage 0 — preflight

- Verify `ffmpeg` is on PATH.
- If `--mode=noisy`, verify `deepFilter` is on PATH; if missing, surface the install command from `/audio-production:denoise` and stop.
- Resolve preset path and load it.

### Stage 1 — denoise (mode=noisy only)

Hand off to `/audio-production:denoise <input> --engine=deepfilternet --out=<input>.s1-denoised.wav`.

In `clean` mode, skip — the next stage's input is the original file.

### Stage 2 — truncate-silence

Hand off to `/audio-production:truncate-silence <stage-1-output> --engine=ffmpeg --threshold-db=<threshold-db> --min-silence=<min-silence> --keep-pad=<keep-pad> --out=<input>.s2-trimmed.wav`.

Skip if `--no-truncate`.

### Stage 3 — EQ chain + loudnorm

Hand off to `/audio-production:apply-chain <stage-2-output> --preset=<preset> --out=<out>` (and `--no-normalize` if the user passed it through).

If `--no-eq` was passed, skip apply-chain entirely. In that case, if `--no-normalize` was *not* passed, run a standalone two-pass loudnorm via `/audio-production:normalize` to the preset's `loudness_target_lufs`. Otherwise just rename the stage-2 output to `<out>`.

### Stage 4 — log

Write `<out-dir>/<out-stem>.log.txt`:

```
Polished: <out>
Source: <input>
Mode: <clean|noisy>
Preset: <preset> (mic: <mic_id>)

Stages run:
  [denoise] DeepFilterNet            → <s1-output>          (skipped if mode=clean)
  [truncate-silence] threshold=-40dB → <s2-output>          (skipped if --no-truncate)
  [apply-chain] <filter chain>       → <out>                (skipped if --no-eq)
  [loudnorm] target=-16 LUFS                                (skipped if --no-normalize)

Loudness:
  Source:     I=-22.4 LUFS  TP=-1.2 dBTP  LRA=8.3 LU
  Polished:   I=-16.0 LUFS  TP=-1.0 dBTP  LRA=4.1 LU

Durations:
  Source:    18:42
  Polished:  16:05  (-14% from silence truncation)

Timestamp: <ISO>
```

Measure source and polished loudness with `loudnorm=print_format=summary` in dry passes (don't re-encode).

### Stage 5 — cleanup

Remove `s1-denoised.wav` and `s2-trimmed.wav` intermediate files, leaving only `<out>` and `<out-stem>.log.txt`.

## Report

- Output path.
- Mode and preset used.
- One-line summary: source vs polished LUFS, source vs polished duration.
- Pointer to the log file for full details.

## Safety

- Never overwrite the input.
- If `<out>` exists and `--out` was not explicit, ask before overwriting.
- If any stage fails, leave intermediates in place (don't clean up) and report which stage failed and why.
- Refuse with a clear message if `--no-truncate --no-eq --no-normalize` are all passed and `--mode=clean` (nothing would happen).

## Notes

- This is the one-shot finisher. For finer control, run the individual stages directly.
- All processing local — no MCPs, no network.
- The default chain matches the user's two stated patterns:
  - `clean`: personal EQ + VAD (truncate) → loudness target
  - `noisy`: denoise + personal EQ + VAD → loudness target
