---
description: Encode a mastered WAV to tagged MP3 with embedded cover art, placed in finished/ (podcast workspace)
---

Export a master to distribution-ready MP3.

Inputs (from `$ARGUMENTS` or ask):
- `--in <master.wav>` (required)
- `--title <episode title>` (required)
- `--number <NNN>` (required)
- `--show <show name>` (required — or read from a project-level config if present)
- `--cover <image file>` (optional; defaults to latest file in `cover-art/`)
- `--date <YYYY-MM-DD>` (optional; defaults to today)

Behavior:
1. Verify the master is normalized — run the `loudnorm` measure pass; warn if integrated LUFS is outside -16 ±1.
2. Encode to MP3 at 192 kbps CBR, 44.1 kHz stereo, with ID3v2.4 tags and embedded cover art:
   ```
   ffmpeg -hide_banner -i "<in>" -i "<cover>" \
     -map 0:a -map 1 -c:a libmp3lame -b:a 192k -ar 44100 -ac 2 \
     -id3v2_version 3 \
     -metadata title="<title>" \
     -metadata artist="<show>" \
     -metadata album="<show>" \
     -metadata track="<number>" \
     -metadata date="<year>" \
     -metadata genre="Podcast" \
     -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" \
     "finished/ep<NNN>-<slug>.mp3"
   ```
3. Verify the output with `ffprobe` — confirm tags and cover art attached.
4. Report final file path, size, duration, and bitrate.
