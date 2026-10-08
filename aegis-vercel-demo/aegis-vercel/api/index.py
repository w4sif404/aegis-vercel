import sys
from pathlib import Path

# app.py, storage.py, templates/ and static/ all live one directory up
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

# Vercel's Python runtime looks for a WSGI-callable named `app`
