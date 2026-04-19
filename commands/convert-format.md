---
description: Convert audio between formats (WAV / FLAC / MP3 / Opus / AAC) with explicit bitrate and sample-rate control
---

Convert an audio file to another format.

Inputs (from `$ARGUMENTS` or ask):
- `--in <file>` (required)
- `--format <wav|flac|mp3|opus|aac>` (required)
- `--bitrate <e.g. 192k>` (optional; format-dependent default)
- `--sample-rate <e.g. 48000>` (optional; preserve source if omitted)
- `--channels <1|2>` (optional; preserve source if omitted)
- `--out <file>` (optional; defaults to `<in-basename>.<format>`)

Codec defaults:
- `wav` → `pcm_s24le`
- `flac` → `flac` (lossless)
- `mp3` → `libmp3lame`, 192k CBR
- `opus` → `libopus`, 96k VBR
- `aac` → `aac`, 192k

Before running, show the user what the command will be and confirm. Do not overwrite an existing output without asking.

Report input vs output format, bitrate, sample rate, channels, duration, and file size.
