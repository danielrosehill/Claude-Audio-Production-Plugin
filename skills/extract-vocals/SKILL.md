---
name: extract-vocals
description: Use when the user wants to quickly extract vocals (or isolated instrumentals) from a song or recording. Convenience wrapper around 2-stem `demucs` mode. Fastest stem separation for the common case.
---

# Extract Vocals (demucs 2-stem)

Isolate vocals from a mixed audio file using `demucs` in 2-stem mode. Fast and focused — produces `vocals.wav` and `accompaniment.wav`. Optionally drop the accompaniment if the user only wants the vocal stem.

## When to use

- The user wants vocals isolated from a song (e.g., for editing, re-recording, or remastering).
- Preparing a karaoke track — extract the accompaniment, discard vocals.
- Extracting a vocal guide from a podcast with music bed.
- Quick turnaround on a single stem (faster than 4-stem `separate-stems`).

Do **not** use this skill for:
- Full stem separation (drums, bass, other) → use `separate-stems`.
- Batch processing many files → use `separate-stems` with GPU for throughput.

## Inputs

1. **Input file** — required. MP3, WAV, FLAC, M4A supported.
2. **Output directory** — defaults to `vocals_<date>/` next to the input.
3. **Keep accompaniment** — boolean flag. Default: keep both stems. If `false`, delete the accompaniment stem and keep only `vocals.wav`.
4. **GPU flag** — optional. Pass `--gpu` to use CUDA; default is CPU.

## Procedure

1. Check if `demucs` is on `PATH` (`which demucs`). If missing, point the user at `install-deps` and note the ~2 GB download on first run.

2. Build the command:

   ```bash
   demucs \
     --two-stems vocals \
     -d <device> \
     -o "<output-dir>" \
     "<input-file>"
   ```

   Set `-d cuda` for GPU, `-d cpu` for CPU. Default is CPU.

3. Monitor progress and capture stderr.

4. After processing:
   - If `keep_accompaniment` is `false`, delete the accompaniment stem: `rm "<output-dir>/accompaniment.wav"`.
   - Else, leave both stems in place.

5. Verify output: confirm `vocals.wav` is present and non-zero size. If accompaniment was kept, confirm that too.

## Output

- Two WAV files (or one if accompaniment was dropped):
  - `vocals.wav` — isolated vocal track.
  - `accompaniment.wav` — (optional) instrumental/music bed, kept only if requested.
- Summary: `<input> → <output-dir> (vocals + accompaniment, 2-stem mode)` or `(vocals only)` if accompaniment was dropped.

## Notes

- 2-stem mode is faster than 4-stem; suitable for real-time turnaround on single files.
- GPU (CUDA) gives 5–10× speedup. Check `nvidia-smi` for availability.
- Output is always 44.1 kHz WAV, matched to the input sample rate where possible.
- The accompaniment includes drums, bass, and all non-vocal elements mixed together.

## Dependencies

Install via `pipx install demucs`. Requires PyTorch. Audio format support via ffmpeg.
