# Podcast Production Workspace

A workspace supporting end-to-end podcast episode production — from raw takes to uploaded episodes.

## Show Context

{Replace this with the show name, host(s), default episode format, distribution platforms, and any recurring conventions.}

## Folder structure

| Folder | Purpose |
|--------|---------|
| `raw-takes/` | Unedited recordings, straight off the mic. Organize by date or episode. |
| `cover-art/` | Episode cover images, show art, thumbnail variants. |
| `podcast-elements/` | Reusable audio assets. Subfolders: `intro-jingles/`, `outro-jingles/`, `stingers/`, `bumpers/`, `music-beds/`. |
| `show-jingles/` | Show-identity jingles (distinct from per-episode intros/outros). |
| `working/` | In-progress edits. Scratch space per episode. |
| `episodes/` | Episode project folders (one subfolder per episode, scaffolded via `/audio-production:new-episode`). |
| `finished/` | Mastered, normalized, tagged final versions ready to publish. |
| `uploaded/` | Published episodes. Moved here via `/audio-production:mark-uploaded` with date stamp. |
| `scripts-and-notes/` | Show notes, scripts, episode outlines. |
| `templates/` | ID3 tag templates, cover-art templates, episode-folder templates. |

## Target audio specs

- **Loudness**: -16 LUFS integrated (stereo podcast standard), -1 dBTP ceiling
- **Sample rate**: 44.1 kHz or 48 kHz
- **Channels**: stereo
- **Format**: MP3 (192 kbps CBR) for distribution; WAV/FLAC for masters
- **ID3**: title, artist (show name), album (show), track, year, genre="Podcast", cover art

## Primitives available (via the audio-production plugin)

- `/audio-production:new-episode` — scaffold a new episode folder under `episodes/`
- `/audio-production:normalize` — EBU R128 two-pass loudnorm
- `/audio-production:check-loudness` — analyze LUFS / true peak / LRA
- `/audio-production:trim-silence` — trim leading/trailing silence
- `/audio-production:assemble-episode` — concat intro + body + outro (with optional crossfades)
- `/audio-production:export-final` — encode master to MP3, tag ID3, embed cover art, place in `finished/`
- `/audio-production:mark-uploaded` — move from `finished/` to `uploaded/` with date stamp
- `/audio-production:transcribe` — transcribe via a transcription MCP or local Whisper
- `/audio-production:suggest-title-description` — title options, description variants, tags, chapter markers
- `/audio-production:generate-cover-art` — text-to-image or image-to-image via Fal AI Nano Banana 2
- `/audio-production:upscale-cover-art` — upscale via Fal AI SeedVR
- `/audio-production:bake-cover-art` — embed cover art into MP3 without re-encoding audio
- `/audio-production:vad-segment` — chunk recordings by voice activity (useful for long interviews)

## Tooling assumptions

- `ffmpeg` on PATH (all audio ops)
- `sox` optional (some trim-silence paths)
- `eyeD3` or `ffmpeg` for ID3 tagging
- `typst` if exporting show notes to PDF

## Non-destructive rules

- Never overwrite originals in `raw-takes/`.
- Work on copies in `working/`.
- Only place mastered, tagged outputs in `finished/`.
- Use `/audio-production:mark-uploaded` once published — do not move manually.
