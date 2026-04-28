# audio-production-plugin

Claude Code plugin for audio engineering & production — voice profiling, EQ preset suggestion and application, compression, de-essing, normalisation, VAD segmentation, mastering, tagging, and podcast assembly. `ffmpeg`-first primitives plus a personal voice-profile workflow that persists to a versioned user-data directory.

Part of the [danielrosehill Claude Code marketplace](https://github.com/danielrosehill/Claude-Code-Plugins).

For transcription, diarisation, or transcript export, install the companion **[Claude-Transcription-Plugin](https://github.com/danielrosehill/Claude-Transcription-Plugin)**.

## What you get

### Voice profiling & EQ workflow

The plugin captures a reference voice sample for each microphone the user records with, analyses its spectral characteristics, and generates tailored EQ + dynamics presets that are bound to that mic. Profiles, presets, and A/B auditions all persist in a versioned user-data directory.

- `/audio-production:onboard` — first-run setup. Creates the user-data directory and walks through registering the user's primary microphone.
- `/audio-production:add-mic` — register a new mic (id, make/model, interface, environment notes), extract a 3-min sample from a source recording, profile it, and seed presets bound to it.
- `/audio-production:list-mics` — show all registered mics and the presets bound to each.
- `/audio-production:extract-sample <input>` — auto-pick the loudest 3-min window from a longer recording.
- `/audio-production:profile-voice [--mic=<id>]` — analyse a mic's reference sample with `librosa`. Writes F0, spectral centroid, sibilance/mud band energy, resonant peaks, and (optionally) formants.
- `/audio-production:suggest-eq --use-case=<podcast|vocals|spoken-word|broadcast> [--mic=<id>]` — translate the analysis into an EQ + dynamics preset and emit a 1-min A/B audition.
- `/audio-production:audition-preset <preset>` — emit a fresh 1-min before/after WAV pair for any saved preset.
- `/audio-production:list-presets` — list saved presets with a one-line summary of each chain.
- `/audio-production:apply-preset <name> <input>` — run a saved preset against an audio file via ffmpeg.

### Audio engineering primitives

- `normalize` — two-pass EBU R128 loudnorm (default target -16 LUFS, configurable)
- `check-loudness` — measure integrated LUFS, true peak, LRA without modifying the file
- `compress` — single-band ffmpeg `acompressor` with use-case shortcuts
- `de-ess` — band-limited dynamic cut for sibilance reduction (ffmpeg-only proxy)
- `apply-chain` — full chain (HPF → EQ → de-ess → compressor → loudnorm) in one invocation, from a preset or use-case shortcut
- `trim-silence` — strip leading/trailing silence via `silenceremove`
- `concat-audio` — concat or crossfade intro + body + outro into a single master
- `convert-format` — convert between WAV / FLAC / MP3 / Opus / AAC with explicit bitrate/sample-rate
- `tag-audio` — show or set ID3/Vorbis/FLAC tags and embed cover art
- `vad-segment` — voice-activity-detect an audio file and emit per-segment outputs or a timing sidecar

### Podcast primitives

- `new-episode` — scaffold an episode folder with notes, metadata, and standard subfolders
- `assemble-episode` — concat/crossfade episode parts into a master
- `export-final` — encode master to tagged MP3 with embedded cover art
- `mark-uploaded` — move a finished episode to `uploaded/` with date stamp
- `suggest-title-description` — generate title options, description variants, tags, chapter markers (give it a transcript, produced separately)
- `generate-cover-art` / `upscale-cover-art` / `bake-cover-art` — Fal AI cover-art pipeline

### Agent

- `audio-engineer` — autonomous audio processing subagent for multi-step chains

### Provisioning skill

- `/audio-production:new-workspace <name> [--variant=audio-engineering|podcast] [--local-only] [--private]`

Scaffolds a new audio workspace (CLAUDE.md + variant-specific folder tree), personalises it from `~/.claude/CLAUDE.md`, and by default creates a public GitHub repo.

### Standalone skill

- `/audio-production:vad` — globally-reachable voice activity detection skill, invokable from any cwd

## Workspace variants

- **`audio-engineering`** (general) — non-destructive processing scaffold with `inputs/` `working/` `processed/` `metadata/` `presets/` `notes/` `archive/`.
- **`podcast`** — end-to-end podcast production scaffold with `raw-takes/` `episodes/` `finished/` `uploaded/` `cover-art/` `podcast-elements/` and more.

## User-data directory

The plugin's mic profiles, EQ presets, and auditions persist outside the install directory so plugin updates never clobber them. Resolution order:

1. `$CLAUDE_USER_DATA/audio-production/` if `CLAUDE_USER_DATA` is set
2. else `$XDG_DATA_HOME/claude-plugins/audio-production/` if `XDG_DATA_HOME` is set
3. else `~/.local/share/claude-plugins/audio-production/`

Layout:

```
<data-dir>/
  config.json                       # defaults — loudness target, default_mic_id, …
  mics/
    <mic-id>/
      metadata.json                 # name, make/model, interface, room notes
      sample.wav                    # 3-min canonical sample
      sample-source.txt             # original source path + offset
      analysis.json                 # spectral profile
  presets/
    <name>.json                     # has mic_id field linking back
  auditions/
    <preset>__<mic-id>__<ts>/       # before.wav / after.wav / diff.txt
  state/                            # runtime state
```

Profiles are mic-bound, so multiple mics can coexist (desk SM7B, lav at the studio, USB condenser on the road) with their own presets. Back up the whole directory to back up every personalisation the plugin holds.

## Pattern

- Primitives live in the plugin → globally available from any cwd.
- Workspace scaffolds are provisioned as **data** → no `.claude/` tree inside provisioned workspaces.
- Voice profile and presets live in a single user-data root → portable, backupable, update-safe.

See [PLAN.md in Claude-Workspace-Reshaping-190426](https://github.com/danielrosehill/Claude-Workspace-Reshaping-190426) for the full pattern spec.

## Dependencies

- `ffmpeg` and `ffprobe` — required for all audio processing
- `python3` with `librosa` and `numpy` — required for voice profiling
- `praat-parselmouth` — optional, enables formant analysis
- `sox` — optional, used by some `trim-silence` paths
- `typst` — optional, used by some export paths

## Install

```
/plugin marketplace add danielrosehill/Claude-Code-Plugins
/plugin install audio-production
```

Then run `/audio-production:onboard` to register your primary microphone and seed the user-data directory.

## License

MIT.
