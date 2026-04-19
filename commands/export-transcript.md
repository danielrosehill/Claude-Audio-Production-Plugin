---
description: Export a transcript to PDF (via Typst), markdown, or plain text
---

Export a transcript.

Steps:

1. Identify the transcript. Prefer `cleaned/` if available; fall back to `raw/`. If not specified, list available transcripts and ask.

2. Ask the user which format(s) they want:
   - **markdown** — polished markdown with YAML frontmatter.
   - **pdf** — rendered via Typst.
   - **text** — plain text with no formatting.
   - **all** — generate all three.

3. For each requested format:

   **Markdown**:
   - Add or update YAML frontmatter (title, date, speakers, source audio).
   - Save to `exports/<basename>.md`.

   **PDF (via Typst)**:
   - Generate a Typst source file with:
     - Title page showing transcript title, date, and speaker list.
     - Speaker labels in bold.
     - Timestamps in a muted style if present.
     - Page numbers in the footer.
   - Compile with `typst compile`.
   - Save to `exports/<basename>.pdf`. Keep or drop the `.typ` file per user preference.

   **Plain text**:
   - Strip markdown formatting.
   - Render speaker labels as plain prefixes (`Speaker 1:`).
   - One blank line between turns.
   - Save to `exports/<basename>.txt`.

4. Use the same base filename as the source transcript for all exports.

5. Confirm which formats were generated and where.
