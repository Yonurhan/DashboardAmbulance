"""
MOBGOA (Multi-Objective Binary Grasshopper Optimization Algorithm) untuk Fuzzy MCLP dua tujuan.

Soal (bobot w, kappa, t_bar) dibaca dari data_bersama.py — sama dengan solver eksak.
File ini TIDAK membaca hasil solver sama sekali.

Satu run (satu p, satu seed):
  1. N belalang acak, masing-masing 99 bit dengan tepat p bit = 1.
  2. Nilai Z1 (maks) = sum w_i max_{j buka} kappa_ij,  Z2 (min) = sum w_i min_{j buka} t_bar_ij.
  3. Arsip = solusi tak terdominasi (kapasitas KAPASITAS_ARSIP). Kalau penuh, satu solusi dibuang
     dengan roulette, peluang sebanding jumlah tetangga (daerah padat lebih mungkin dibuang).
     Tetangga dihitung di ruang tujuan yang DINORMALISASI min-max ke [0, 1].
  4. Ulangi ITERASI kali:
       a. target dipilih dari arsip dengan roulette, peluang ~ 1 / jumlah tetangga
       b. langkah GOA: dX_i = c * sum_j c * (ub-lb)/2 * s(d_ij) * (x_j - x_i)/d_ij,
          s(r) = f e^(-r/l) - e^(-r), jarak dinormalisasi ke [1, 4], c turun linear C_MAX -> C_MIN
       c. aturan biner (lihat ATURAN):
            "target" : salin bit target, tiap bit dibalik dengan peluang max(|tanh(B dX)|, 1/J).
                       SATU target dipakai semua belalang dalam satu iterasi (seperti MOGOA asli).
            "target_sendiri" : sama, tetapi SETIAP belalang memilih targetnya sendiri dari arsip
                       (roulette yang sama), supaya belalang menyebar ke seluruh front.
            "bgoa"   : BGOA asli, bit = 1 dengan peluang sigmoid(dX)
            "acak"   : pencarian acak (pembanding)
       d. repair acak: jumlah bit 1 dipaksa tepat p
       e. nilai, perbarui arsip
  5. Isi arsip akhir = front Pareto MOBGOA.

Cara pakai untuk RUN UTAMA (setelah uji pilot menentukan N dan T):
    isi N_BELALANG dan ITERASI di PENGATURAN, lalu:   python mobgoa.py
    hasil: hasil_mobgoa/mobgoa_mentah.jsonl (checkpoint; kalau terhenti jalankan lagi)
           hasil_mobgoa/mobgoa_front.csv    (semua titik arsip akhir setiap p dan seed)
Akurasi dihitung terpisah dengan hitung_akurasi.py.

Kebutuhan:  pip install pandas numpy
"""
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd

import data_bersama as db

# ============================== PENGATURAN ==============================
# Parameter GOA (nilai dari paper GOA/MOGOA asli)
F_GOA, L_GOA = 0.5, 1.5
C_MAX, C_MIN = 1.0, 0.00001
B_TANH = 20.0              # pengali pada |tanh(B dX)| untuk aturan "target"
KAPASITAS_ARSIP = 50       # >= 2 x jumlah titik Pareto terbanyak solver (16 di p = 11)
RADIUS_TETANGGA = 0.1      # di ruang tujuan ternormalisasi [0, 1]

# Run utama — ISI SETELAH UJI PILOT
N_BELALANG = 200          # contoh: 100
ITERASI = 2000             # contoh: 150
ATURAN = "target"          # "target" atau "target_sendiri" (lihat hasil_pilot/pilot_keputusan.json)
P_UTAMA = list(range(1, 21))
SEED_UTAMA = list(range(1, 31))     # 30 seed
FOLDER_HASIL = "hasil_mobgoa"
# ========================================================================


# ------------------------------------------------------------------ dasar
def evaluasi(X, K, T, w):
    """X: (N, J) bool. Kembalikan Z1 (N,) dan Z2 (N,)."""
    Kx = np.where(X[:, :, None], K[None, :, :], -np.inf).max(axis=1)     # (N, I)
    Tx = np.where(X[:, :, None], T[None, :, :], np.inf).min(axis=1)
    return Kx @ w, Tx @ w


def non_dominasi(z1, z2):
    """Indeks solusi tak terdominasi (Z1 maks, Z2 min). Solusi dengan nilai tujuan kembar disimpan satu."""
    z1r = np.round(z1, 12)
    urut = np.lexsort((z2, -z1r))          # Z1 turun, lalu Z2 naik
    hasil, terbaik = [], np.inf
    for k in urut:
        if z2[k] < terbaik - 1e-12:
            hasil.append(k)
            terbaik = z2[k]
    return np.array(hasil, dtype=int)


