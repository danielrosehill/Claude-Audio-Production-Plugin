# Podcast Production Workspace

End-to-end podcast production workspace. Provisioned by the [`audio-production` Claude Code plugin](https://github.com/danielrosehill/audio-production-plugin).

## Typical episode flow

1. Record into `raw-takes/`.
2. `/audio-production:new-episode 042 ai-deep-dive` — scaffold the episode folder.
3. Edit in `episodes/ep042-ai-deep-dive/edited/`.
4. `/audio-production:assemble-episode --intro ... --body ... --outro ... --out episodes/ep042.../master.wav`
5. `/audio-production:normalize` + `/audio-production:check-loudness`.
6. `/audio-production:generate-cover-art` (or reuse).
7. `/audio-production:export-final` → drops into `finished/`.
8. Upload, then `/audio-production:mark-uploaded`.

See `CLAUDE.md` for the full primitive list.
