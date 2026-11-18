"""Fungsi murni dasbor: memilih solusi dan menyiapkan isi tampilan.

Tidak ada komponen Dash di sini, supaya setiap fungsi bisa diuji dengan pytest.
Pengelompokan mengikuti DFD: 3.0 Tampilkan Solusi, 4.0 Tampilkan Analisis,
5.0 Tampilkan Detail Kelurahan.
"""
import config


# ============================================================ Proses 3.0 Tampilkan Solusi
def daftar_solusi(data, kunci, p):
    """Semua solusi Pareto pada p, urut solusi_id."""
    return data["indeks"][kunci].get(int(p), [])


def solusi_aktif(data, kunci, p, solusi_id):
    """Solusi dengan solusi_id; kalau tidak ada (atau None) kembali ke solusi_id 1."""
    daftar = daftar_solusi(data, kunci, p)
    for s in daftar:
        if s["solusi_id"] == solusi_id:
            return s
    return daftar[0]


def warna_kelurahan(solusi, kondisi):
    """Warna kategori waktu tempuh tiap kelurahan pada kondisi lalu lintas."""
    return {kel: config.WARNA_KATEGORI[v["kategori"][kondisi]] for kel, v in solusi["hasil_kelurahan"].items()}


def ringkasan_metrik(solusi, kondisi):
    """Z1, Z2, dan persentase permintaan berbobot ≤ 15 / ≤ 40 menit pada kondisi."""
    m = solusi["metrik"][kondisi]
    return {"Z1": solusi["Z1"], "Z2": solusi["Z2"], "persen_15": m["persen_15"], "persen_40": m["persen_40"]}


# ============================================================ Proses 4.0 Tampilkan Analisis
def _info_kelurahan(data):
    return {f["properties"]["kode"]: f["properties"] for f in data["geojson"]["features"]}


def kelurahan_terendah(solusi, data, kondisi, n=10):
    """n kelurahan dengan cakupan terendah (urut naik, lalu nama)."""
    info = _info_kelurahan(data)
    baris = [{"nama": info[k]["nama"], "kecamatan": info[k]["kecamatan"], "cakupan": v["cakupan"],
              "kategori": v["kategori"][kondisi]} for k, v in solusi["hasil_kelurahan"].items()]
    return sorted(baris, key=lambda r: (r["cakupan"], r["nama"]))[:n]


def pos_inti(data, kunci, p_awal):
    """Faskes dengan frekuensi ≥ AMBANG_POS_INTI untuk p_awal..20, urut frekuensi turun."""
    frek = data["metrik"][kunci]["frekuensi_faskes"].get(str(int(p_awal)), {})
    lolos = [(k, f) for k, f in frek.items() if f >= config.AMBANG_POS_INTI]
    return sorted(lolos, key=lambda x: (-x[1], x[0]))


# ============================================================ Proses 5.0 Tampilkan Detail Kelurahan
def detail_kelurahan(data, kunci, solusi, kode_kel):
    """Isi panel detail satu kelurahan (tanpa angka menit)."""
    info = _info_kelurahan(data)[kode_kel]
    v = solusi["hasil_kelurahan"][kode_kel]
    pos = data["faskes"][v["pos_melayani"]]
    return {"kode": kode_kel, "nama": info["nama"], "kecamatan": info["kecamatan"],
            "penduduk": info["penduduk"], "lansia": info["lansia"],
            "bobot": data["hasil"][kunci]["bobot_kelurahan"][kode_kel],
            "pos_kode": pos["kode"], "pos_nama": pos["nama"], "cakupan": v["cakupan"],
            "tercakup": v["tercakup"], "kategori": dict(v["kategori"]),
            "garis": [[info["centroid_lat"], info["centroid_lng"]], [pos["lat"], pos["lng"]]]}
