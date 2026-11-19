"""Ambil rute jalan pos → kelurahan dari OSRM (data OpenStreetMap), sekali saja.

Jalankan dari root proyek (butuh internet):  .venv\\Scripts\\python scripts\\ambil_rute.py
Pasangan diambil dari semua file hasil_*.json (kelurahan dan pos yang melayaninya).
Rute yang sudah ada di data/olahan/rute_osrm.json dilewati, jadi skrip aman dijalankan ulang
setelah data hasil berubah. Waktu tempuh OSRM TIDAK dipakai; dasbor hanya memakai bentuk jalurnya.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

import shapely

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402

TOLERANSI_JALUR = 0.00005      # derajat (~5 m), penyederhanaan geometri agar file kecil


def pasangan_rute(daftar_hasil):
    """Pasangan unik (kode_kelurahan, kode_pos) dari semua solusi, terurut."""
    pasangan = {(kel, v["pos_melayani"]) for h in daftar_hasil for s in h["solusi"]
                for kel, v in s["hasil_kelurahan"].items()}
    return sorted(pasangan)


def url_rute(asal, tujuan):
    """URL OSRM untuk rute mobil dari asal (lat, lng) ke tujuan (lat, lng)."""
    return (f"{config.OSRM_URL}{asal[1]},{asal[0]};{tujuan[1]},{tujuan[0]}"
            "?overview=full&geometries=geojson")


def ubah_geometri(resp, toleransi=TOLERANSI_JALUR):
    """Respons OSRM → [[lat, lng], ...] yang disederhanakan; None kalau rute tidak ada."""
    if resp.get("code") != "Ok" or not resp.get("routes"):
        return None
    koord = resp["routes"][0]["geometry"]["coordinates"]
    garis = shapely.LineString(koord)
    if toleransi > 0:
        garis = garis.simplify(toleransi, preserve_topology=False)
    return [[round(lat, 5), round(lng, 5)] for lng, lat in garis.coords]


def _ambil(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dasbor-pos-gd/1.0 (prototipe skripsi)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    baca = lambda p: json.loads(p.read_text(encoding="utf-8"))  # noqa: E731
    daftar_hasil = [baca(p) for p in sorted(config.DIR_OLAHAN.glob("hasil_*.json"))]
    faskes = {f["kode"]: f for f in baca(config.DIR_OLAHAN / "faskes.json")}
    kel = {f["properties"]["kode"]: f["properties"]
           for f in baca(config.DIR_OLAHAN / "kelurahan.geojson")["features"]}

    path = config.DIR_OLAHAN / config.FILE_RUTE
    rute = baca(path) if path.exists() else {}
    semua = pasangan_rute(daftar_hasil)
    sisa = [(k, p) for k, p in semua if f"{k}|{p}" not in rute]
    print(f"{len(semua)} pasangan, {len(sisa)} belum diambil. Perkiraan {len(sisa) * config.OSRM_JEDA_DETIK / 60:.0f} menit.")

    gagal = []
    for i, (k, p) in enumerate(sisa, 1):
        asal = (faskes[p]["lat"], faskes[p]["lng"])                      # pos (ambulans berangkat)
        tujuan = (kel[k]["centroid_lat"], kel[k]["centroid_lng"])       # titik wakil kelurahan
        try:
            jalur = ubah_geometri(_ambil(url_rute(asal, tujuan)))
        except Exception as e:  # jaringan/server: catat, lanjut
            jalur, galat = None, str(e)
        else:
            galat = "rute tidak ditemukan" if jalur is None else ""
        if jalur:
            rute[f"{k}|{p}"] = jalur
        else:
            gagal.append(f"{k}|{p}: {galat}")
        if i % 25 == 0 or i == len(sisa):
            path.write_text(json.dumps(rute, separators=(",", ":")), encoding="utf-8")   # simpan berkala
            print(f"  {i}/{len(sisa)}")
        time.sleep(config.OSRM_JEDA_DETIK)

    path.write_text(json.dumps(rute, separators=(",", ":")), encoding="utf-8")
    print(f"Selesai: {len(rute)} rute tersimpan ({path.stat().st_size / 1024:.0f} KB), {len(gagal)} gagal.")
    for g in gagal:
        print("  GAGAL", g)


if __name__ == "__main__":
    main()
