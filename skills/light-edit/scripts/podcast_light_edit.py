"""Light edit chain for spoken-word recordings.

Stages, in order:
  1. decode    ffmpeg -> 48 kHz mono float working copy
  2. fillers   Uhm (desert-ant-labs/uhm, ONNX) frame classifier -> cut uh/um/hmm spans
  3. silences  energy gate on the de-filled audio -> shorten pauses longer than --max-silence
  4. eq        voice-fitted EQ: flatten octave-band bumps/dips relative to the speaker's own
               spectral trend (capped), plus fixed high-pass, gentle compression, de-ess
  5. loudness  two-pass ffmpeg loudnorm -> MP3

Every cut is written to <out>.edits.json so the edit can be audited or replayed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
UHM_SR = 16000
UHM_WINDOW = 30 * UHM_SR  # model input is fixed at 480000 samples
UHM_HOP_S = 20.0  # 10 s overlap between windows; each frame is taken from its most central window
UHM_FRAME_S = 0.02
UHM_LABELS = {"not_filler": 0, "uh": 1, "um": 2, "hmm": 3, "and": 4, "other": 5}
OCTAVE_BANDS = [125, 250, 500, 1000, 2000, 4000, 8000]


@dataclass
class Cut:
    start: float  # seconds, in the timeline of the stage's input
    end: float
    kind: str  # "filler" or "silence"
    detail: str


# ---------------------------------------------------------------- io


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def decode(path: Path, sr: int) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        check=True,
        capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr_in), "-ac", "1", "-i", "-",
         "-ar", str(sr_out), "-f", "f32le", "-"],
        input=x.astype(np.float32).tobytes(),
        check=True,
        capture_output=True,
    ).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


# ---------------------------------------------------------------- cutting


def splice(x: np.ndarray, cuts: list[Cut], sr: int, xfade_s: float = 0.01) -> np.ndarray:
    """Remove the cut spans, joining the kept pieces with short equal-power crossfades."""
    keep, pos = [], 0
    for c in sorted(cuts, key=lambda c: c.start):
        s, e = int(c.start * sr), int(c.end * sr)
        if s > pos:
            keep.append((pos, s))
        pos = max(pos, e)
    if pos < len(x):
        keep.append((pos, len(x)))

    n = int(xfade_s * sr)
    fade_in = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    fade_out = 1 - fade_in
    out: list[np.ndarray] = []
    for s, e in keep:
        piece = x[s:e].copy()
        if out and len(piece) > n and len(out[-1]) > n:
            tail = out[-1][-n:] * fade_out + piece[:n] * fade_in
            out[-1] = np.concatenate([out[-1][:-n], tail])
            piece = piece[n:]
        out.append(piece)
    return np.concatenate(out) if out else x[:0]


def merge_spans(mask: np.ndarray, frame_s: float, max_gap_s: float, min_len_s: float) -> list[tuple[int, int]]:
    """Boolean frame mask -> (start_frame, end_frame) runs, bridging short gaps, dropping short runs."""
    spans, start = [], None
    for i, v in enumerate(np.append(mask, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            spans.append([start, i])
            start = None
    merged: list[list[int]] = []
    for s, e in spans:
        if merged and (s - merged[-1][1]) * frame_s <= max_gap_s:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged if (e - s) * frame_s >= min_len_s]


# ---------------------------------------------------------------- stage 2: fillers


def filler_probs(x16: np.ndarray, model: str) -> np.ndarray:
    """Per-20ms-frame class probabilities over the whole file, shape (frames, 6)."""
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download

    sess = ort.InferenceSession(hf_hub_download("desert-ant-labs/uhm", model), providers=["CPUExecutionProvider"])
    in_name = sess.get_inputs()[0].name
    total = int(np.ceil(len(x16) / UHM_SR / UHM_FRAME_S))
    probs = np.zeros((total, 6), dtype=np.float32)
    best_dist = np.full(total, np.inf)
    hop = int(UHM_HOP_S * UHM_SR)
    for off in range(0, max(1, len(x16) - UHM_WINDOW + hop), hop):
        chunk = x16[off:off + UHM_WINDOW]
        valid = len(chunk)
        chunk = np.pad(chunk, (0, UHM_WINDOW - valid))[None, :].astype(np.float32)
        p = sess.run(None, {in_name: chunk})[0][0]  # (1499, 6)
        n_valid = min(len(p), int(valid / UHM_SR / UHM_FRAME_S))
        first = int(round(off / UHM_SR / UHM_FRAME_S))
        centre = n_valid / 2
        for j in range(n_valid):
            g = first + j
            if g >= total:
                break
            d = abs(j - centre)
            if d < best_dist[g]:
                best_dist[g] = d
                probs[g] = p[j]
    return probs


def detect_fillers(x: np.ndarray, args) -> tuple[list[Cut], np.ndarray]:
    if args.probs and args.probs.exists():
        probs = np.load(args.probs)
    else:
        probs = filler_probs(resample(x, SR, UHM_SR), args.model)
        if args.probs:
            np.save(args.probs, probs)
    classes = [UHM_LABELS[c] for c in args.fillers]
    score = probs[:, classes].sum(axis=1)
    cuts = []
    for s, e in merge_spans(score >= args.filler_threshold, UHM_FRAME_S, max_gap_s=0.06, min_len_s=args.min_filler):
        seg = probs[s:e]
        label = max(args.fillers, key=lambda c: seg[:, UHM_LABELS[c]].mean())
        conf = float(score[s:e].mean())
        start = max(0.0, s * UHM_FRAME_S - args.filler_pad)
        end = min(len(x) / SR, e * UHM_FRAME_S + args.filler_pad)
        cuts.append(Cut(round(start, 3), round(end, 3), "filler", f"{label} p={conf:.2f}"))
    return cuts, score


# ---------------------------------------------------------------- stage 3: silences


def frame_db(x: np.ndarray, frame_s: float = 0.02, hop_s: float = 0.01) -> np.ndarray:
    f, h = int(frame_s * SR), int(hop_s * SR)
    n = max(1, 1 + (len(x) - f) // h)
    idx = np.arange(f)[None, :] + h * np.arange(n)[:, None]
    rms = np.sqrt(np.mean(x[idx] ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms)


def detect_silences(x: np.ndarray, args) -> tuple[list[Cut], float]:
    hop_s = 0.01
    db = frame_db(x, hop_s=hop_s)
    if args.silence_db is not None:
        thr = args.silence_db
    else:
        floor, speech = np.percentile(db, 10), np.percentile(db, 90)
        thr = float(min(floor + 10, speech - 20))  # adaptive: 10 dB over the room floor
    cuts = []
    for s, e in merge_spans(db < thr, hop_s, max_gap_s=0.05, min_len_s=args.max_silence):
        t0, t1 = s * hop_s, e * hop_s
        half = args.keep_silence / 2
        cuts.append(Cut(round(t0 + half, 3), round(t1 - half, 3), "silence", f"{t1 - t0:.2f}s -> {args.keep_silence:.2f}s"))
    return cuts, thr


# ---------------------------------------------------------------- stage 4: voice-fitted EQ


def voice_profile(x: np.ndarray, speech_thr_db: float) -> dict:
    """Octave-band long-term spectrum of speech frames, and each band's deviation from a
    straight-line (log-frequency) fit of the same spectrum. Bumps/dips relative to the speaker's
    own trend are mostly mic/room colouration; the trend itself is the voice, and is left alone."""
    n_fft, hop = 4096, 2048
    win = np.hanning(n_fft)
    frames = np.lib.stride_tricks.sliding_window_view(x, n_fft)[::hop]
    rms_db = 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-12)
    speech = frames[rms_db > speech_thr_db + 6]
    power = (np.abs(np.fft.rfft(speech * win, axis=1)) ** 2).mean(axis=0)
    freqs = np.fft.rfftfreq(n_fft, 1 / SR)
    levels = []
    for fc in OCTAVE_BANDS:
        band = (freqs >= fc / np.sqrt(2)) & (freqs < fc * np.sqrt(2))
        levels.append(10 * np.log10(power[band].sum() + 1e-20))
    levels = np.array(levels)
    logf = np.log2(OCTAVE_BANDS)
    slope, icpt = np.polyfit(logf, levels, 1)
    dev = levels - (slope * logf + icpt)
    return {
        "bands_hz": OCTAVE_BANDS,
        "level_db": [round(float(v), 2) for v in levels - levels.max()],
        "trend_db_per_octave": round(float(slope), 2),
        "deviation_db": [round(float(v), 2) for v in dev],
        "speech_frames": int(len(speech)),
    }


def eq_from_profile(profile: dict, strength: float, max_gain: float, deadband: float) -> list[dict]:
    bands = []
    for fc, dev in zip(profile["bands_hz"], profile["deviation_db"]):
        if fc < 250 or abs(dev) < deadband:  # below 250 Hz the high-pass and the voice's own body dominate
            continue
        gain = float(np.clip(-dev * strength, -max_gain, max_gain))
        bands.append({"f": fc, "width_octaves": 1.0, "gain_db": round(gain, 1)})
    return bands


def build_filter(preset: dict) -> str:
    parts = [f"highpass=f={preset['highpass_hz']}:poles=2"]
    for b in preset["eq"]:
        parts.append(f"equalizer=f={b['f']}:t=o:w={b['width_octaves']}:g={b['gain_db']}")
    c = preset["compressor"]
    parts.append(
        f"acompressor=threshold={c['threshold_db']}dB:ratio={c['ratio']}:attack={c['attack_ms']}"
        f":release={c['release_ms']}:makeup={c['makeup_db']}dB"
    )
    if preset.get("deess", 0) > 0:
        parts.append(f"deesser=i={preset['deess']}:m=0.5:f=0.5:s=o")
    return ",".join(parts)


DEFAULT_DYNAMICS = {
    "highpass_hz": 80,
    "compressor": {"threshold_db": -20, "ratio": 2.5, "attack_ms": 15, "release_ms": 200, "makeup_db": 2},
    "deess": 0.3,
}


# ---------------------------------------------------------------- stage 5: loudness + export


def loudnorm_export(src: Path, dst: Path, chain: str, lufs: float, tp: float, bitrate: str) -> dict:
    ln = f"loudnorm=I={lufs}:TP={tp}:LRA=11"
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", f"{chain},{ln}:print_format=json", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    )
    m = json.loads(p.stderr[p.stderr.rindex("{"):p.stderr.rindex("}") + 1])
    second = (f"{ln}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", f"{chain},{second}",
         "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", bitrate, str(dst)])
    return m


def measure_lufs(path: Path) -> float:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    line = [l for l in p.stderr.splitlines() if l.strip().startswith("I:")][-1]
    return float(line.split()[1])


# ---------------------------------------------------------------- cli


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="default: <input-stem>.edited.mp3 next to the input")
    ap.add_argument("--fillers", default="uh,um,hmm", help="Uhm classes to cut (uh,um,hmm,and,other)")
    ap.add_argument("--filler-threshold", type=float, default=0.6, help="min summed class prob per frame")
    ap.add_argument("--min-filler", type=float, default=0.12, help="ignore filler spans shorter than this (s)")
    ap.add_argument("--filler-pad", type=float, default=0.0, help="extra audio cut either side of a filler (s)")
    ap.add_argument("--max-silence", type=float, default=0.8, help="pauses longer than this get shortened (s)")
    ap.add_argument("--keep-silence", type=float, default=0.5, help="what a long pause is shortened to (s)")
    ap.add_argument("--silence-db", type=float, help="fixed silence gate in dBFS (default: adaptive)")
    ap.add_argument("--preset", type=Path, help="EQ/dynamics preset JSON (default: fit one to this recording)")
    ap.add_argument("--save-preset", type=Path, help="write the fitted preset here for reuse")
    ap.add_argument("--eq-strength", type=float, default=0.6, help="fraction of each band deviation corrected")
    ap.add_argument("--eq-max", type=float, default=3.0, help="max boost/cut per band (dB)")
    ap.add_argument("--lufs", type=float, default=-16.0)
    ap.add_argument("--true-peak", type=float, default=-1.5)
    ap.add_argument("--bitrate", default="128k")
    ap.add_argument("--no-fillers", action="store_true")
    ap.add_argument("--no-silence", action="store_true")
    ap.add_argument("--no-eq", action="store_true")
    ap.add_argument("--model", default="uhm-web-fp16.onnx", help="Uhm ONNX file (uhm.onnx for fp32)")
    ap.add_argument("--probs", type=Path, help="cache of Uhm frame probabilities (.npy): read if present, else written")
    ap.add_argument("--dry-run", action="store_true", help="detect and write the edit list, render nothing")
    args = ap.parse_args(argv)
    args.fillers = [f.strip() for f in args.fillers.split(",") if f.strip()]

    out = args.out or args.input.with_name(f"{args.input.stem}.edited.mp3")
    if out.resolve() == args.input.resolve():
        sys.exit("refusing to overwrite the input")

    x = decode(args.input, SR)
    src_dur = len(x) / SR
    report: dict = {"input": str(args.input), "output": str(out), "source_seconds": round(src_dur, 2)}

    filler_cuts: list[Cut] = []
    if not args.no_fillers:
        filler_cuts, _ = detect_fillers(x, args)
        x = splice(x, filler_cuts, SR)
    report["filler_cuts"] = [asdict(c) for c in filler_cuts]
    print(f"fillers: {len(filler_cuts)} cut, {sum(c.end - c.start for c in filler_cuts):.1f}s", file=sys.stderr)

    silence_cuts: list[Cut] = []
    thr = None
    if not args.no_silence:
        silence_cuts, thr = detect_silences(x, args)
        x = splice(x, silence_cuts, SR)
    report["silence_gate_dbfs"] = None if thr is None else round(thr, 1)
    report["silence_cuts_note"] = "timestamps are in the de-filled timeline (after filler cuts)"
    report["silence_cuts"] = [asdict(c) for c in silence_cuts]
    print(f"silences: {len(silence_cuts)} shortened, {sum(c.end - c.start for c in silence_cuts):.1f}s removed", file=sys.stderr)

    if args.preset:
        preset = json.loads(args.preset.read_text())
    else:
        gate = thr if thr is not None else float(np.percentile(frame_db(x), 10) + 10)
        profile = voice_profile(x, gate)
        preset = {**DEFAULT_DYNAMICS, "eq": eq_from_profile(profile, args.eq_strength, args.eq_max, 1.0),
                  "profile": profile, "fitted_from": args.input.name}
    if args.save_preset:
        args.save_preset.write_text(json.dumps(preset, indent=2) + "\n")
    report["preset"] = preset

    chain = "anull" if args.no_eq else build_filter(preset)
    report["filter_chain"] = chain
    report["edited_seconds"] = round(len(x) / SR, 2)

    if not args.dry_run:
        with tempfile.TemporaryDirectory() as td:
            mid = Path(td) / "edited.wav"
            sf.write(mid, x, SR, subtype="FLOAT")
            m = loudnorm_export(mid, out, chain, args.lufs, args.true_peak, args.bitrate)
        report["loudness"] = {"pre_norm_lufs": float(m["input_i"]), "output_lufs": measure_lufs(out)}
        print(f"wrote {out} ({src_dur / 60:.1f} -> {len(x) / SR / 60:.1f} min)", file=sys.stderr)

    edits = out.with_name(out.name + ".edits.json")
    edits.write_text(json.dumps(report, indent=2) + "\n")
    print(f"edit list: {edits}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
