---
description: Trim leading and trailing silence from an audio file using ffmpeg silenceremove
---

Trim silence from the start and end of a file (keeps internal pauses intact).

Input: file path from `$ARGUMENTS`. Default threshold: -50 dB, minimum silence: 0.5 s. Override via `--threshold=<dB>` and `--duration=<seconds>`.

Run:
```
ffmpeg -hide_banner -i "<input>" -af "silenceremove=start_periods=1:start_duration=<duration>:start_threshold=<threshold>dB:detection=peak,areverse,silenceremove=start_periods=1:start_duration=<duration>:start_threshold=<threshold>dB:detection=peak,areverse" "<input-basename>-trimmed.wav"
```

Report before/after duration. To strip internal silences as well, recommend `/audio-production:vad-segment` followed by `/audio-production:concat-audio`.
