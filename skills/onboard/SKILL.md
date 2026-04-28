---
name: onboard
description: First-run setup for the audio-production plugin. Provisions the persistent user-data directory, captures a reference voice sample from the user, profiles it, and saves seed EQ presets (podcast, vocals, spoken-word). Run this once before using profile-voice, suggest-eq, or apply-preset. Re-run any time to refresh the voice profile.
disable-model-invocation: true
allowed-tools: Bash(mkdir *), Bash(cp *), Bash(test *), Bash(ls *), Bash(cat *), Bash(ffprobe *), Bash(ffmpeg *), Bash(python3 *), Bash(pip *), Bash(pip3 *), Read, Write
---

# Onboard — Audio-Production Plugin

This skill provisions the plugin's persistent user-data directory and captures the user's voice profile. Everything that follows (EQ suggestion, preset application, audio chains) reads from the artifacts created here.

## Data directory convention

Resolve the plugin's data directory as `$CLAUDE_USER_DATA/audio-production/` if `CLAUDE_USER_DATA` is set; otherwise `$XDG_DATA_HOME/claude-plugins/audio-production/` if `XDG_DATA_HOME` is set; otherwise `~/.local/share/claude-plugins/audio-production/`. Create it if it doesn't exist.

Layout:

```
<data-dir>/
  config.json                 # plugin defaults (loudness target, workspace parent, …)
  voice/
    sample.wav                # user reference sample (canonical copy)
    analysis.json             # spectral profile from profile-voice
  presets/
    <name>.json               # EQ + dynamics presets
  state/                      # runtime state (last-applied preset, etc.)
```

Never write plugin data under `~/.claude/`. That is Claude Code's install surface and is overwritten on plugin update.

## Procedure

### 1. Resolve and create the data dir

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
mkdir -p "$PLUGIN_DATA_DIR/voice" "$PLUGIN_DATA_DIR/presets" "$PLUGIN_DATA_DIR/state"
```

### 2. Migrate any legacy data (one-time)

If `~/.claude/audio-production/` or `~/.claude/plugins/audio-production/data/` exists, move contents into `$PLUGIN_DATA_DIR` and delete the legacy directory. Log what was moved.

### 3. Write or update `config.json`

If `config.json` doesn't exist, create it with sensible defaults:

```json
{
  "loudness_target_lufs": -16,
  "true_peak_ceiling_dbtp": -1,
  "default_workspace_parent": "~/repos/github/my-repos",
  "default_use_case": "podcast"
}
```

If it exists, leave existing values alone — only fill in any new fields with defaults.

### 4. Verify Python audio dependencies

The voice-profiling pipeline needs `librosa` and `numpy`. `parselmouth` (Praat) is optional for formant analysis.

```bash
python3 -c "import librosa, numpy" 2>/dev/null
```

If the import fails, tell the user the install command:

```
pip install --user librosa numpy
# optional: pip install --user praat-parselmouth
```

Do **not** install automatically — let the user choose their Python environment.

### 5. Capture a reference voice sample

Ask the user for a path to a clean voice sample (30 seconds to a few minutes; mono or stereo; any common format). Guidance to surface:

- Should be the user speaking naturally, no background music.
- Recorded with the microphone they typically use for production.
- WAV / FLAC preferred; MP3/Opus acceptable but lossy.

Copy (don't move) the sample to `$PLUGIN_DATA_DIR/voice/sample.wav`. If the source isn't WAV, transcode with ffmpeg:

```bash
ffmpeg -y -i "<source>" -ac 1 -ar 48000 -c:a pcm_s16le "$PLUGIN_DATA_DIR/voice/sample.wav"
```

### 6. Run the profiling step

Invoke `/audio-production:profile-voice` (or run its logic inline) against `voice/sample.wav`. This writes `voice/analysis.json` containing:

- F0 (fundamental frequency) median and range
- Spectral centroid, rolloff
- Sibilance band (5–9 kHz) average energy
- Mud band (200–500 Hz) average energy
- Top 3 resonant peaks below 1 kHz
- Optional: F1/F2 formants if `parselmouth` is installed

### 7. Seed default presets

For each of `podcast`, `vocals`, `spoken-word`, invoke `/audio-production:suggest-eq --use-case=<case>` to generate and save a starting preset under `presets/<case>.json`.

Each preset JSON should look like:

```json
{
  "name": "podcast",
  "use_case": "podcast",
  "derived_from": "voice/analysis.json",
  "created_at": "<ISO timestamp>",
  "filters": {
    "highpass_hz": 80,
    "bands": [
      {"freq_hz": 250, "gain_db": -3, "q": 1.0, "reason": "tame mud"},
      {"freq_hz": 3000, "gain_db": 2, "q": 0.9, "reason": "presence"},
      {"freq_hz": 6500, "gain_db": -2, "q": 4.0, "reason": "sibilance control"}
    ],
    "deesser": {"freq_hz": 6500, "threshold_db": -24, "ratio": 3.0},
    "compressor": {"threshold_db": -20, "ratio": 3.0, "attack_ms": 5, "release_ms": 80, "makeup_db": 3}
  },
  "loudness_target_lufs": -16
}
```

### 8. Report

Tell the user:

- The data directory path.
- That the voice sample was saved and analysed.
- Which presets were seeded and how to inspect them (`/audio-production:list-presets`).
- That the user can re-run this skill any time to refresh the profile.
- That all plugin user data lives under one root and can be backed up by copying that directory.

## Notes

- Never reference any user-specific MCP server in this skill — this plugin is publicly distributed. All audio analysis must run via standard CLI tools (`ffmpeg`, `python3 + librosa`).
- If the user declines to provide a voice sample, still create the data dir and `config.json`, and seed *generic* presets (no `derived_from`). Mark them with `"derived_from": null` so other commands know they're not personalised.
