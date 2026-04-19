# Transcript Cleanup Workspace

Audio-to-transcript pipeline workspace. Provisioned by the [`audio-production` Claude Code plugin](https://github.com/danielrosehill/audio-production-plugin).

## Flow

```
audio/  →  raw/  →  cleaned/  →  exports/
```

## Typical session

1. Drop audio into `audio/`.
2. `/audio-production:transcribe audio/meeting.mp3` → `raw/meeting.md`.
3. `/audio-production:cleanup-transcript raw/meeting.md` → `cleaned/meeting.md`.
4. `/audio-production:diarize cleaned/meeting.md` (optional).
5. `/audio-production:export-transcript cleaned/meeting.md --format=all` → `exports/`.

For long recordings, run `/audio-production:vad-segment --mode=split` on the audio first to break it into per-utterance chunks before transcribing.

See `CLAUDE.md` for the full workspace rules.
