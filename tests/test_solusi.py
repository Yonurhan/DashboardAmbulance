"""Tes pembentukan solusi, kategori, dan front gabungan MOBGOA (olah/solusi.py)."""
import numpy as np
import pandas as pd
import pytest

from olah import solusi as so


def d_sintetis():
    """3 faskes x 2 kelurahan."""
    K = np.array([[0.8, 0.1],
                  [0.8, 0.2],
                  [0.3, 0.0]])
    T = np.array([[20.0, 50.0],
                  [12.0, 45.0],
                  [30.0, 60.0]])
    D = {
        "opt": np.array([[10.0, 50.0], [30.0, 35.0], [40.0, 60.0]]),
        "bg": np.array([[14.0, 50.0], [16.0, 45.0], [40.0, 60.0]]),
        "pes": np.array([[30.0, 50.0], [20.0, 41.0], [40.0, 60.0]]),
    }
    return {"fas": ["RS-01", "PKM-01", "PKM-02"], "kel": ["K1", "K2"],
            "K": K, "T": T, "D": D, "w": np.array([0.25, 0.75])}


def test_kategori_batas():
    assert so.kategori_menit(15.0) == "<=15"
    assert so.kategori_menit(15.01) == "15-40"
    assert so.kategori_menit(40.0) == "15-40"
    assert so.kategori_menit(40.01) == ">40"


def test_pos_melayani_seri_pilih_tbar_kecil():
    d = d_sintetis()
    j, kap, tercakup = so.pos_melayani(d["K"][:, 0], d["T"][:, 0], [0, 1])
    assert j == 1 and kap == pytest.approx(0.8) and tercakup is True


def test_pos_melayani_kappa_nol():
    K = np.array([0.0, 0.0])
    T = np.array([25.0, 18.0])
    j, kap, tercakup = so.pos_melayani(K, T, [0, 1])
    assert j == 1 and kap == 0.0 and tercakup is False


def test_kategori_pakai_pos_tercepat_per_kondisi():
    d = d_sintetis()
    hk = so.hasil_kelurahan(d, [0, 1])
    # K1: opt min(10,30)=10 -> <=15; bg min(14,16)=14 -> <=15; pes min(30,20)=20 -> 15-40
    assert hk["K1"]["kategori"] == {"lengang": "<=15", "biasa": "<=15", "sibuk": "15-40"}
    # K2: opt 35 -> 15-40; bg 45 -> >40; pes 41 -> >40
    assert hk["K2"]["kategori"] == {"lengang": "15-40", "biasa": ">40", "sibuk": ">40"}
    assert hk["K1"]["pos_melayani"] == "PKM-01"
    assert hk["K2"]["pos_melayani"] == "PKM-01" and hk["K2"]["cakupan"] == pytest.approx(0.2)
    assert not any("menit" in k for v in hk.values() for k in v)


def test_metrik_kondisi_bentuk():
    m = so.metrik_kondisi(d_sintetis(), [0, 1])
    assert set(m) == {"lengang", "biasa", "sibuk"}
    assert m["biasa"] == {"persen_15": pytest.approx(25.0), "persen_40": pytest.approx(25.0)}


def _tulis_mobgoa(tmp_path, baris):
    kol = ["tahap", "aturan", "N", "iterasi", "p", "seed", "titik_ke", "Z1", "Z2_menit", "detik_run",
           "faskes_dibuka"]
    path = tmp_path / "mobgoa.csv"
    pd.DataFrame(baris, columns=kol).to_csv(path, index=False)
    return path


def test_front_mobgoa_gabung_dedup_nondominasi(tmp_path):
    path = _tulis_mobgoa(tmp_path, [
        ["utama", "target", 200, 2000, 2, 1, 1, 0.9, 20.0, 1.0, "RS-01;PKM-01"],
        ["utama", "target", 200, 2000, 2, 2, 1, 0.9, 20.0, 1.0, "PKM-01;RS-01"],   # himpunan sama
        ["utama", "target", 200, 2000, 2, 2, 2, 0.8, 18.0, 1.0, "RS-01;PKM-02"],
        ["utama", "target", 200, 2000, 2, 3, 1, 0.7, 25.0, 1.0, "PKM-01;PKM-02"],  # terdominasi
    ])
    hasil = so.baca_front_mobgoa(path, None)
    f = hasil["utama"]["front"]
    assert len(f) == 2
    assert all(len(pos) == 2 for pos in f["pos"])
    assert sorted(f["Z1"]) == [0.8, 0.9]
    assert hasil["utama"]["jumlah_seed"] == 3
    assert hasil["utama"]["konfigurasi"] == {"aturan": "target", "N": 200, "iterasi": 2000}


def test_front_mobgoa_konfigurasi_ganda_berhenti(tmp_path):
    path = _tulis_mobgoa(tmp_path, [
        ["utama", "target", 200, 2000, 1, 1, 1, 0.9, 20.0, 1.0, "RS-01"],
        ["utama", "target", 100, 2000, 1, 1, 1, 0.9, 20.0, 1.0, "RS-01"],
    ])
    with pytest.raises(ValueError, match="konfigurasi"):
        so.baca_front_mobgoa(path, None)


def test_solusi_id_urut_z1():
    d = d_sintetis()
    front = pd.DataFrame({"p": [1, 1, 1], "Z1": [0.1, 0.4, 0.3], "Z2": [10.0, 30.0, 20.0],
                          "pos": [["RS-01"], ["PKM-01"], ["PKM-02"]]})
    sol = so.bangun_solusi(d, front)
    assert [s["solusi_id"] for s in sol] == [1, 2, 3]
    assert [s["Z1"] for s in sol] == [0.4, 0.3, 0.1]
    assert set(sol[0]) >= {"p", "solusi_id", "Z1", "Z2", "pos", "hasil_kelurahan", "metrik"}
