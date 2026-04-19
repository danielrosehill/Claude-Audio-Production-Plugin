---
description: Voice-activity-detect an audio file and emit a timing sidecar or per-utterance segment files
---

Run VAD on an audio file. This command is a thin wrapper around the `vad` skill — for anything beyond the happy path (custom thresholds, split mode, engine choice), invoke the skill directly.

Inputs (from `$ARGUMENTS` or ask):
- `<input>` (required)
- `--mode=<sidecar|split>` (optional, default `sidecar`)
- `--min-speech=<seconds>` (optional, default `0.3`)
- `--min-silence=<seconds>` (optional, default `0.5`)
- `--engine=<auto|silero|webrtc|ffmpeg>` (optional, default `auto`)

Behavior:
1. Prefer Silero VAD if available, falling back to WebRTC VAD, then `ffmpeg silencedetect`.
2. In `sidecar` mode, write `<basename>.vad.json` and `<basename>.vad.csv` next to the input.
3. In `split` mode, write per-segment files to `<input-dir>/vad-segments/`.
4. Report engine used, segment count, total speech time, speech ratio, output paths.

See the `/audio-production:vad` skill for full argument reference and engine details.
