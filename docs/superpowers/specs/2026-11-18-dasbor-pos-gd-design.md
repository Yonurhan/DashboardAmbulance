# Desain — Prototipe Dasbor Lokasi Pos Gawat Darurat Kota Bekasi

Tanggal: 2026-11-18 · Status: disetujui Yonathan (2026-11-18)

## 1. Maksud dan alasan

Prototipe pertama dasbor web untuk skripsi *Optimasi Lokasi Pos Layanan Gawat Darurat Kota Bekasi Menggunakan Fuzzy MCLP dan MOBGOA*. Dasbor ditunjukkan ke dosen pembimbing CS. Penggunanya adalah perencana (Dinas Kesehatan / PSC 119), bukan masyarakat umum.

Dasbor **hanya menampilkan hasil olahan model**. Ia tidak menjalankan optimasi dan tidak memanggil Google API. Angka di dasbor harus **identik** dengan angka di skripsi, jadi semua rumus diimpor dari kode model, bukan ditulis ulang.

## 2. Tujuan, non-tujuan, anti-tujuan

**Tujuan**
- Perencana bisa memilih skenario/metode, jumlah pos p, dan kondisi lalu lintas, lalu melihat:
  - lokasi pos;
  - kategori waktu tempuh tiap kelurahan;
  - front Pareto;
  - kenaikan cakupan;
  - pos inti;
  - kelurahan yang kurang terlayani;
  - detail tiap kelurahan.
- Kode terstruktur (modul berisi fungsi, tanpa hierarki kelas) yang mudah dipetakan ke DFD level 1 skripsi.
- Data bisa diganti (MOBGOA baru, skenario baru), lalu dasbor ikut menyesuaikan cukup dengan menjalankan ulang skrip penyiapan.

**Non-tujuan (prototipe ini)**
- Fitur Admin, login, database, unggah file (DFD proses 1.0 dan 2.0).
- Rute jalan OSRM.
- Tile peta offline.
- Tampilan ponsel.
- Tema gelap.
- Perbandingan model klasik/sigmoid.

**Anti-tujuan (gagal walaupun "jalan")**
- Angka Z1/Z2/persentase di dasbor berbeda dari CSV model.
- Menit waktu tempuh per pasangan asal–tujuan bocor ke data olahan atau ke UI.
- Data mentah Google masuk Git.
- Memakai Google Maps.
- Tampilan generik "AI slop" (Inter/Roboto, gradien mencolok, emoji).
- Ketidakcocokan data diperbaiki diam-diam.

## 3. Batasan

- **Teknologi:** Python 3.11, Dash (Plotly), dash-leaflet, Plotly. Versi dikunci di `requirements.txt` setelah dipasang. API dash-leaflet / dash-extensions dicek terhadap versi yang **terpasang**.
- **Peta dasar:** tile standar OpenStreetMap (`tile.openstreetmap.org`). Atribusi "© OpenStreetMap contributors" selalu terlihat dan menaut ke https://www.openstreetmap.org/copyright. Tile CARTO atau tile lain tidak dipakai.
- **Bahasa:** UI, komentar, dan docstring dalam Bahasa Indonesia.
- **File model tidak diubah:** `model_eksak.py`, `data_bersama.py`, `mobgoa.py`, dan semua data mentah/hasil model.
- **Waktu tempuh:** `checkpoint_waktu_tempuh_final.csv` tidak boleh masuk Git.
- **Konstanta:** batas 15/40 menit, warna, ambang pos inti, p default, dan path disimpan di `config.py`. Tidak ada angka yang di-hardcode di banyak tempat.
- **Lingkungan:** proyek di `C:\Users\yonur\Documents\Thesis Application` (di luar OneDrive). venv `.venv` dibuat dari Python 3.11.

## 4. Pendekatan

| Pendekatan | Untung-rugi | Keputusan |
|---|---|---|
| **A. Skrip penyiapan membuat JSON olahan; dasbor hanya membaca JSON itu** | Dasbor ringan dan cepat. Angka divalidasi sekali. Data mentah tidak dibutuhkan saat runtime. Perlu menjalankan ulang skrip kalau data berubah. | **Dipilih** (sesuai prompt). |
| B. Dasbor membaca CSV mentah dan menghitung κ saat start | Tidak perlu langkah penyiapan, tetapi start lambat (integral κ 99×56 per skenario), file Google ikut dibutuhkan saat runtime, dan validasi bercampur dengan UI. | Ditolak. Melanggar batasan "dasbor tidak boleh membaca file mentah". |
| C. Dasbor statis (HTML + Leaflet JS, tanpa server) | Mudah dibagikan, tetapi keluar dari stack Python/Dash yang diwajibkan dan sulit dipetakan ke DFD berbasis fungsi Python. | Ditolak. |

