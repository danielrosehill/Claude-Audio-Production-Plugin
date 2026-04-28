---
description: Remove background noise from an audio file. Local-first — DeepFilterNet (ML, validated) or ffmpeg afftdn (non-ML, instant). Use before mastering, before applying EQ presets, or whenever a recording has hum, hiss, room noise, or constant background sound that needs reducing.
---

Reduce background noise in a recording.

## Why local-first

This plugin is for production-quality audio, where round-tripping to a cloud denoiser adds latency, cost, and a privacy surface for material that may be unreleased. Local DeepFilterNet (validated in the user's [Crying-Baby-Audio-Scrub](https://github.com/danielrosehill/Crying-Baby-Audio-Scrub) experiment) gives near-cloud quality on CPU. ffmpeg `afftdn` is a zero-deps fallback for stationary noise (HVAC hum, tape hiss).

For transcription-only flows, denoising is usually unnecessary — modern ASR handles moderate noise. Use the companion `Claude-Transcription-Plugin` for those flows.

## Inputs

`$ARGUMENTS`:
- First positional: input audio file. Required.
- `--engine=<deepfilternet|afftdn>` — default `deepfilternet`.
- `--out=<path>` — default: `<input-dir>/<stem>.denoised.<ext>`.
- `--strength=<0-1>` — afftdn only. Maps to `nf` (noise floor). Default 0.85 → `nf=-25`.
- `--dry-run` — print the command and stop.

## Procedure

### 1. Verify the engine

**DeepFilterNet** — invoke the venv-installed binary directly:

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
DEEPFILTER="$PLUGIN_DATA_DIR/venv/bin/deepFilter"
test -x "$DEEPFILTER" || { echo "deepFilter missing. Run /audio-production:install-deps."; exit 1; }
```

Use `$DEEPFILTER` everywhere this command shells out — never rely on PATH lookup.

**afftdn** — built into ffmpeg, no check needed beyond `which ffmpeg`.

### 2. DeepFilterNet path

```bash
"$DEEPFILTER" "<input>" -o "<out-dir>"
```

`deepFilter` writes `<input-stem>_DeepFilterNet3.wav` into the output directory. Move/rename to the canonical `<stem>.denoised.<ext>` afterward:

```bash
mv "<out-dir>/<stem>_DeepFilterNet3.wav" "<out>"
```

DeepFilterNet expects 48 kHz mono/stereo PCM. If the input is something else, transcode first:

```bash
ffmpeg -y -i "<input>" -ar 48000 -c:a pcm_s16le "<tmp>.wav"
```

Then run `deepFilter` on the temp file and clean up.

### 3. afftdn path

```bash
ffmpeg -y -i "<input>" -af "afftdn=nf=<noise-floor-db>:nr=20" -c:a pcm_s16le "<out>"
```

Where `noise-floor-db = -10 - (strength * 20)` (so `--strength=0.85` → `nf=-27`, `--strength=1.0` → `nf=-30`). Clamp to `[-40, -10]`.

`nr=20` is the noise reduction in dB — leave at 20 for general use.

### 4. Verify and report

- Output path and size.
- A/B-friendly: suggest the user listen to before/after, e.g.:
  - `mpv "<input>"` then `mpv "<out>"`
- Engine used and the parameters.
- If the input was a mic reference sample, suggest re-running `/audio-production:profile-voice --mic=<id> --sample=<out>` so future EQ suggestions target the cleaned signal.

## Safety

- Never overwrite the input.
- If `<out>` exists and `--out` was not explicit, ask before overwriting.
- DeepFilterNet can over-process very dynamic content (music, applause). Warn if the input duration is long (>30 min) and recommend processing a 60s sample first.

## Notes

- Pure local — no MCPs, no network calls, no cloud costs.
- DeepFilterNet runs fine on CPU; ROCm/CUDA acceleration is optional and usually not worth the setup time.
- For nuanced noise (gated reverb, music bleed), reach for Auphonic / RX iZotope outside this plugin — both are out of scope here.
