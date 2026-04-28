---
description: List all registered microphone profiles in the plugin's user-data directory, with metadata and the presets bound to each.
---

List registered mic profiles.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
MICS_DIR="$PLUGIN_DATA_DIR/mics"
PRESETS_DIR="$PLUGIN_DATA_DIR/presets"
```

If `$MICS_DIR` doesn't exist or is empty, tell the user to run `/audio-production:onboard` or `/audio-production:add-mic` first.

## Procedure

For each subdir of `$MICS_DIR`, read `metadata.json` and `analysis.json` (if present), and scan all preset JSONs in `$PRESETS_DIR` for a matching `mic_id`.

Render as a table:

| ID | Name | Make/model | Interface | Captured | Pitch median | Bound presets | Default |
|---|---|---|---|---|---|---|---|
| sm7b-desk | Desk SM7B | Shure SM7B | Scarlett 2i2 | 2026-04-28 | 103 Hz | podcast--sm7b-desk, vocals--sm7b-desk | ★ |

Mark the entry whose id matches `default_mic_id` in `config.json` with ★.

End with hints:

> Switch default with `/audio-production:set-default-mic <id>`. Add a new one with `/audio-production:add-mic`. Audition a preset with `/audio-production:audition-preset <preset>`.

## Notes

- Read-only.
- If a mic dir is missing `metadata.json`, list it with a `(unregistered)` marker.
