# Audio Engineering Workspace

A workspace for general audio processing tasks — noise reduction, silence trimming, loudness normalization, metadata editing, EQ/filtering, format conversion, and segmentation.

## Project Context

{Replace this text with a description of the current audio project — e.g. "podcast episode 12 cleanup", "batch-normalize field recordings", "concatenate and master interview segments".}

## Scope

This workspace is designed for audio engineering tasks:

- **Auto processing** — noise reduction, silence trimming, loudness normalization (LUFS/EBU R128), declipping, dereverb
- **Metadata editing** — ID3/Vorbis/FLAC tag management, cover art embedding, chapter markers
- **Track concatenation** — joining multiple files, crossfading, gap management
- **EQ and filtering** — parametric/graphic EQ, high/low-pass filters, voice presence shaping
- **Format conversion** — WAV / FLAC / MP3 / Opus / AAC with explicit bitrate/sample-rate control
- **Segmentation** — splitting on silence, markers, or timestamps; VAD-based per-utterance splits

Out of scope: MIDI composition, DAW-style multitrack mixing, realtime audio routing.

## Primitives available (via the audio-production plugin)

These commands are globally reachable once the plugin is installed:

- `/audio-production:normalize` — two-pass EBU R128 loudnorm
- `/audio-production:check-loudness` — measure LUFS / true peak / LRA
- `/audio-production:trim-silence` — strip leading/trailing silence
- `/audio-production:concat-audio` — concat or crossfade multiple files
- `/audio-production:convert-format` — transcode with explicit parameters
- `/audio-production:tag-audio` — view or set metadata tags
- `/audio-production:vad-segment` — voice-activity-based segmentation
- `/audio-production:audio-engineer` — autonomous subagent for multi-step chains

## Working Rules

### Preferred tooling

- `ffmpeg` for conversion, concatenation, filtering, metadata
- `sox` for EQ, effects chains, batch processing
- `ffprobe` for inspecting stream info
- `mid3v2` / `mutagen` / `eyeD3` for tag editing when ffmpeg flags aren't enough
- `loudnorm` (ffmpeg filter) for two-pass EBU R128 normalization
- `rnnoise` / `arnndn` for ML noise suppression when available

Confirm the tool is installed before invoking it. If a step requires a tool not present, tell the user and suggest an install command — do not silently substitute.

### Non-destructive processing

- **Never overwrite the original input.** Originals live in `inputs/` and are treated as read-only.
- Write processed output to `working/` or `processed/` with a clear suffix describing what was done (e.g. `interview_normalized.wav`).
- When running multi-step chains, keep intermediate files until the user confirms the final is good, then offer to clean up.

### Reproducibility

- Record the exact command used for any non-trivial processing step in `notes/` or as a sidecar `.txt` next to the output.
- For reusable EQ / filter chains, save parameters to `presets/` (e.g. `presets/voice-cleanup.txt`).

### Metadata edits

- Always show current tags before modifying them.
- For batch tag edits, dry-run and report all changes before applying.

### Loudness targets

Unless the user specifies otherwise:
- Spoken word / podcast: **-16 LUFS integrated, -1 dBTP**
- Music: **-14 LUFS integrated, -1 dBTP** (streaming target)
- Broadcast: **-23 LUFS integrated, -1 dBTP** (EBU R128)

Ask if unclear which target applies.

## Directory Map

- `inputs/` — original source files. Read-only.
- `working/` — in-progress intermediate files.
- `processed/` — final, user-approved outputs ready for delivery or archival.
- `metadata/` — sidecar files: tag sheets, chapter marker CSVs, cue sheets, cover art.
- `presets/` — reusable EQ/filter chain definitions.
- `notes/` — processing logs, decision notes, parameter rationales.
- `archive/` — superseded versions kept for reference.

## Repository Lifecycle

This workspace may hold a single job (one podcast episode) or a long-running series. Keep a short status note at the top of this file when the project spans multiple sessions so the next agent can pick up quickly.
