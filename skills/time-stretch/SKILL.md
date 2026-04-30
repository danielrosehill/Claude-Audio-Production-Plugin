---
name: time-stretch
description: Use when the user wants to speed up or slow down audio while preserving pitch — podcast tightening (1.05–1.15× is common), slow-talker correction, fitting an episode to a target duration, or de-chipmunking a sped-up source. Wraps `rubberband-cli` for high-quality time-stretch; falls back to ffmpeg `atempo` if rubberband isn't installed.
---

# Time Stretch

Change playback speed without changing pitch (and optionally vice-versa). `rubberband` is the quality engine — ffmpeg's `atempo` works for mild changes but artefacts at extremes; `rubberband` holds up to ~0.5×–2× cleanly.

## When to use

- Podcast post: tighten an episode by 5–15% to match a pace target.
- Recover a slow recording without making the speaker sound chipmunked.
- Fit an audio file to a target duration (e.g. ad slot).
- Pitch-shift without changing duration (less common — singing/voice acting work).

Do **not** use this skill for:
- Beat-aligned tempo changes — that's a music-production concern not in scope.
- Sample-rate conversion — use `convert-format`.

## Inputs

1. **Input file** — required.
2. **Mode** — one of:
   - `tempo` — change speed, preserve pitch. Takes a ratio (`1.10` = 10% faster, `0.95` = 5% slower).
   - `duration` — fit to a target duration in seconds; the skill computes the ratio.
   - `pitch` — shift pitch in semitones, preserve duration. Takes a number (`+2` = up two semitones, `-3` = down three).
3. **Output path** — defaults to `<input-stem>.stretched.<ext>`.

## Procedure

1. Detect engine. Prefer `rubberband` if on `PATH`; else fall back to ffmpeg `atempo` (and warn if the requested ratio is outside `[0.5, 2.0]` — `atempo` requires chaining beyond that range, which compounds artefacts).

2. **rubberband (preferred):**

   ```bash
   # tempo: ratio 1.10 = 10% faster
   rubberband --tempo <ratio> "<input>" "<output>"

   # duration: fit to N seconds
   #   ratio = orig_duration / target_duration
   rubberband --tempo <ratio> "<input>" "<output>"

   # pitch: shift by N semitones
   rubberband --pitch <semitones> "<input>" "<output>"
   ```

   Add `--fine` for high-quality (slower) processing on critical material; default mode is fine for most podcast use.

3. **ffmpeg fallback (atempo, tempo mode only):**

   ```bash
   ffmpeg -i "<input>" -filter:a "atempo=<ratio>" "<output>"
   ```

   For ratios outside `[0.5, 2.0]`, chain: `atempo=2.0,atempo=<remainder>` (or the inverse for slow-down). Warn the user that quality degrades.

   ffmpeg has no clean equivalent of `--pitch` without changing duration; if pitch mode is requested and rubberband is missing, tell the user to install rubberband — don't fake it.

4. Verify output: `ffprobe -i "<output>"`. Report old vs new duration and the ratio applied.

## Output

- Stretched/shifted audio file at the resolved output path.
- One-line summary: `<input> (<orig-duration>s) → <output> (<new-duration>s, ratio <ratio>, engine <rubberband|atempo>)`.
- For pitch mode: `<input> → <output> (pitch <±N> semitones, engine rubberband)`.

## Notes

- `rubberband-cli` is `apt install rubberband-cli` — tiny footprint. Add via `install-deps`.
- For very long files, rubberband processes single-threaded and is slower than atempo. Acceptable trade for quality on episode-length material.
- Tempo changes alter LUFS slightly; if the file was previously loudness-normalised, re-run `normalize` after.
