# Transcript Cleanup Workspace

A workspace for processing audio recordings into clean, readable transcripts. Supports the full pipeline from raw audio to formatted exports.

## Purpose

Take audio files (interviews, meetings, lectures, podcasts, voice notes) and produce well-structured, readable transcripts in multiple output formats.

## Pipeline

Transcripts move through a defined version chain:

1. **Raw** (`raw/`) — machine-generated transcript from audio, unedited.
2. **Cleaned** (`cleaned/`) — edited for readability: filler words removed, grammar corrected, punctuation added, speaker labels applied.
3. **Exported** (`exports/`) — final formatted output in markdown, PDF (via Typst), or plain text.

Each stage preserves the previous version. Never overwrite a raw transcript when cleaning — always write to the next stage directory.

## Directory Structure

- **audio/** — source audio files (mp3, wav, m4a, ogg, flac)
- **raw/** — unedited machine transcripts
- **cleaned/** — edited, readable transcripts with speaker labels
- **exports/** — final formatted outputs (md, pdf, txt)

## Primitives available (via the audio-production plugin)

- `/audio-production:transcribe` — generate a raw transcript via MCP or local Whisper
- `/audio-production:cleanup-transcript` — edit for readability, save to `cleaned/`
- `/audio-production:diarize` — add speaker labels
- `/audio-production:export-transcript` — render to markdown / PDF / text
- `/audio-production:vad-segment` — chunk long audio before transcribing (keeps files inside model context windows)
- `/audio-production:trim-silence`, `/audio-production:normalize` — optional audio preprocessing

## Cleanup Rules

When editing a raw transcript for readability:

- Remove filler words (um, uh, like, you know, sort of, kind of) unless they carry meaning.
- Fix obvious grammar errors and incomplete sentences.
- Add proper punctuation and paragraph breaks.
- Break long monologues into logical paragraphs.
- Preserve the speaker's voice and meaning — do not rephrase or editorialize.
- Mark unclear or inaudible sections with `[inaudible]` or `[unclear]`.
- Add section headers where natural topic changes occur.

## Speaker Diarisation

- Default labels: `**Speaker 1:**`, `**Speaker 2:**`, ...
- Replace with actual names when known (`**Alice:**`).
- Place labels at the start of each turn, on their own line.
- Group consecutive statements by the same speaker into a single block.
- Separate turns with blank lines.

## Export Formats

### Markdown
Standard markdown with YAML frontmatter containing title, date, speakers, and source audio filename.

### PDF (via Typst)
Title page with transcript metadata; speaker labels bold; timestamps muted if present; page numbers in footer.

### Plain Text
Stripped-down version. Speaker labels as plain prefixes (`Speaker 1:`). One blank line between turns.

## File Naming

Use the audio file's base name throughout the pipeline:

- Audio: `audio/team-standup-2025-03-15.mp3`
- Raw: `raw/team-standup-2025-03-15.md`
- Cleaned: `cleaned/team-standup-2025-03-15.md`
- Export: `exports/team-standup-2025-03-15.pdf`

Use kebab-case for all filenames. Include dates where relevant.

## Writing Style

- Never use emojis.
- Keep metadata blocks concise.
- Use consistent formatting across all transcripts in the repository.
