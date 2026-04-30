---
description: Prep an audio file for transcription pipelines (Whisper/Gemini) — optional VAD, then mono 16 kHz Opus @ 24 kbps
argument-hint: <input-file> [--no-vad] [--no-denoise] [--bitrate 24k] [--sample-rate 16000] [--format opus]
---

Produce a transcription-ready copy of `$1` as `<name>_transcribe.opus` (or `.wav` if `--format wav`).

## Pipeline

Before running, offer the user a short plan and ask whether to apply VAD and/or denoising. Default is: VAD on, denoise off.

1. **Probe** the input with `ffprobe`.
2. **VAD** (unless `--no-vad`): invoke the same logic as `/apply-vad` to produce a silence-cut intermediate. Requires `silero_vad.installed`.
3. **Denoise** (only if the user opts in or passes `--denoise`): invoke `/apply-noise-removal` logic. Requires `deep_filter.installed`.
4. **Convert** to the target format. Defaults tuned for Whisper / Gemini / Deepgram:
   - codec: `libopus`
   - bitrate: `24k` (speech-transparent; Whisper/Gemini accept 16–32k comfortably)
   - sample rate: `16000` Hz
   - channels: `1` (mono)
   - container: `.opus` (Ogg Opus)
   ```
   ffmpeg -i "$STAGE" -c:a libopus -b:a 24k -ar 16000 -ac 1 \
          -application voip "$OUTPUT"
   ```
   If `--format wav`: `-c:a pcm_s16le -ar 16000 -ac 1`, write `.wav`.
5. Report each stage's duration and size reduction, plus the final output path.

## Rationale

- Whisper resamples to 16 kHz internally — feeding 16 kHz avoids wasted bandwidth.
- Mono is sufficient for speech; stereo doubles token cost on multimodal LLM pipelines with no transcription benefit.
- Opus `-application voip` is tuned for speech intelligibility at low bitrates.
- VAD before compression shrinks files significantly and drops dead air the model would otherwise chew on.

## Guardrails

- If any required tool (`silero_vad`, `deep_filter`) is missing, tell the user which `/install-*` command to run and skip that stage rather than failing the whole pipeline.
- Never overwrite the original file.
