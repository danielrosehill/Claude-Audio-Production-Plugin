---
description: Measure an audio file's integrated LUFS, true peak, and loudness range without modifying it
---

Measure loudness stats for a file.

Input: file path from `$ARGUMENTS`. If absent, ask. Optional `--target=<LUFS>` (default -16) for the verdict calculation.

Run:
```
ffmpeg -hide_banner -i "<input>" -af loudnorm=I=<target>:TP=-1:LRA=11:print_format=json -f null -
```

Parse the JSON summary and report in a clean table:
- Integrated loudness (LUFS)
- True peak (dBTP)
- Loudness range (LU)
- Threshold
- Verdict: within ±1 LU of target and TP ≤ -1 dBTP = pass, otherwise recommend `/audio-production:normalize`.

Also report duration via `ffprobe -v error -show_entries format=duration -of csv=p=0 "<input>"`.
