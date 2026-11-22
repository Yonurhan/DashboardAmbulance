"""Isi templat_penjelasan.html dengan SVG DFD terbaru -> penjelasan-dfd.html (halaman panduan)."""
import re
from pathlib import Path

FOLDER = Path(__file__).resolve().parent


def svg(nama, nomor):
    """SVG tanpa deklarasi XML, dengan id panah unik agar tidak bentrok dalam satu halaman."""
    teks = (FOLDER / f"{nama}.svg").read_text(encoding="utf-8")
    teks = re.sub(r"<\?xml[^>]*\?>\s*", "", teks)
    teks = re.sub(r' width="\d+" height="\d+">', ">", teks, count=1)
    return teks.replace('id="panah"', f'id="panah{nomor}"').replace("url(#panah)", f"url(#panah{nomor})")


isi = (FOLDER / "templat_penjelasan.html").read_text(encoding="utf-8")
ganti = {"{{SVG_KONTEKS}}": svg("dfd-0-konteks", 1), "{{SVG_KONTEKS_GS}}": svg("dfd-0-konteks-gane-sarson", 2),
         "{{SVG_LEVEL1}}": svg("dfd-1-level1", 3), "{{SVG_LEVEL1_GS}}": svg("dfd-1-level1-gane-sarson", 4),
         "{{SVG_LEVEL2}}": svg("dfd-2-proses2", 5), "{{SVG_LEVEL2_GS}}": svg("dfd-2-proses2-gane-sarson", 6)}
for kunci, nilai in ganti.items():
    assert kunci in isi, kunci
    isi = isi.replace(kunci, nilai)
(FOLDER / "penjelasan-dfd.html").write_text(isi, encoding="utf-8")
print("ditulis:", FOLDER / "penjelasan-dfd.html")
