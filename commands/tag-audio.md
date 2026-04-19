---
description: View or set audio metadata tags (ID3 / Vorbis / FLAC) and embed cover art
---

View or modify audio file metadata.

Modes (via `$ARGUMENTS`):

- `--show <file>` — dump current tags via `ffprobe -show_format -show_streams -print_format json <file>`. Present in a readable table.
- `--set <file> --title "..." --artist "..." --album "..." --track "..." --date "..." --genre "..."` — write tags via ffmpeg with `-c:a copy`.
- `--cover <file> --image <jpg|png>` — embed cover art without re-encoding audio (see below).

For `--set`, always show the user the current tags first and ask for confirmation before writing.

For batch tag edits across a folder, dry-run and report all changes before applying.

**Embed cover art without re-encoding audio** (works for MP3):
```
ffmpeg -hide_banner -i "<audio>" -i "<image>" \
  -map 0:a -map 1 -c:a copy -c:v mjpeg \
  -id3v2_version 3 \
  -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" \
  "<out>"
```

For FLAC/Vorbis, use `metaflac --import-picture-from="<image>"`.

Verify results with `ffprobe` afterwards.
