"""Penyiapan data dasbor: ubah output model menjadi file di data/olahan/.

Jalankan dari root proyek:  .venv\\Scripts\\python scripts\\siapkan_data.py
Dasbor hanya membaca hasil skrip ini, tidak pernah membaca data mentah.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from olah import geo, metrik, model_io, solusi  # noqa: E402


def _bulat(x):
    """Bulatkan float secara rekursif ke 8 desimal agar file ringkas."""
    if isinstance(x, float):
        return round(x, 8)
    if isinstance(x, dict):
        return {k: _bulat(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_bulat(v) for v in x]
    return x


def tulis_json(nama, isi):
    path = config.DIR_OLAHAN / nama
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_bulat(isi), f, ensure_ascii=False, separators=(",", ":"))
    return path.stat().st_size / 1024


def info_skenario(id_s, metode, d, sumber):
    s = config.SKENARIO[id_s]
    return {"id": id_s, "nama": s["nama"], "keterangan": s["keterangan"], "metode": metode,
            "parameter": {"rho": d["param"]["RHO"], "t_baik": d["param"]["T_BAIK"],
                          "t_buruk": d["param"]["T_BURUK"]},
            "sumber": sumber}


def tulis_hasil(id_s, metode, d, front, sumber, laporan):
    """Tulis hasil_<id>_<metode>.json dan metrik_<id>_<metode>.json."""
    sol = solusi.bangun_solusi(d, front)
    hasil = {"skenario": info_skenario(id_s, metode, d, sumber),
             "bobot_kelurahan": {k: float(w) for k, w in zip(d["kel"], d["w"])},
             "solusi": sol}
    met = {"kenaikan_cakupan": metrik.kenaikan_cakupan(sol),
           "frekuensi_faskes": metrik.frekuensi_faskes(sol, d["fas"])}
    kb_h = tulis_json(f"hasil_{id_s}_{metode}.json", hasil)
    kb_m = tulis_json(f"metrik_{id_s}_{metode}.json", met)
    per_p = dict(sorted(Counter(s["p"] for s in sol).items()))
    laporan["hasil"][f"{id_s}_{metode}"] = {"jumlah_solusi": len(sol), "titik_per_p": per_p,
                                           "ukuran_hasil_kb": round(kb_h, 1), "ukuran_metrik_kb": round(kb_m, 1)}
    print(f"  hasil_{id_s}_{metode}.json: {len(sol)} solusi, {kb_h:.0f} KB")


def main():
    config.DIR_OLAHAN.mkdir(parents=True, exist_ok=True)
    laporan = {"hasil": {}}

    print("Memuat model per skenario ...")
    model = {id_s: model_io.muat_model(id_s) for id_s in config.SKENARIO}
    d0 = model["utama"]

    print("Menulis faskes.json dan kelurahan.geojson ...")
    tulis_json("faskes.json", geo.buat_faskes(config.PATH_FASKES_CSV, d0["fas"]))
    fc, lap_geo = geo.buat_kelurahan(config.PATH_GDB, config.PATH_CENTROID_CSV, d0)
    tulis_json("kelurahan.geojson", fc)
    laporan["kelurahan"] = lap_geo
    print(f"  kelurahan.geojson: {lap_geo['ukuran_sebelum_kb']} KB -> {lap_geo['ukuran_sesudah_kb']} KB "
          f"(toleransi {lap_geo['toleransi']} derajat)")

    print("Menulis hasil eksak ...")
    for id_s, s in config.SKENARIO.items():
        front = solusi.baca_front_eksak(s["eksak"])
        tulis_hasil(id_s, "eksak", model[id_s], front, {"file": s["eksak"].name, "model": "fuzzy"}, laporan)

    print("Menulis hasil MOBGOA ...")
    for tahap, isi in solusi.baca_front_mobgoa(config.MOBGOA["path"], config.MOBGOA["konfigurasi"]).items():
        if tahap not in config.SKENARIO:
            sys.exit(f"tahap MOBGOA '{tahap}' tidak ada di config.SKENARIO; tambahkan dulu skenarionya.")
        sumber = {"file": config.MOBGOA["path"].name, "konfigurasi": isi["konfigurasi"],
                  "jumlah_seed": isi["jumlah_seed"]}
        tulis_hasil(tahap, "mobgoa", model[tahap], isi["front"], sumber, laporan)

    # Menit Google per pasangan untuk panel detail. File ini DI-IGNORE Git (data Google).
    tulis_json(config.FILE_MENIT, {"fas": d0["fas"], "kel": d0["kel"],
                                   **{k: [[round(float(x), 2) for x in baris] for baris in d0["D"][k]]
                                      for k in config.KONDISI.values()}})

    tulis_json("laporan_siapkan.json", laporan)
    print("Selesai.")


if __name__ == "__main__":
    main()
