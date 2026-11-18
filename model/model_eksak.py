"""
MODEL EKSAK (versi 2): Fuzzy MCLP dua tujuan (epsilon-constraint) + dua model pembanding.
Bahan masukan (bobot, TFN, kappa, t_bar) diambil dari data_bersama.py — sama dengan yang dipakai MOBGOA.

Tiga model, untuk setiap p:
  klasik  : maks sum w_i [min_j tM_ij <= BATAS_KLASIK]   (lalu min rata-rata tM sebagai pemecah seri)
  sigmoid : Z1 = sum w_i max_j phi(tM_ij),  Z2 = sum w_i min_j tM_ij      -> front Pareto
  fuzzy   : Z1 = sum w_i max_j kappa_ij,    Z2 = sum w_i min_j t_bar_ij   -> front Pareto
Front Pareto dengan epsilon-constraint dua tahap:
  tahap 1: maks Z1 dengan Z2 <= eps;  tahap 2: min Z2 dengan Z1 >= Z1*;  lalu eps = Z2 - ETA, ulangi.

Kebutuhan (sekali saja):  pip install pandas numpy "pulp==3.3.2" highspy
Cara pakai:  taruh model_eksak.py, data_bersama.py, checkpoint_waktu_tempuh_final.csv, dan
             dataset-penduduk-usia-kelurahan-bekasi-2025.csv dalam satu folder, lalu:
                 python model_eksak.py
             Kalau terhenti, jalankan lagi: hasil yang sudah selesai tidak dihitung ulang.

Hasil per skenario (folder hasil_model_eksak/<skenario>/):
  front_pareto.csv, perbandingan_model.csv, detail_kelurahan.csv, log_waktu_hitung.csv,
  bobot_kelurahan.csv, koreksi_tfn.csv, matriks_kappa.csv, matriks_tbar.csv,
  parameter_model.json, hasil_sementara.jsonl (checkpoint, jangan diedit)
"""
import hashlib
import itertools
import json
import os
import platform
import sys
import time

import numpy as np
import pandas as pd
import pulp

import data_bersama as db

# ============================== PENGATURAN ==============================
# Skenario: "utama" = nilai di data_bersama.py (15/40 menit, rho 2,93).
# Uji sensitivitas cukup menimpa nilai yang berubah.
SKENARIO = {
    "utama": {},
    "jakarta10": {"t_baik": 10.0, "batas_klasik": 10.0},   # target respons Jakarta 10 menit (Brice dkk., 2022)
    "rho1": {"rho": 1.0},                                  # lansia tidak diberi bobot lebih
}
SKENARIO_DIJALANKAN = ["utama"]          # contoh: ["utama", "jakarta10", "rho1"]

P_DIJALANKAN = list(range(1, 21))        # p = 1..20
MODEL_DIJALANKAN = ["klasik", "sigmoid", "fuzzy"]

ETA = 1e-5              # langkah epsilon (menit)
MAKS_TITIK = 2000       # pengaman jumlah titik Pareto per model per p
UJI_ENUMERASI_P = [1, 2]   # p kecil dicek ulang dengan mencoba SEMUA kombinasi
BOBOT_UKURAN_NETRAL = "permintaan"   # "permintaan" (w_i) atau "penduduk" (P_i)
FOLDER_HASIL = "hasil_model_eksak"
# ========================================================================

TOL = 1e-6
URUTAN_MODEL = {"klasik": 0, "sigmoid": 1, "fuzzy": 2}


# ------------------------------------------------------------------ solver
def pilih_solver():
    try:
        if pulp.HiGHS(msg=False).available():
            return (lambda: pulp.HiGHS(msg=False, gapRel=0.0, gapAbs=1e-9)), "HiGHS (highspy)"
    except Exception:  # noqa: BLE001
        pass
    if pulp.PULP_CBC_CMD(msg=False).available():
        return (lambda: pulp.PULP_CBC_CMD(msg=False, gapRel=0.0, gapAbs=1e-9)), "CBC"
    db.berhenti("tidak ada solver. Jalankan:  pip install highspy")


