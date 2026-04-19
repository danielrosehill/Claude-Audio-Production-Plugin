---
description: Scaffold a new episode folder under episodes/ with standard subfolders and a notes template (podcast workspace)
---

Scaffold a new podcast episode. Requires a podcast-variant workspace (has an `episodes/` directory at the root).

1. Ask the user for the episode number and short slug if not provided in `$ARGUMENTS` (e.g. `042 ai-automation-deep-dive`).
2. Create `episodes/ep<NNN>-<slug>/` with subfolders: `raw/`, `edited/`, `elements/`, `exports/`.
3. Create `episodes/ep<NNN>-<slug>/notes.md` with headings: `# Episode <NNN> — <title>`, `## Guest(s)`, `## Outline`, `## Show notes`, `## Links`, `## Timestamps`.
4. Create `episodes/ep<NNN>-<slug>/metadata.yaml` with keys: `title`, `number`, `recorded_date`, `publish_date`, `duration`, `guests`, `tags`, `description`.
5. Report the created path and remind the user to drop raw takes into `raw/` or symlink from the top-level `raw-takes/`.
