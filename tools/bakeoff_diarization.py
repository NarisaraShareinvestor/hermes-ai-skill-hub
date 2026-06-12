#!/usr/bin/env python3
"""
Speaker-diarization bake-off — Gladia vs Deepgram vs Speechmatics.

Sends ONE audio clip through whichever providers have an API key set, with
speaker diarization + timestamps, and writes each result as a readable
  [MM:SS] Speaker N: text
transcript so you can judge Thai⇄English code-switching + speaker accuracy.

WHY a bake-off: which engine wins on *Thai business-meeting code-switching*
can't be read off benchmark blogs — it has to be measured on your real audio.

USAGE
-----
1. Get free-tier API keys (no/low cost, all have free credit):
     Deepgram      https://console.deepgram.com/signup     ($200 free credit)
     Gladia        https://app.gladia.io/                    (free hours/month)
     Speechmatics  https://portal.speechmatics.com/sign-up   (free trial hours)

2. Put the keys in an env file (NEVER paste keys into chat). Create
   tools/bakeoff.env  (already gitignored via *.env):
     DEEPGRAM_API_KEY=...
     GLADIA_API_KEY=...
     SPEECHMATICS_API_KEY=...

3. Run with a 10–15 min sample that has ≥2 speakers + real English terms:
     set -a; source tools/bakeoff.env; set +a
     python3 tools/bakeoff_diarization.py /path/to/sample.m4a

4. Read bakeoff_<provider>.txt and paste them back for a side-by-side verdict.

Only `requests` is required (already in the project venv).
"""
import os
import sys
import time
import json
import requests


def ts(seconds: float) -> str:
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def render(segments: list) -> str:
    """segments: list of {speaker, start, text} → readable transcript,
    collapsing consecutive turns by the same speaker."""
    lines, cur_spk, buf, cur_start = [], None, [], 0.0
    for seg in segments:
        spk = str(seg.get("speaker", "?"))
        if spk != cur_spk:
            if buf:
                lines.append(f"[{ts(cur_start)}] Speaker {cur_spk}: {' '.join(buf).strip()}")
            cur_spk, buf, cur_start = spk, [], seg.get("start", 0.0)
        buf.append((seg.get("text") or "").strip())
    if buf:
        lines.append(f"[{ts(cur_start)}] Speaker {cur_spk}: {' '.join(buf).strip()}")
    return "\n".join(lines)


def save(provider: str, segments: list, elapsed: float, raw_note: str = ""):
    out = f"bakeoff_{provider}.txt"
    body = render(segments)
    n_spk = len({str(s.get("speaker")) for s in segments})
    header = (f"=== {provider.upper()} ===\n"
              f"segments: {len(segments)} | speakers detected: {n_spk} | "
              f"processing time: {elapsed:.1f}s {raw_note}\n" + "-" * 60 + "\n")
    with open(out, "w", encoding="utf-8") as f:
        f.write(header + body + "\n")
    print(f"  ✔ wrote {out}  ({len(segments)} segments, {n_spk} speakers, {elapsed:.1f}s)")


# ── Deepgram (Nova-3, prerecorded) ────────────────────────────────────────────
def run_deepgram(path: str, key: str):
    print("[deepgram] uploading + transcribing (nova-3, diarize, multi-lang)...")
    t0 = time.time()
    with open(path, "rb") as f:
        data = f.read()
    # language=multi → code-switching mode (Thai+English); diarize + utterances
    params = {
        "model": "nova-3", "diarize": "true", "punctuate": "true",
        "utterances": "true", "smart_format": "true", "language": "multi",
    }
    r = requests.post(
        "https://api.deepgram.com/v1/listen",
        params=params,
        headers={"Authorization": f"Token {key}", "Content-Type": "application/octet-stream"},
        data=data, timeout=600,
    )
    if r.status_code != 200:
        # retry once with explicit Thai if multi is rejected for this account/model
        params["language"] = "th"
        r = requests.post(
            "https://api.deepgram.com/v1/listen", params=params,
            headers={"Authorization": f"Token {key}", "Content-Type": "application/octet-stream"},
            data=data, timeout=600,
        )
    r.raise_for_status()
    js = r.json()
    utts = js.get("results", {}).get("utterances", [])
    segments = [{"speaker": u.get("speaker", 0), "start": u.get("start", 0.0),
                 "text": u.get("transcript", "")} for u in utts]
    save("deepgram", segments, time.time() - t0, f"(lang={params['language']})")


