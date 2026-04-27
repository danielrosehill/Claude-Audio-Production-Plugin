---
name: ccr-import
description: Use when Daniel wants to import call recordings from Cube Call Recorder (CCR) on his Android phone via ADB. Triggers on phrases like "import from cube", "grab the CCR recording", "pull yesterday's call from my phone", "import call recorder file", or any request to fetch an audio file produced by Cube Call Recorder from a connected Android device.
---

# CCR Import — Cube Call Recorder → Local Filesystem

Cube Call Recorder ACR (`com.catalinagroup.callrecorder`) is Daniel's default Android call recorder. Both regular phone calls and VoIP/WhatsApp calls are captured.

## Save path

```
/sdcard/Calls/CCR/CubeCallRecorder/All/
```

**Important:** Do not confuse with `/sdcard/Recordings/Calls/`, which is the Android system call recorder and contains a different filename format (`YYYYMMDD_HHMMSS.SS+TZ_{IN|OUT}_simN_+PHONENUMBER.oga`). CCR's own recordings are under `/sdcard/Calls/CCR/CubeCallRecorder/All/`.

To confirm path at any time:
```bash
adb shell 'find /sdcard/Calls -maxdepth 5 -type d' | tr -d '\r'
```

## Filename format

```
{source}_{YYYYMMDD}-{HHMMSS}_{contact}.amr
```

Examples:
```
mic_20260327-052816.amr
whatsapp_20260421-221612_Claire Rosehill.amr
```

Fields:

| Field | Example | Meaning |
|---|---|---|
| Source | `mic` / `whatsapp` / `voip` | Capture channel. `mic` = phone microphone (regular call or fallback). `whatsapp` = WhatsApp accessibility-stream capture (VoIP). Other VoIP apps may show as their own prefix. |
| Date | `20260421` | Local date, `YYYYMMDD` |
| Time | `221612` | Local start time, `HHMMSS` |
| Contact | `Claire Rosehill` | CCR's resolved contact name (may contain spaces). Absent for unknown/unresolved numbers. |

File extension is **`.amr`** (Adaptive Multi-Rate, narrow-band). ffmpeg, AssemblyAI, and Whisper all handle it directly. Bit rate is low (~12 kbps) — fine for speech transcription, marginal for music or tonal analysis.

## `mic_` vs `whatsapp_` (or other VoIP) for the same time window

When CCR has both capture modes active for a VoIP call, you may see **overlapping `mic_` and `whatsapp_` files for the same interval**. Prefer the `whatsapp_` (or app-specific) file for transcription — it captures the VoIP stream via accessibility service, bypassing speaker-to-mic loss and ambient noise. `mic_` is useful as fallback if the app-stream capture is corrupted or missing.

**Never transcribe both streams concatenated — they're the same audio captured twice, and concatenating produces a garbled transcript.**

## Standard import workflow

### 1. Confirm device is connected

```bash
adb devices
```

### 2. List recent recordings

```bash
# All, newest last (alphabetic sort happens to be chronological thanks to the filename format)
adb shell 'ls "/sdcard/Calls/CCR/CubeCallRecorder/All/"' | tr -d '\r' | tail -30

# By date
adb shell 'ls "/sdcard/Calls/CCR/CubeCallRecorder/All/" | grep 20260421' | tr -d '\r'

# By contact
adb shell 'ls "/sdcard/Calls/CCR/CubeCallRecorder/All/" | grep "Claire Rosehill"' | tr -d '\r'
```

### 3. Pull files

`adb pull` doesn't accept globs — loop over filenames. Quote paths, since CCR filenames contain spaces.

```bash
DEST=recordings/inbox
while IFS= read -r f; do
  adb pull "/sdcard/Calls/CCR/CubeCallRecorder/All/$f" "$DEST/" 2>&1 | tail -1
done < <(adb shell 'ls "/sdcard/Calls/CCR/CubeCallRecorder/All/" | grep 20260421' | tr -d '\r')
```

### 4. Concatenate fragmented sessions

CCR often splits a single conversation into multiple files (call drops, reconnections, mode switches). To stitch back into one file for transcription:

```bash
cd recordings/inbox
ls whatsapp_20260421-*_Claire\ Rosehill.amr | sort > /tmp/concat_list.txt
# ffmpeg concat demuxer needs a file listing with `file '...'` per line
awk '{ printf "file %s\n", "\x27"$0"\x27" }' /tmp/concat_list.txt > /tmp/concat.ffmpeg
ffmpeg -y -f concat -safe 0 -i /tmp/concat.ffmpeg -c copy 2026-04-21-ac-concatenated.amr
```

For cross-codec safety (if files have differing codec params), re-encode rather than stream-copy:

```bash
ffmpeg -y -f concat -safe 0 -i /tmp/concat.ffmpeg -c:a libopus -b:a 24k 2026-04-21-ac-concatenated.opus
```

## Common pitfalls

- **Path confusion.** `/sdcard/Recordings/Calls/` (system recorder, `.oga`) is NOT the CCR path. CCR lives at `/sdcard/Calls/CCR/CubeCallRecorder/All/` (`.amr`).
- **Spaces in filenames.** Contact names contain spaces. Always quote. `ls` output with `tr -d '\r'` and a `while read -r` loop is safer than `for f in $(...)`.
- **Double-capture overlap.** `mic_` + `{app}_` files from the same time window are the same audio. Don't concatenate across sources.
- **Low bit-rate.** AMR is narrow-band (8 kHz sample rate). Don't expect waveform or speaker-embedding quality comparable to WAV/Opus. For voice ID via resemblyzer, you can still extract embeddings but accuracy drops vs. clean samples.
- **Daily rollovers.** CCR's "All" folder is flat and can accumulate thousands of files. Prefer targeted `grep` by date or contact over `ls` full-listing.

## Related

- `adb-ops:pull-folder` — generic pull utility
- `~/repos/github/my-repos/Maternal-Conversation-Analysis/.claude/commands/import-from-phone.md` — workspace-specific CCR import
