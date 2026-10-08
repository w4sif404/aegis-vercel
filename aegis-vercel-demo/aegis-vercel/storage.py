"""
storage.py — demo state storage for the Aegis Cyber Systems training app.

WHY THIS EXISTS
----------------
Vercel's Python functions run in a read-only filesystem except for /tmp,
and /tmp is ephemeral: it can be wiped whenever Vercel spins up a new
instance of your function (a "cold start"). The original local-only demo
used a plain file (".compromised") sitting next to app.py — that trick
does NOT survive on Vercel.

This module gives you two backends, picked automatically:

1. Upstash Redis (recommended for a live, public demo) — a free, tiny,
   serverless-friendly Redis you connect to over plain HTTPS. State
   survives cold starts and is shared across every visitor.
2. /tmp fallback (zero setup) — works fine for a solo presenter demo
   where you control the only browser hitting the site, but the state
   can reset if Vercel cold-starts the function between your clicks.

Nothing here executes uploaded content or reaches outside this one
key/value pair. It only ever stores two things: a COMPROMISED/ORIGINAL
flag and the custom headline text you type into the admin page.
"""
import os
import json
from pathlib import Path
from datetime import datetime

import requests

UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
_USE_UPSTASH = bool(UPSTASH_URL and UPSTASH_TOKEN)

TMP = Path("/tmp")
MARKER = TMP / "aegis_demo_state.json"
LOG = TMP / "aegis_demo.log"

_DEFAULT_STATE = {"compromised": False, "headline": "", "uploaded_name": ""}


def _upstash_call(path):
    r = requests.get(
        f"{UPSTASH_URL}/{path}",
        headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
        timeout=5,
    )
    r.raise_for_status()
    return r.json().get("result")


def get_state():
    if _USE_UPSTASH:
        try:
            raw = _upstash_call("get/aegis_demo_state")
            if raw:
                return json.loads(raw)
            return dict(_DEFAULT_STATE)
        except Exception:
            pass  # fall through to /tmp
    if MARKER.exists():
        try:
            return json.loads(MARKER.read_text())
        except Exception:
            return dict(_DEFAULT_STATE)
    return dict(_DEFAULT_STATE)


def set_state(**kwargs):
    state = get_state()
    state.update(kwargs)
    payload = json.dumps(state)
    if _USE_UPSTASH:
        try:
            # Upstash REST "set" takes the value as an extra path segment,
            # URL-safe-encoded via requests' own quoting.
            r = requests.post(
                f"{UPSTASH_URL}/set/aegis_demo_state",
                headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                data=payload,
                timeout=5,
            )
            r.raise_for_status()
        except Exception:
            pass
    MARKER.write_text(payload)
    return state


def reset_state():
    set_state(compromised=False, headline="", uploaded_name="")


def log_event(message):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
    # Vercel captures stdout as function logs — this is the reliable part.
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass  # /tmp write failing is non-fatal; stdout logging already happened
