"""Konstanta dan path proyek dasbor lokasi pos gawat darurat Kota Bekasi.

Semua angka batas, warna, ambang, dan path hanya didefinisikan di sini.
"""
from pathlib import Path

# ------------------------------------------------------------------ path
ROOT = Path(__file__).resolve().parent
DIR_MODEL = ROOT / "model"
DIR_MENTAH = ROOT / "data" / "mentah"
DIR_OLAHAN = ROOT / "data" / "olahan"

PATH_FASKES_CSV = DIR_MENTAH / "dataset-faskes-bekasi-final-koordinat2.csv"
PATH_CENTROID_CSV = DIR_MENTAH / "centroid_kelurahan_kota_bekasi.csv"
PATH_GDB = DIR_MENTAH / "BATASWILAYAH_DESA_20260601.gdb"
LAYER_GDB = "BATAS_DESAKEL_AR"
FILTER_GDB = "WADMKK = 'Kota Bekasi'"

# ------------------------------------------------------------------ skenario
# parameter_json = None berarti memakai nilai bawaan data_bersama.siapkan().
# Folder matriks_kappa juga berisi bobot_kelurahan.csv dan detail_kelurahan.csv hasil model
# (dipakai cek_data.py untuk memastikan dasbor sama dengan hasil penelitian).
SKENARIO = {
    "utama": {
        "nama": "Skenario Utama (ρ = 2,93)",
        "nama_pendek": "Utama",
        "keterangan": "Batas waktu 15/40 menit, bobot lansia ρ = 2,93.",
        "parameter_json": DIR_MENTAH / "utama" / "parameter_model.json",
        "eksak": DIR_MENTAH / "front_pareto_eksak.csv",
        "matriks_kappa": DIR_MENTAH / "utama" / "matriks_kappa.csv",
    },
    "jakarta10": {
        "nama": "Sensitivitas batas 10 menit",
        "nama_pendek": "Batas 10 menit",
        "keterangan": "Fungsi keanggotaan memakai batas baik 10 menit (bukan 15).",
        "parameter_json": DIR_MENTAH / "jakarta10" / "parameter_model.json",
        "eksak": DIR_MENTAH / "jakarta10" / "front_pareto_jakarta.csv",
        "matriks_kappa": DIR_MENTAH / "jakarta10" / "matriks_kappa.csv",
    },
    "rho1": {
        "nama": "Tanpa pembobotan lansia (ρ = 1)",
        "nama_pendek": "Tanpa bobot lansia",
        "keterangan": "Permintaan sebanding jumlah penduduk (ρ = 1).",
        "parameter_json": DIR_MENTAH / "rho1" / "parameter_model.json",
        "eksak": DIR_MENTAH / "rho1" / "front_pareto_rho.csv",
        "matriks_kappa": DIR_MENTAH / "rho1" / "matriks_kappa.csv",
    },
}

# konfigurasi = None: setiap tahap harus berisi tepat satu kombinasi (aturan, N, iterasi).
# Kalau ada lebih dari satu, isi misalnya {"aturan": "target", "N": 200, "iterasi": 2000}.
MOBGOA = {"path": DIR_MENTAH / "mobgoa_front.csv", "konfigurasi": None}

ID_DEFAULT = ("utama", "mobgoa")
NAMA_METODE = {"eksak": "Eksak", "mobgoa": "MOBGOA (gabungan {seed} run)"}

# ------------------------------------------------------------------ ukuran netral
BATAS_MENIT = (15.0, 40.0)            # harus sama dengan data_bersama.BATAS_NETRAL
KONDISI = {"lengang": "opt", "biasa": "bg", "sibuk": "pes"}
LABEL_KONDISI = {"lengang": "Lengang", "biasa": "Biasa", "sibuk": "Sibuk"}
KONDISI_DEFAULT = "biasa"

# ------------------------------------------------------------------ dasbor
P_MIN, P_MAKS = 1, 20
P_DEFAULT = 10
AMBANG_POS_INTI = 75.0               # persen

WARNA_KATEGORI = {"<=15": "#1F6FB0", "15-40": "#E0A33A", ">40": "#9E2A2B"}
LABEL_KATEGORI = {"<=15": "≤ 15 menit", "15-40": "15–40 menit", ">40": "> 40 menit"}
WARNA_AKSEN = "#3B3FB6"
WARNA_LATAR = "#F6F5F2"
WARNA_TEKS = "#1C1B19"
WARNA_GARIS = "#E2DFD8"

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_ATRIBUSI = ('© <a href="https://www.openstreetmap.org/copyright" target="_blank">'
                 'OpenStreetMap</a> contributors')
