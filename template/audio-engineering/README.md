# Audio Engineering Workspace

Workspace for general audio processing. Provisioned by the [`audio-production` Claude Code plugin](https://github.com/danielrosehill/audio-production-plugin) — the plugin's commands (`/audio-production:normalize`, `/audio-production:vad-segment`, etc.) are globally reachable; this repo is pure data.

## Layout

```
├── CLAUDE.md          # agent instructions
├── inputs/            # source files (read-only)
├── working/           # in-progress intermediate files
├── processed/         # final outputs
├── metadata/          # sidecar metadata (tag sheets, chapter CSVs, cover art)
├── presets/           # reusable EQ/filter chain presets
├── notes/             # processing logs and decision notes
└── archive/           # superseded versions
```

## Typical session

1. Drop source files into `inputs/`.
2. `/audio-production:check-loudness inputs/foo.wav`
3. `/audio-production:normalize inputs/foo.wav` → `working/foo-normalized.wav`
4. `/audio-production:trim-silence working/foo-normalized.wav` → `working/foo-trimmed.wav`
5. Move the accepted result to `processed/`.

For multi-step chains, delegate to the `audio-engineer` subagent.