class ModelLokasi:
    """y_j = 1 kalau faskes j dibuka (sum y = p).
       x_ij: kelurahan i memakai kappa dari faskes j (sum_j x_ij <= 1, x_ij <= y_j)  -> maks kappa
       z_ij: kelurahan i dilayani faskes j untuk waktu (sum_j z_ij = 1, z_ij <= y_j) -> min waktu"""

    def __init__(self, K, T, w, p, buat_solver):
        J, I = K.shape
        self.J, self.buat_solver = J, buat_solver
        self.y = [pulp.LpVariable(f"y_{j}", cat="Binary") for j in range(J)]
        x = [[pulp.LpVariable(f"x_{j}_{i}", 0, 1) for i in range(I)] for j in range(J)]
        z = [[pulp.LpVariable(f"z_{j}_{i}", 0, 1) for i in range(I)] for j in range(J)]
        self.Z1 = pulp.lpSum(float(w[i] * K[j, i]) * x[j][i] for j in range(J) for i in range(I) if K[j, i] > 0)
        self.Z2 = pulp.lpSum(float(w[i] * T[j, i]) * z[j][i] for j in range(J) for i in range(I))
        self.dasar = [pulp.lpSum(self.y) == p]
        for i in range(I):
            self.dasar.append(pulp.lpSum(x[j][i] for j in range(J)) <= 1)
            self.dasar.append(pulp.lpSum(z[j][i] for j in range(J)) == 1)
        for j in range(J):
            for i in range(I):
                self.dasar.append(x[j][i] <= self.y[j])
                self.dasar.append(z[j][i] <= self.y[j])

    def selesaikan(self, arah, tujuan, tambahan):
        m = pulp.LpProblem("lokasi", arah)
        m += tujuan
        for c in self.dasar + tambahan:
            m += c
        m.solve(self.buat_solver())
        status = pulp.LpStatus[m.status]
        if status == "Infeasible":
            return None
        if status != "Optimal":
            db.berhenti(f"solver mengembalikan status '{status}' (bukan Optimal/Infeasible)")
        return tuple(j for j in range(self.J) if self.y[j].value() > 0.5)

    def leksikografis(self, eps=None):
        batas = [] if eps is None else [self.Z2 <= eps]
        buka = self.selesaikan(pulp.LpMaximize, self.Z1, batas)
        if buka is None:
            return None
        z1 = pulp.value(self.Z1)
        return self.selesaikan(pulp.LpMinimize, self.Z2, batas + [self.Z1 >= z1 - 1e-9])


def front_pareto(K, T, w, p, buat_solver):
    mdl = ModelLokasi(K, T, w, p, buat_solver)
    hasil, eps = [], None
    while len(hasil) < MAKS_TITIK:
        buka = mdl.leksikografis(eps)
        if buka is None:
            break
        if len(buka) != p:
            db.berhenti(f"solver membuka {len(buka)} faskes, padahal p = {p}")
        z1, z2 = db.nilai(buka, K, T, w)
        if hasil and not (z2 < hasil[-1][1] - ETA / 2 and z1 < hasil[-1][0] + TOL):
            db.berhenti(f"urutan front tidak wajar di p={p}: {hasil[-1][:2]} lalu {(z1, z2)}")
        hasil.append((z1, z2, buka))
        print(f"      titik {len(hasil):3d}: Z1 = {z1:.6f}  Z2 = {z2:.4f} menit", flush=True)
        eps = z2 - ETA
    else:
        print(f"  PERINGATAN: MAKS_TITIK ({MAKS_TITIK}) tercapai, front mungkin belum lengkap")
    return hasil


def front_enumerasi(K, T, w, p):
    """Semua kombinasi p dari J faskes -> titik tak terdominasi (untuk mengecek solver)."""
    J = K.shape[0]
    z1s, z2s = [], []
    for kombinasi in itertools.combinations(range(J), p):
        b = list(kombinasi)
        z1s.append(w @ K[b].max(axis=0))
        z2s.append(w @ T[b].min(axis=0))
    z1s, z2s = np.round(np.array(z1s), 10), np.array(z2s)
    titik, terbaik = [], np.inf
    for k in np.lexsort((z2s, -z1s)):
        if z2s[k] < terbaik - ETA / 2:
            titik.append((float(z1s[k]), float(z2s[k])))
            terbaik = z2s[k]
    return titik