def repair(X, p, rng):
    """Jumlah bit 1 tiap baris dipaksa tepat p (tambah/buang acak)."""
    for a in range(X.shape[0]):
        on = np.flatnonzero(X[a])
        if len(on) > p:
            X[a, rng.choice(on, len(on) - p, replace=False)] = False
        elif len(on) < p:
            off = np.flatnonzero(~X[a])
            X[a, rng.choice(off, p - len(on), replace=False)] = True
    return X


def acak_sah(N, J, p, rng):
    X = np.zeros((N, J), bool)
    for a in range(N):
        X[a, rng.choice(J, p, replace=False)] = True
    return X


class Arsip:
    def __init__(self, kapasitas, radius, rng):
        self.kap, self.radius, self.rng = kapasitas, radius, rng
        self.X = None
        self.z1 = np.zeros(0)
        self.z2 = np.zeros(0)

    def tetangga(self):
        """Jumlah tetangga tiap solusi (termasuk dirinya), di ruang tujuan ternormalisasi min-max."""
        f = np.column_stack([self.z1, self.z2])
        rentang = f.max(0) - f.min(0)
        rentang[rentang == 0] = 1.0
        f = (f - f.min(0)) / rentang
        D = np.sqrt(((f[:, None, :] - f[None, :, :]) ** 2).sum(2))
        return (D <= self.radius).sum(1)

    def perbarui(self, X, z1, z2):
        if self.X is not None:
            X = np.vstack([self.X, X])
            z1 = np.concatenate([self.z1, z1])
            z2 = np.concatenate([self.z2, z2])
        _, unik = np.unique(X, axis=0, return_index=True)     # buang susunan kembar
        unik = np.sort(unik)
        X, z1, z2 = X[unik], z1[unik], z2[unik]
        nd = non_dominasi(z1, z2)
        self.X, self.z1, self.z2 = X[nd], z1[nd], z2[nd]
        while len(self.z1) > self.kap:                        # penuh: buang dari daerah padat
            n = self.tetangga().astype(float)
            k = self.rng.choice(len(n), p=n / n.sum())
            m = np.ones(len(n), bool)
            m[k] = False
            self.X, self.z1, self.z2 = self.X[m], self.z1[m], self.z2[m]

    def pilih_target(self):
        pr = 1.0 / self.tetangga()
        return self.X[self.rng.choice(len(pr), p=pr / pr.sum())]

    def pilih_target_banyak(self, n):
        """n target sekaligus (boleh berulang), satu untuk tiap belalang."""
        pr = 1.0 / self.tetangga()
        return self.X[self.rng.choice(len(pr), size=n, p=pr / pr.sum())]


def langkah_goa(X, c):
    """dX untuk setiap belalang dan setiap bit (ruang biner: ub - lb = 1)."""
    N = X.shape[0]
    P = X.astype(float)
    # jarak Euclid antar-belalang; untuk bit 0/1: d_ij^2 = |x_i| + |x_j| - 2 x_i.x_j (bilangan bulat, eksak)
    G = P @ P.T
    n1 = np.diag(G)
    dist = np.sqrt(np.maximum(n1[:, None] + n1[None, :] - 2.0 * G, 0.0))
    luar = ~np.eye(N, dtype=bool)
    lo, hi = dist[luar].min(), dist[luar].max()
    dn = 1 + 3 * (dist - lo) / (hi - lo) if hi > lo else np.full_like(dist, 2.5)   # jarak -> [1, 4]
    s = F_GOA * np.exp(-dn / L_GOA) - np.exp(-dn)
    s[~luar] = 0.0
    koef = np.where(dist > 0, s / np.where(dist > 0, dist, 1.0), 0.0)
    # sum_j koef_ij (x_j - x_i)  =  koef @ P  -  (sum_j koef_ij) x_i
    return c * (c * 0.5 * (koef @ P - koef.sum(axis=1, keepdims=True) * P))


# ------------------------------------------------------------------ satu run
def jalankan(K, T, w, p, seed, N, iterasi, aturan="target"):
    """Satu run MOBGOA. Kembalikan (X_arsip, Z1, Z2, detik). Urut Z1 turun."""
    if aturan not in ("target", "target_sendiri", "bgoa", "acak"):
        raise ValueError(f"aturan tidak dikenal: {aturan}")
    mulai = time.perf_counter()
    rng = np.random.default_rng(seed)
    J = K.shape[0]
    X = acak_sah(N, J, p, rng)
    arsip = Arsip(KAPASITAS_ARSIP, RADIUS_TETANGGA, rng)
    z1, z2 = evaluasi(X, K, T, w)
    arsip.perbarui(X, z1, z2)
    for t in range(1, iterasi + 1):
        c = C_MAX - t * (C_MAX - C_MIN) / iterasi
        if aturan == "acak":
            Xb = acak_sah(N, J, p, rng)
        else:
            dX = langkah_goa(X, c)
            r = rng.random((N, J))
            if aturan == "target":
                tg = arsip.pilih_target()
                peluang = np.maximum(np.abs(np.tanh(B_TANH * dX)), 1.0 / J)
                Xb = tg[None, :] ^ (r < peluang)
            elif aturan == "target_sendiri":
                tg = arsip.pilih_target_banyak(N)
                peluang = np.maximum(np.abs(np.tanh(B_TANH * dX)), 1.0 / J)
                Xb = tg ^ (r < peluang)
            else:   # "bgoa"
                Xb = r < 1.0 / (1.0 + np.exp(-dX))
            Xb = repair(Xb.copy(), p, rng)
        X = Xb
        z1, z2 = evaluasi(X, K, T, w)
        arsip.perbarui(X, z1, z2)
    urut = np.argsort(-arsip.z1)
    return arsip.X[urut], arsip.z1[urut], arsip.z2[urut], time.perf_counter() - mulai


