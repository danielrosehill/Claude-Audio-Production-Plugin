---
description: Register a new microphone profile in the plugin's user-data directory. Captures mic metadata, extracts a 3-min sample from a source recording, runs voice profiling, and (optionally) seeds default presets bound to this mic.
---

Add a new mic profile.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
MICS_DIR="$PLUGIN_DATA_DIR/mics"
```

## Inputs

`$ARGUMENTS` may contain:
- `--id=<mic-id>` — kebab-case identifier (used as directory name). Required if not asked interactively.
- `--name="Friendly name"` — required.
- `--make-model="Shure SM7B"` — required.
- `--interface="Focusrite Scarlett 2i2"` — optional.
- `--source=<path>` — path to a source recording captured with this mic. Required.
- `--start=<auto|HH:MM:SS>` — passed through to `/audio-production:extract-sample`. Default `auto`.
- `--duration=<seconds>` — passed through. Default 180.
- `--seed-presets` — after profiling, also generate `podcast`, `vocals`, `spoken-word` presets bound to this mic. Default: yes (off only if `--no-seed-presets`).
- `--make-default` — set this mic as `default_mic_id` in `config.json`. Default: yes if no default exists.

If any required field is missing, ask the user for it.

## Procedure

### 1. Create the mic directory

```bash
MIC_DIR="$MICS_DIR/<mic-id>"
mkdir -p "$MIC_DIR"
```

If `<mic-id>` already exists, ask the user whether to overwrite or pick a different id.

### 2. Write `metadata.json`

```json
{
  "id": "<mic-id>",
  "name": "<friendly name>",
  "make_model": "<make and model>",
  "interface": "<audio interface, optional>",
  "captured_at": "<ISO timestamp>",
  "source_path": "<original audio file path>",
  "source_offset_seconds": 0,
  "sample_duration_seconds": 180,
  "environment_notes": "<optional — room treatment, distance, etc.>"
}
```

If the user wants to add freeform notes (room, mic distance, gain setting), prompt for them and put them in `environment_notes`.

### 3. Extract the sample

Invoke `/audio-production:extract-sample <source> --duration=<duration> --start=<start> --out=<MIC_DIR>/sample.wav`.

After extraction, write `<MIC_DIR>/sample-source.txt` with the original source path and chosen start offset for reproducibility.

### 4. Profile

Invoke `/audio-production:profile-voice --mic=<mic-id>`. This reads `<MIC_DIR>/sample.wav` and writes `<MIC_DIR>/analysis.json`.

### 5. Optionally seed presets

If `--seed-presets` (default), invoke `/audio-production:suggest-eq --mic=<mic-id> --use-case=podcast --name=podcast--<mic-id>`, then again for `vocals` and `spoken-word`. Each preset's JSON gets a `mic_id` field linking it back to this mic.

### 6. Update default mic

If `default_mic_id` in `config.json` is unset, OR `--make-default` was passed, set it to `<mic-id>`.

### 7. Report

- Mic id, name, make/model, interface.
- Sample path, duration, source offset.
- Analysis summary (one line: pitch median, mud vs sibilance read, brightness).
- Presets created (if any).
- Whether this mic is now the default.
- Suggest auditioning a preset: `/audio-production:audition-preset <preset>`.

## Notes

- Multiple mics can coexist. Use `/audio-production:list-mics` to see them all.
- `default_mic_id` is the implicit `--mic` value for any command that takes one and isn't given an explicit value.
- No external services or MCPs — everything runs locally.
