---
name: silence-cut-edl
description: Use when the user wants the silence-cut decisions as an editable timeline (Kdenlive / Final Cut Pro / Premiere / Shotcut XML) rather than a baked audio file, so they can review and adjust cuts in a video/audio editor before committing. Wraps `auto-editor` with a timeline export target.
---

# Silence Cut → EDL (auto-editor)

Detect silent sections with `auto-editor` and emit an editable timeline file instead of a finished audio render. Useful when the user wants final-say control: review the cut points in their editor, nudge any aggressive cuts, then render from the editor.

## When to use

- The user wants to review cuts before committing.
- The user is integrating cleaned audio into a video edit and wants the timeline directly.
- The user prefers their NLE's crossfade/render quality to auto-editor's.

Do **not** use this skill when:
- The user wants a finished audio file → use `silence-cut`.
- The user wants both → run `silence-cut` for the bake and this skill for the timeline; they're cheap.

## Inputs

1. **Input file** — required.
2. **Editor target** — one of: `kdenlive` (default — Daniel's editor), `final-cut-pro`, `premiere`, `shotcut`, `resolve`, `clip-sequence` (raw cut list as JSON).
3. **Threshold** — same semantics as `silence-cut`. Default `4%`.
4. **Margin** — same semantics. Default `0.2s`.
5. **Output path** — defaults to `<input-stem>.<editor-ext>` next to the input. Extension is editor-dependent (`.kdenlive`, `.fcpxml`, `.xml`, `.mlt`, `.json`).

## Procedure

1. Confirm `auto-editor` is installed.

2. Map the editor target to auto-editor's `--export` flag:

   | Target | `--export` value | Output extension |
   |---|---|---|
   | `kdenlive` | `kdenlive` | `.kdenlive` |
   | `final-cut-pro` | `final-cut-pro` | `.fcpxml` |
   | `premiere` | `premiere` | `.xml` |
   | `shotcut` | `shotcut` | `.mlt` |
   | `resolve` | `resolve` | `.fcpxml` |
   | `clip-sequence` | `clip-sequence` | `.json` |

   (Verify against the installed auto-editor version's `--export --help` if a target rejects.)

3. Build the command:

   ```bash
   auto-editor "<input>" \
     --edit "audio:threshold=<threshold>" \
     --margin <margin>sec \
     --export <target> \
     --output "<output>" \
     --no-open
   ```

4. Confirm the output file exists and is non-empty.

## Output

- Timeline file at the resolved path.
- One-line summary: `<input> → <output> (<n> clips kept, <pct>% cut)`.
- Hint to the user: open in their editor, review, adjust margins on tight cuts, render audio out.

## Notes

- The timeline file references the **input audio file by absolute path**. If the user moves either file, the timeline breaks — call this out.
- `clip-sequence` (JSON) is useful for downstream tooling that wants raw timestamps without parsing an editor format.
- For very fine-grained review, lower the threshold and tighten the margin — over-cutting is easier to fix in an editor than under-cutting.
