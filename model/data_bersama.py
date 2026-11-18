"""
DATA BERSAMA — dipakai oleh model_eksak.py DAN mobgoa.py.

File ini hanya menyiapkan "soal" (bahan masukan), bukan mencari jawaban:
  1. Membaca waktu tempuh Google (3 kondisi) dan data penduduk, lalu memeriksanya.
  2. Bobot permintaan   d_i = P_i + (rho - 1) L_i ,  w_i = d_i / sum(d)
  3. TFN waktu tempuh   (tL, tM, tU) = (OPTIMISTIC 03.00, BEST_GUESS 11.00, PESSIMISTIC 18.00)
       - kalau opt > pes: keduanya ditukar (tL = yang kecil, tU = yang besar)
       - kalau tM di luar [tL, tU]: tM digeser ke batas terdekat
  4. Sigmoid cakupan    phi(t) = 1 / (1 + exp(-alpha (t - gamma))),  phi(T_BAIK) = 0,95 dan phi(T_BURUK) = 0,05
  5. kappa_ij = int phi^2 (1-phi) mu dt / int phi (1-phi) mu dt   (centroid),   t_bar_ij = (tL + tM + tU) / 3
  6. Fungsi bantu: nilai Z1/Z2 sebuah susunan pos, dan ukuran netral.

Karena solver dan MOBGOA sama-sama memanggil siapkan() dari file ini, keduanya dijamin
mengerjakan soal yang persis sama. MOBGOA TIDAK membaca hasil solver.

Kebutuhan:  pip install pandas numpy
"""
import hashlib
import math
import os
import re
import sys

import numpy as np
import pandas as pd

# ============================== PENGATURAN DATA ==============================
FILE_WAKTU = "checkpoint_waktu_tempuh_final.csv"
KOLOM_OPT = "menit_optimistic_0300"
KOLOM_BG = "menit_bestguess_1100"
KOLOM_PES = "menit_pessimistic_1800"
KOLOM_STATUS = {KOLOM_OPT: "status_optimistic_0300",
                KOLOM_BG: "status_bestguess_1100",
                KOLOM_PES: "status_pessimistic_1800"}

FILE_PENDUDUK = "dataset-penduduk-usia-kelurahan-bekasi-2025.csv"
KOLOM_P = "total_penduduk"
KOLOM_L = "lansia_total"          # lansia 65+

# Nilai utama (bisa ditimpa per skenario lewat siapkan(...))
RHO = 2.93                        # rasio laju panggilan lansia 65+ (Krammel dkk., 2023)
T_BAIK, PHI_BAIK = 15.0, 0.95     # 15 menit -> derajat cakupan 0,95
T_BURUK, PHI_BURUK = 40.0, 0.05   # 40 menit -> derajat cakupan 0,05
BATAS_KLASIK = 15.0               # MCLP klasik: tercakup kalau tM <= 15 menit

# Ukuran netral: batas TETAP untuk semua skenario, supaya hasil antarskenario bisa dibandingkan
BATAS_NETRAL = (15.0, 40.0)
TITIK_INTEGRAL = 4001             # jumlah titik integral numerik kappa
# =============================================================================

KONDISI = {"opt": "optimistic 03.00", "bg": "best guess 11.00", "pes": "pessimistic 18.00"}


def normal(s):
    return re.sub(r"[^A-Z]", "", str(s).upper())


def berhenti(pesan):
    print("\nBERHENTI:", pesan)
    sys.exit(1)


