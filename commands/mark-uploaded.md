---
description: Move a finished episode from finished/ to uploaded/ with an ISO date stamp (podcast workspace)
---

Mark an episode as uploaded.

Input: filename (from `finished/`) via `$ARGUMENTS`. If missing, list `finished/` and ask.

Steps:
1. Verify the file exists in `finished/`.
2. Move it to `uploaded/<YYYY-MM-DD>-<original-filename>` using today's date.
3. If there's a matching `episodes/ep<NNN>-<slug>/metadata.yaml`, update `publish_date` to today.
4. Report the new path.
