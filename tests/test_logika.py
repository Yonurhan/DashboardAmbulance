"""Tes fungsi murni dasbor (data_loader.py, logika.py) dengan data olahan asli."""
import pytest

import config
import data_loader
import logika


@pytest.fixture(scope="module")
def data():
    return data_loader.muat_semua(config.DIR_OLAHAN)


def test_muat_semua_kunci_dan_opsi(data):
    assert set(data["hasil"]) == {"utama|eksak", "utama|mobgoa", "jakarta10|eksak", "rho1|eksak"}
    nilai = [o["value"] for o in data["opsi_skenario"]]
    assert nilai == ["utama|eksak", "utama|mobgoa", "jakarta10|eksak", "rho1|eksak"]
    label_mobgoa = data["opsi_skenario"][1]["label"]
    assert "MOBGOA" in label_mobgoa and "30" in label_mobgoa
    assert len(data["faskes"]) == 99


def test_daftar_solusi_urut_id(data):
    sol = logika.daftar_solusi(data, "utama|eksak", 4)
    assert [s["solusi_id"] for s in sol] == list(range(1, 10))
    assert all(s["p"] == 4 for s in sol)


def test_solusi_aktif_kembali_ke_default(data):
    assert logika.solusi_aktif(data, "utama|eksak", 2, 9)["solusi_id"] == 1
    assert logika.solusi_aktif(data, "utama|eksak", 2, None)["solusi_id"] == 1
    assert logika.solusi_aktif(data, "utama|eksak", 4, 3)["solusi_id"] == 3


def test_warna_kelurahan_56_dan_palet(data):
    s = logika.solusi_aktif(data, "utama|mobgoa", 10, 1)
    w = logika.warna_kelurahan(s, "sibuk")
    assert len(w) == 56
    assert set(w.values()) <= set(config.WARNA_KATEGORI.values())


def test_kelurahan_terendah_urut(data):
    s = logika.solusi_aktif(data, "utama|eksak", 3, 1)
    t = logika.kelurahan_terendah(s, data, "biasa")
    assert len(t) == 10
    nilai = [r["cakupan"] for r in t]
    assert nilai == sorted(nilai)
    assert set(t[0]) == {"nama", "kecamatan", "cakupan", "kategori"}
    semua = sorted(v["cakupan"] for v in s["hasil_kelurahan"].values())
    assert nilai == semua[:10]


def test_pos_inti_urut_dan_ambang(data):
    inti = logika.pos_inti(data, "utama|eksak", 10)
    assert inti and all(f >= config.AMBANG_POS_INTI for _, f in inti)
    assert [f for _, f in inti] == sorted((f for _, f in inti), reverse=True)


def test_pos_inti_kosong(data, monkeypatch):
    monkeypatch.setattr(config, "AMBANG_POS_INTI", 101.0)
    assert logika.pos_inti(data, "utama|eksak", 10) == []


def test_detail_kelurahan_bobot_ikut_skenario(data):
    kel = "32.75.01.1001"
    s_u = logika.solusi_aktif(data, "utama|eksak", 5, 1)
    s_r = logika.solusi_aktif(data, "rho1|eksak", 5, 1)
    d_u = logika.detail_kelurahan(data, "utama|eksak", s_u, kel)
    d_r = logika.detail_kelurahan(data, "rho1|eksak", s_r, kel)
    assert d_u["bobot"] == data["hasil"]["utama|eksak"]["bobot_kelurahan"][kel]
    assert d_r["bobot"] == data["hasil"]["rho1|eksak"]["bobot_kelurahan"][kel]
    assert d_u["bobot"] != d_r["bobot"]
    assert d_u["pos_kode"] in s_u["pos"]
    assert len(d_u["garis"]) == 2 and set(d_u["kategori"]) == {"lengang", "biasa", "sibuk"}


def test_detail_memuat_menit_tercepat(data):
    """Atas permintaan pengguna (revisi 2) panel menampilkan menit ke pos tercepat per kondisi."""
    s = logika.solusi_aktif(data, "utama|eksak", 5, 1)
    d = logika.detail_kelurahan(data, "utama|eksak", s, "32.75.01.1001")
    assert d["menit"] == logika.menit_tercepat(data, s, "32.75.01.1001")
    d0 = logika.detail_kelurahan({**data, "menit": None}, "utama|eksak", s, "32.75.01.1001")
    assert d0["menit"] is None


def test_ringkasan_metrik(data):
    s = logika.solusi_aktif(data, "utama|eksak", 7, 2)
    r = logika.ringkasan_metrik(s, "lengang")
    assert r == {"Z1": s["Z1"], "Z2": s["Z2"], "persen_15": s["metrik"]["lengang"]["persen_15"],
                 "persen_40": s["metrik"]["lengang"]["persen_40"]}


def test_menit_tercepat_bintarajaya_p2(data):
    """Bintarajaya, Utama · MOBGOA p = 2: kondisi biasa 14,82 menit ke RS-35 (data Google mentah)."""
    if data["menit"] is None:
        pytest.skip("menit_google.json tidak ada (data Google hanya lokal)")
    kode = [f["properties"]["kode"] for f in data["geojson"]["features"]
            if f["properties"]["nama"] == "Bintarajaya"][0]
    s = logika.solusi_aktif(data, "utama|mobgoa", 2, 1)
    m = logika.menit_tercepat(data, s, kode)
    assert m["biasa"]["pos"] == "RS-35"
    assert m["biasa"]["menit"] == pytest.approx(14.82, abs=0.005)
    assert set(m) == {"lengang", "biasa", "sibuk"}
    # kategori di hasil olahan harus konsisten dengan menit ini
    for k, v in m.items():
        b, a = config.BATAS_MENIT
        kat = "<=15" if v["menit"] <= b else ("15-40" if v["menit"] <= a else ">40")
        assert kat == s["hasil_kelurahan"][kode]["kategori"][k]


def test_menit_tercepat_tanpa_data(data):
    s = logika.solusi_aktif(data, "utama|mobgoa", 2, 1)
    assert logika.menit_tercepat({**data, "menit": None}, s, next(iter(s["hasil_kelurahan"]))) is None


def test_detail_rute_jalan_bila_ada(data):
    s = logika.solusi_aktif(data, "utama|eksak", 5, 1)
    kel = "32.75.01.1001"
    pos = s["hasil_kelurahan"][kel]["pos_melayani"]
    jalur = [[-6.2, 107.0], [-6.21, 107.01], [-6.22, 107.02]]
    d = logika.detail_kelurahan({**data, "rute": {f"{kel}|{pos}": jalur}}, "utama|eksak", s, kel)
    assert d["rute"] == jalur
    d0 = logika.detail_kelurahan({**data, "rute": {}}, "utama|eksak", s, kel)
    assert d0["rute"] is None
