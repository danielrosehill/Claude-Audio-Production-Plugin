---
name: onboard
description: First-run setup for the audio-production plugin. Provisions the persistent user-data directory, registers the user's primary microphone, captures a 3-min sample, profiles it, seeds default EQ presets, and produces 1-min A/B auditions. Run once before using profile-voice, suggest-eq, or apply-preset. Re-run any time to refresh.
disable-model-invocation: true
allowed-tools: Bash(mkdir *), Bash(cp *), Bash(test *), Bash(ls *), Bash(cat *), Bash(date *), Bash(ffprobe *), Bash(ffmpeg *), Bash(python3 *), Bash(pip *), Bash(pip3 *), Read, Write
---

# Onboard — Audio-Production Plugin

This skill provisions the plugin's persistent user-data directory and walks the user through registering their first microphone profile.

Profiles are mic-bound: each registered mic gets its own sample, analysis, and presets, so the user can switch microphones without retraining the whole pipeline.

## Data directory convention

Resolve the plugin's data directory as `$CLAUDE_USER_DATA/audio-production/` if `CLAUDE_USER_DATA` is set; otherwise `$XDG_DATA_HOME/claude-plugins/audio-production/` if `XDG_DATA_HOME` is set; otherwise `~/.local/share/claude-plugins/audio-production/`.

Layout:

```
<data-dir>/
  config.json                 # defaults — loudness target, default_mic_id, …
  mics/
    <mic-id>/
      metadata.json           # mic name, make/model, interface, room notes
      sample.wav              # 3-min canonical sample
      sample-source.txt       # original source path + offset
      analysis.json           # spectral profile
  presets/
    <name>.json               # has mic_id field
  auditions/
    <preset>__<mic-id>__<ts>/ # before.wav / after.wav / diff.txt
  state/                      # runtime state
```

Never write plugin data under `~/.claude/`. That's the install surface and is overwritten on plugin update.

## Procedure

### 1. Resolve and create the data dir

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
mkdir -p "$PLUGIN_DATA_DIR/mics" "$PLUGIN_DATA_DIR/presets" "$PLUGIN_DATA_DIR/auditions" "$PLUGIN_DATA_DIR/state"
```

### 2. Migrate any legacy data

If `<data-dir>/voice/` exists from a pre-mic-aware version of the plugin:

- Ask the user for an id and friendly name to attach to the existing data (suggest `default` if they don't care).
- Move `<data-dir>/voice/sample.wav` → `<data-dir>/mics/<mic-id>/sample.wav`.
- Move `<data-dir>/voice/analysis.json` → `<data-dir>/mics/<mic-id>/analysis.json`.
- Synthesise a `<data-dir>/mics/<mic-id>/metadata.json` with whatever the user can recall.
- For each existing preset in `<data-dir>/presets/`, add a `mic_id` field pointing at the new mic.
- Remove the empty `<data-dir>/voice/` directory.

### 3. Write or update `config.json`

If absent, create:

```json
{
  "loudness_target_lufs": -16,
  "true_peak_ceiling_dbtp": -1,
  "default_workspace_parent": "~/repos/github/my-repos",
  "default_use_case": "podcast",
  "default_mic_id": null
}
```

If present, fill in any missing fields with defaults; leave existing values alone.

### 4. Verify Python audio dependencies

```bash
python3 -c "import librosa, numpy" 2>/dev/null
```

If the import fails, surface the install command and stop:

```
pip install --user librosa numpy
# optional: pip install --user praat-parselmouth
```

Do not install automatically.

### 5. Register the mic

Hand off to `/audio-production:add-mic`. Walk the user through:

- A kebab-case **mic id** (used as directory name). Suggest something descriptive: `sm7b-desk`, `at2020-usb`, `lav-zoom-h6`.
- A **friendly name** for display.
- **Make / model** (e.g. "Shure SM7B").
- **Interface** (optional — e.g. "Focusrite Scarlett 2i2", "USB direct", "Zoom H6 channel 1").
- **Source recording** — path to a clean voice sample of the user speaking with this mic. At least 3 minutes preferred.
- **Environment notes** (optional — room treatment, mic distance, gain setting).

`add-mic` extracts a 3-min sample from the source via `/audio-production:extract-sample`, runs `/audio-production:profile-voice`, seeds presets via `/audio-production:suggest-eq`, and sets `default_mic_id` if it was unset.

### 6. Audition the seeded presets

For the `podcast`, `vocals`, and `spoken-word` presets just created, invoke `/audio-production:audition-preset` to produce 1-min A/B WAV pairs the user can play back to evaluate the suggestion.

### 7. Report

- Data directory path.
- Registered mic summary (id, name, make/model).
- Sample location and a one-line read of the analysis (pitch median, brightness, mud-vs-sibilance).
- Presets created and their audition paths.
- Note that re-running this skill or `/audio-production:add-mic` adds another mic profile rather than overwriting.
- Note that all plugin user data lives under one root and can be backed up by copying that directory.

## Notes

- Public plugin → never reference user-specific MCPs. All audio analysis runs via standard CLI tools (`ffmpeg`, `python3 + librosa`).
- If the user declines to register a mic, still create the data dir and `config.json`, leave `default_mic_id` null, and tell them they can register one any time with `/audio-production:add-mic`.
