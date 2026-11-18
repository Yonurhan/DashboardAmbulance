"""Validasi data olahan terhadap model.

Jalankan dari root proyek:  .venv\\Scripts\\python scripts\\cek_data.py
Ketidakcocokan hanya DILAPORKAN, tidak diperbaiki. Kode keluar 1 kalau ada yang gagal.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from olah import model_io  # noqa: E402
from olah.model_io import db  # noqa: E402

TOL_Z = 1e-6
TOL_PCT = 1e-3          # CSV model membulatkan pct_* ke 3 desimal


def _baca(nama):
    with open(config.DIR_OLAHAN / nama, encoding="utf-8") as f:
        return json.load(f)


def _file_hasil():
    return sorted(p.name for p in config.DIR_OLAHAN.glob("hasil_*.json"))


def cek_struktur(hasil, faskes, kode_geo):
    """Pemeriksaan 1–5 dan 7 untuk satu file hasil. Kembalikan daftar pesan kesalahan per kelompok."""
    salah = {k: [] for k in ("pos_p", "pos_dikenal", "kel_56", "melayani", "cakupan", "p_lengkap")}
    for s in hasil["solusi"]:
        tag = f"p={s['p']} id={s['solusi_id']}"
        if len(s["pos"]) != s["p"] or len(set(s["pos"])) != len(s["pos"]):
            salah["pos_p"].append(tag)
        if not set(s["pos"]) <= faskes:
            salah["pos_dikenal"].append(tag)
        hk = s["hasil_kelurahan"]
        if len(hk) != 56 or set(hk) != kode_geo:
            salah["kel_56"].append(tag)
        for kel, v in hk.items():
            if v["pos_melayani"] not in s["pos"]:
                salah["melayani"].append(f"{tag} {kel}")
            if not 0.0 <= v["cakupan"] <= 1.0:
                salah["cakupan"].append(f"{tag} {kel}")
    ada_p = {s["p"] for s in hasil["solusi"]}
    kurang = sorted(set(range(config.P_MIN, config.P_MAKS + 1)) - ada_p)
    if kurang:
        salah["p_lengkap"].append(f"p hilang: {kurang}")
    return salah


def cek_angka(hasil, d, csv_eksak):
    """Pemeriksaan 6: Z1/Z2 dan metrik dihitung ulang dengan fungsi model."""
    salah_z, salah_m, salah_csv = [], [], []
    for s in hasil["solusi"]:
        tag = f"p={s['p']} id={s['solusi_id']}"
        idx = model_io.idx_faskes(d, s["pos"])
        z1, z2 = db.nilai(idx, d["K"], d["T"], d["w"])
        if abs(z1 - s["Z1"]) > TOL_Z or abs(z2 - s["Z2"]) > TOL_Z:
            salah_z.append(f"{tag}: Z1 {s['Z1']:.8f} vs {z1:.8f}, Z2 {s['Z2']:.6f} vs {z2:.6f}")
        un = db.ukuran_netral(idx, d["D"], d["w"])
        for nama, kode in config.KONDISI.items():
            for b, kunci in zip(config.BATAS_MENIT, ("persen_15", "persen_40")):
                if abs(un[f"pct_le{b:g}_{kode}"] - s["metrik"][nama][kunci]) > TOL_PCT:
                    salah_m.append(f"{tag} {nama} {kunci}")
        if csv_eksak is not None:
            r = csv_eksak.get((s["p"], frozenset(s["pos"])))
            if r is None:
                salah_csv.append(f"{tag}: tidak ada di CSV")
                continue
            for nama, kode in config.KONDISI.items():
                for b, kunci in zip(config.BATAS_MENIT, ("persen_15", "persen_40")):
                    if abs(r[f"pct_le{b:g}_{kode}"] - s["metrik"][nama][kunci]) > TOL_PCT:
                        salah_csv.append(f"{tag} {nama} {kunci}: {s['metrik'][nama][kunci]} vs CSV "
                                         f"{r[f'pct_le{b:g}_{kode}']}")
    return salah_z, salah_m, salah_csv


def baca_csv_eksak(path):
    a = pd.read_csv(path)
    a = a[a["model"] == "fuzzy"]
    return {(int(r["p"]), frozenset(str(r["faskes_dibuka"]).split(";"))): r for _, r in a.iterrows()}


def cek_matriks(id_s, d):
    """Pemeriksaan 8: K (dan T bila file lokal ada) sama dengan matriks hasil model."""
    s = config.SKENARIO[id_s]
    if s["matriks_kappa"] is None:
        return None, "tidak ada matriks referensi (skenario utama)"
    K = pd.read_csv(s["matriks_kappa"], index_col=0).loc[d["fas"], d["kel"]].to_numpy(float)
    galat_k = float(np.abs(K - d["K"]).max())
    pesan = f"maks |ΔK| = {galat_k:.2e}"
    ok = galat_k <= 1e-8
    path_t = s["matriks_kappa"].with_name("matriks_tbar.csv")
    if path_t.exists():
        T = pd.read_csv(path_t, index_col=0).loc[d["fas"], d["kel"]].to_numpy(float)
        galat_t = float(np.abs(T - d["T"]).max())
        pesan += f", maks |ΔT| = {galat_t:.2e}"
        ok = ok and galat_t <= 1e-6
    else:
        pesan += ", T dilewati (matriks_tbar.csv tidak ada secara lokal)"
    return ok, pesan


def jalankan_pemeriksaan():
    """Kembalikan daftar (nama, lulus, keterangan)."""
    hasil_cek = []
    tambah = hasil_cek.append
    tambah(("BATAS_MENIT config sama dengan BATAS_NETRAL model",
            tuple(config.BATAS_MENIT) == tuple(db.BATAS_NETRAL),
            f"{config.BATAS_MENIT} vs {db.BATAS_NETRAL}"))

    faskes = {f["kode"] for f in _baca("faskes.json")}
    geo = _baca("kelurahan.geojson")
    kode_geo = {f["properties"]["kode"] for f in geo["features"]}
    tambah(("faskes.json berisi 99 faskes", len(faskes) == 99, f"{len(faskes)} faskes"))
    tambah(("kelurahan.geojson berisi 56 kelurahan", len(kode_geo) == 56, f"{len(kode_geo)} fitur"))

    model, csv_cache = {}, {}
    for nama in _file_hasil():
        hasil = _baca(nama)
        id_s, metode = hasil["skenario"]["id"], hasil["skenario"]["metode"]
        if id_s not in model:
            model[id_s] = model_io.muat_model(id_s)
        d = model[id_s]
        label = nama.removeprefix("hasil_").removesuffix(".json")

        salah = cek_struktur(hasil, faskes, kode_geo)
        judul = {"pos_p": "1. tepat p pos, tanpa ganda", "pos_dikenal": "2. semua pos ada di faskes.json",
                 "kel_56": "3. 56 kelurahan, cocok dengan geojson", "melayani": "4. pos_melayani termasuk pos",
                 "cakupan": "5. 0 ≤ cakupan ≤ 1", "p_lengkap": "7. p lengkap 1–20"}
        for k, j in judul.items():
            tambah((f"[{label}] {j}", not salah[k], "; ".join(salah[k][:3]) or "OK"))

        csv_e = None
        if metode == "eksak":
            path = config.SKENARIO[id_s]["eksak"]
            csv_e = csv_cache.setdefault(path, baca_csv_eksak(path))
        sz, sm, sc = cek_angka(hasil, d, csv_e)
        tambah((f"[{label}] 6a. Z1/Z2 = nilai() (tol {TOL_Z})", not sz, "; ".join(sz[:3]) or "OK"))
        tambah((f"[{label}] 6b. metrik = ukuran_netral() (tol {TOL_PCT})", not sm, "; ".join(sm[:3]) or "OK"))
        if csv_e is not None:
            tambah((f"[{label}] 6c. metrik = pct_* di CSV eksak", not sc, "; ".join(sc[:3]) or "OK"))
        bobot_ok = np.allclose([hasil["bobot_kelurahan"][k] for k in d["kel"]], d["w"], atol=1e-8)
        tambah((f"[{label}] bobot_kelurahan = w skenario", bool(bobot_ok), "OK" if bobot_ok else "berbeda"))

    for id_s, d in model.items():
        ok, pesan = cek_matriks(id_s, d)
        if ok is not None:
            tambah((f"[{id_s}] 8. matriks model cocok", ok, pesan))
    return hasil_cek


def cetak_ringkasan():
    """Informasi pelacakan: konfigurasi MOBGOA, titik front per p, jumlah pos inti per p awal."""
    for nama in _file_hasil():
        hasil = _baca(nama)
        label = nama.removeprefix("hasil_").removesuffix(".json")
        sk = hasil["skenario"]
        print(f"\n[{label}] sumber: {sk['sumber']}")
        per_p = {}
        for s in hasil["solusi"]:
            per_p[s["p"]] = per_p.get(s["p"], 0) + 1
        print("  titik front per p: " + ", ".join(f"{p}:{n}" for p, n in sorted(per_p.items())))
        frek = _baca(f"metrik_{label}.json")["frekuensi_faskes"]
        inti = {p: sum(v >= config.AMBANG_POS_INTI for v in f.values()) for p, f in frek.items()}
        print(f"  jumlah pos inti (≥ {config.AMBANG_POS_INTI:g}%) per p awal: "
              + ", ".join(f"{p}:{n}" for p, n in sorted(inti.items(), key=lambda x: int(x[0]))))


def main():
    sys.stdout.reconfigure(encoding="utf-8")   # konsol Windows (cp1252) tidak bisa mencetak "≤"
    hasil = jalankan_pemeriksaan()
    lebar = max(len(n) for n, _, _ in hasil)
    for nama, ok, ket in hasil:
        print(f"{'LULUS' if ok else 'GAGAL'}  {nama.ljust(lebar)}  {ket}")
    cetak_ringkasan()
    gagal = sum(not ok for _, ok, _ in hasil)
    print(f"\n{len(hasil) - gagal}/{len(hasil)} pemeriksaan lulus.")
    sys.exit(1 if gagal else 0)


if __name__ == "__main__":
    main()