# ------------------------------------------------------------------ satu skenario
def jalankan_skenario(nama, ubah, buat_solver, nama_solver):
    print(f"\n=================== SKENARIO: {nama} ===================")
    folder = os.path.join(FOLDER_HASIL, nama)
    os.makedirs(folder, exist_ok=True)
    jalur = lambda f: os.path.join(folder, f)
    d = db.siapkan(**ubah)
    fas, kel = d["fas"], d["kel"]
    J, I = len(fas), len(kel)
    w = d["w"]
    bobot_netral = w if BOBOT_UKURAN_NETRAL == "permintaan" else d["P"] / d["P"].sum()

    # file pendukung
    pd.DataFrame({"kode_kelurahan": kel, "kecamatan": d["kec_k"], "kelurahan": d["nama_k"],
                  "penduduk_P": d["P"].astype(int), "lansia65_L": d["L"].astype(int),
                  "permintaan_d": d["dem"].round(2), "bobot_w": w.round(8)}).to_csv(jalur("bobot_kelurahan.csv"), index=False)
    jj, ii = np.where(d["tukar"] | d["naik"] | d["turun"])
    pd.DataFrame({"id_faskes": [fas[j] for j in jj], "kode_kelurahan": [kel[i] for i in ii],
                  "kelurahan": [d["nama_k"][i] for i in ii],
                  "opt_asli": d["OPT"][jj, ii], "bg_asli": d["BG"][jj, ii], "pes_asli": d["PES"][jj, ii],
                  "tL": d["tL"][jj, ii], "tM": d["tM"][jj, ii], "tU": d["tU"][jj, ii],
                  "jenis": np.where(d["tukar"][jj, ii], "opt>pes ditukar",
                                    np.where(d["naik"][jj, ii], "tM<tL: tM=tL", "tM>tU: tM=tU"))
                  }).to_csv(jalur("koreksi_tfn.csv"), index=False)
    K_f, T_f = d["MASUKAN"]["fuzzy"]
    pd.DataFrame(K_f, index=fas, columns=kel).round(8).to_csv(jalur("matriks_kappa.csv"))
    pd.DataFrame(T_f, index=fas, columns=kel).round(6).to_csv(jalur("matriks_tbar.csv"))

    param = {**d["param"], "skenario": nama, "ETA": ETA}
    tanda = hashlib.sha256(json.dumps(param, sort_keys=True).encode()).hexdigest()[:16]
    with open(jalur("parameter_model.json"), "w", encoding="utf-8") as f:
        json.dump({**param, "alpha": d["alpha"], "gamma": d["gamma"], "tanda_checkpoint": tanda,
                   "solver": nama_solver, "bobot_ukuran_netral": BOBOT_UKURAN_NETRAL,
                   "versi": {"python": platform.python_version(), "pulp": pulp.__version__,
                             "numpy": np.__version__, "pandas": pd.__version__},
                   "koreksi_tfn": {"opt_gt_pes": int(d["tukar"].sum()), "tM_naik_ke_tL": int(d["naik"].sum()),
                                   "tM_turun_ke_tU": int(d["turun"].sum())}}, f, indent=2, ensure_ascii=False)

    # checkpoint
    file_cp = jalur("hasil_sementara.jsonl")
    selesai = {}
    if os.path.exists(file_cp):
        lain = 0
        with open(file_cp, encoding="utf-8") as f:
            for baris in f:
                if baris.strip():
                    r = json.loads(baris)
                    if r["tanda"] == tanda:
                        selesai[(r["model"], r["p"])] = r
                    else:
                        lain += 1
        print(f"Checkpoint: {len(selesai)} hasil dipakai ulang"
              + (f", {lain} hasil lama diabaikan (data/parameter berbeda)" if lain else ""))

    for p in P_DIJALANKAN:
        for model in MODEL_DIJALANKAN:
            if (model, p) in selesai:
                continue
            K, T = d["MASUKAN"][model]
            mulai = time.time()
            print(f"\n[{nama} | p = {p:2d}] model {model} ...", flush=True)
            if model == "klasik":
                buka = ModelLokasi(K, T, w, p, buat_solver).leksikografis()
                z1, z2 = db.nilai(buka, K, T, w)
                titik = [(z1, z2, buka)]
                print(f"      cakupan = {z1:.6f}  rata-rata tM = {z2:.4f} menit")
            else:
                titik = front_pareto(K, T, w, p, buat_solver)
            detik = time.time() - mulai

            uji = ""
            if p in UJI_ENUMERASI_P:
                if model == "klasik":
                    terbaik = max(db.nilai(c, K, T, w)[0] for c in itertools.combinations(range(J), p))
                    ok = abs(terbaik - titik[0][0]) < TOL
                else:
                    benar = front_enumerasi(K, T, w, p)
                    ok = len(benar) == len(titik) and all(abs(a[0] - b[0]) < TOL and abs(a[1] - b[1]) < 1e-4
                                                          for a, b in zip(benar, titik))
                uji = "LULUS" if ok else "GAGAL"
                print(f"      cek enumerasi semua kombinasi: {uji}")
                if not ok:
                    db.berhenti(f"hasil solver berbeda dengan enumerasi pada model {model}, p = {p}")

            r = {"tanda": tanda, "model": model, "p": p, "detik": round(detik, 2), "solver": nama_solver,
                 "uji_enumerasi": uji,
                 "titik": [{"Z1": z1, "Z2": z2, "buka": [fas[j] for j in b]} for z1, z2, b in titik]}
            with open(file_cp, "a", encoding="utf-8") as f:
                f.write(json.dumps(r) + "\n")
            selesai[(model, p)] = r
            print(f"      selesai: {len(titik)} titik, {detik:.1f} detik")
            tulis_hasil(selesai, d, bobot_netral, jalur)

    tulis_hasil(selesai, d, bobot_netral, jalur)


