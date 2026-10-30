"""Score the filler cuts in an .edits.json against AssemblyAI's disfluency-tagged words.

AssemblyAI with `disfluencies: true` returns "um", "uh", "hmm" etc. as words with ms timestamps.
Those are the reference; a reference filler counts as caught if any filler cut overlaps it, and a
cut counts as correct if it overlaps a reference filler. A cut that overlaps a non-filler word is
reported as a possible overcut (it may have clipped the word's edge or removed a real word).

  with-secrets uv run python -I scripts/eval_fillers.py <original-audio> <out.mp3.edits.json> [--transcript t.json]

The audio is uploaded to AssemblyAI. Pass --transcript to reuse a saved response.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FILLERS = {"um", "uh", "hmm", "mm", "er", "ah", "uhm", "umm", "mhm"}
API = "https://api.assemblyai.com/v2"


def call(path, data=None, raw=False):
    req = urllib.request.Request(API + path, data=data, headers={"authorization": os.environ["ASSEMBLYAI_API_KEY"]})
    if data is not None and not raw:
        req.add_header("content-type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def transcribe(audio: Path) -> dict:
    url = call("/upload", audio.read_bytes(), raw=True)["upload_url"]
    body = json.dumps({"audio_url": url, "speech_model": "universal", "language_code": "en", "disfluencies": True}).encode()
    tid = call("/transcript", body)["id"]
    while True:
        t = call(f"/transcript/{tid}")
        if t["status"] in ("completed", "error"):
            if t["status"] == "error":
                sys.exit(t["error"])
            return t
        time.sleep(5)


def overlaps(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0) > 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", type=Path)
    ap.add_argument("edits", type=Path)
    ap.add_argument("--transcript", type=Path, help="saved AssemblyAI response (written here if missing)")
    a = ap.parse_args()

    if a.transcript and a.transcript.exists():
        t = json.loads(a.transcript.read_text())
    else:
        t = transcribe(a.audio)
        if a.transcript:
            a.transcript.write_text(json.dumps(t))

    words = [(w["start"] / 1000, w["end"] / 1000, w["text"].lower().strip(".,?!-")) for w in t["words"]]
    ref = [w for w in words if w[2] in FILLERS]
    other = [w for w in words if w[2] not in FILLERS]
    cuts = [(c["start"], c["end"]) for c in json.loads(a.edits.read_text())["filler_cuts"]]

    caught = [r for r in ref if any(overlaps(r[0], r[1], c0, c1) for c0, c1 in cuts)]
    correct = [c for c in cuts if any(overlaps(c[0], c[1], r[0], r[1]) for r in ref)]
    overcut = []
    for c0, c1 in cuts:
        hit = [w for w in other if overlaps(c0, c1, w[0], w[1])]
        # a word counts as clipped only if the cut takes >= 80 ms and >= 30% of it; smaller contact
        # is AssemblyAI word-boundary jitter, not a removed word
        hit = [w for w in hit if min(c1, w[1]) - max(c0, w[0]) >= max(0.08, 0.3 * (w[1] - w[0]))]
        if hit:
            overcut.append({"cut": [c0, c1], "words": [f"{w[2]}@{w[0]:.2f}" for w in hit]})

    missed = [r for r in ref if r not in caught]
    print(json.dumps({
        "reference_fillers": len(ref),
        "cuts": len(cuts),
        "recall": round(len(caught) / max(1, len(ref)), 3),
        "precision": round(len(correct) / max(1, len(cuts)), 3),
        "cuts_touching_real_words": len(overcut),
        "overcut_examples": overcut[:15],
        "missed_examples": [f"{m[2]}@{m[0]:.2f}" for m in missed[:20]],
    }, indent=2))


if __name__ == "__main__":
    main()
