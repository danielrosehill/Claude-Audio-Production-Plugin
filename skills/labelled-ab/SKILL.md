---
name: labelled-ab
description: Build one listening file that compares two or more versions of a clip (original vs denoised, raw vs EQ'd, model A vs model B) with a spoken label before each version ("Original" ... "Denoised" ...), played through twice so the user can listen again without tracking which file is which. Use when the user asks for an A/B, a before/after, "let me hear the difference", or a comparison clip to open and listen to. Labels are rendered once with edge-tts and cached.
---

# Labelled A/B

One file, spoken labels, no UI: the user opens it in any player and hears
`"Original"` → clip → `"Denoised"` → clip, then the same again.

Script: `labelled_ab.py` next to this file. Skills read from the catalogue arrive without the
plugin, so run it from the local clone of `danielrosehill/Claude-Audio-Production-Plugin`
(`skills/labelled-ab/labelled_ab.py`), or clone it.

## Run

```bash
uv run --with numpy --with scipy --with soundfile python -I <clone>/skills/labelled-ab/labelled_ab.py \
  OUT.flac "Original=raw.flac" "Denoised=clean.flac" [--repeat 2] [--gap 0.8] [--match-loudness]
```

- Pairs are `Label=path`, in play order; any number of versions. The label is what gets spoken,
  so name versions in words the user will recognise ("Original", "Denoised", "Podcast chain").
- `--repeat` (default 2) plays the whole sequence that many times.
- `--match-loudness` scales each clip to the first one's speech level. Use it when comparing tone
  (EQ, compression); leave it off when the level change is part of what is being judged.
- Output takes the first clip's sample rate; FLAC/WAV are written 24-bit. Clips are never changed
  except for the optional loudness match. The script prints a timeline of where each label starts.

## Where things go

- **Cues**: `<data-dir>/tts/<slug>.wav`, the same folder `generate-cues` uses
  (`$CLAUDE_USER_DATA/audio-production`, else `${XDG_DATA_HOME:-~/.local/share}/claude-plugins/audio-production`).
  A missing label is rendered on first use with `edge-tts` (voice `en-US-AndrewNeural`,
  `--voice` to change), falling back to `espeak-ng`; delete the WAV to re-render it. Only the label
  text is sent to Microsoft's TTS endpoint, never the audio.
- **Output**: wherever the user wants it. With no other instruction, the user's exchange folder if
  one is configured. Give the absolute path and open it (`xdg-open <file>` on Linux).

## Choosing the clip

Pick a clip where the difference is audible: for a denoise, one with pauses (the noise lives in
the gaps); for EQ, continuous speech. Five to fifteen seconds per version is enough. Say what to
listen for (noise in the pauses, warbling "musical noise", a hollow or lispy voice, sibilance).