def tulis_hasil(selesai, d, bobot_netral, jalur):
    fas, kel, w = d["fas"], d["kel"], d["w"]
    D = d["D"]
    K_f, T_f = d["MASUKAN"]["fuzzy"]
    idx = {f: j for j, f in enumerate(fas)}
    kunci = sorted(selesai, key=lambda k: (k[1], URUTAN_MODEL.get(k[0], 9)))
    baris_front, baris_wakil, baris_detail, baris_log = [], [], [], []
    for model, p in kunci:
        r = selesai[(model, p)]
        baris_log.append({"model": model, "p": p, "jumlah_titik": len(r["titik"]), "detik": r["detik"],
                          "solver": r["solver"], "uji_enumerasi": r["uji_enumerasi"]})
        for n, t in enumerate(r["titik"], 1):
            buka = [idx[f] for f in t["buka"]]
            z1f, z2f = db.nilai(buka, K_f, T_f, w)
            baris = {"model": model, "p": p, "titik_ke": n, "Z1_model": round(t["Z1"], 8),
                     "Z2_model_menit": round(t["Z2"], 6), "Z1_fuzzy": round(z1f, 8), "Z2_fuzzy_menit": round(z2f, 6),
                     **db.ukuran_netral(buka, D, bobot_netral),
                     "faskes_dibuka": ";".join(t["buka"]),
                     "nama_faskes_dibuka": ";".join(d["nama_f"][j] for j in buka)}
            baris_front.append(baris)
            if n == 1:
                baris_wakil.append(baris)
                tm, kap = D["bg"][buka], K_f[buka]
                for i in range(len(kel)):
                    j = buka[int(np.argmin(tm[:, i]))]
                    baris_detail.append({
                        "model": model, "p": p, "kode_kelurahan": kel[i], "kecamatan": d["kec_k"][i],
                        "kelurahan": d["nama_k"][i], "bobot_w": round(float(w[i]), 8),
                        "faskes_tercepat_bg": fas[j], "nama_faskes": d["nama_f"][j],
                        "menit_opt": round(float(D["opt"][j, i]), 3), "menit_bg": round(float(D["bg"][j, i]), 3),
                        "menit_pes": round(float(D["pes"][j, i]), 3),
                        "phi_bg": round(float(db.phi(D["bg"][j, i], d["alpha"], d["gamma"])), 6),
                        "kappa_terbesar": round(float(kap[:, i].max()), 6),
                        "faskes_kappa_terbesar": fas[buka[int(np.argmax(kap[:, i]))]]})
    pd.DataFrame(baris_front).to_csv(jalur("front_pareto.csv"), index=False)
    pd.DataFrame(baris_wakil).to_csv(jalur("perbandingan_model.csv"), index=False)
    pd.DataFrame(baris_detail).to_csv(jalur("detail_kelurahan.csv"), index=False)
    pd.DataFrame(baris_log).to_csv(jalur("log_waktu_hitung.csv"), index=False)


def main():
    t0 = time.time()
    for s in SKENARIO_DIJALANKAN:
        if s not in SKENARIO:
            db.berhenti(f"skenario '{s}' tidak dikenal. Pilihan: {list(SKENARIO)}")
    for m in MODEL_DIJALANKAN:
        if m not in URUTAN_MODEL:
            db.berhenti(f"model '{m}' tidak dikenal. Pilihan: {list(URUTAN_MODEL)}")
    buat_solver, nama_solver = pilih_solver()
    print(f"Solver: {nama_solver} | PuLP {pulp.__version__} | Python {platform.python_version()}")
    for s in SKENARIO_DIJALANKAN:
        jalankan_skenario(s, SKENARIO[s], buat_solver, nama_solver)
    print(f"\nSEMUA SELESAI dalam {(time.time() - t0) / 60:.1f} menit. Hasil di folder '{FOLDER_HASIL}'.")


if __name__ == "__main__":
    main()