---
description: Generate episode title and description suggestions from a transcript or show notes
---

Generate title and description suggestions for an episode.

Input (from `$ARGUMENTS` or ask): path to a transcript (`.md` / `.txt`) or show notes file. If only an audio file is given, ask the user to run a transcription first via the `Claude-Transcription-Plugin` and pass the resulting transcript here.

Produce:
1. **5 title options** — mix of: descriptive, question-form, provocative/hooky, SEO-keyword-led, short-and-punchy. Keep under 70 chars each.
2. **3 description variants** (for episode metadata / show notes):
   - **Short** (~280 chars, tweet-length)
   - **Medium** (~500 chars, podcast-directory standard)
   - **Long** (~1200 chars, full show-notes intro with key themes, guest mention if any, and a CTA)
3. **Tag/keyword suggestions** — 8–12 topical tags.
4. **Chapter markers** — if the transcript contains timestamps, propose 4–8 chapter markers with `HH:MM:SS Title` format.

Write all output to `episodes/<ep-folder>/title-description-suggestions.md` if an episode folder is implied, otherwise print to chat.
