# Dashboard Lokasi Pos Gawat Darurat Kota Bekasi

Prototipe dasbor web untuk skripsi *Optimasi Lokasi Pos Layanan Gawat Darurat Kota Bekasi Menggunakan Fuzzy Maximal Covering Location Problem dan Multi-Objective Binary Grasshopper Optimization Algorithm*.

Dasbor ini ditujukan untuk **perencana** (Dinas Kesehatan / PSC 119), bukan masyarakat umum. Dasbor **hanya menampilkan hasil olahan model**. Ia tidak menjalankan optimasi dan tidak memanggil Google API. Peta dasar memakai OpenStreetMap.

## Pemasangan

Butuh Python 3.11.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Menyiapkan data

Data mentah yang dibutuhkan di `data/mentah/`:
- `checkpoint_waktu_tempuh_final.csv` (tidak ada di Git);
- GDB `BATASWILAYAH_DESA_20260601.gdb` (tidak ada di Git);
- CSV faskes, penduduk, dan centroid;
- `front_pareto_eksak.csv` dan `mobgoa_front.csv`;
- folder `utama/`, `jakarta10/`, `rho1/`.

```powershell
.venv\Scripts\python scripts\siapkan_data.py
```

```powershell
.venv\Scripts\python scripts\cek_data.py
```

`siapkan_data.py` menulis semua file ke `data/olahan/`, termasuk `menit_google.json` (menit Google per pasangan untuk panel detail). File menit ini **tidak masuk Git**; di komputer tanpa data mentah, panel detail tetap jalan tanpa angka menit.

Rute jalan (sekali saja, butuh internet, ±12 menit untuk ±470 pasangan; aman dijalankan ulang karena rute yang sudah ada dilewati):

```powershell
.venv\Scripts\python scripts\ambil_rute.py
```

Rute diambil dari server demo OSRM (`router.project-osrm.org`, data © OpenStreetMap contributors) untuk setiap pasangan kelurahan → pos yang melayani di semua file hasil, lalu disimpan di `data/olahan/rute_osrm.json`. Dasbor hanya memakai bentuk jalurnya; angka menit tetap dari Google. Tanpa file ini, dasbor menampilkan garis lurus (ilustrasi). `cek_data.py` memeriksa struktur data, menghitung ulang Z1/Z2 dan persentase dengan fungsi dari `model/`, lalu memastikan hasilnya **sama dengan hasil penelitian**: front CSV, `bobot_kelurahan.csv`, `detail_kelurahan.csv`, dan `mobgoa_front.csv`. Ketidakcocokan hanya dilaporkan, tidak diperbaiki.

### Mengganti data MOBGOA atau menambah skenario

1. Ganti `data/mentah/mobgoa_front.csv`. Kolomnya harus tetap `tahap, aturan, N, iterasi, p, seed, titik_ke, Z1, Z2_menit, faskes_dibuka`.
2. Kalau ada `tahap` baru (misalnya `rho1`), skenario itu harus sudah terdaftar di `config.SKENARIO`.
3. Kalau satu `tahap` berisi lebih dari satu konfigurasi (aturan, N, iterasi), tetapkan konfigurasi yang dipakai di `config.MOBGOA["konfigurasi"]`.
4. Jalankan `siapkan_data.py` dan `cek_data.py`, lalu mulai ulang `app.py`.

**Catatan MOBGOA.** Front MOBGOA di dasbor adalah **gabungan 30 run**: semua seed digabung, himpunan pos yang ganda dibuang, lalu hanya yang tak terdominasi yang diambil. Ini **bukan** ukuran akurasi per run seperti di skripsi (`akurasi_per_run.csv`).

## Menjalankan

```powershell
.venv\Scripts\python app.py
```

Buka http://127.0.0.1:8050. Tile peta membutuhkan koneksi internet.

## Deploy (Render)