def tanda_konfigurasi(d):
    """Sidik jari data + parameter GOA, supaya checkpoint dari pengaturan lain tidak tercampur."""
    isi = {**d["param"], "F": F_GOA, "L": L_GOA, "CMAX": C_MAX, "CMIN": C_MIN, "B": B_TANH,
           "KAP": KAPASITAS_ARSIP, "RADIUS": RADIUS_TETANGGA}
    return hashlib.sha256(json.dumps(isi, sort_keys=True).encode()).hexdigest()[:16]


def jalankan_banyak(daftar, file_cp, keterangan=""):
    """daftar: list of dict(kunci, p, seed, N, iterasi, aturan, tahap). Hasil disimpan per run (checkpoint)."""
    d = db.siapkan(cetak=True)
    K, T = d["MASUKAN"]["fuzzy"]
    w, fas = d["w"], d["fas"]
    tanda = tanda_konfigurasi(d)
    os.makedirs(os.path.dirname(file_cp) or ".", exist_ok=True)
    selesai = {}
    if os.path.exists(file_cp):
        with open(file_cp, encoding="utf-8") as f:
            for baris in f:
                if baris.strip():
                    r = json.loads(baris)
                    if r["tanda"] == tanda:
                        selesai[r["kunci"]] = r
    sisa = [x for x in daftar if x["kunci"] not in selesai]
    print(f"{keterangan}: {len(daftar)} run, {len(daftar) - len(sisa)} sudah ada di checkpoint, {len(sisa)} dijalankan")
    for n, x in enumerate(sisa, 1):
        Xa, z1, z2, detik = jalankan(K, T, w, x["p"], x["seed"], x["N"], x["iterasi"], x["aturan"])
        r = {**x, "tanda": tanda, "detik": round(detik, 3), "jumlah_titik": len(z1),
             "titik": [{"Z1": float(a), "Z2": float(b), "buka": [fas[j] for j in np.flatnonzero(xx)]}
                       for a, b, xx in zip(z1, z2, Xa)]}
        with open(file_cp, "a", encoding="utf-8") as f:
            f.write(json.dumps(r) + "\n")
        selesai[x["kunci"]] = r
        print(f"  [{n}/{len(sisa)}] {x['kunci']}: {len(z1)} titik, {detik:.1f} detik", flush=True)
    return [selesai[x["kunci"]] for x in daftar]


def ke_tabel(hasil):
    baris = []
    for r in hasil:
        for n, t in enumerate(r["titik"], 1):
            baris.append({"tahap": r.get("tahap", ""), "aturan": r["aturan"], "N": r["N"], "iterasi": r["iterasi"],
                          "p": r["p"], "seed": r["seed"], "titik_ke": n, "Z1": t["Z1"], "Z2_menit": t["Z2"],
                          "detik_run": r["detik"], "faskes_dibuka": ";".join(t["buka"])})
    return pd.DataFrame(baris)


def main():
    if ATURAN not in ("target", "target_sendiri"):
        db.berhenti("ATURAN untuk run utama harus 'target' atau 'target_sendiri'")
    if N_BELALANG is None or ITERASI is None:
        db.berhenti("isi dulu N_BELALANG dan ITERASI di PENGATURAN mobgoa.py (dari hasil uji_pilot.py)")
    daftar = [dict(kunci=f"utama|{ATURAN}|N{N_BELALANG}|T{ITERASI}|p{p}|s{s}", tahap="utama", p=p, seed=s,
                   N=N_BELALANG, iterasi=ITERASI, aturan=ATURAN) for p in P_UTAMA for s in SEED_UTAMA]
    hasil = jalankan_banyak(daftar, os.path.join(FOLDER_HASIL, "mobgoa_mentah.jsonl"), "Run utama MOBGOA")
    ke_tabel(hasil).to_csv(os.path.join(FOLDER_HASIL, "mobgoa_front.csv"), index=False)
    print(f"Selesai. Hasil: {FOLDER_HASIL}/mobgoa_front.csv  -> lanjut: python hitung_akurasi.py")


if __name__ == "__main__":
    main()