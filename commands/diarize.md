---
description: Add speaker labels to a transcript
---

Add speaker labels to a transcript.

Steps:

1. Identify the transcript to diarise. Prefer files in `cleaned/` if available; fall back to `raw/`. If nothing is specified, list available transcripts and ask.

2. Ask the user if they know the speaker names. If yes, use those. If not, use generic labels (`**Speaker 1:**`, `**Speaker 2:**`, ...).

3. Read through and identify speaker turns based on:
   - Shifts in topic, tone, or speaking style.
   - Conversational cues (questions followed by answers, greetings, turn-taking).
   - Existing contextual clues in the text.

4. Apply speaker labels:
   - Each speaker label on its own line at the start of their turn, in bold: `**Speaker 1:**`.
   - Group consecutive statements by the same speaker into a single block.
   - Separate speaker turns with a blank line.

5. If the transcript already has partial labels, normalise them rather than starting from scratch.

6. Save the diarised transcript in `cleaned/` (or overwrite if the user confirms). Update the metadata block to include a `diarised` date field.

7. For tighter boundaries on longer files, consider running `/audio-production:vad-segment` on the source audio first to anchor speaker turns to speech regions.

8. Confirm what was processed, how many speakers were identified, and where the output was saved.
