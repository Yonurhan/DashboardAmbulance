"""Tes transisi state dasbor (callbacks.state_baru)."""
from callbacks import state_baru

AWAL = {"kunci": "utama|mobgoa", "p": 10, "kondisi": "biasa", "solusi_id": 4, "kel": "32.75.01.1001"}


def test_ganti_skenario_reset_solusi_kel_tetap():
    s = state_baru(AWAL, "dd-skenario", "rho1|eksak")
    assert s["kunci"] == "rho1|eksak" and s["solusi_id"] == 1 and s["kel"] == AWAL["kel"]


def test_ganti_p_reset_solusi():
    s = state_baru(AWAL, "sl-p", 3)
    assert s["p"] == 3 and s["solusi_id"] == 1


def test_ganti_kondisi_tidak_ubah_solusi():
    s = state_baru(AWAL, "rb-kondisi", "sibuk")
    assert s["kondisi"] == "sibuk" and s["solusi_id"] == 4 and s["p"] == 10


def test_klik_pareto_dan_kelurahan_dan_tutup():
    assert state_baru(AWAL, "g-pareto", 2)["solusi_id"] == 2
    assert state_baru(AWAL, "geo-kel", "32.75.02.1001")["kel"] == "32.75.02.1001"
    assert state_baru(AWAL, "btn-tutup", None)["kel"] is None


def test_nilai_kosong_tidak_mengubah_state():
    for pemicu in ("dd-skenario", "sl-p", "rb-kondisi", "g-pareto", "geo-kel"):
        assert state_baru(AWAL, pemicu, None) == AWAL
    assert state_baru(AWAL, "rb-kondisi", "salah") == AWAL
    assert AWAL["solusi_id"] == 4   # state asal tidak dimutasi
