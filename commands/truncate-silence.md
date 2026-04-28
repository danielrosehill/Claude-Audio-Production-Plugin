---
description: Remove internal silences (gaps, pauses, dead air) throughout a recording using VAD. Different from trim-silence (which only strips the leading/trailing edges) and vad-segment (which splits into per-utterance files). Use to compact a long recording for podcast assembly or to tighten meandering takes.
---

Strip silent regions from inside a recording.

## When to use what

- **trim-silence** — strip leading/trailing silence only. Doesn't touch the middle.
- **truncate-silence** (this command) — collapse all silent regions throughout to a fixed maximum duration. Output is a single contiguous file.
- **vad-segment** — split into per-utterance files. Output is many files plus a sidecar.

## Inputs

`$ARGUMENTS`:
- First positional: input audio file. Required.
- `--engine=<ffmpeg|silero>` — default `ffmpeg`. `silero` requires `silero-vad` Python package.
- `--threshold-db=<dB>` — default `-40`. Threshold below which is silence.
- `--min-silence=<seconds>` — default `1.0`. Silences shorter than this are kept as-is.
- `--keep-pad=<seconds>` — default `0.3`. Leave this much silence at each gap (so cuts don't sound abrupt). ffmpeg engine only.
- `--out=<path>` — default: `<input-dir>/<stem>.trimmed.<ext>`.
- `--dry-run` — print the command(s) and stop.

## ffmpeg engine (default)

Validated tuning from the user's transcription plugin (`Claude-Transcription-Plugin/skills/truncate-silence`). Two `silenceremove` passes — first to strip leading silence, second (with `stop_periods=-1`) to collapse all internal silences:

```bash
ffmpeg -y -i "<input>" \
  -af "silenceremove=start_periods=1:start_duration=0.5:start_threshold=<threshold>dB:detection=peak,\
       silenceremove=stop_periods=-1:stop_duration=<min-silence>:stop_threshold=<threshold>dB:detection=peak" \
  -c:a pcm_s16le "<out>"
```

`detection=peak` is intentional — RMS detection misclassifies short loud transients during quiet speech.

To keep `<keep-pad>` of silence at each gap rather than removing it entirely, replace the second pass:

```
silenceremove=stop_periods=-1:stop_duration=<min-silence>:stop_threshold=<threshold>dB:detection=peak:stop_silence=<keep-pad>
```

### Tuning notes

- For close-miked podcasts: defaults work.
- For room-recorded / lower-SNR audio: try `--threshold-db=-35`.
- For very quiet speakers: try `--threshold-db=-45` and `--min-silence=1.5`.
- If the output sounds choppy (truncates breathing): bump `--keep-pad` to `0.5` or `0.7`.

## silero engine (more accurate, slower)

Use when ffmpeg's threshold-based approach leaves residual silence or chops words. Requires:

```
pip install --user silero-vad torch torchaudio
```

Procedure (inline Python via heredoc):

1. Load audio with `silero_vad.read_audio` at 16 kHz.
2. Run `get_speech_timestamps(wav, model, sampling_rate=16000, min_speech_duration_ms=250, min_silence_duration_ms=int(<min-silence>*1000), return_seconds=True)`.
3. Concatenate the speech regions back to the original sample rate using ffmpeg `aselect=between(t,start,end)+...` or by stitching clips with `ffmpeg-python`.

For most production work the ffmpeg engine is enough — only switch to silero when the user explicitly asks or the ffmpeg result is poor.

## Output convention

`<source-stem>.trimmed.<ext>` in the same directory unless `--out` is given.

## Report

- Input duration, output duration, percent reduction.
- Engine and parameters used.
- Filter chain string (auditability).

## Safety

- Never overwrite the input.
- Refuse to write the output over the input even if the user passes the same path explicitly — that path is destructive on long files.

## Notes

- Pure local. No MCPs, no network.
- For podcasts: use this *after* denoise but *before* loudness normalisation, so the loudness measurement reflects the actual content rather than averaging over silences.
