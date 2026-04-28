---
description: List EQ + dynamics presets saved in the plugin's user-data directory. Shows name, use case, when created, and a one-line summary of the filter chain.
---

List the user's saved presets.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
PRESETS_DIR="$PLUGIN_DATA_DIR/presets"
```

If `$PRESETS_DIR` doesn't exist or is empty, tell the user to run `/audio-production:onboard` first (or `/audio-production:suggest-eq --use-case=...` to create one ad-hoc).

## Procedure

For each `*.json` in `$PRESETS_DIR`:

- Parse the JSON.
- Extract: `name`, `use_case`, `created_at`, HPF freq, band count, de-esser presence, compressor ratio, loudness target.
- Note whether `derived_from` is `voice/analysis.json` (personalised) or `null` (generic).

Render as a table:

| Name | Use case | HPF | Bands | De-ess | Comp | Target | Personalised | Created |
|---|---|---|---|---|---|---|---|---|
| podcast | podcast | 80 Hz | 3 | yes | 3:1 | -16 LUFS | yes | 2026-04-28 |

End with a hint:

> Apply with `/audio-production:apply-preset <name> <input.wav>`. Edit by opening the JSON directly at `<path>`.

## Notes

- Read-only — never mutates files.
- If a preset JSON fails to parse, list it with a `(corrupt)` marker and continue with the rest.
