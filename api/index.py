"""Titik masuk Vercel: semua permintaan diarahkan ke sini (lihat vercel.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import server as app  # noqa: E402  (Vercel mencari objek WSGI bernama `app`)
