"""Pembentukan entri solusi untuk dasbor: pos melayani, kategori, metrik, front.

Rumus Z dan ukuran netral diimpor dari model/data_bersama.py; penggabungan
front MOBGOA memakai non_dominasi() dari model/mobgoa.py.
"""
import numpy as np
import pandas as pd

import config
from olah.model_io import db, idx_faskes

import mobgoa  # noqa: E402  (folder model sudah masuk sys.path lewat model_io)


def kategori_menit(t):
    """Kelompokkan waktu tempuh (menit) ke "<=15", "15-40", atau ">40"."""
    bawah, atas = config.BATAS_MENIT
    if t <= bawah:
        return "<=15"
    if t <= atas:
        return "15-40"
    return ">40"


def pos_melayani(K_kol, T_kol, idx):
    """Pos di S dengan κ tertinggi (seri -> t̄ terkecil) untuk satu kelurahan.

    Kembalikan (indeks faskes, cakupan, tercakup). Kalau semua κ = 0, pos dengan
    t̄ terkecil dipakai dan tercakup = False.
    """
    idx = list(idx)
    kap = np.asarray(K_kol)[idx]
    tb = np.asarray(T_kol)[idx]
    if kap.max() <= 0:
        j = idx[int(np.argmin(tb))]
        return j, 0.0, False
    urut = np.lexsort((tb, -kap))      # κ turun, lalu t̄ naik
    j = idx[int(urut[0])]
    return j, float(K_kol[j]), True


def hasil_kelurahan(d, idx):
    """Isi hasil_kelurahan untuk satu solusi. Menit tidak disimpan di sini; ada di menit_google.json (lokal)."""
    tercepat = {nama: d["D"][kode][list(idx)].min(axis=0) for nama, kode in config.KONDISI.items()}
    out = {}
    for i, kel in enumerate(d["kel"]):
        j, kap, tercakup = pos_melayani(d["K"][:, i], d["T"][:, i], idx)
        out[kel] = {
            "pos_melayani": d["fas"][j],
            "cakupan": round(kap, 8),
            "tercakup": tercakup,
            "kategori": {nama: kategori_menit(float(t[i])) for nama, t in tercepat.items()},
        }
    return out


def metrik_kondisi(d, idx):
    """Persentase permintaan berbobot ≤ 15 dan ≤ 40 menit per kondisi (ukuran_netral model)."""
    un = db.ukuran_netral(list(idx), d["D"], d["w"])
    b, a = (f"{x:g}" for x in config.BATAS_MENIT)
    return {nama: {"persen_15": un[f"pct_le{b}_{kode}"], "persen_40": un[f"pct_le{a}_{kode}"]}
            for nama, kode in config.KONDISI.items()}


def _pecah(teks):
    return [k.strip() for k in str(teks).split(";") if k.strip()]


def baca_front_eksak(path):
    """Front eksak model fuzzy: DataFrame berkolom p, Z1, Z2, pos."""
    a = pd.read_csv(path)
    a = a[a["model"] == "fuzzy"]
    return pd.DataFrame({"p": a["p"].astype(int).to_numpy(), "Z1": a["Z1_fuzzy"].to_numpy(float),
                         "Z2": a["Z2_fuzzy_menit"].to_numpy(float),
                         "pos": [_pecah(x) for x in a["faskes_dibuka"]]})


def _gabung_per_p(a):
    """Gabungkan semua seed: buang himpunan ganda, ambil yang tak terdominasi."""
    baris = []
    for p, g in a.groupby("p", sort=True):
        g = g.assign(_kunci=[frozenset(_pecah(x)) for x in g["faskes_dibuka"]])
        g = g.drop_duplicates("_kunci")
        z1, z2 = g["Z1"].to_numpy(float), g["Z2_menit"].to_numpy(float)
        for k in mobgoa.non_dominasi(z1, z2):
            r = g.iloc[int(k)]
            baris.append({"p": int(p), "Z1": float(r["Z1"]), "Z2": float(r["Z2_menit"]),
                          "pos": sorted(r["_kunci"])})
    return pd.DataFrame(baris, columns=["p", "Z1", "Z2", "pos"])


def baca_front_mobgoa(path, konfigurasi):
    """Front MOBGOA gabungan per tahap: {tahap: {front, konfigurasi, jumlah_seed}}."""
    a = pd.read_csv(path)
    hasil = {}
    for tahap, g in a.groupby("tahap", sort=True):
        if konfigurasi is not None:
            g = g[(g["aturan"] == konfigurasi["aturan"]) & (g["N"] == konfigurasi["N"])
                  & (g["iterasi"] == konfigurasi["iterasi"])]
        kombinasi = g[["aturan", "N", "iterasi"]].drop_duplicates()
        if len(kombinasi) != 1:
            raise ValueError(
                f"tahap '{tahap}' berisi {len(kombinasi)} kombinasi (aturan, N, iterasi): "
                f"{kombinasi.to_dict('records')}. Tetapkan satu di config.MOBGOA[\"konfigurasi\"].")
        k = kombinasi.iloc[0]
        hasil[str(tahap)] = {
            "front": _gabung_per_p(g),
            "konfigurasi": {"aturan": str(k["aturan"]), "N": int(k["N"]), "iterasi": int(k["iterasi"])},
            "jumlah_seed": int(g["seed"].nunique()),
        }
    return hasil


def bangun_solusi(d, front):
    """Ubah front (p, Z1, Z2, pos) menjadi daftar entri solusi untuk file hasil."""
    out = []
    for p, g in front.groupby("p", sort=True):
        g = g.sort_values(["Z1", "Z2"], ascending=[False, True], kind="stable")
        for sid, (_, r) in enumerate(g.iterrows(), start=1):
            idx = idx_faskes(d, r["pos"])
            out.append({"p": int(p), "solusi_id": sid, "Z1": float(r["Z1"]), "Z2": float(r["Z2"]),
                        "pos": list(r["pos"]), "hasil_kelurahan": hasil_kelurahan(d, idx),
                        "metrik": metrik_kondisi(d, idx)})
    return out
