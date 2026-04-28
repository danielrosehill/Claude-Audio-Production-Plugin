---
name: vad
description: Voice activity detection (VAD) — detect speech regions in an audio file and either emit a timing sidecar (JSON/CSV) or split the file into per-utterance segments. Use when the user wants to chunk long recordings for transcription, trim non-speech regions, find silence boundaries between speakers, or preprocess audio for a pipeline that expects short utterances. The cluster's namesake primitive — globally reachable from any cwd.
---

# Voice Activity Detection

Detect speech regions in an audio file. Two output modes:

1. **Sidecar mode** (default) — write a JSON + CSV of `[start, end]` speech segments next to the input.
2. **Split mode** — cut the input into per-utterance files in a `vad-segments/` folder.

## Arguments (`$ARGUMENTS`)

- **`<input>`** (required) — path to an audio file (any format ffmpeg handles).
- **`--mode=<sidecar|split>`** (optional, default `sidecar`).
- **`--out=<dir>`** (optional) — output directory. Defaults to the input's directory for sidecar mode, `<input-dir>/vad-segments/` for split mode.
- **`--min-speech=<seconds>`** (optional, default `0.3`) — minimum segment length to keep.
- **`--min-silence=<seconds>`** (optional, default `0.5`) — minimum silence to treat as a break.
- **`--threshold=<dB>`** (optional, default `-40`) — peak threshold below which counts as silence (used when falling back to ffmpeg).
- **`--engine=<auto|silero|webrtc|ffmpeg>`** (optional, default `auto`).

## Engine selection

### 1. If the user's goal is "chunk and transcribe"

Hand off to the `Claude-Transcription-Plugin` — it already wraps VAD-aware transcription presets (Gemini, Whisper, AssemblyAI). Only run this skill standalone when the user wants the raw VAD output (timing sidecar or split files) without transcription.

### 2. Prefer Silero VAD (Python)

If `silero-vad` is importable in the user's Python environment, use it:

```python
import torch, torchaudio
from silero_vad import load_silero_vad, get_speech_timestamps, read_audio

model = load_silero_vad()
wav = read_audio("<input>", sampling_rate=16000)
segs = get_speech_timestamps(
    wav, model,
    sampling_rate=16000,
    min_speech_duration_ms=int(<min-speech>*1000),
    min_silence_duration_ms=int(<min-silence>*1000),
    return_seconds=True,
)
```

### 3. Fallback — WebRTC VAD

If Silero isn't available but `webrtcvad` is, use 30 ms frames at aggressiveness 2, coalesce adjacent voiced frames, and apply the same min-speech / min-silence filters.

### 4. Last-resort fallback — ffmpeg silencedetect

```
ffmpeg -hide_banner -i "<input>" -af silencedetect=noise=<threshold>dB:d=<min-silence> -f null - 2>&1
```

Parse `silence_start` / `silence_end` lines; invert to derive speech regions.

Tell the user which engine was used in the final report.

## Sidecar mode

Emit two files next to the input:

- `<basename>.vad.json` — `[{"start": <float>, "end": <float>, "duration": <float>}, ...]`
- `<basename>.vad.csv` — `index,start,end,duration` with seconds to 3 decimal places.

Include a summary block in the chat response: engine used, segment count, total speech time, total silence time, speech ratio.

## Split mode

For each detected segment, cut losslessly where possible:

```
ffmpeg -hide_banner -ss <start> -to <end> -i "<input>" -c copy "<out>/<basename>-seg<NNN>-<start>s.<ext>"
```

If stream-copy is not viable (e.g. the container/codec can't start at non-keyframe boundaries), re-encode to WAV PCM:

```
ffmpeg -hide_banner -ss <start> -to <end> -i "<input>" -c:a pcm_s16le -ar 16000 -ac 1 "<out>/<basename>-seg<NNN>.wav"
```

Report: number of segments written, output directory, total output size.

## Safety

- Never overwrite the original input.
- If the output directory already contains `vad-segments/`, ask before overwriting.
- If the detected speech ratio is < 5% of the file, warn the user — the threshold may be too aggressive.

## Typical use cases

- **Transcribe long recordings** — split before transcribing to stay inside model context windows.
- **Remove dead air** — reassemble only the speech segments for a condensed version (follow up with `/audio-production:concat-audio`).
- **Diarisation prep** — VAD segmentation gives the diariser clean boundaries to work from.
- **Find silent gaps** — invert the sidecar to get silence regions for trimming or cue-point markup.
