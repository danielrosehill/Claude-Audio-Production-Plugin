---
name: denoise-deepfilter
description: Use when the user wants to denoise audio using modern ML-based filtering. DeepFilterNet produces cleaner speech than traditional FFT/rnnoise methods — no watery/hollow artifacts. Wraps `deepFilter` binary for podcast/voice cleanup.
---

# Denoise (DeepFilterNet)

Remove background noise from audio using DeepFilterNet 3, a state-of-the-art ML-based denoiser. Preserves natural voice timbre better than rnnoise or ffmpeg's afftdn — ideal for podcast, interview, and voice-memo cleanup.

## When to use

- The user has a noisy podcast recording or interview.
- The source is speech-heavy (podcast, voice memo, audiobook); DeepFilterNet is tuned for voice.
- Existing denoise (rnnoise, afftdn) leaves artifacts (hollowness, over-suppression) → try DeepFilterNet for comparison.
- The user wants a single-pass, set-and-forget denoise without threshold tweaking.

Do **not** use this skill for:
- Music with noise — DeepFilterNet is speech-optimized; may remove subtle instruments.
- Surgical noise reduction needing manual control → use ffmpeg `afftdn` or rnnoise with threshold tuning.

## Inputs

1. **Input file** — required. WAV, MP3, FLAC supported.
2. **Output path** — defaults to `<input-stem>.deepfilter.<ext>`.
3. **Attenuation limit** — optional, in dB. Controls how aggressively the model suppresses noise. Default: unlimited (let model decide). Range: `1–40 dB`. Lower = more aggressive. Common: `10–20 dB` for heavy noise.
4. **Model version** — optional. Default: latest (v3). Can specify `deepfilter-v3` or `deepfilter-v2` if needed for compatibility.

## Procedure

1. Check if `deepFilter` is on `PATH` (`which deepFilter`). If missing, provide install instructions:
   - **Option A (binary):** Download from GitHub releases: `https://github.com/Rikorose/DeepFilterNet/releases`. Unzip and add to `PATH`.
   - **Option B (Rust):** `cargo install deep_filter`.
   - Or run `install-deps` if the plugin includes it.

2. Build the command:

   ```bash
   deepFilter \
     "<input-file>" \
     -o "<output-file>" \
     [--attenuation-limit <dB>]
   ```

   If `--attenuation-limit` is provided, insert it. Example: `--attenuation-limit 15`.

3. Run the command and capture stdout/stderr. DeepFilterNet reports progress (model loading, processing).

4. Verify output: `ffprobe -i "<output-file>" -hide_banner` to confirm the file is valid and report duration (should match input).

## Output

- Denoised WAV file at the resolved output path, same sample rate and bit depth as input.
- Summary: `<input> → <output> (denoised, attenuation-limit <limit|unlimited>, duration <N>s)`.
- If the output is noticeably quieter (not the expected outcome), suggest checking `ffmpeg -i <output> -filter:a "loudnorm"` to re-normalize.

## Notes

- First run may download model weights (~100 MB); subsequent runs are fast.
- DeepFilterNet preserves sample rate and bit depth — no re-encoding. Output is WAV.
- Model is tuned for speech; best results on voice/podcast. Not recommended for music or highly dynamic sources.
- If the user wants more/less aggressive filtering, suggest adjusting `--attenuation-limit` or trying `denoise-rnnoise` as an alternative.
- Output duration may be slightly different from input due to internal buffering; report actual output duration to confirm.

## Dependencies

Install `deepFilter` binary from GitHub releases or via `cargo install deep_filter`. Requires no Python or special runtime — it's a standalone Rust binary. Audio format support via ffmpeg or embedded codecs.
