---
name: tune-preset
description: Iteratively A/B tune an EQ preset to the user's taste. Each round renders two 15-second variants of the user's mic sample (with side-by-side spectrograms), the user picks A or B (or describes what they want changed), and the skill perturbs the preset accordingly until the user is happy. Then saves the winner. Use after suggest-eq when the heuristic preset doesn't quite land.
disable-model-invocation: true
allowed-tools: Bash(mkdir *), Bash(cp *), Bash(mv *), Bash(rm *), Bash(date *), Bash(ffmpeg *), Bash(ffprobe *), Bash(python3 *), Read, Write, Edit
---

# Tune Preset — Interactive A/B

Iteratively narrow in on an EQ + dynamics preset by listening to short A/B clips and either picking a side or describing what's still wrong.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
MICS_DIR="$PLUGIN_DATA_DIR/mics"
PRESETS_DIR="$PLUGIN_DATA_DIR/presets"
TUNE_DIR="$PLUGIN_DATA_DIR/tuning"
```

## Inputs

`$ARGUMENTS`:
- `--from=<preset>` — starting preset. Default: `<use-case>--<default_mic_id>` if `--use-case` is given, else ask.
- `--use-case=<podcast|vocals|spoken-word|broadcast>` — used both as the seed if `--from` is absent and as the loudness/dynamics target.
- `--mic=<mic-id>` — defaults to `default_mic_id`. Determines which sample is auditioned.
- `--name=<final-preset-name>` — name to save the winner as. Default: `<base-name>--tuned`.
- `--clip-duration=<seconds>` — default `15`.
- `--clip-start=<auto|HH:MM:SS|<seconds>>` — default `auto` (loudest 15s window in the mic's sample).

## Procedure

Each round produces a self-contained directory under `<TUNE_DIR>/<session-id>/round-<n>/` containing:

```
round-<n>/
  base.json          # preset state at the start of the round
  variant-a.json
  variant-b.json
  before.wav         # 15s reference clip (no processing)
  variant-a.wav      # 15s with variant A applied
  variant-b.wav      # 15s with variant B applied
  compare.wav        # ["Sample 1"] + variant-a + ["Sample 2"] + variant-b — single-file A/B
  spectrogram-a.png  # 0–8 kHz log-magnitude spectrogram
  spectrogram-b.png
  diff.txt           # which parameters differ between A and B, in plain English
```

### Round 0 — initialise

1. Load the base preset:
   - If `--from` is given, copy that preset JSON into the new session as `round-0/base.json`.
   - Else, if `--use-case` is given, copy `<PRESETS_DIR>/<use-case>--<mic-id>.json`.
   - Else, ask the user which preset to start from (list available via `/audio-production:list-presets`).

2. Cut a 15s `before.wav` from `<MICS_DIR>/<mic-id>/sample.wav`:
   - If `--clip-start=auto`, pick the loudest 15s window using ffmpeg `astats` (same logic as `/audio-production:extract-sample`).
   - Otherwise honour the explicit value.

3. Tell the user what was loaded and what the loudest 15s window contains.

### Each tuning round

#### 1. Choose a perturbation axis

Pick the axis that most likely shifts the user's perceived sound:

- **Round 1** default: `mud-cut` — render variant A with current `bands[freq=200..500].gain_db` and variant B with that gain ±2 dB.
- **Round 2** default: `presence` — perturb the 2.5–4 kHz band's gain ±1.5 dB.
- **Round 3** default: `de-ess` — perturb `deesser.threshold_db` ±3 dB.
- **Round 4** default: `compression` — perturb `compressor.ratio` (e.g. 2.5 ↔ 3.5).
- **Round 5+**: cycle, or pick the axis the user's previous feedback implicates.

If the user's previous-round feedback names a specific issue ("too sibilant", "muddy", "honky", "compressed-sounding", "thin", "boomy"), map it directly:

| User says | Axis | Direction |
|---|---|---|
| muddy / boxy / boomy | mud cut | more cut (−1 to −2 dB) |
| thin / hollow | mud cut | less cut |
| harsh / sibilant / sharp | de-ess | lower threshold (−3 dB) or +1 dB cut at sibilance peak |
| dull / dark / closed | presence | +1–2 dB at 3 kHz |
| nasal / honky | resonance band | −2 dB at the strongest 800–1500 Hz peak |
| compressed / squashed | compressor ratio | lower (e.g. 3:1 → 2:1) |
| dynamic / wild | compressor ratio | higher |
| pumping | release | longer (e.g. 80 → 150 ms) |
| rumble / boom | HPF | raise to 90–100 Hz |

So variant A = current, variant B = current + perturbation. (Or current ± perturbation if the previous-round feedback was just "neither — try a different direction".)

#### 2. Materialise variants

Write `variant-a.json` and `variant-b.json` with the appropriate perturbation, including a `tuning_metadata` block that records what was perturbed and by how much:

```json
{
  ...preset fields...,
  "tuning_metadata": {
    "session_id": "<id>",
    "round": <n>,
    "axis": "mud-cut",
    "delta": "+2 dB at 211 Hz",
    "parent": "round-<n-1>/<chosen-variant>.json"
  }
}
```

#### 3. Render audio

For each variant, build the ffmpeg filter chain (same translation as `/audio-production:apply-preset`) and render a 15s output:

```bash
ffmpeg -y -i "round-<n>/before.wav" -af "<chain>" -c:a pcm_s16le "round-<n>/variant-a.wav"
ffmpeg -y -i "round-<n>/before.wav" -af "<chain>" -c:a pcm_s16le "round-<n>/variant-b.wav"
```

Always run on the round's `before.wav` (not the source) so the audition window is byte-identical between variants.

#### 3b. Assemble the announced comparison clip

Stitch the pre-generated TTS cues from `<PLUGIN_DATA_DIR>/tts/` around the variants so the user hears one self-explanatory file:

```bash
ffmpeg -y \
  -i "<TTS_DIR>/sample-1.wav" \
  -i "round-<n>/variant-a.wav" \
  -i "<TTS_DIR>/sample-2.wav" \
  -i "round-<n>/variant-b.wav" \
  -filter_complex "[0:a][1:a][2:a][3:a]concat=n=4:v=0:a=1[out]" \
  -map "[out]" -c:a pcm_s16le "round-<n>/compare.wav"
