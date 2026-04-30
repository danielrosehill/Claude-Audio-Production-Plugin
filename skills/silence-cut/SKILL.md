---
name: silence-cut
description: Use when the user wants to remove silent sections from a recording with real cuts (not just collapsed gaps), producing a tightened audio file. Wraps `auto-editor` for podcast/voice cleanup. Distinct from `truncate-silence` — that collapses internal silences via ffmpeg `silenceremove`; this performs threshold-driven edit decisions with margin/padding and crossfades, more aggressive at finding good cut points.
---

# Silence Cut (auto-editor)

Tighten a recording by detecting and cutting silent sections with `auto-editor`. Optimised for spoken-word / podcast / voice memo cleanup where unfilled pauses, breath gaps, and dead air should be removed.

## When to use

- The user has a long-form spoken recording with significant silent gaps.
- The user wants real cuts with crossfades, not in-place silence collapse.
- Used as a pre-step before EQ/loudnorm in a polish chain — saves processing time on later stages.

Do **not** use this skill when:
- The user wants the edit *decisions* (cut list / EDL) for review in a video editor → use `silence-cut-edl`.
- The user wants to merely shrink long pauses without changing structure → use `truncate-silence`.

## Inputs

1. **Input file** — required. WAV / FLAC / MP3 / M4A all supported.
2. **Threshold** — silence detection level. Default: `4%` (auto-editor's default). Lower = more aggressive cutting (catches quieter speech as silence). Common range: `2%`–`6%`.
3. **Margin** — padding around kept audio so cuts don't clip word edges. Default: `0.2s` on each side. Use `0.1s` for tight edits, `0.4s` for breathing room.
4. **Output** — defaults to `<input-stem>.cut.<ext>` next to the input. Caller can override.

## Procedure

1. Verify `auto-editor` is on `PATH` (`which auto-editor`). If missing, point the user at `install-deps` (it's an optional dependency).

2. Build the command:

   ```bash
   auto-editor "<input>" \
     --edit "audio:threshold=<threshold>" \
     --margin <margin>sec \
     --output "<output>" \
     --no-open
   ```

   `--no-open` prevents auto-editor from launching a player on completion (it will otherwise on desktop systems).

3. Capture the auto-editor stdout. It reports the resulting duration and percentage cut — surface those numbers in the response.

4. Loudness sanity check (optional but recommended): run `ffprobe -i <output> -hide_banner` to confirm the file is valid and report duration delta.

## Output

- Tightened audio file at the resolved output path.
- One-line summary: `<input> (<orig-duration>) → <output> (<new-duration>, <pct>% cut)`.
- If the cut percentage is suspiciously high (>50%) or low (<5%), call it out and suggest threshold adjustment rather than silently accepting.

## Notes

- auto-editor will re-encode to match the input format. For lossless preservation, prefer WAV input/output.
- For very long files (>2h), auto-editor uses meaningful memory — the user may want to chunk first.
- Default threshold is calibrated for clean recordings; for noisy environments raise the threshold or denoise first (`/audio-production:denoise`).