Pemilihan solusi aktif di dasbor: semua state (skenario, p, kondisi, solusi_id, kelurahan terpilih) disimpan di `dcc.Store`. Callback dipecah per proses DFD.

## 5. Struktur folder (disetujui, Q26)

```
Thesis Application/            ← root repo Git (lokal, tanpa push)
├── app.py  config.py  data_loader.py  layout.py  callbacks.py
├── model/            model_eksak.py, data_bersama.py, mobgoa.py   (dipindah, isi tidak berubah)
├── data/
│   ├── mentah/       centroid_kelurahan_kota_bekasi.csv, checkpoint_waktu_tempuh_final.csv,
│   │                 dataset-faskes-bekasi-final-koordinat2.csv, dataset-penduduk-usia-kelurahan-bekasi-2025.csv,
│   │                 front_pareto_eksak.csv, mobgoa_front.csv, jakarta10/, rho1/, BATASWILAYAH_DESA_20260601.gdb
│   └── olahan/       hasil skrip penyiapan (di-commit)
├── scripts/          siapkan_data.py, cek_data.py
├── tests/            pytest untuk fungsi murni
├── assets/           style.css, fonts/ (IBM Plex Sans + Mono, OFL), skrip JS pewarnaan GeoJSON bila diperlukan
├── docs/superpowers/specs/
├── requirements.txt  README.md  .gitignore
└── reference_image/  (tidak di-commit)
```

