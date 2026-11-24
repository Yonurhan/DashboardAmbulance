"""Cetak isi environment variable MENIT_GOOGLE_GZ_B64 untuk Vercel (menit_google.json -> gzip -> base64).

Jalankan:  .venv\\Scripts\\python scripts\\menit_ke_env.py > menit_env.txt   lalu salin isinya ke Vercel.
File keluaran berisi data Google: jangan di-commit, hapus setelah dipakai.
"""
import base64
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

m = json.loads((config.DIR_OLAHAN / config.FILE_MENIT).read_text(encoding="utf-8"))
print(base64.b64encode(gzip.compress(json.dumps(m, separators=(",", ":")).encode(), 9)).decode())
