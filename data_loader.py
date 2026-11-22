"""Membaca semua data olahan sekali saat aplikasi mulai (penyimpan data DFD)."""
import json

import config


def _baca(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def label_opsi(hasil):
    """Label dropdown, misalnya 'Utama · MOBGOA (gabungan 30 run)'."""
    sk = hasil["skenario"]
    nama = config.SKENARIO.get(sk["id"], {}).get("nama_pendek", sk["nama"])
    metode = config.NAMA_METODE[sk["metode"]].format(seed=sk["sumber"].get("jumlah_seed", ""))
    return f"{nama} · {metode}"


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

    periksa_kelengkapan_p(indeks)
    urutan_s = list(config.SKENARIO)
    urutan_m = list(config.NAMA_METODE)
    kunci_urut = sorted(hasil, key=lambda k: (urutan_s.index(k.split("|")[0]), urutan_m.index(k.split("|")[1])))
    opsi = [{"label": label_opsi(hasil[k]), "value": k} for k in kunci_urut]
    return {"faskes": faskes, "geojson": geojson, "hasil": hasil, "metrik": metrik, "indeks": indeks,
            "opsi_skenario": opsi, "menit": muat_menit(dir_olahan), "rute": muat_rute(dir_olahan)}


def periksa_kelengkapan_p(indeks):
    """Pastikan setiap file hasil punya solusi untuk semua p; kalau tidak, gagal dengan pesan jelas saat start."""
    for kunci, per_p in indeks.items():
        hilang = [p for p in range(config.P_MIN, config.P_MAKS + 1) if not per_p.get(p)]
        if hilang:
            raise ValueError(f"hasil {kunci} tidak punya solusi untuk p = {', '.join(map(str, hilang))}; "
                             "jalankan ulang scripts/siapkan_data.py dan scripts/cek_data.py")


def muat_menit(dir_olahan):
    """Menit Google per pasangan faskes-kelurahan (file lokal, tidak ada di Git). None kalau tidak ada.

    Bentuk: {"fas": {kode: baris}, "kel": {kode: kolom}, "opt"/"bg"/"pes": matriks [faskes][kelurahan]}.
    """
    path = dir_olahan / config.FILE_MENIT
    if not path.exists():
        return None
    m = _baca(path)
    return {"fas": {k: i for i, k in enumerate(m["fas"])}, "kel": {k: j for j, k in enumerate(m["kel"])},
            **{c: m[c] for c in config.KONDISI.values()}}


def muat_rute(dir_olahan):
    """Rute jalan OSRM {"<kelurahan>|<faskes>": [[lat, lng], ...]}. Dict kosong kalau belum diambil."""
    path = dir_olahan / config.FILE_RUTE
    return _baca(path) if path.exists() else {}
