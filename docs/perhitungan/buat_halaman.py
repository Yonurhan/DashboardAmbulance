"""Isi templat.html dengan grafik_sigmoid.svg -> penjelasan-perhitungan.html."""
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
isi = (FOLDER / "templat.html").read_text(encoding="utf-8")
assert "{{GRAFIK}}" in isi
isi = isi.replace("{{GRAFIK}}", (FOLDER / "grafik_sigmoid.svg").read_text(encoding="utf-8"))
(FOLDER / "penjelasan-perhitungan.html").write_text(isi, encoding="utf-8")
print("ditulis:", FOLDER / "penjelasan-perhitungan.html")
