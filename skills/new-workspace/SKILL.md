---
name: new-workspace
description: Provision a new audio-production workspace on disk. Use when the user wants to start a new audio engineering project, podcast production repo, or transcript cleanup workspace. Accepts a workspace name and optional variant (audio-engineering | podcast | transcript). Scaffolds the workspace, personalises CLAUDE.md from the user's global memory, and (by default) creates a GitHub repo.
disable-model-invocation: true
allowed-tools: Bash(mkdir *), Bash(cp *), Bash(cat *), Bash(git init *), Bash(git add *), Bash(git commit *), Bash(gh repo create *), Bash(gh auth status), Bash(git push *), Read
---

# Provision Audio-Production Workspace

Creates a new workspace for audio work. This plugin's commands (`/audio-production:normalize`, `/audio-production:vad-segment`, `/audio-production:transcribe`, etc.) are globally available once installed — this skill only provisions the **data scaffold** (CLAUDE.md + folder tree) that those commands read from and write to.

## Arguments

`$ARGUMENTS` is parsed as:

- **First positional**: workspace name (kebab-case, used as directory and GitHub repo name). Required.
- **Second positional** (optional): target parent path. Defaults to `~/repos/github/my-repos`.
- **`--variant=<audio-engineering|podcast|transcript>`** (optional): which scaffold to copy. Default: `audio-engineering`.
- **`--local-only`** (optional): skip GitHub repo creation and push. Default: create a public GitHub repo and push.
- **`--private`** (optional): create the GitHub repo as private. Default: public.

### Examples

```
/audio-production:new-workspace interview-cleanup
/audio-production:new-workspace ai-pod --variant=podcast
/audio-production:new-workspace meeting-transcripts --variant=transcript --local-only
```

## Procedure

### 1. Parse arguments

Extract workspace name, target parent path, variant, and flags from `$ARGUMENTS`. If workspace name is missing, ask the user for it. If variant is not one of `audio-engineering`, `podcast`, `transcript`, tell the user which variants are available.

### 2. Resolve the scaffold path

The bundled scaffold lives at `${CLAUDE_SKILL_DIR}/../../template/<variant>/`. Confirm it exists.

### 3. Read ambient facts

Read `~/.claude/CLAUDE.md` if it exists. Extract OS, locale, timezone, and user identity facts. These personalise the workspace CLAUDE.md at step 5.

### 4. Create the workspace directory

```bash
mkdir -p <target-parent>/<workspace-name>
cp -r ${CLAUDE_SKILL_DIR}/../../template/<variant>/. <target-parent>/<workspace-name>/
```

Do **not** copy any `.claude/` tree. The plugin's primitives are global.

### 5. Personalise CLAUDE.md

Open the new workspace's `CLAUDE.md` and:

- Replace any placeholder identity with facts from step 3.
- Add a short header noting the workspace name and variant.
- If ambient facts include OS/locale/timezone, embed them so downstream commands can skip re-asking.

### 6. Prompt for workspace-specific facts (variant-dependent)

- **audio-engineering**: ask for the project focus (e.g. "podcast ep 12 cleanup", "field recording batch normalize"). Write into `CLAUDE.md` under `## Project Context`.
- **podcast**: ask for show name, default loudness target (default -16 LUFS), and distribution format (default MP3 192 kbps CBR). Write these into `CLAUDE.md`.
- **transcript**: ask whether speakers are known and, if so, list them for future `/audio-production:diarize` runs.

### 7. Initialise git and (optionally) publish

```bash
cd <target-parent>/<workspace-name>
git init
git add .
git commit -m "Initial workspace from audio-production plugin"
```

Unless `--local-only` is set:

```bash
gh repo create <workspace-name> --<public|private> --source=. --push
```

Use `--public` by default, `--private` if flag was passed.

### 8. Print next steps

Tell the user:

- Workspace path and variant chosen.
- Which plugin commands apply:
  - **audio-engineering**: `/audio-production:normalize`, `/audio-production:check-loudness`, `/audio-production:trim-silence`, `/audio-production:concat-audio`, `/audio-production:convert-format`, `/audio-production:tag-audio`, `/audio-production:vad-segment`.
  - **podcast**: everything above plus `/audio-production:new-episode`, `/audio-production:assemble-episode`, `/audio-production:export-final`, `/audio-production:generate-cover-art`, `/audio-production:upscale-cover-art`, `/audio-production:bake-cover-art`, `/audio-production:mark-uploaded`, `/audio-production:suggest-title-description`, `/audio-production:transcribe`.
  - **transcript**: `/audio-production:transcribe`, `/audio-production:cleanup-transcript`, `/audio-production:diarize`, `/audio-production:export-transcript`, plus `/audio-production:vad-segment` for chunking long recordings.
- Reminder that the workspace is **data** — the user can delete/move it freely without losing the plugin's commands.

## Notes

- Resolve the scaffold path via `${CLAUDE_SKILL_DIR}/../../template/` (not `${CLAUDE_PLUGIN_ROOT}`, which isn't exported in skill bash injection — only in hooks/MCP).
- Never copy `.claude/` into the new workspace. If the user wants workspace-local overrides, they can add them manually later.
- Do not hard-code personal paths or identifiers — everything comes from user memory or prompts.
