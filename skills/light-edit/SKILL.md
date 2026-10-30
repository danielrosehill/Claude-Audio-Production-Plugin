---
name: light-edit
description: One-command light edit of a solo spoken-word recording (voice note, podcast monologue, MP3/WAV/M4A) to make it fit to share publicly. Cuts "um"/"uh"/"hmm" fillers with the Uhm frame classifier (no ASR), shortens long pauses, applies EQ fitted to the speaker's own voice, compresses gently and normalises to -16 LUFS. Writes an audited edit list. Use when the user says "clean up this recording", "remove the ums", "scrub the disfluencies", "light edit for the podcast", "make this voice note publishable", or wants the whole podcast production chain on one file.
---

# Light edit (fillers → pauses → voice EQ → loudness)

The full chain in one script: `${CLAUDE_SKILL_DIR}/scripts/podcast_light_edit.py`. Upstream repo, with the measured demo and the parameter sweep: https://github.com/danielrosehill/Podcast-Light-Edit-Chain. Keep the two copies of the script identical: change upstream first, then copy here.

| Stage | What | Default |
|---|---|---|
| fillers | Uhm (`desert-ant-labs/uhm`, ONNX fp16, CPU), per-20 ms frame probabilities; frames where uh+um+hmm ≥ threshold, merged, cut with 10 ms crossfades | thr 0.6, min 0.12 s, pad 0 |
| pauses | energy gate (10 dB over the room floor, adaptive) on the de-filled audio; long pauses shortened | > 0.8 s → 0.5 s |
| EQ | octave-band spectrum of the speech, deviations from the speaker's own log-frequency trend corrected 60%, ±3 dB cap; 80 Hz HPF, 2.5:1 compressor, light de-ess | fitted per file, or `--preset` |
| loudness | two-pass `loudnorm`, 128 kbps mono MP3 | -16 LUFS, -1.5 dBTP |

Measured on a 22.5-minute solo phone recording (2026-10-30), against AssemblyAI's disfluency tags: recall 0.68, precision 0.85, about 10 real words clipped. The defaults favour precision, so some ums stay. Details are in the upstream README.

## Inputs

- The input audio. Required. Never overwrite it.
- Output: default `<input-stem>.edited.mp3` next to the input, or wherever the user says.
- Preset: if the user has a saved light-edit preset for this voice/mic, pass it. Otherwise let the script fit one and save it.

## Procedure

1. Preflight: `ffmpeg`, `ffprobe` and `uv` on PATH. The Uhm weights (51 MB) download from Hugging Face on first run, into the HF cache.
2. Resolve the preset directory, `PRESETS="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production/light-edit"`, and list `$PRESETS/*.json`. If one matches the speaker, use `--preset`. If none does, add `--save-preset "$PRESETS/<speaker-or-mic>.json"` (create the directory).
3. Run it. Detection takes about 3 minutes of CPU per 20 minutes of audio, so run it in the background for long files:

   ```bash
   uv run --with onnxruntime --with huggingface_hub --with numpy --with soundfile \
     python "${CLAUDE_SKILL_DIR}/scripts/podcast_light_edit.py" "<input>" -o "<out.mp3>" \
     --probs "<out>.probs.npy" [--preset … | --save-preset …]
   ```

   `--probs` caches the model output, so a re-run with different settings skips detection. Use `--dry-run` to see the cut list without rendering.
4. Read `<out.mp3>.edits.json` and report: duration before/after, the number of filler cuts and their seconds, pauses shortened, gate dBFS, the EQ bands applied, and output LUFS. If more than 10% of the duration was cut as fillers, or there are fewer than 2 filler cuts in 10 minutes of speech, say so and suggest a threshold change.
5. Tuning on request:
   - "it cut words": raise `--filler-threshold` to 0.7.
   - "still too many ums": lower it to 0.5, or add `--fillers uh,um,hmm,other`. That raises recall but clips about twice as many words.
   - "pauses too tight": raise `--keep-silence`.
   - "EQ too strong": lower `--eq-strength`, or use `--no-eq`.

   Re-run with the same `--probs`.

## Optional: measure the filler cuts

When the user wants proof, or is tuning for a new voice, run `scripts/eval_fillers.py <original> <out.mp3>.edits.json --transcript <file>.aai.json` with `ASSEMBLYAI_API_KEY` set. It uploads the original to AssemblyAI (`disfluencies: true`, billed per audio hour). Say that before running it. It prints recall, precision and the cuts that clip real words.

## Notes

- Uhm is trained on English. Non-English fillers (Hebrew "eh") are not targeted.
- Uhm's licence is Desert Ant Labs Source-Available 1.0: free for most apps, with a commercial licence required at scale. Don't bundle the weights.
- For noisy sources, run `/audio-production:denoise` first and pass its output.
- This skill does not upload or publish anything.
