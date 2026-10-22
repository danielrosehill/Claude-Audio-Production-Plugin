#!/usr/bin/env python3
"""Build one listening file that announces each version before playing it.

    uv run --with numpy --with scipy --with soundfile labelled_ab.py OUT.flac \
        "Original=raw.flac" "Denoised=clean.flac" [--repeat 2] [--gap 0.8]

Each LABEL=PATH pair becomes: spoken label, short pause, the clip, gap. The whole sequence is
repeated --repeat times. Spoken labels are cached as 48 kHz mono WAVs in the generate-cues folder
(<data-dir>/tts/<slug>.wav) and rendered once with edge-tts, falling back to espeak-ng. Only the
label text leaves the machine (edge-tts calls Microsoft's TTS endpoint). The clips are never
modified: output takes the first clip's sample rate, cues are resampled and levelled to the
clips' speech level, and nothing is loudness-matched unless --match-loudness is passed.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

DATA = Path(os.environ.get("CLAUDE_USER_DATA") or os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / (
    "audio-production" if os.environ.get("CLAUDE_USER_DATA") else "claude-plugins/audio-production")
CUE_SR = 48000


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def render_cue(text, cue_dir, voice):
    path = cue_dir / f"{slug(text)}.wav"
    if path.exists():
        return path
    cue_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "cue"
        if shutil.which("edge-tts"):
            r = subprocess.run(["edge-tts", "--voice", voice, "--text", text, "--write-media", f"{raw}.mp3"],
                               capture_output=True, text=True)
            src = f"{raw}.mp3" if r.returncode == 0 else None
        else:
            src = None
        if src is None:
            if not shutil.which("espeak-ng"):
                sys.exit("No TTS engine: install edge-tts (uv tool install edge-tts) or espeak-ng.")
            subprocess.run(["espeak-ng", "-v", "en+m3", "-s", "150", "-w", f"{raw}.wav", text], check=True)
            src = f"{raw}.wav"
        # Same padding as generate-cues: 200 ms lead, 400 ms tail.
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", str(CUE_SR),
                        "-af", "adelay=200|200,apad=pad_dur=0.4", "-c:a", "pcm_s16le", str(path)], check=True)
    return path


def mono(x):
    return x if x.ndim == 1 else x.mean(axis=1)


def to_rate(x, sr, target):
    if sr == target:
        return x
    g = gcd(sr, target)
    return resample_poly(x, target // g, sr // g)


def speech_rms(x, sr):
    """RMS of the loudest 30% of 50 ms frames: the level of the voice, ignoring pauses."""
    f = max(1, int(0.05 * sr))
    fr = x[: len(x) // f * f].reshape(-1, f)
    e = np.sqrt((fr ** 2).mean(axis=1))
    return float(np.sqrt((np.sort(e)[-max(1, len(e) * 3 // 10):] ** 2).mean())) or 1e-9


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("pairs", nargs="+", help='"Label=path/to/clip" in play order')
    ap.add_argument("--repeat", type=int, default=2, help="times to play the whole sequence (default 2)")
    ap.add_argument("--gap", type=float, default=0.8, help="seconds of silence after each clip")
    ap.add_argument("--voice", default="en-US-AndrewNeural")
    ap.add_argument("--cue-dir", type=Path, default=DATA / "tts")
    ap.add_argument("--match-loudness", action="store_true",
                    help="scale every clip to the first clip's speech level (compare tone, not level)")
    a = ap.parse_args()

    clips = []
    for p in a.pairs:
        label, _, path = p.partition("=")
        if not path:
            sys.exit(f"Expected Label=path, got {p!r}")
        x, sr = sf.read(path, dtype="float64", always_2d=False)
        clips.append((label.strip(), mono(x), sr, path))
    out_sr = clips[0][2]
    clips = [(l, to_rate(x, sr, out_sr), p) for l, x, sr, p in clips]
    ref = speech_rms(clips[0][1], out_sr)
    if a.match_loudness:
        clips = [(l, x * ref / speech_rms(x, out_sr), p) for l, x, p in clips]

    gap = np.zeros(int(a.gap * out_sr))
    parts, timeline, t = [], [], 0.0
    for rnd in range(a.repeat):
        for label, x, path in clips:
            cue, csr = sf.read(render_cue(label, a.cue_dir, a.voice), dtype="float64")
            cue = to_rate(mono(cue), csr, out_sr)
            cue *= 0.7 * ref / speech_rms(cue, out_sr)  # a little under the voice
            for seg, what in ((cue, f"cue '{label}'"), (x, f"{label}: {path}"), (gap, None)):
                if what:
                    timeline.append(f"{t:7.2f}s  {what}")
                parts.append(seg)
                t += len(seg) / out_sr
    y = np.concatenate(parts)
    peak = np.abs(y).max()
    if peak > 0.99:  # only possible via --match-loudness or a hot cue; scale the whole file, never clip
        y *= 0.99 / peak
    sub = "PCM_24" if a.out.lower().endswith((".flac", ".wav")) else None
    sf.write(a.out, y, out_sr, subtype=sub)
    print(f"wrote {a.out}  ({t:.1f} s, {out_sr} Hz, {a.repeat}x)")
    print("\n".join(timeline))


if __name__ == "__main__":
    main()