# ── Gladia (v2, Whisper + pyannote, async) ────────────────────────────────────
def run_gladia(path: str, key: str):
    print("[gladia] uploading...")
    t0 = time.time()
    hdr = {"x-gladia-key": key}
    with open(path, "rb") as f:
        up = requests.post("https://api.gladia.io/v2/upload", headers=hdr,
                           files={"audio": (os.path.basename(path), f)}, timeout=600)
    up.raise_for_status()
    audio_url = up.json()["audio_url"]
    print("[gladia] starting transcription (diarization on)...")
    start = requests.post(
        "https://api.gladia.io/v2/pre-recorded", headers={**hdr, "Content-Type": "application/json"},
        json={"audio_url": audio_url, "diarization": True}, timeout=60,
    )
    start.raise_for_status()
    result_url = start.json()["result_url"]
    for _ in range(600):
        time.sleep(3)
        g = requests.get(result_url, headers=hdr, timeout=60).json()
        st = g.get("status")
        if st == "done":
            utts = g.get("result", {}).get("transcription", {}).get("utterances", [])
            segments = [{"speaker": u.get("speaker", 0), "start": u.get("start", 0.0),
                         "text": u.get("text", "")} for u in utts]
            save("gladia", segments, time.time() - t0)
            return
        if st == "error":
            print(f"  ✗ gladia error: {json.dumps(g)[:300]}")
            return
    print("  ✗ gladia timed out")


# ── Speechmatics (v2 batch, async) ────────────────────────────────────────────
def run_speechmatics(path: str, key: str):
    print("[speechmatics] submitting job (th, diarization=speaker, enhanced)...")
    t0 = time.time()
    hdr = {"Authorization": f"Bearer {key}"}
    config = {
        "type": "transcription",
        "transcription_config": {
            "language": "th", "diarization": "speaker", "operating_point": "enhanced",
        },
    }
    with open(path, "rb") as f:
        sub = requests.post(
            "https://asr.api.speechmatics.com/v2/jobs", headers=hdr,
            files={"data_file": (os.path.basename(path), f), "config": (None, json.dumps(config))},
            timeout=600,
        )
    sub.raise_for_status()
    job_id = sub.json()["id"]
    for _ in range(600):
        time.sleep(3)
        j = requests.get(f"https://asr.api.speechmatics.com/v2/jobs/{job_id}", headers=hdr, timeout=60).json()
        st = j.get("job", {}).get("status")
        if st == "done":
            tr = requests.get(
                f"https://asr.api.speechmatics.com/v2/jobs/{job_id}/transcript",
                headers=hdr, params={"format": "json-v2"}, timeout=60,
            ).json()
            segments = []
            for item in tr.get("results", []):
                alt = (item.get("alternatives") or [{}])[0]
                segments.append({
                    "speaker": alt.get("speaker", "?"),
                    "start": item.get("start_time", 0.0),
                    "text": alt.get("content", ""),
                })
            save("speechmatics", segments, time.time() - t0)
            return
        if st in ("rejected", "deleted", "expired"):
            print(f"  ✗ speechmatics job {st}: {json.dumps(j)[:300]}")
            return
    print("  ✗ speechmatics timed out")


PROVIDERS = [
    ("DEEPGRAM_API_KEY", run_deepgram),
    ("GLADIA_API_KEY", run_gladia),
    ("SPEECHMATICS_API_KEY", run_speechmatics),
]


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 bakeoff_diarization.py <audio-file>")
    path = sys.argv[1]
    if not os.path.exists(path):
        sys.exit(f"file not found: {path}")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"sample: {path} ({size_mb:.1f} MB)\n")
    ran = 0
    for env_key, fn in PROVIDERS:
        key = os.getenv(env_key)
        if not key:
            print(f"— skipping {fn.__name__} ({env_key} not set)")
            continue
        ran += 1
        try:
            fn(path, key)
        except Exception as e:
            print(f"  ✗ {fn.__name__} failed: {e}")
        print()
    if not ran:
        sys.exit("No API keys set — see the header of this file for setup.")
    print("Done. Open the bakeoff_*.txt files and compare:\n"
          "  1) English terms kept in English (not Thai-transliterated)?\n"
          "  2) Speaker turns attributed correctly during Thai speech?\n"
          "  3) Timestamps usable per turn?")


if __name__ == "__main__":
    main()