def sidik_jari(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ baca data
def baca_data():
    for f in (FILE_WAKTU, FILE_PENDUDUK):
        if not os.path.exists(f):
            berhenti(f"file '{f}' tidak ditemukan di folder {os.getcwd()}")
    a = pd.read_csv(FILE_WAKTU)
    pdk = pd.read_csv(FILE_PENDUDUK)

    perlu = ["id_faskes", "nama_faskes", "kode_kelurahan", "kecamatan_tujuan", "kelurahan_tujuan",
             KOLOM_OPT, KOLOM_BG, KOLOM_PES, *KOLOM_STATUS.values()]
    hilang = [k for k in perlu if k not in a.columns]
    if hilang:
        berhenti(f"kolom {hilang} tidak ada di {FILE_WAKTU}")
    hilang = [k for k in ("kecamatan", "kelurahan", KOLOM_P, KOLOM_L) if k not in pdk.columns]
    if hilang:
        berhenti(f"kolom {hilang} tidak ada di {FILE_PENDUDUK}")

    fas = list(dict.fromkeys(a["id_faskes"]))
    kel = list(dict.fromkeys(a["kode_kelurahan"]))
    J, I = len(fas), len(kel)
    if a.duplicated(["id_faskes", "kode_kelurahan"]).any():
        berhenti(f"ada pasangan faskes-kelurahan ganda di {FILE_WAKTU}")
    if len(a) != J * I:
        berhenti(f"{FILE_WAKTU} berisi {len(a)} baris, harus {J} x {I} = {J * I}")
    if (J, I) != (99, 56):
        print(f"  PERINGATAN: biasanya 99 x 56, di sini {J} x {I}.")

    def matriks(kolom):
        st = a[KOLOM_STATUS[kolom]] != "ROUTE_EXISTS"
        if st.any():
            berhenti(f"{st.sum()} pasangan di kolom {KOLOM_STATUS[kolom]} bukan ROUTE_EXISTS")
        m = a.pivot(index="id_faskes", columns="kode_kelurahan", values=kolom).loc[fas, kel].to_numpy(float)
        if not np.isfinite(m).all() or (m < 0).any():
            berhenti(f"ada nilai kosong/negatif di kolom {kolom}")
        return m

    OPT, BG, PES = matriks(KOLOM_OPT), matriks(KOLOM_BG), matriks(KOLOM_PES)

    # satu faskes / kelurahan harus punya satu koordinat saja
    for kunci, la, lo in (("id_faskes", "lat_faskes", "lon_faskes"), ("kode_kelurahan", "lat_kelurahan", "lon_kelurahan")):
        if la in a.columns and a.groupby(kunci)[[la, lo]].nunique().max().max() > 1:
            berhenti(f"ada {kunci} dengan lebih dari satu koordinat")

    info_f = a.drop_duplicates("id_faskes").set_index("id_faskes").loc[fas]
    info_k = a.drop_duplicates("kode_kelurahan").set_index("kode_kelurahan").loc[kel]

    # penduduk: dicocokkan lewat nama kecamatan + kelurahan yang dinormalisasi
    pdk["_kunci"] = pdk["kecamatan"].map(normal) + "|" + pdk["kelurahan"].map(normal)
    if pdk["_kunci"].duplicated().any():
        berhenti(f"ada kelurahan ganda di {FILE_PENDUDUK}")
    kunci_k = (info_k["kecamatan_tujuan"].map(normal) + "|" + info_k["kelurahan_tujuan"].map(normal)).tolist()
    ada = set(pdk["_kunci"])
    tidak = [f"{kel[i]} {info_k['kelurahan_tujuan'].iloc[i]}" for i in range(I) if kunci_k[i] not in ada]
    if tidak or len(pdk) != I:
        berhenti(f"nama kelurahan tidak cocok dengan {FILE_PENDUDUK}: {tidak} (baris penduduk: {len(pdk)})")
    pdk = pdk.set_index("_kunci").loc[kunci_k]
    P = pdk[KOLOM_P].to_numpy(float)
    L = pdk[KOLOM_L].to_numpy(float)
    if (P <= 0).any() or (L < 0).any() or (L > P).any():
        berhenti("nilai penduduk/lansia tidak wajar (P <= 0, L < 0, atau L > P)")

    kat = info_f["kategori_faskes"].tolist() if "kategori_faskes" in info_f.columns else [""] * J
    return dict(fas=fas, kel=kel, OPT=OPT, BG=BG, PES=PES, P=P, L=L,
                nama_f=info_f["nama_faskes"].tolist(), kat_f=kat,
                kec_k=info_k["kecamatan_tujuan"].tolist(), nama_k=info_k["kelurahan_tujuan"].tolist())


# ------------------------------------------------------------------ rumus
def alpha_gamma(t_baik, phi_baik, t_buruk, phi_buruk):
    """Dua titik jangkar -> alpha (kecuraman, negatif) dan gamma (titik tengah, phi = 0,5)."""
    l1 = math.log(1 / phi_baik - 1)
    l2 = math.log(1 / phi_buruk - 1)
    alpha = -(l2 - l1) / (t_buruk - t_baik)
    gamma = t_baik + l1 / alpha
    return alpha, gamma


def phi(t, alpha, gamma):
    return 1.0 / (1.0 + np.exp(-alpha * (np.asarray(t, float) - gamma)))


def koreksi_tfn(OPT, BG, PES):
    tL = np.minimum(OPT, PES)
    tU = np.maximum(OPT, PES)
    tM = np.clip(BG, tL, tU)
    return tL, tM, tU


def _trapesium(y, x):
    return np.sum((y[:, 1:] + y[:, :-1]) * (x[:, 1:] - x[:, :-1]), axis=1) / 2.0


def hitung_kappa(tL, tM, tU, alpha, gamma, n=TITIK_INTEGRAL, potong=400):
    l, m, u = tL.ravel(), tM.ravel(), tU.ravel()
    K = np.empty(l.size)
    for s in range(0, l.size, potong):
        ll, mm, uu = l[s:s + potong, None], m[s:s + potong, None], u[s:s + potong, None]
        lebar = uu - ll
        t = ll + lebar * np.linspace(0.0, 1.0, n)[None, :]
        with np.errstate(divide="ignore", invalid="ignore"):
            kiri = np.where(mm > ll, (t - ll) / (mm - ll), 1.0)
            kanan = np.where(uu > mm, (uu - t) / (uu - mm), 1.0)
        mu = np.clip(np.minimum(kiri, kanan), 0.0, 1.0)
        f = phi(t, alpha, gamma)
        v = f * (1 - f) * mu
        atas, bawah = _trapesium(f * v, t), _trapesium(v, t)
        pm = phi(mm[:, 0], alpha, gamma)
        sempit = (lebar[:, 0] < 1e-9) | (bawah <= 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            K[s:s + potong] = np.where(sempit, pm, atas / bawah)
    K = K.reshape(tL.shape)
    if (K < phi(tU, alpha, gamma) - 1e-9).any() or (K > phi(tL, alpha, gamma) + 1e-9).any():
        berhenti("kappa keluar dari selang [phi(tU), phi(tL)] — ada yang salah dengan integral")
    return K


# ------------------------------------------------------------------ siapkan soal
def siapkan(rho=RHO, t_baik=T_BAIK, phi_baik=PHI_BAIK, t_buruk=T_BURUK, phi_buruk=PHI_BURUK,
            batas_klasik=BATAS_KLASIK, cetak=True):
    """Kembalikan semua bahan model dalam satu dict. Urutan baris = faskes, kolom = kelurahan."""
    d = baca_data()
    dem = d["P"] + (rho - 1) * d["L"]
    w = dem / dem.sum()

    tL, tM, tU = koreksi_tfn(d["OPT"], d["BG"], d["PES"])
    tukar = d["OPT"] > d["PES"]
    naik = d["BG"] < tL
    turun = d["BG"] > tU

    alpha, gamma = alpha_gamma(t_baik, phi_baik, t_buruk, phi_buruk)
    K_fuzzy = hitung_kappa(tL, tM, tU, alpha, gamma)
    T_fuzzy = (tL + tM + tU) / 3.0

    d.update(
        w=w, dem=dem, tL=tL, tM=tM, tU=tU, alpha=alpha, gamma=gamma,
        tukar=tukar, naik=naik, turun=turun,
        MASUKAN={
            "klasik": ((d["BG"] <= batas_klasik).astype(float), d["BG"]),
            "sigmoid": (phi(d["BG"], alpha, gamma), d["BG"]),
            "fuzzy": (K_fuzzy, T_fuzzy),
        },
        D={"opt": d["OPT"], "bg": d["BG"], "pes": d["PES"]},
        param={"FILE_WAKTU": FILE_WAKTU, "KOLOM_OPT": KOLOM_OPT, "KOLOM_BG": KOLOM_BG, "KOLOM_PES": KOLOM_PES,
               "FILE_PENDUDUK": FILE_PENDUDUK, "KOLOM_P": KOLOM_P, "KOLOM_L": KOLOM_L,
               "RHO": rho, "T_BAIK": t_baik, "PHI_BAIK": phi_baik, "T_BURUK": t_buruk, "PHI_BURUK": phi_buruk,
               "BATAS_KLASIK": batas_klasik, "BATAS_NETRAL": list(BATAS_NETRAL), "TITIK_INTEGRAL": TITIK_INTEGRAL,
               "hash_file": {FILE_WAKTU: sidik_jari(FILE_WAKTU), FILE_PENDUDUK: sidik_jari(FILE_PENDUDUK)}},
    )
    if cetak:
        print(f"Data: {len(d['fas'])} faskes x {len(d['kel'])} kelurahan | penduduk {d['P'].sum():,.0f}, "
              f"lansia 65+ {d['L'].sum():,.0f} | rho = {rho}")
        print(f"Koreksi TFN: opt > pes ditukar {tukar.sum()} | tM naik ke tL {naik.sum()} | "
              f"tM turun ke tU {turun.sum()} | dari {tukar.size} pasangan")
        print(f"Sigmoid: phi({t_baik:g}) = {phi_baik}, phi({t_buruk:g}) = {phi_buruk} -> "
              f"alpha = {alpha:.6f}, gamma = {gamma:.4f} menit | MCLP klasik: tM <= {batas_klasik:g} menit")
    return d


# ------------------------------------------------------------------ fungsi bantu
def nilai(buka, K, T, w):
    """Z1 = sum w_i max_{j buka} K_ij,  Z2 = sum w_i min_{j buka} T_ij."""
    b = list(buka)
    return float(w @ K[b].max(axis=0)), float(w @ T[b].min(axis=0))


def ukuran_netral(buka, D, bobot):
    """% permintaan <= batas netral dan rata-rata menit ke pos terdekat, di 3 kondisi (waktu Google mentah)."""
    b = list(buka)
    out = {}
    for kode in KONDISI:
        t = D[kode][b].min(axis=0)
        for batas in BATAS_NETRAL:
            out[f"pct_le{batas:g}_{kode}"] = round(100 * float(bobot @ (t <= batas)), 3)
        out[f"rata_menit_{kode}"] = round(float(bobot @ t), 3)
    return out