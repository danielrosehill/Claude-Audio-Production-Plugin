---
description: Clean up a raw transcript for readability — remove fillers, fix grammar, add paragraphs and section headers
---

Clean up a raw transcript.

Steps:

1. Identify the transcript to clean. If the user hasn't specified a file, list the contents of `raw/` (if the workspace has one) and ask. If there is only one file, proceed.

2. Read the raw transcript.

3. Edit for readability:
   - Remove filler words (um, uh, like, you know, sort of, kind of) unless they carry meaning.
   - Fix grammar errors and incomplete sentences.
   - Add proper punctuation and capitalisation.
   - Break long blocks into logical paragraphs.
   - Insert section headers where natural topic shifts occur.
   - Mark unclear or inaudible sections with `[inaudible]` or `[unclear]`.

4. Preserve the speaker's original voice and intent. Do not rephrase, summarise, or editorialize.

5. Carry forward the metadata block from the raw version and add a `cleaned` date field:
   ```
   ---
   source: meeting.mp3
   transcribed: 2025-03-15
   cleaned: 2025-03-16
   tool: whisper-large-v3
   ---
   ```

6. Save to `cleaned/<basename>.md` (transcript workspace) or next to the original with `-cleaned` suffix.

7. Do not modify or delete the original raw transcript.

8. Confirm what was cleaned and where the output was saved.
