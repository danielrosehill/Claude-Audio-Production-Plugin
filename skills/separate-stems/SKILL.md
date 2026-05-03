---
name: separate-stems
description: Use when the user wants to separate an audio file into vocal and instrumental stems (or 6-stem separation). Wraps `demucs` for isolating drums, bass, vocals, and other instruments. Common uses — karaoke prep, podcast remixing, music production.
---

# Separate Stems (demucs)

Decompose an audio file into isolated instrument stems using Meta's `demucs` model. Produces WAV files for vocals, drums, bass, and other instruments — or 6-stem breakdown with the `htdemucs_6s` model.

## When to use

- The user wants to isolate vocals or drums from a mixed recording.
- Preparing a song for karaoke or remixing.
- Extracting a vocal layer from a podcast with music bed.
- Building separated stems for music production or remastering.

Do **not** use this skill for:
- Quick vocal isolation with minimal processing time → use `extract-vocals` (faster 2-stem mode).
- Removing vocals entirely → use a different skill or post-process stems.

## Inputs

1. **Input file** — required. MP3, WAV, FLAC, M4A supported.
2. **Model** — default `htdemucs` (4-stem). Options:
   - `htdemucs` — 4-stem (vocals, drums, bass, other).
   - `htdemucs_6s` — 6-stem (vocals, drums, bass, piano, other, sample).
   - `mdx_extra` — alternative model, slightly different separation quality.
3. **Output directory** — defaults to a timestamped `stems_<date>/` next to the input.
4. **GPU flag** — optional. Pass `--gpu` to use CUDA (much faster on NVIDIA hardware); default is CPU.
5. **Device** — optional. Specify `cuda` or `cpu` explicitly via `-d <device>`.

## Procedure

1. Check if `demucs` is on `PATH` (`which demucs`). If missing, point the user at `install-deps` and note that first run downloads ~2 GB of model weights.

2. Build the command:

   ```bash
   demucs \
     --model <model> \
     -d <device> \
     -o "<output-dir>" \
     "<input-file>"
   ```

   For 6-stem, specify `--model htdemucs_6s`. For GPU, use `-d cuda`; for CPU, `-d cpu`.

3. Monitor progress. `demucs` reports progress to stderr; capture and relay key milestones (loading model, processing, writing stems).

4. On first run, warn the user: "First run will download ~2 GB of model weights to `~/.cache/demucs/`. This is one-time; subsequent runs are instant."

5. Verify output: list the stems directory and confirm all WAV files are present and non-zero size.

## Output

- Directory containing WAV stems: `vocals.wav`, `drums.wav`, `bass.wav`, `other.wav` (4-stem), or with `piano` and `sample` added for 6-stem.
- Summary: `<input> → <output-dir> (4 stems, model htdemucs, processed in X seconds)`.
- If using GPU, note: `(CUDA device <N>, processed in X seconds)`.

## Notes

- First run requires ~2 GB download; don't block, just warn upfront.
- GPU (CUDA) is 5–10× faster. Check `nvidia-smi` or note `CUDA_VISIBLE_DEVICES` if needed.
- Output stems are always 44.1 kHz WAV, matched to the input sample rate as closely as demucs supports.
- For very long files (>1h), CPU processing can take several minutes. GPU recommended for batch work.

## Dependencies

Install via `pipx install demucs` or `pip install demucs`. Requires PyTorch; demucs handles the download. Audio format support via ffmpeg.
