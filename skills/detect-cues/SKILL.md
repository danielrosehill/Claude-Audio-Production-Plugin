---
name: detect-cues
description: Use when the user wants automatic cue/chapter timestamps based on acoustic features (onsets, energy spikes, silence boundaries, beat positions, pitch changes) rather than transcript content. Wraps the `aubio` CLI tools to emit a sidecar JSON with timestamps and metadata. Complements `suggest-title-description` (which derives chapters from a transcript) by surfacing places to *look* in the audio that the transcript may not flag.
---

# Detect Cues

Acoustic cue detection — find timestamps where *something happens* in the audio, independent of what was said. Useful for:

- Chapter markers anchored to topic-shift moments (which usually coincide with energy/onset changes).
- Crossfade alignment when assembling multi-part episodes.
- Pre-edit triage: skim a long recording by jumping to onset clusters.
- Beat detection on music beds for cue-point editing.

## When to use

- Long recording where the user wants a "table of acoustic events" without transcribing first.
- Episode assembly: align cuts to actual silences/onsets rather than guessed offsets.
- Music: find beat positions for cueing.

Do **not** use this skill when:
- The user wants chapter markers from *transcript content* — that's `suggest-title-description`.
- The user wants silence-based *cuts* — that's `silence-cut` / `silence-cut-edl`.

## Inputs

1. **Input file** — required. WAV preferred; aubio handles common formats but is happiest with PCM.
2. **Mode** — one of:
   - `onset` (default) — generic note/event onsets. Best for spoken-word topic shifts.
   - `beat` — beat detection. For music or rhythmic material.
   - `pitch` — pitch track. Returns a stream, not discrete cues; reduce to cue points by detecting large jumps.
3. **Onset method** (mode=onset only) — `default`, `energy`, `hfc`, `complex`, `phase`, `specdiff`, `kl`, `mkl`, `specflux`. Default = `default` (HFC-based). For voice, `energy` or `hfc` work well; for music, `complex` or `specflux`.
4. **Threshold** — picking peakiness. Default `0.3`. Lower = more cues (more sensitive); higher = only strongest events.
5. **Min interval** — minimum seconds between accepted cues, to deduplicate clusters. Default `2.0` for voice, `0.3` for music/beat.
6. **Output path** — defaults to `<input-stem>.cues.json` next to the input.

## Procedure

1. Verify the relevant aubio binary is on `PATH` (`which aubioonset` / `aubiotrack` / `aubiopitch`).

2. Build the command per mode:

   **onset:**
   ```bash
   aubioonset -i "<input>" -O <method> -t <threshold> -M <min-interval>
   ```
   Output is one timestamp per line (seconds, float).

   **beat:**
   ```bash
   aubiotrack -i "<input>"
   ```
   Output is one beat-time per line.

   **pitch:**
   ```bash
   aubiopitch -i "<input>"
   ```
   Output is two columns: `<time> <pitch-hz>`. To reduce to cues, post-process: emit a cue every time the pitch changes by more than N semitones from the running median, separated by ≥ min-interval.

3. Parse the output and assemble JSON:

   ```json
   {
     "input": "<absolute-path>",
     "duration": <seconds>,
     "mode": "<onset|beat|pitch>",
     "params": { "method": "...", "threshold": 0.3, "min_interval": 2.0 },
     "cues": [
       { "t": 12.34, "label": "onset" },
       { "t": 47.81, "label": "onset" },
       ...
     ],
     "count": <n>
   }
   ```

   For `pitch` mode, label each cue with the detected pitch in Hz and a coarse note name (optional).

4. Write JSON to the output path.

## Output

- Sidecar JSON file at the resolved path.
- One-line summary: `<input> (<duration>s) → <output> (<n> cues, mode <mode>)`.
- If cues are suspiciously dense (>1 every 5s for voice in onset mode) or sparse (none in a long file), call it out and suggest threshold adjustment.

## Notes

- aubio's defaults are tuned for music. For voice, prefer `-O energy` and a higher `-M` (2–5s) — voice has many micro-onsets you don't want as cues.
- Time alignment: aubio cues are reasonably accurate (~10ms) but not sample-perfect; nudge in an editor if used for hard cuts.
- For very long files, consider denoising first (`/audio-production:denoise`) — background noise inflates onset counts.
- The JSON sidecar is structured to be consumable by `assemble-episode` for crossfade alignment, and by `suggest-title-description` as a complement to transcript-derived chapters.
