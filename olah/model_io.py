"""Memuat bahan model (κ, t̄, w, waktu Google mentah) per skenario.

Semua rumus berasal dari model/data_bersama.py; modul ini hanya memanggilnya
dengan parameter skenario yang benar.
"""
import json
import os
import sys

import config

if str(config.DIR_MODEL) not in sys.path:
    sys.path.insert(0, str(config.DIR_MODEL))

import data_bersama as db  # noqa: E402

# kunci parameter_model.json -> argumen siapkan()
_PETA_PARAM = {"RHO": "rho", "T_BAIK": "t_baik", "PHI_BAIK": "phi_baik",
               "T_BURUK": "t_buruk", "PHI_BURUK": "phi_buruk", "BATAS_KLASIK": "batas_klasik"}


def parameter_skenario(id_skenario):
    """Argumen siapkan() untuk skenario; skenario tanpa file parameter memakai nilai bawaan."""
    path = config.SKENARIO[id_skenario]["parameter_json"]
    if path is None:
        return {}
    with open(path, encoding="utf-8") as f:
        p = json.load(f)
    return {arg: p[kunci] for kunci, arg in _PETA_PARAM.items()}


def muat_model(id_skenario):
    """Kembalikan dict fas, kel, K, T, w, D, P, L, param untuk satu skenario.

    siapkan() membaca file relatif terhadap direktori kerja, jadi direktori kerja
    dipindah sementara ke data/mentah dan selalu dikembalikan.
    """
    argumen = parameter_skenario(id_skenario)
    asal = os.getcwd()
    try:
        os.chdir(config.DIR_MENTAH)
        d = db.siapkan(cetak=False, **argumen)
    except SystemExit as e:
        raise RuntimeError(f"siapkan() gagal untuk skenario '{id_skenario}' (kode {e.code})") from e
    finally:
        os.chdir(asal)
    K, T = d["MASUKAN"]["fuzzy"]
    return {"fas": d["fas"], "kel": d["kel"], "K": K, "T": T, "w": d["w"], "D": d["D"],
            "P": d["P"], "L": d["L"], "param": d["param"]}


def idx_faskes(d, kode):
    """Ubah daftar kode faskes menjadi indeks baris matriks. Kode tak dikenal -> KeyError."""
    posisi = {k: i for i, k in enumerate(d["fas"])}
    return [posisi[k] for k in kode]
