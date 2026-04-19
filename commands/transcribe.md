---
description: Transcribe an audio file using a transcription MCP or local Whisper, saving markdown and plain-text outputs
---

Transcribe an audio file.

Input: audio file path from `$ARGUMENTS`. If missing, list the current directory's `audio/` (or `raw-takes/`) folder and ask.

Steps:
1. Pick the best available transcription path:
   - If a gemini-transcription MCP tool is available (e.g. `mcp__jungle-local__gemini-transcription__transcribe_audio` or `transcribe_with_preset`), prefer that.
   - Else if Whisper is installed locally (`whisper` CLI or `whisperx`), use it.
   - Else inform the user and suggest installing one of the above.
2. If the user supplies `--preset=<name>` and a preset-capable MCP is available, list presets first (`list_transcription_presets`) and use the selected one.
3. If the audio is longer than ~45 minutes, warn the user — consider running `/audio-production:vad-segment --mode=split` first to chunk by speech.
4. Save two outputs next to the audio (or in the workspace's `raw/` folder if one exists):
   - `<basename>-transcript.md` with a header and YAML frontmatter (`source`, `transcribed`, `tool`).
   - `<basename>-transcript.txt` (plain text) for pipeline use.
5. Preserve timestamps from the tool if provided, formatted inline as `[HH:MM:SS]`.
6. Report word count, duration, and the output paths.
