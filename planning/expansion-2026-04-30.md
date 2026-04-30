# Audio-Production Plugin — Expansion Plan (2026-04-30)

## Plugin

- **Name:** `audio-production`
- **Path:** `~/repos/github/my-repos/Claude-Audio-Production-Plugin`
- **Scope:** Voice/podcast/music production — profiling, EQ, dynamics, denoise, loudness, segmentation, podcast assembly, cover art. **`ffmpeg`-first**, with `sox`, `deepfilternet`, `silero-vad`, `librosa` already in deps.

## Audit

**Already covered:**
- Loudness & EQ chain — `ffmpeg` (loudnorm, EQ filters, acompressor, de-ess proxy).
- Denoise — `deepfilternet` (ML, default), `afftdn` (ffmpeg fallback).
- Silence — `trim-silence`, `truncate-silence` (ffmpeg `silenceremove`, optional silero-vad).
- VAD — `silero-vad`.
- Profiling — `librosa`, `parselmouth`.
- Format conversion — `ffmpeg`.
- Tagging / cover art — ffmpeg + Fal pipeline.

**Gaps (domain operations not exposed):**
- Smart silence-based cut editing (vs. just collapsing — no edit-decision output).
- Stem separation (vocals vs. music — useful when raw recording has music bleed or for isolating speech).
- Reference-track mastering (match loudness *and* spectral profile of a target track — the "make this episode sound like NPR" move).
- Onset / beat detection for chapter-marker / cue generation.
- Time-stretch / pitch-shift without artefacts (slight speed-up of podcast episodes is a common ask; ffmpeg's `atempo` is OK but rubberband is the quality option).

## Recommended additions

### 1. `auto-editor` — smart cut editor (REQUIRED)

- **Licence:** Public domain (Unlicense).
- **Install:** `pipx install auto-editor` (Python, single CLI).
- **Why it fits:** The plugin currently only *collapses* silences in place. `auto-editor` produces real cut edits with crossfades, supports per-segment thresholds, and emits to multiple formats including timeline files (`final-cut-pro`, `premiere`, `kdenlive`, `shotcut`) — useful for podcast workflows where the user wants an EDL rather than a baked WAV.
- **Why not somewhere else:** It's an audio-first editor with optional video; the audio side is its core use case. Not a video-plugin's job.
- **Skills to add:**
  - `silence-cut` — Use when the user wants to remove silent sections from a recording with real cuts (not just collapsed gaps). Takes input file, optional silence threshold and margin, emits a tightened audio file.
  - `silence-cut-edl` — Use when the user wants an editable timeline (Kdenlive / Final Cut / Premiere XML) rather than a baked file, so they can review cuts in a video editor before committing.
- **Install required?** Required if either skill is invoked; `install-deps` should add it as **optional** with a clear "needed for silence-cut*" note.

### 2. `demucs` — vocal/music stem separation (OPTIONAL, heavy)

- **Licence:** MIT.
- **Install:** `uv pip install demucs` into the existing plugin venv. Pulls torch — already present if silero-vad bundle is installed.
- **Why it fits:** Cleaning podcast audio that has music bleed, isolating dialogue from a noisy capture, or stripping vocals from a music bed for re-use. Complements but does not overlap with `deepfilternet` (which is for stationary noise, not music/speech separation).
- **Why not somewhere else:** Stem separation for *production* (clean up a recording before EQ) lives with the production tools. It's not a transcription concern.
- **Skills to add:**
  - `isolate-vocals` — Use when the user wants to separate speech from background music or other non-speech sound (podcast with bleed, recorded interview with music in the room). Outputs `vocals.wav` and `accompaniment.wav`.
- **Install required?** Optional bundle. Heavy (torch + model download on first run). Document model cache location (`~/.cache/torch/hub/`).

### 3. `matchering` — reference-track mastering (OPTIONAL)

- **Licence:** GPL-3.0. Wrap-only — do not vendor.
- **Install:** `uv pip install matchering` into the plugin venv.
- **Why it fits:** Closes the loop on the EQ/loudness workflow. Today the plugin generates presets from a *voice profile*; matchering generates a master from a *target track*. Different input, same output category. Direct extension of `apply-chain` / `polish`.
- **Why not somewhere else:** Mastering is squarely production.
- **Skills to add:**
  - `match-master` — Use when the user has a reference track (an episode they like, a competitor's podcast, a song) and wants to master a new file to match its loudness curve and spectral profile. Inputs: target file, reference file. Output: mastered WAV.
- **Install required?** Optional. Add to the install-deps optional bundle.

### 4. `rubberband-cli` — time-stretch / pitch-shift (OPTIONAL)

- **Licence:** GPL-2.0 — wrap-only.
- **Install:** `sudo apt install rubberband-cli`.
- **Why it fits:** ffmpeg's `atempo` is workable for ±2× but artefacts at extremes; `rubberband` is the quality option for podcast speed-up (1.05–1.15× is a common authoring choice) and for fixing slow recordings without chipmunk pitch shift.
- **Why not somewhere else:** Speed/pitch is a production primitive.
- **Skills to add:**
  - `time-stretch` — Use when the user wants to speed up or slow down audio while preserving pitch (podcast tightening, slow-talker correction). Single skill takes a tempo ratio.
- **Install required?** Optional. apt-only, tiny footprint.

### 5. `aubio` — onset / beat / pitch detection (OPTIONAL)

- **Licence:** GPL-3.0 — wrap-only.
- **Install:** `sudo apt install aubio-tools` (provides `aubioonset`, `aubiotrack`, `aubiopitch`, `aubionotes`).
- **Why it fits:** The plugin already has a `suggest-title-description` skill that emits chapter markers — but those come from a transcript. `aubio` lets the plugin emit *acoustic* cue points (topic shifts mark on energy/onset changes, not just word changes) and could feed `assemble-episode` for crossfade alignment.
- **Why not somewhere else:** Audio-cue detection is production work.
- **Skills to add:**
  - `detect-cues` — Use when the user wants automatic cue/chapter timestamps based on audio onsets (energy spikes, silences, transitions) rather than transcript content. Emits a sidecar JSON with timestamps and confidence scores.
- **Install required?** Optional.

## Rejected candidates

- **Whisper / whisper.cpp** — Transcription. Different plugin (`Claude-Transcription-Plugin`). Already explicitly punted by the README. Do not absorb.
- **Audacity (mod-script-pipe)** — GUI-bound, stateful pipe, Wayland-fragile. Bad agent target. Use the underlying CLIs directly.
- **rnnoise / rnnoise-cli** — Redundant with `deepfilternet`. DFN is higher quality and already required. Adding rnnoise duplicates without filling a gap.
- **bs1770gain / loudgain** — Redundant with ffmpeg `loudnorm`, which the plugin already uses with two-pass EBU R128.
- **lame** — Redundant; ffmpeg already encodes MP3 via libmp3lame.
- **SoX effects beyond what's wrapped** — `sox` is already optional. If specific SoX-only effects (e.g. `phaser`, `tremolo`, `bend`) are wanted, expose them by extending existing skills, not by adding a CLI.
- **PaulXStretch** — niche extreme time-stretch, GUI-leaning. Out of scope for podcast/voice production.

## Concrete diffs

### Edits to `skills/install-deps/SKILL.md`

Add to the system-binary table:

```
| `rubberband` | `which rubberband` | optional | `sudo apt install rubberband-cli` | `brew install rubber-band` |
| `aubioonset` | `which aubioonset` | optional | `sudo apt install aubio-tools` | `brew install aubio` |
| `auto-editor` | `which auto-editor` | optional | `pipx install auto-editor` | `pipx install auto-editor` |
```

Add to the Python optional-packages bundle:

```
| `matchering` | optional | match-master |
| `demucs` | optional (heavy, pulls torch) | isolate-vocals |
```

Stage command additions:

```bash
# light optional bundle
uv pip install --python "$VENV_DIR/bin/python" matchering

# heavy ML bundle (also pulls demucs's torch dep — large)
uv pip install --python "$VENV_DIR/bin/python" demucs
```

### New skill directories to create

- `skills/silence-cut/SKILL.md`
- `skills/silence-cut-edl/SKILL.md`
- `skills/isolate-vocals/SKILL.md`
- `skills/match-master/SKILL.md`
- `skills/time-stretch/SKILL.md`
- `skills/detect-cues/SKILL.md`

### README.md updates

Under "Audio engineering primitives":
- Add `silence-cut`, `silence-cut-edl` (auto-editor)
- Add `time-stretch` (rubberband)
- Add `detect-cues` (aubio)
- Add `isolate-vocals` (demucs, optional)
- Add `match-master` (matchering)

### `onboard` updates

No structural change required. After `install-deps`, recommend the user run the optional bundle if they want the heavy capabilities (demucs).

## Order of operations

Recommended implementation sequence — cheapest-impact-first:

1. **`silence-cut` + `silence-cut-edl` (auto-editor)** — biggest immediate workflow win, smallest install footprint, no torch dependency. Start here.
2. **`time-stretch` (rubberband)** — trivial apt install, single skill, satisfies a real recurring need.
3. **`detect-cues` (aubio)** — apt-only, complements existing chapter-marker work.
4. **`match-master` (matchering)** — Python-only, but the workflow is more involved (need a reference track). Land after the cheap wins.
5. **`isolate-vocals` (demucs)** — last. Heavy install (torch + model download), edge-case use, easy to defer.

Per Daniel's plans rule: as each item is implemented in subsequent turns, **delete it from this file** rather than ticking it off.