```

If the cue files don't exist (`<TTS_DIR>/sample-1.wav` missing), surface a one-line message — `Run /audio-production:generate-cues to create the announcement clips, or skip; variants are still in variant-a.wav / variant-b.wav` — and continue without `compare.wav`.

#### 4. Render spectrograms

Inline Python via heredoc, using `librosa.display.specshow` + matplotlib:

- Load `variant-a.wav` and `variant-b.wav`.
- For each: compute `librosa.stft(n_fft=2048, hop_length=512)`, magnitude in dB.
- Plot with `librosa.display.specshow(..., y_axis='log', x_axis='time', sr=sr)`, `vmin=-80, vmax=0`, frequency range 60–8000 Hz.
- Save as PNG, 800×400 px, tight bbox.

If matplotlib isn't available, skip silently and note the omission in the round report.

#### 5. Write `diff.txt`

Plain-English comparison:

```
Round <n> — axis: mud-cut

Variant A (current):
  Mud cut: -4 dB @ 211 Hz, Q 1.0
Variant B (perturbation):
  Mud cut: -6 dB @ 211 Hz, Q 1.0

Everything else identical.
```

#### 6. Present to the user

Print:

- The round directory path.
- Playback hints:
  ```
  mpv "<round-dir>/compare.wav"            # single-file A/B with announcements
  # or audition the variants individually:
  mpv "<round-dir>/variant-a.wav"
  mpv "<round-dir>/variant-b.wav"
  ```
- Reference the spectrogram PNG paths so the user can open them visually.
- The plain-English diff.

Ask: **"A, B, both fine, neither, or describe what to change?"**

#### 7. Interpret the user's response and iterate

- **"A"** — pick variant A as the new base. Move to next axis (next round).
- **"B"** — pick variant B as the new base.
- **"both"** — record that the axis is dialled in; pick variant A and move on.
- **"neither"** — pick the round's previous base; try a different perturbation direction next round, or move to the next axis.
- **"happy" / "good" / "save this"** — finalise (see step 8).
- **freeform feedback** — map to the table in step 1 and start the next round.

The chosen variant becomes `round-<n+1>/base.json`. Increment round number.

### 8. Finalise

When the user signals satisfaction:

1. Copy the current base preset to `<PRESETS_DIR>/<final-name>.json`.
2. Strip the `tuning_metadata` block (it was per-session bookkeeping).
3. Update `derived_from` to reference the analysis path of the bound mic.
4. Add a top-level `tuned_via` field pointing at the session directory for traceability:

   ```json
   "tuned_via": "tuning/<session-id>/round-<final-n>/"
   ```

5. Run `/audio-production:audition-preset <final-name>` to emit a fresh full-length audition with the saved preset.
6. Report the final preset path, the audition path, and how many rounds it took.

## Safety

- Each round is non-destructive — base preset and prior rounds remain on disk.
- If the user wants to abandon mid-session, leave `<TUNE_DIR>/<session-id>/` in place; they can resume by re-invoking with `--from=<round-n-base>`.
- Never modify the original preset specified by `--from`. The final save is always to a new file unless the user explicitly opts to overwrite (`--overwrite-from`).

## Notes

- Pure local — no MCPs, no network.
- Spectrograms are optional sugar; the audio A/B is the load-bearing comparison.
- Matplotlib is in the dependency matrix as optional. If absent, suggest `/audio-production:install-deps`.
- 15 seconds is short enough to compare without ear fatigue; bump `--clip-duration` for longer auditions.
- For users who prefer to listen on identical material across all rounds, the same `before.wav` is reused unless they explicitly pass a new `--clip-start`.
