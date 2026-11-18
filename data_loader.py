"""Membaca semua data olahan sekali saat aplikasi mulai (penyimpan data DFD)."""
import json

import config


def _baca(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def label_opsi(hasil):
    """Label dropdown, misalnya 'Skenario Utama (ρ = 2,93) — MOBGOA (gabungan 30 run)'."""
    sk = hasil["skenario"]
    metode = config.NAMA_METODE[sk["metode"]].format(seed=sk["sumber"].get("jumlah_seed", ""))
    return f"{sk['nama']} — {metode}"


def muat_semua(dir_olahan):
    """Kembalikan dict faskes, geojson, hasil, metrik, indeks, opsi_skenario.

    Kunci hasil berbentuk "<id_skenario>|<metode>". indeks[kunci][p] adalah daftar
    solusi p tersebut, urut solusi_id.
    """
    faskes = {f["kode"]: f for f in _baca(dir_olahan / "faskes.json")}
    geojson = _baca(dir_olahan / "kelurahan.geojson")
    hasil, metrik, indeks = {}, {}, {}
    for path in sorted(dir_olahan.glob("hasil_*.json")):
        h = _baca(path)
        kunci = f"{h['skenario']['id']}|{h['skenario']['metode']}"
        hasil[kunci] = h
        metrik[kunci] = _baca(dir_olahan / path.name.replace("hasil_", "metrik_", 1))
        per_p = {}
        for s in h["solusi"]:
            per_p.setdefault(s["p"], []).append(s)
        indeks[kunci] = {p: sorted(v, key=lambda s: s["solusi_id"]) for p, v in per_p.items()}

    urutan_s = list(config.SKENARIO)
    urutan_m = list(config.NAMA_METODE)
    kunci_urut = sorted(hasil, key=lambda k: (urutan_s.index(k.split("|")[0]), urutan_m.index(k.split("|")[1])))
    opsi = [{"label": label_opsi(hasil[k]), "value": k} for k in kunci_urut]
    return {"faskes": faskes, "geojson": geojson, "hasil": hasil, "metrik": metrik, "indeks": indeks,
            "opsi_skenario": opsi}
