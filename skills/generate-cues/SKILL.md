---
name: generate-cues
description: Pre-generate the TTS announcement clips ("Sample 1", "Sample 2") that tune-preset and audition-preset stitch into combined comparison files so the user can identify which take is which without context-switching to a UI. Uses edge-tts (Microsoft Edge neural voices) by default; falls back to espeak-ng if edge-tts isn't installed or has no network. Idempotent — only re-runs when forced.
disable-model-invocation: true
allowed-tools: Bash(mkdir *), Bash(test *), Bash(ls *), Bash(cat *), Bash(ffmpeg *), Bash(ffprobe *), Bash(espeak-ng *), Read, Write
---

# Generate TTS Cues

Pre-render the spoken announcements that downstream A/B comparison tooling concatenates with audio clips. Generated once, reused on every tune session and audition.

## Resolve paths

```bash
PLUGIN_DATA_DIR="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/audio-production"
TTS_DIR="$PLUGIN_DATA_DIR/tts"
VENV="$PLUGIN_DATA_DIR/venv"
```

## Inputs

`$ARGUMENTS`:
- `--voice=<edge-voice-id>` — default `en-US-AndrewNeural` (clear, neutral male). See `python -m edge_tts --list-voices` for the catalogue.
- `--engine=<edge-tts|espeak-ng>` — default `edge-tts`. If edge-tts isn't installed or the network is unreachable, fall back to espeak-ng.
- `--force` — regenerate even if the cue files already exist.
- `--cues="Sample 1,Sample 2,Original,Variant A,Variant B"` — comma-separated list of phrases to render. Default just `Sample 1,Sample 2` (sufficient for tune-preset and audition-preset).

## Procedure

### 1. Skip if already done

If `<TTS_DIR>/sample-1.wav` and `<TTS_DIR>/sample-2.wav` exist and `--force` was not passed, report "cues already present" and exit.

### 2. Pick the engine

```bash
if [ "<engine>" = "edge-tts" ] && "$VENV/bin/python" -c "import edge_tts" 2>/dev/null; then
  ENGINE=edge-tts
elif command -v espeak-ng >/dev/null; then
  ENGINE=espeak-ng
else
  echo "No TTS engine available. Run /audio-production:install-deps to install edge-tts."
  exit 1
fi
```

### 3. Render each cue

For each phrase in the cue list, derive a slug (lowercase, spaces → hyphens) and render to `<TTS_DIR>/<slug>.wav` at 48 kHz mono PCM (matching the rest of the plugin's audio).

#### edge-tts path

```bash
mkdir -p "$TTS_DIR"
"$VENV/bin/python" - <<'PY'
import asyncio, os, re, sys
import edge_tts

phrases = sys.argv[1].split(",")
voice = sys.argv[2]
out_dir = sys.argv[3]

async def render(text, path):
    comm = edge_tts.Communicate(text, voice)
    await comm.save(path)

async def main():
    for p in phrases:
        slug = re.sub(r"[^a-z0-9]+", "-", p.lower()).strip("-")
        await render(p.strip(), os.path.join(out_dir, f"{slug}.mp3"))

asyncio.run(main())
PY "<cues>" "<voice>" "$TTS_DIR"
```

Then transcode each MP3 to canonical 48 kHz mono PCM WAV and remove the MP3:

```bash
for f in "$TTS_DIR"/*.mp3; do
  ffmpeg -y -i "$f" -ac 1 -ar 48000 -c:a pcm_s16le "${f%.mp3}.wav"
  rm "$f"
done
```

#### espeak-ng path (fallback)

```bash
for phrase in <cue list>; do
  slug=...
  espeak-ng -v en+m3 -s 150 -w "$TTS_DIR/${slug}.raw.wav" "$phrase"
  ffmpeg -y -i "$TTS_DIR/${slug}.raw.wav" -ac 1 -ar 48000 -c:a pcm_s16le "$TTS_DIR/${slug}.wav"
  rm "$TTS_DIR/${slug}.raw.wav"
done
```

### 4. Pad each cue with silence

Add 200 ms of leading silence and 400 ms of trailing silence so the cue doesn't sit flush against the audio sample it announces:

```bash
ffmpeg -y -i "$TTS_DIR/<slug>.wav" \
  -af "adelay=200|200,apad=pad_dur=0.4" \
  -c:a pcm_s16le "$TTS_DIR/<slug>.padded.wav"
mv "$TTS_DIR/<slug>.padded.wav" "$TTS_DIR/<slug>.wav"
```

### 5. Report

List each cue file with duration and the engine/voice used. Suggest the user audition them once:

```
mpv ~/.local/share/claude-plugins/audio-production/tts/sample-1.wav
```

## Notes

- edge-tts calls Microsoft's neural TTS endpoint over the network; expect ~1–2 seconds per phrase. No API key required, but offline use needs the espeak-ng fallback.
- Cues are 48 kHz mono PCM to match plugin canonical format — concatenation with audio clips is then a single `ffmpeg -i a.wav -i b.wav -filter_complex concat` call with no resampling.
- This skill is idempotent — re-run with `--force` if you change voices or want to regenerate.
- No cue content is sensitive; voicing `Sample 1` to a Microsoft endpoint is acceptable for everyone.