**SHA-256 file model** (identik dengan versi di `OneDrive\...\Final Thesis\Code\`; dicatat di README):
- `model_eksak.py`: `4f27c43f…ceb07`
- `data_bersama.py`: `8f3da1b3…476295`

**`.gitignore`:** `.venv/`, `__pycache__/`, `data/mentah/checkpoint_waktu_tempuh_final.csv`, `*waktu_tempuh*`, `*.gdb/`, `*.gdb.zip`, `reference_image/`, `.claude-flow/`, `data/mentah/*/hasil_sementara.jsonl`, serta **semua file berisi menit per pasangan** di folder skenario: `data/mentah/*/koreksi_tfn.csv`, `data/mentah/*/detail_kelurahan.csv`, `data/mentah/*/matriks_tbar.csv` *(keputusan builder: t̄ per pasangan adalah turunan langsung menit Google, jadi diperlakukan sebagai data mentah Google)*. Yang di-commit dari folder skenario: `front_pareto_*.csv`, `matriks_kappa.csv`, `bobot_kelurahan.csv`, `parameter_model.json`, `perbandingan_model.csv`, `log_waktu_hitung.csv`.

## 6. Fakta sumber data (hasil penelusuran)

**Faskes**
- 99 faskes: `RS-01..RS-44` dan `PKM-01..PKM-55`.
- `jenis` diturunkan dari kolom `kategori`: "Rumah Sakit" → `RS`, "Puskesmas" → `PKM`.
- Koordinat dan kecamatan diambil dari dataset faskes.

**Kelurahan**
- 56 kelurahan, kode KDEPUM BIG (contoh `32.75.01.1001`).
- Poligon dari GDB layer `BATAS_DESAKEL_AR` dengan filter `WADMKK = 'Kota Bekasi'`. CRS-nya gabungan WGS84 + EGM2008, jadi sumbu Z dibuang dan hasilnya diubah ke EPSG:4326.
- Centroid dari `centroid_kelurahan_kota_bekasi.csv`, identik dengan yang dipakai model.
- Nama di CSV penduduk berbeda spasi. Ini ditangani `data_bersama.normal()`.

**Fungsi model yang dipakai** (`data_bersama.py`)
- `siapkan(rho, t_baik, phi_baik, t_buruk, phi_buruk, batas_klasik, cetak)` mengembalikan `w`, `MASUKAN["fuzzy"] = (K, T)` (baris = faskes, kolom = kelurahan) dan `D = {"opt","bg","pes"}` (waktu Google mentah).
  - Fungsi ini membaca file relatif terhadap cwd dan memanggil `sys.exit` kalau gagal.
  - Karena itu skrip memanggilnya dengan `chdir` sementara ke `data/mentah/`, dibungkus `try/finally`.
- `nilai(buka, K, T, w)` menghasilkan (Z1, Z2).
- `ukuran_netral(buka, D, bobot)` menghasilkan `pct_le15_*`, `pct_le40_*`, `rata_menit_*` untuk opt/bg/pes.
- `buka` adalah daftar **indeks baris** faskes.

**Fungsi MOBGOA yang dipakai** (`mobgoa.py`)
- `non_dominasi(z1, z2)`.

**Parameter skenario**
- `utama` memakai default `data_bersama`: ρ = 2,93, t_baik = 15, t_buruk = 40.
- `jakarta10` dan `rho1` memakai parameter dari `parameter_model.json` di foldernya masing-masing.
- Sebagai pengaman tambahan, matriks κ dan t̄ hasil `siapkan()` dibandingkan dengan `matriks_kappa.csv` / `matriks_tbar.csv` yang tersedia.

**Pemetaan kondisi lalu lintas**

| Kondisi | Kolom Google mentah | Kode model |
|---|---|---|
| Lengang | `menit_optimistic_0300` | `opt` |
| Biasa | `menit_bestguess_1100` | `bg` |
| Sibuk | `menit_pessimistic_1800` | `pes` |

## 7. Skenario × metode (Q17, Q27, Q30)

| id | Nama tampilan | Eksak | MOBGOA |
|---|---|---|---|
| `utama` | Skenario Utama (ρ = 2,93) | `front_pareto_eksak.csv`, `model == "fuzzy"` (170 baris) | `mobgoa_front.csv`, `tahap == "utama"` |
| `jakarta10` | Sensitivitas batas 10 menit | `jakarta10/front_pareto_jakarta.csv` (fuzzy) | — |
| `rho1` | Tanpa pembobotan lansia (ρ = 1) | `rho1/front_pareto_rho.csv` (fuzzy) | — |

- Hanya model **fuzzy** yang ditampilkan.
- Dropdown berisi satu pilihan per kombinasi yang ada, dikelompokkan per skenario. Default: **Utama — MOBGOA**.
- Nama tampilan dan path diatur di `config.py`.

**Aturan MOBGOA**
- Untuk setiap nilai `tahap`, skrip membuat satu file `hasil_<tahap>_mobgoa.json`.
- Kalau dalam satu `tahap` ada lebih dari satu kombinasi (`aturan`, `N`, `iterasi`), skrip berhenti dengan pesan jelas. Kombinasi yang dipakai kemudian ditetapkan di `config.py`.
- **Front gabungan** dibentuk per p:
  1. gabungkan semua seed;
  2. buang himpunan pos yang ganda (himpunan dibandingkan setelah diurutkan);
  3. ambil hanya yang lolos `non_dominasi`.
- Setiap solusi tetap berisi tepat p pos.
- `cek_data.py` mencetak konfigurasi, jumlah seed, dan jumlah titik front per p.

**Fleksibilitas.** Kalau data diganti, jalankan `siapkan_data.py`, lalu `cek_data.py`, lalu mulai ulang `app.py`. Syaratnya, format kolom tetap sama.

## 8. Data olahan (`data/olahan/`)

**`faskes.json`**
- Field: `[{kode, nama, jenis, kecamatan, lat, lng}]`, 99 entri.

**`kelurahan.geojson`**
- 56 fitur, EPSG:4326, disederhanakan dengan `simplify(preserve_topology=True)`.
- Toleransi dipilih supaya file kecil tetapi batas tetap wajar. Ukuran sebelum dan sesudah dilaporkan.
- `properties`: `kode, nama, kecamatan, penduduk, lansia, centroid_lat, centroid_lng`.
- **Tanpa `bobot`**, karena w berbeda per skenario (keputusan brainstorming no. 1).

**`hasil_<skenario>_<metode>.json`**

```json
{
  "skenario": {"id", "nama", "keterangan", "metode", "parameter": {rho, t_baik, t_buruk}, "sumber": {...}},
  "bobot_kelurahan": {"<kode_kel>": w},
  "solusi": [{
    "p", "solusi_id", "Z1", "Z2", "pos": [...],
    "hasil_kelurahan": {"<kode_kel>": {"pos_melayani", "cakupan", "tercakup",
                                       "kategori": {"lengang","biasa","sibuk"}}},
    "metrik": {"lengang": {"persen_15","persen_40"}, "biasa": {...}, "sibuk": {...}}
  }]
}
```

Aturan isinya:
- `solusi_id` berurutan dari Z1 tertinggi dalam satu p. `solusi_id = 1` adalah default.
- `Z1`, `Z2`:
  - eksak: diambil dari `Z1_fuzzy` / `Z2_fuzzy_menit` di CSV;
  - MOBGOA: diambil dari `Z1` / `Z2_menit`.
  - Keduanya diverifikasi ulang dengan `nilai()`.
- `pos_melayani`: pos di S dengan κ tertinggi. Kalau seri, ambil yang t̄-nya terkecil.
  - Kalau semua κ = 0: `tercakup: false`, `pos_melayani` = pos dengan t̄ terkecil, dan `cakupan = 0` (Q4). Catatan: di data saat ini κ minimum 0,0023 (tidak pernah tepat 0), jadi cabang ini **penjagaan defensif** yang tidak muncul; diuji dengan data buatan di pytest. Tidak ada ambang ε *(keputusan builder)*.
- `cakupan`: κ ke `pos_melayani`. Ini **tingkat cakupan** (nilai antara 0 dan 1), bukan persentase.
- `kategori` per kondisi, mengikuti `ukuran_netral`:
  - waktu yang dipakai adalah waktu Google mentah ke pos **tercepat** pada kondisi itu;
  - pengelompokan: `"<=15"` (≤ 15), `"15-40"` (lebih dari 15 sampai 40), `">40"` (lebih dari 40);
  - batas tetap 15/40 di semua skenario, termasuk `jakarta10` (Q11).
- `metrik`: `persen_15` / `persen_40` = `pct_le15_*` / `pct_le40_*` dari `ukuran_netral(buka, D, w_skenario)`.
  - Ini berbobot permintaan w (di rho1 sama dengan berbobot penduduk).
  - Untuk eksak, nilainya harus sama dengan kolom `pct_*` di CSV.
- **Tidak ada angka menit** yang ditulis, kecuali Z2 (agregat).

**`metrik_<skenario>_<metode>.json`**
- `kenaikan_cakupan`: untuk p = 1..20, berisi `Z1_terbaik` dan `selisih` terhadap p − 1 (null untuk p = 1).
- `frekuensi_faskes`, untuk **Q5(c)**:
  - Untuk setiap p_awal = 1..20 dan setiap faskes, frekuensi = rata-rata, untuk p dari p_awal sampai 20, dari (jumlah solusi Pareto di p yang memuat faskes ÷ jumlah solusi Pareto di p) × 100.
  - Setiap p berbobot sama.
  - Dasbor menampilkan baris p_awal = p slider.

## 9. Validasi (`scripts/cek_data.py`)

Skrip mencetak laporan lulus/gagal per pemeriksaan:
1. Setiap solusi berisi tepat p pos, tanpa kode ganda.
2. Semua kode pos ada di `faskes.json`.
3. `hasil_kelurahan` berisi tepat 56 kelurahan, dan semuanya ada di `kelurahan.geojson`.
4. `pos_melayani` selalu termasuk dalam `pos`.
5. `0 ≤ cakupan ≤ 1`.
6. Z1 dan Z2 hasil `nilai()` sama dengan output (toleransi 1e-6). `pct_*` hasil hitung ulang sama dengan CSV eksak.
7. p lengkap dari 1 sampai 20 untuk setiap file hasil.
8. Untuk `jakarta10` dan `rho1`: K hasil `siapkan()` sama dengan `matriks_kappa.csv`; T dibandingkan dengan `matriks_tbar.csv` **hanya jika file itu ada secara lokal** (tidak di-commit), selain itu pemeriksaan T dilewati dengan keterangan.

Kalau ada ketidakcocokan, **dilaporkan ke Yonathan, tidak diperbaiki diam-diam**.

## 10. Aplikasi dasbor

**Pemetaan modul ke DFD**

| Modul / callback | Proses DFD level 1 |
|---|---|
| Pilihan skenario, slider p, kondisi lalu lintas, klik front Pareto → peta dan ringkasan metrik | 3.0 *Tampilkan Solusi* |
| Grafik kenaikan cakupan, pos inti, tabel 10 kelurahan terendah | 4.0 *Tampilkan Analisis* |
| Klik kelurahan → panel detail dan garis jalur | 5.0 *Tampilkan Detail Kelurahan* |
| Admin | 1.0 dan 2.0 (belum ada) |

- `data_loader.py` membaca semua file olahan **sekali** saat start.
- `callbacks.py` dipisah dalam blok fungsi per proses. Logika (pewarnaan, pemilihan default, top-10, frekuensi) ditulis sebagai **fungsi murni** yang bisa diuji pytest. Callback hanya memanggilnya.

**Tata letak (Q22, Q28: ikut referensi terang "Dataplay" dan panel detail referensi 3)**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Dasbor Lokasi Pos Gawat Darurat Kota Bekasi · subjudul         (bilah tipis)│
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐            PETA OSM PENUH LAYAR             ┌─────────────┐ │
│ │ KONTROL  │                                              │ DETAIL KEL. │ │
│ │ skenario │   poligon berwarna kategori, pos, jalur      │ (saat klik, │ │
│ │ slider p │                                              │  tombol ×)  │ │
│ │ kondisi  │                                              └─────────────┘ │
│ │ sakelar  │                                              ┌─────────────┐ │
│ ├──────────┤                                              │  LEGENDA    │ │
│ │ METRIK   │                                              └─────────────┘ │
│ └──────────┘                                                              │
│ ┌──────── laci analisis (bisa dilipat, default terbuka) ───────────────┐ │
│ │ Front Pareto      │ Kenaikan cakupan     │ 10 kelurahan terendah      │ │
│ └───────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Isi kartu kontrol**
- dropdown skenario/metode;
- slider p 1–20 dengan nilai besar terlihat (default **p = 10** dari `config.py`);
- tombol segmen Lengang / Biasa / Sibuk (default Biasa);
- sakelar "Tampilkan pos inti" (mati);
- sakelar "Tampilkan kandidat lain" (mati).

**Isi kartu metrik**
- Z1 dan Z2;
- "% permintaan berbobot ≤ 15 menit" dan "≤ 40 menit" pada kondisi terpilih.

**Peta**
- **Tile dan batas:** tile OSM diberi filter CSS (grayscale sebagian, kontras sedikit turun) hanya pada lapisan tile. Batas peta otomatis memuat seluruh Kota Bekasi, dengan padding yang memperhitungkan panel.
- **Poligon kelurahan:**
  - warna kategori `<=15` `#2A6F97`, `15-40` `#E0A33A`, `>40` `#9E2A2B`;
  - tooltip berisi nama dan kategori;
  - kelurahan terpilih diberi garis tepi tebal berwarna aksen.
- **Pos terpilih:** lingkaran pekat dengan cincin putih; tooltip berisi kode, nama, dan jenis.
- **Kandidat lain:** titik kecil abu-abu.
- **Pos inti:**
  - faskes dengan frekuensi ≥ **75%** (`config.py`) diberi cincin ganda;
  - tooltip berisi persentase frekuensi;
  - kalau tidak ada yang lolos ambang, muncul pesan singkat.
- **Garis jalur:**
  - garis lurus putus-putus berwarna aksen, dari centroid ke `pos_melayani`;
  - label di panel: "Garis lurus (ilustrasi), bukan rute jalan";
  - garis hilang saat panel ditutup atau kelurahan lain dipilih.

**Panel detail**
- **Data kelurahan:** nama, kecamatan, penduduk, lansia (65+), bobot w skenario aktif.
- **Pos melayani:** kode dan nama.
- **Cakupan:** nilai cakupan. Kalau `tercakup: false`, tampil teks "Tidak tercakup (κ = 0); ditampilkan pos terdekat".
- **Kategori:** kategori di ketiga kondisi, dengan catatan kecil "Kategori diukur ke pos tercepat pada tiap kondisi lalu lintas." Angka menit tidak ditampilkan.

**Front Pareto**
- Scatter dengan X = Z2 (menit) dan Y = Z1, untuk p terpilih. Solusi aktif berwarna aksen dan lebih besar.
- Klik titik menjadikannya solusi aktif. Peta, metrik, dan tabel ikut berubah.
- Saat p atau skenario berubah, solusi aktif kembali ke `solusi_id = 1`.
- Kalau hanya ada satu solusi, tampil satu titik dengan keterangan.

**Kenaikan cakupan**
- Garis Z1 terbaik terhadap p, ditambah batang selisih di sumbu kedua.
- p terpilih ditandai warna aksen.

**Tabel 10 kelurahan terendah**
- Kolom: nama, kecamatan, cakupan (3 desimal), kategori pada kondisi terpilih.

**Gaya visual (Q21, Q24, Q25, Q29)**
- Tema terang, latar netral hangat `#F6F5F2`, teks `#1C1B19`, garis `#E2DFD8`, aksen indigo `#3B3FB6`.
- Kartu putih semi-transparan dengan blur latar, sudut 14 px, bayangan lembut.
- Font IBM Plex Sans untuk teks, IBM Plex Mono untuk angka dan kode. Font dibundel lokal.
- Label kecil berhuruf kapital dengan spasi huruf lebar.
- Tanpa animasi berlebihan, gradien mencolok, atau emoji.
- Palet diuji dengan simulasi deuteranopia.

**Perilaku**
- State aktif disimpan di `dcc.Store`.
- `prevent_initial_call` dipakai bila sesuai, dan nilai kosong ditangani.
- Kelurahan terpilih tetap terpilih saat skenario, p, atau kondisi berubah, dan panelnya diperbarui *(keputusan builder)*.
- Tidak boleh ada error di konsol browser maupun terminal.

## 11. Pengujian dan dokumentasi

- **pytest** untuk fungsi murni di `callbacks.py` dan `scripts/`, termasuk kategori, pos_melayani/seri/κ = 0, front gabungan, frekuensi, dan default solusi.
- **Uji manual** di browser bawaan aplikasi. Hasilnya ditulis dalam tabel (ID, skenario, input, hasil yang diharapkan, hasil, status), mencakup 7 skenario uji dari prompt Yonathan:
  1. menggeser slider p dari 1 ke 20 → jumlah titik pos selalu sama dengan p;
  2. mengganti kondisi lalu lintas → warna kelurahan berubah, lokasi pos **tidak** berubah;
  3. mengganti skenario → semua komponen ikut berubah;
  4. mengklik titik di front Pareto → peta dan tabel berubah sesuai solusi itu;
  5. mengklik kelurahan → panel detail dan garis jalur muncul; menutup panel → keduanya hilang;
  6. menyalakan/mematikan pos inti;
  7. Z1/Z2 di ringkasan sama dengan data olahan untuk minimal tiga solusi acak.
- **Tangkapan layar** dikirim ke Yonathan untuk penyesuaian visual.
- **README** (Bahasa Indonesia) berisi:
  - cara instalasi (venv Python 3.11 + `pip install -r requirements.txt`);
  - cara menyiapkan data dan cara menjalankan;
  - cara mengganti data MOBGOA;
  - struktur folder dan pemetaan ke DFD;
  - hash file model;
  - keterbatasan: butuh internet untuk tile, garis jalur lurus, belum ada Admin, MOBGOA hanya untuk skenario utama.
- **Git:** init lokal, tidak di-push.

## 12. Alur kerja dan titik berhenti

1. Rapikan folder (Q26). Folder GDB berisi dua file `.sr.lock` (kemungkinan sisa dari ArcGIS/QGIS); tutup aplikasi GIS sebelum pemindahan. Kalau pemindahan gagal karena terkunci, GDB dibiarkan di tempatnya dan path-nya diatur di `config.py`.
2. Laporan Tahap 0 ringkas.
3. Tahap 1: `siapkan_data.py` dan `cek_data.py`. **Berhenti** dan tunjukkan hasilnya.
4. Tahap 2: dasbor, lalu kirim tangkapan layar.
5. Tahap 3: pengujian, README, Git.

## 13. Diserahkan ke builder

- Toleransi penyederhanaan geometri.
- Detail implementasi pewarnaan GeoJSON di dash-leaflet versi terpasang (fungsi JS di `assets/` atau `hideout`).
- Ukuran dan tinggi persis panel dan laci.
- Struktur internal callback.
- Isi teks subjudul dan `keterangan` skenario.
