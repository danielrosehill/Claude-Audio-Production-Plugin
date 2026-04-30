---
description: Strip all metadata (tags, comments, cover art, encoder history) from an audio file for privacy or a clean slate
argument-hint: <audio-file> [--keep-cover-art] [--keep basic|none] [--in-place]
---

Remove metadata from `$1`. Writes `<name>_scrubbed.<ext>` unless `--in-place`.

## Steps

1. `ffprobe` the input — show what will be removed (tag count, cover art presence, encoder info).
2. Build ffmpeg command:
   - Full scrub (default):
     ```
     ffmpeg -i "$INPUT" -map_metadata -1 -map 0:a -c:a copy \
       -fflags +bitexact -flags:a +bitexact "$OUTPUT"
     ```
   - `--keep basic`: preserve `title`, `artist`, `album` only:
     ```
     ffmpeg -i "$INPUT" -map_metadata -1 -map 0:a -c:a copy \
       -metadata title="<from input>" -metadata artist="<...>" -metadata album="<...>" \
       "$OUTPUT"
     ```
   - `--keep-cover-art`: include `-map 0:v -c:v copy -disposition:v attached_pic` to preserve embedded art.
3. Also strip:
   - ID3v1 + ID3v2 trailing tags (`-write_id3v1 0 -id3v2_version 0` where applicable)
   - iTunes-specific atoms on M4A
   - Vorbis comments on Opus/FLAC
4. Verify by re-probing — confirm tag count dropped to 0 (or just the whitelisted fields).
5. Report what was removed and the output size delta.

Use before uploading anywhere public — audio files can leak recording device, DAW, user name, and embedded GPS (rare but happens on phone recordings).
