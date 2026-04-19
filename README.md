# audio-production-plugin

Claude Code plugin for audio production — processing, normalization, voice-activity detection, transcription, diarisation, and publishing. Ships a batch of `ffmpeg`-first primitives plus a provisioning skill with three workspace variants: audio-engineering, podcast, and transcript.

Part of the [danielrosehill Claude Code marketplace](https://github.com/danielrosehill/Claude-Code-Plugins).

## What you get

### Core audio primitives (`/audio-production:*`)

- `normalize` — two-pass EBU R128 loudnorm (default target -16 LUFS, configurable)
- `check-loudness` — measure integrated LUFS, true peak, LRA without modifying the file
- `trim-silence` — strip leading/trailing silence via `silenceremove`
- `concat-audio` — concat or crossfade intro + body + outro into a single master
- `convert-format` — convert between WAV / FLAC / MP3 / Opus / AAC with explicit bitrate/sample-rate
- `tag-audio` — show or set ID3/Vorbis/FLAC tags and embed cover art
- `vad-segment` — **the VAD primitive**. Voice-activity-detect an audio file and emit per-segment outputs or a timing sidecar

### Podcast primitives

- `new-episode` — scaffold an episode folder with notes, metadata, and standard subfolders
- `assemble-episode` — concat/crossfade episode parts into a master
- `export-final` — encode master to tagged MP3 with embedded cover art
- `mark-uploaded` — move a finished episode to `uploaded/` with date stamp
- `suggest-title-description` — generate title options, description variants, tags, chapter markers
- `generate-cover-art` / `upscale-cover-art` / `bake-cover-art` — Fal AI cover-art pipeline

### Transcription primitives

- `transcribe` — transcribe an audio file via MCP (gemini-transcription) or local Whisper
- `cleanup-transcript` — edit a raw transcript for readability
- `diarize` — add speaker labels to a transcript
- `export-transcript` — render to markdown / PDF (Typst) / plain text

### Agent

- `audio-engineer` — autonomous audio processing subagent for multi-step chains

### Provisioning skill

- `/audio-production:new-workspace <name> [--variant=audio-engineering|podcast|transcript] [--local-only] [--private]`

Scaffolds a new audio workspace (CLAUDE.md + variant-specific folder tree), personalises it from `~/.claude/CLAUDE.md`, and by default creates a public GitHub repo.

### Standalone skill

- `/audio-production:vad` — globally-reachable voice activity detection skill (the cluster's namesake primitive — invokable from any cwd without pulling in video/media tooling)

## Variants

- **`audio-engineering`** (general) — non-destructive processing scaffold with `inputs/` `working/` `processed/` `metadata/` `presets/` `notes/` `archive/`.
- **`podcast`** — end-to-end podcast production scaffold with `raw-takes/` `episodes/` `finished/` `uploaded/` `cover-art/` `podcast-elements/` and more.
- **`transcript`** — audio-to-transcript pipeline scaffold with `audio/` `raw/` `cleaned/` `exports/`.

## Pattern

Primitives live in the plugin → globally available from any cwd.
Workspace scaffolds are provisioned as **data** → no `.claude/` tree inside provisioned workspaces.
Plugin updates never touch your workspace data.

See [PLAN.md in Claude-Workspace-Reshaping-190426](https://github.com/danielrosehill/Claude-Workspace-Reshaping-190426) for the full pattern spec.

## Install

```
/plugin marketplace add danielrosehill/Claude-Code-Plugins
/plugin install audio-production
```

## License

MIT.