Dasbor bisa dipasang di [Render](https://render.com) (paket gratis) dari repo GitHub privat. `render.yaml` sudah berisi semua pengaturannya:

1. Push repo ke GitHub (repo privat).
2. Di Render: **New → Blueprint**, pilih repo ini, lalu **Apply**.
3. Render memasang `requirements-deploy.txt` (hanya paket untuk menjalankan dasbor) dan menjalankan `gunicorn app:server`.

Angka menit Google (`data/olahan/menit_google.json`) **tidak masuk Git**. Agar tetap tampil di versi deploy, unggah file itu sebagai *Secret File* Render:

4. Di service Render: **Environment → Secret Files → Add Secret File**, nama `menit_google.json`, isi = isi file `data/olahan/menit_google.json` dari laptop. Simpan, lalu **Manual Deploy → Deploy latest commit**.
5. Render menaruhnya di `/etc/secrets/menit_google.json`; `data_loader.muat_menit` membaca dari sana kalau file tidak ada di `data/olahan`. Tanpa Secret File, dasbor tetap jalan, hanya tanpa angka menit.

Catatan:
- Angka menit ikut tampil di dasbor publik dan berasal dari data Google Maps Platform; pertimbangkan ketentuan penggunaannya sebelum membagikan link secara luas.
- Paket gratis tertidur setelah 15 menit tanpa pengunjung; kunjungan pertama setelahnya butuh ±30–60 detik.
- Tidak ada login: siapa pun yang punya link bisa membuka dasbor.

## Struktur folder

```
app.py            titik masuk, membuat aplikasi Dash
config.py         konstanta: batas 15/40 menit, warna, ambang pos inti, p default, path, skenario
data_loader.py    membaca data olahan sekali saat start
logika.py         fungsi murni: pilih solusi, warna, tabel terendah, pos inti, detail kelurahan
grafik.py         figur Plotly: front Pareto, kenaikan cakupan
format_angka.py   format angka gaya Indonesia (1.234,5), dipakai layout dan grafik
peta.py           lapisan dash-leaflet: poligon, logo pos, kandidat, pos inti, rute
layout.py         kerangka tampilan dan isi kartu/panel
callbacks.py      interaksi, dikelompokkan per proses DFD (+ blok kerangka tampilan: paskan peta, lipat laci)
assets/           style.css, peta.js (gaya/klik GeoJSON), fonts/ (IBM Plex, OFL)
olah/             fungsi penyiapan data (model_io, solusi, metrik, geo)
scripts/          siapkan_data.py, cek_data.py, ambil_rute.py (rute OSRM)
model/            model_eksak.py, data_bersama.py, mobgoa.py (salinan tanpa perubahan)
data/mentah/      data input dan hasil model penelitian
data/olahan/      data yang dibaca dasbor
tests/            pytest
docs/             spesifikasi, rencana, laporan uji
```

Hash SHA-256 file model (identik dengan versi di folder `Code` penelitian):

| File | SHA-256 |
|---|---|
| `model_eksak.py` | `4f27c43f860e99964db687d96d54b61648a649617221a703bd089bafb79ceb07` |
| `data_bersama.py` | `8f3da1b38c5ca281f5abe673408087394c3cbfa346d29a8603baa20392476295` |
| `mobgoa.py` | `f7b35dfa93fe26e5e8c79d66366d1594ee76458390499d5aceaaff85ca665256` |

## Pemetaan ke DFD level 1

| Proses DFD | Implementasi |
|---|---|
| 1.0, 2.0 (Admin) | Belum ada di prototipe ini |
| 3.0 Tampilkan Solusi | `callbacks.py` blok 3.0: skenario, slider p, kondisi, klik front Pareto → peta, kartu metrik, front Pareto (`logika.py` bagian 3.0). Kartu metrik secara visual ada di laci analisis, tetapi diisi oleh proses 3.0 karena menggambarkan solusi aktif |
| 4.0 Tampilkan Analisis | `callbacks.py` blok 4.0: kenaikan cakupan, pos inti, 10 kelurahan terendah (`logika.py` bagian 4.0) |
| 5.0 Tampilkan Detail Kelurahan | `callbacks.py` blok 5.0: klik kelurahan → panel detail (menit ke pos tercepat) dan rute jalan (`logika.py` bagian 5.0) |
| (bukan proses DFD) | `callbacks.py` blok kerangka tampilan: memaskan peta ke Kota Bekasi dan melipat laci |
| Penyimpan data | `data/olahan/` dibaca oleh `data_loader.py` |

## Definisi yang dipakai

- **Kategori waktu tempuh** per kondisi mengikuti `ukuran_netral` di model. Waktu yang dipakai adalah waktu Google mentah ke pos *tercepat* pada kondisi itu:

  | Kondisi | Kolom waktu |
  |---|---|
  | Lengang | optimistic 03.00 |
  | Biasa | best guess 11.00 |
  | Sibuk | pessimistic 18.00 |

  Kategorinya ≤ 15, 15–40, dan > 40 menit, dan batas ini tetap sama di semua skenario.
- **Persentase ≤ 15 / ≤ 40 menit** adalah persentase permintaan berbobot w (sudah memuat ρ lansia).
- **Pos melayani** adalah pos dengan κ tertinggi; kalau seri, dipilih yang t̄-nya terkecil. **Cakupan** adalah κ ke pos itu.
- **Pos inti**: untuk p awal = nilai slider, frekuensi faskes adalah rata-rata, untuk p sampai 20, dari persentase solusi Pareto yang memuatnya. Setiap p berbobot sama. Ambangnya 75%.

## Pengujian

```powershell
.venv\Scripts\python -m pytest -q
```

Laporan uji manual ada di `docs/pengujian/`.

## Keterbatasan prototipe

- Tile peta OpenStreetMap butuh internet. Poligon, pos, dan grafik tetap tampil tanpa internet.
- Rute jalan OSRM tidak memperhitungkan lalu lintas dan bisa berbeda dari rute yang dipakai Google untuk menghitung menit. Rute ditarik dari pos ke centroid kelurahan.
- Angka menit di panel detail hanya muncul di komputer yang memiliki data mentah Google (file `menit_google.json` tidak di Git).
- Belum ada fitur Admin, login, database, atau unggah file (DFD 1.0 dan 2.0).
- Hasil MOBGOA baru tersedia untuk skenario utama.
- Pemeriksaan matriks t̄ dan `detail_kelurahan.csv` hanya berjalan di komputer yang memiliki file itu, karena keduanya berisi menit per pasangan dan tidak masuk Git.
- Tampilan dioptimalkan untuk laptop (lebar ≥ 1366 px), tidak untuk ponsel.
