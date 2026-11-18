# Dasbor Lokasi Pos Gawat Darurat Kota Bekasi — Rencana Implementasi

> **Untuk agen pelaksana:** SUB-SKILL WAJIB: superpowers:subagent-driven-development (disarankan) atau superpowers:executing-plans. Setiap langkah memakai checkbox (`- [ ]`).

**Tujuan:** Membangun prototipe dasbor Dash yang menampilkan hasil Fuzzy MCLP (eksak dan MOBGOA) untuk perencana PSC 119 Kota Bekasi.

**Arsitektur:**
- Paket `olah/` berisi fungsi murni pengolahan data. Paket ini dipanggil oleh `scripts/siapkan_data.py`, yang menulis JSON/GeoJSON ke `data/olahan/`. `scripts/cek_data.py` memvalidasinya.
- Dasbor (`app.py`, `config.py`, `data_loader.py`, `layout.py`, `callbacks.py`, `logika.py`, `grafik.py`, `peta.py`) hanya membaca `data/olahan/`, sekali saat start.
- Semua rumus model diimpor dari `model/data_bersama.py` dan `model/mobgoa.py`.

**Stack:** Python 3.11, pandas, numpy, geopandas/pyogrio, shapely, Dash, dash-leaflet, Plotly, pytest.

**Spesifikasi:** `docs/superpowers/specs/2026-11-18-dasbor-pos-gd-design.md`. Baca spesifikasi bersama rencana ini. Nomor §X di bawah merujuk ke spesifikasi itu.

## Batasan Global

- Python 3.11. venv `.venv` di root proyek, dibuat dengan `py -3.11 -m venv .venv`.
- UI, komentar, docstring, dan pesan dalam Bahasa Indonesia.
- Kode terstruktur: modul berisi fungsi, **tanpa kelas**. Setiap file di bawah 500 baris.
- File di `model/` dan `data/mentah/` **tidak boleh diubah** isinya.
- Tile: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, atribusi `© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors`. Dilarang Google Maps dan tile lain.
- Konstanta hanya ada di `config.py`:
  - `BATAS_MENIT = (15.0, 40.0)`, `AMBANG_POS_INTI = 75.0`, `P_DEFAULT = 10`, `KONDISI_DEFAULT = "biasa"`;
  - `WARNA_KATEGORI = {"<=15": "#2A6F97", "15-40": "#E0A33A", ">40": "#9E2A2B"}`;
  - `WARNA_AKSEN = "#3B3FB6"`, `WARNA_LATAR = "#F6F5F2"`, `WARNA_TEKS = "#1C1B19"`, `WARNA_GARIS = "#E2DFD8"`;
  - `KONDISI = {"lengang": "opt", "biasa": "bg", "sibuk": "pes"}`.
  - Catatan: `BATAS_MENIT` harus sama dengan `data_bersama.BATAS_NETRAL`; `cek_data.py` memeriksanya.
- Label kategori: `"<=15"`, `"15-40"`, `">40"`.
- Tidak ada angka menit per pasangan di `data/olahan/` maupun di UI. Hanya Z2 (agregat) yang boleh.
- Ketidakcocokan data **dilaporkan, tidak diperbaiki diam-diam**.
- Commit lokal saja. Pesan commit diakhiri `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Tidak ada push.

## Fokus Review

1. **`solusi_id` aktif tidak ada lagi** setelah skenario atau p berubah (misalnya 9 solusi menjadi 1). Yang diharapkan: kembali ke `solusi_id = 1` tanpa error. Diuji di Task 8 (`test_solusi_aktif_kembali_ke_default`).
2. **Klik titik di front Pareto** saat beberapa solusi punya Z1 atau Z2 kembar. Solusi dikenali dari `customdata = solusi_id`, bukan dari indeks titik. Diuji di Task 10 (`test_figur_pareto_customdata`).
3. **Kelurahan terpilih saat skenario berganti.** Panel diperbarui dengan data skenario baru, termasuk bobot w yang berbeda di rho1. Diuji di Task 8 (`test_detail_kelurahan_bobot_ikut_skenario`).
4. **Tidak ada faskes yang lolos ambang pos inti** untuk suatu p awal. Peta menampilkan pesan singkat, bukan lapisan kosong tanpa keterangan. Diuji di Task 8 (`test_pos_inti_kosong`).
5. **Path dengan spasi** (`Thesis Application`) dan `chdir` sementara saat `siapkan()`. Setelah error, cwd harus kembali seperti semula. Diuji di Task 2 (`test_muat_model_cwd_kembali`).

---

### Task 1: Penataan folder, venv, Git, dan `config.py`

**File:**
- Pindahkan: `model_eksak.py`, `data_bersama.py`, `mobgoa.py` ke `model/`.
- Pindahkan ke `data/mentah/`: 4 CSV input, `front_pareto_eksak.csv`, `mobgoa_front.csv`, `jakarta10/`, `rho1/`, `BATASWILAYAH_DESA_20260601.gdb/`.
- Buat: `config.py`, `.gitignore`, `requirements.txt`, `olah/__init__.py`, `tests/__init__.py`, `tests/conftest.py`.

**Antarmuka yang dihasilkan** (`config.py`):
- `ROOT: Path`, `DIR_MODEL`, `DIR_MENTAH`, `DIR_OLAHAN`, `PATH_GDB`, `LAYER_GDB = "BATAS_DESAKEL_AR"`, `FILTER_GDB = "WADMKK = 'Kota Bekasi'"`.
- `SKENARIO: dict[str, dict]` dengan kunci `utama`, `jakarta10`, `rho1`. Setiap entri berisi:
  - `nama` (teks §7), `keterangan`;
  - `parameter_json` (None untuk utama);
  - `eksak` (path CSV front);
  - `matriks_kappa` (None untuk utama).
- `MOBGOA = {"path": ..., "konfigurasi": None}`. `konfigurasi` berupa dict `{aturan, N, iterasi}` atau None (artinya "harus tunggal").
- `ID_DEFAULT = ("utama", "mobgoa")`.
- Semua konstanta dari Batasan Global.

- [ ] **Langkah 1:** Catat SHA-256 ketiga file model, lalu pindahkan file dan folder. Kalau GDB gagal dipindah karena `.sr.lock`, biarkan di root dan set `PATH_GDB` ke root.
- [ ] **Langkah 2:** `py -3.11 -m venv .venv`, lalu pasang `pandas numpy geopandas pyogrio shapely pyproj pytest` dengan versi yang sama seperti di Python 3.11 global (pandas 2.3.3, numpy 2.3.5, geopandas 1.2.0, pyogrio 0.13.0, shapely 2.2.0, pyproj 3.7.2).
- [ ] **Langkah 3:** Tulis `config.py`, `.gitignore` (isinya persis seperti §5), dan `tests/conftest.py`. File `conftest.py` menambahkan `ROOT` dan `DIR_MODEL` ke `sys.path`.
- [ ] **Langkah 4: Verifikasi.** Hash file di `model/` sama dengan hash yang dicatat di Langkah 1. `python -c "import config, sys; sys.path.insert(0, str(config.DIR_MODEL)); import data_bersama, mobgoa"` berjalan tanpa error.
- [ ] **Langkah 5:** `git init`, lalu `git add -A`. `git status --ignored` harus menunjukkan bahwa `checkpoint_waktu_tempuh_final.csv`, `*.gdb`, `koreksi_tfn.csv`, `detail_kelurahan.csv`, `matriks_tbar.csv`, `reference_image/`, dan `.venv/` **tidak** di-stage. Commit dengan pesan `chore: tata folder proyek dan konfigurasi`.

- [ ] **Langkah 6:** Kirim laporan Tahap 0 ringkas ke Yonathan, tanpa berhenti. Isinya rangkuman §6–§8 spesifikasi:
  - daftar file beserta fungsinya;
  - pemetaan field ke sumbernya;
  - field yang dihitung;
  - hal yang belum pasti.

### Task 2: `olah/model_io.py` — memuat model per skenario

**Antarmuka:**
- Dipakai: `config.SKENARIO`, `data_bersama.siapkan`.
- Dihasilkan:
  - `muat_model(id_skenario: str) -> dict`, berisi kunci:
    - `fas: list[str]`, `kel: list[str]`;
    - `K: ndarray (99, 56)`, `T: ndarray (99, 56)`, `w: ndarray (56,)`;
    - `D: {"opt","bg","pes"} -> ndarray`;
    - `P`, `L: ndarray (56,)`;
    - `param: dict`.
  - `idx_faskes(d: dict, kode: list[str]) -> list[int]`.

- [ ] **Langkah 1: Tes gagal** di `tests/test_model_io.py`:
  - `test_muat_model_rho1_cocok_matriks`: K hasil `muat_model("rho1")` sama dengan `data/mentah/rho1/matriks_kappa.csv` (baris/kolom diurutkan sesuai `fas`/`kel`), `atol=1e-8`.
  - `test_muat_model_cwd_kembali`: cwd sebelum dan sesudah pemanggilan sama, termasuk saat `siapkan` dipaksa melempar `SystemExit` (gunakan monkeypatch).
  - `test_idx_faskes`: `idx_faskes(d, ["RS-01", "PKM-01"])` mengembalikan indeks yang benar; kode yang tidak dikenal memunculkan `KeyError`.
- [ ] **Langkah 2:** Jalankan `.venv\Scripts\python -m pytest tests/test_model_io.py -v`. Hasil: FAIL.
- [ ] **Langkah 3:** Implementasikan.
  - Parameter dibaca dari `parameter_model.json` (`RHO`, `T_BAIK`, `PHI_BAIK`, `T_BURUK`, `PHI_BURUK`, `BATAS_KLASIK`). Untuk utama, pakai default `siapkan()`.
  - `chdir` ke `DIR_MENTAH` di dalam `try/finally`, panggil `siapkan(cetak=False)`.
  - `SystemExit` diubah menjadi `RuntimeError` dengan pesan yang sama.
  - `K, T = d["MASUKAN"]["fuzzy"]`.
- [ ] **Langkah 4:** Jalankan pytest. Hasil: PASS.
- [ ] **Langkah 5:** Commit `feat(olah): muat model per skenario`.

### Task 3: `olah/solusi.py` — membangun entri solusi

**Antarmuka:**
- Dipakai: `muat_model`, `idx_faskes`, `data_bersama.nilai`, `data_bersama.ukuran_netral`, `mobgoa.non_dominasi`, `config.BATAS_MENIT`, `config.KONDISI`.
- Dihasilkan:
  - `kategori_menit(t: float) -> str`, memakai `BATAS_MENIT`. Nilai tepat 15 masuk `"<=15"`, tepat 40 masuk `"15-40"`.
  - `pos_melayani(K_kol: ndarray, T_kol: ndarray, idx: list[int]) -> tuple[int, float, bool]`, mengembalikan (indeks pos, cakupan, tercakup).
  - `hasil_kelurahan(d: dict, idx: list[int]) -> dict[str, dict]`.
  - `metrik_kondisi(d: dict, idx: list[int]) -> dict`, membungkus `ukuran_netral(idx, d["D"], d["w"])` ke bentuk `{"lengang": {"persen_15", "persen_40"}, ...}`.
  - `baca_front_eksak(path: Path) -> DataFrame`, berkolom `p, Z1, Z2, pos(list[str])`. Hanya `model == "fuzzy"`, dengan `Z1_fuzzy` → Z1 dan `Z2_fuzzy_menit` → Z2.
  - `baca_front_mobgoa(path: Path, konfigurasi: dict | None) -> dict[str, DataFrame]` (per `tahap`). Memunculkan `ValueError` kalau sebuah `tahap` punya lebih dari satu kombinasi (`aturan`, `N`, `iterasi`) dan `konfigurasi` bernilai None. Front gabungan dibentuk per p:
    1. buang himpunan ganda (`frozenset`);
    2. ambil hanya `non_dominasi(z1, z2)`.
  - `bangun_solusi(d: dict, front: DataFrame) -> list[dict]`. Bentuk keluarannya mengikuti §8. `solusi_id` diurutkan dari Z1 menurun, lalu Z2 menaik.

- [ ] **Langkah 1: Tes gagal** di `tests/test_solusi.py` (data sintetis kecil, 3 faskes × 2 kelurahan):
  - `test_kategori_batas`: 15.0 → `"<=15"`, 15.01 → `"15-40"`, 40.0 → `"15-40"`, 40.01 → `">40"`.
  - `test_pos_melayani_seri_pilih_tbar_kecil`: dua pos dengan κ sama 0,8 dan t̄ 20 vs 12. Yang dipilih pos dengan t̄ 12.
  - `test_pos_melayani_kappa_nol`: semua κ = 0. Hasilnya `tercakup is False`, `cakupan == 0`, dan pos yang dipilih punya t̄ terkecil.
  - `test_kategori_pakai_pos_tercepat_per_kondisi`: pos A tercepat saat opt, pos B tercepat saat pes. Kategori dihitung dari minimum per kondisi.
  - `test_front_mobgoa_gabung_dedup_nondominasi`: dua seed dengan himpunan yang sama (urutan kode berbeda) dan satu titik terdominasi. Hasil per p hanya titik non-dominated tanpa duplikat, dan setiap `pos` berisi tepat p kode.
  - `test_front_mobgoa_konfigurasi_ganda_berhenti`: dua kombinasi `N` dalam satu `tahap` → `ValueError`, pesannya menyebut `config.MOBGOA["konfigurasi"]`.
  - `test_solusi_id_urut_z1`.
- [ ] **Langkah 2:** Jalankan pytest. Hasil: FAIL.
- [ ] **Langkah 3:** Implementasikan fungsi-fungsi di atas di `olah/solusi.py`.
- [ ] **Langkah 4:** Jalankan pytest. Hasil: PASS.
- [ ] **Langkah 5:** Commit `feat(olah): bangun solusi, kategori, front gabungan MOBGOA`.

### Task 4: `olah/metrik.py` — kenaikan cakupan dan frekuensi pos inti

**Antarmuka:**
- Dihasilkan:
  - `kenaikan_cakupan(solusi: list[dict]) -> list[dict]`, bentuk `[{p, Z1_terbaik, selisih}]` untuk p = 1..20. `selisih` bernilai None untuk p = 1.
  - `frekuensi_faskes(solusi: list[dict], kode_faskes: list[str]) -> dict[str, dict[str, float]]`, dipetakan `p_awal (str) -> kode -> persen`. Rumusnya mengikuti §8: rata-rata, untuk p = p_awal..20, dari persentase solusi di p tersebut yang memuat faskes. Setiap p berbobot sama.

- [ ] **Langkah 1: Tes gagal** di `tests/test_metrik.py`:
  - `test_kenaikan_selisih`: Z1 terbaik 0,6 / 0,7 / 0,75 menghasilkan selisih None / 0,1 / 0,05 (`approx`).
  - `test_frekuensi_bobot_p_sama`:
    - data: p = 1 punya 1 solusi `{A}`, p = 2 punya 4 solusi yang semuanya memuat A;
    - hasil untuk p_awal 1: A = 100;
    - data lain: p = 2 punya 2 solusi, dan hanya 1 yang memuat B;
    - hasil untuk p_awal 2: B = 50.
  - `test_frekuensi_semua_faskes_ada`: setiap kode di `kode_faskes` muncul, termasuk yang bernilai 0.
- [ ] **Langkah 2:** Jalankan pytest. Hasil: FAIL.
- [ ] **Langkah 3:** Implementasikan.
- [ ] **Langkah 4:** Jalankan pytest. Hasil: PASS.
- [ ] **Langkah 5:** Commit `feat(olah): kenaikan cakupan dan frekuensi pos inti`.

### Task 5: `olah/geo.py` — faskes dan poligon kelurahan

**Antarmuka:**
- Dihasilkan:
  - `buat_faskes(path_csv: Path, fas: list[str]) -> list[dict]`, bentuk `{kode, nama, jenis, kecamatan, lat, lng}`. `jenis` dipetakan dari `"Rumah Sakit"` → `RS` dan `"Puskesmas"` → `PKM`; nilai lain memunculkan `ValueError`.
  - `buat_kelurahan(path_gdb, path_centroid, d: dict, toleransi: float) -> tuple[dict, dict]`, mengembalikan (FeatureCollection, laporan `{ukuran_sebelum_kb, ukuran_sesudah_kb, toleransi, tidak_cocok: list}`). Properti: `kode, nama, kecamatan, penduduk, lansia, centroid_lat, centroid_lng`. `penduduk` dan `lansia` diambil dari `d["P"]` / `d["L"]` dengan urutan `d["kel"]`.

- [ ] **Langkah 1: Tes gagal** di `tests/test_geo.py`:
  - `test_buat_faskes_99`: 99 entri, 44 RS dan 55 PKM, semua kode ada di `d["fas"]`.
  - `test_kelurahan_56_epsg4326` (integrasi dengan GDB asli; di-skip kalau GDB tidak ada):
    - 56 fitur, semua kode ada di `d["kel"]`, koordinat 2D;
    - `centroid_lat` / `centroid_lng` sama persis dengan `centroid_kelurahan_kota_bekasi.csv`;
    - tidak ada kunci `bobot` di properti.
- [ ] **Langkah 2:** Jalankan pytest. Hasil: FAIL.
- [ ] **Langkah 3:** Implementasikan.
  - Baca dengan `pyogrio.read_dataframe(..., layer=LAYER_GDB, where=FILTER_GDB)`.
  - Buang sumbu Z dengan `shapely.force_2d`, lalu `set_crs`/`to_crs(4326)`.
  - Jalankan `simplify(toleransi, preserve_topology=True)`.
  - Pilih toleransi dengan mencoba 0,00005 / 0,0001 / 0,0002 derajat. Pilih yang terbesar dengan ukuran ≤ 300 KB dan perubahan luas tiap kelurahan < 1%. Catat pilihan itu di laporan.
- [ ] **Langkah 4:** Jalankan pytest. Hasil: PASS.
- [ ] **Langkah 5:** Commit `feat(olah): faskes.json dan kelurahan.geojson`.

### Task 6: `scripts/siapkan_data.py`

**Antarmuka:**
- Dipakai: semua fungsi dari Task 2–5.
- Dihasilkan, di `data/olahan/`:
  - `faskes.json`, `kelurahan.geojson`;
  - `hasil_<id>_<metode>.json`, berisi `skenario` (`id, nama, keterangan, metode, parameter{rho, t_baik, t_buruk}, sumber{file, konfigurasi?, jumlah_seed?}`), `bobot_kelurahan`, dan `solusi`;
  - `metrik_<id>_<metode>.json`, berisi `kenaikan_cakupan` dan `frekuensi_faskes`;
  - `laporan_siapkan.json` (ringkasan ukuran file dan jumlah titik front per p).

- [ ] **Langkah 1:** Implementasikan `main() -> None`.
  - Untuk setiap skenario di `config.SKENARIO`: `muat_model`, lalu tulis hasil eksak.
  - Untuk setiap `tahap` di `baca_front_mobgoa`: tulis hasil MOBGOA. Kalau `tahap` tidak ada di `config.SKENARIO`, berhenti dengan pesan.
  - JSON ditulis dengan `ensure_ascii=False` dan nilai float dibulatkan 8 desimal.
- [ ] **Langkah 2:** Jalankan `.venv\Scripts\python scripts\siapkan_data.py`. Verifikasi:
  - terbentuk 4 file `hasil_*` (`utama_eksak`, `utama_mobgoa`, `jakarta10_eksak`, `rho1_eksak`) dan 4 file `metrik_*`;
  - `Select-String -Path data\olahan\* -Pattern "menit"` hanya cocok dengan kata "Z2", tanpa angka per pasangan.
- [ ] **Langkah 3:** Commit `feat: skrip penyiapan data` beserta isi `data/olahan/`.

### Task 7: `scripts/cek_data.py` — validasi, **lalu BERHENTI**

**Antarmuka:**
- Dihasilkan: `jalankan_pemeriksaan() -> list[tuple[str, bool, str]]` (nama, lulus, keterangan) dan `main()`. `main()` mencetak tabel dan keluar dengan kode 1 kalau ada pemeriksaan yang gagal.

- [ ] **Langkah 1:** Implementasikan delapan pemeriksaan §9, ditambah dua pemeriksaan lain:
  - `config.BATAS_MENIT == tuple(data_bersama.BATAS_NETRAL)`;
  - cetak konfigurasi MOBGOA, jumlah seed, jumlah titik front per p, dan jumlah faskes ≥ 75% untuk setiap p_awal.
  - Z1 dan Z2 dihitung ulang dengan `nilai()`.
  - `pct_*` eksak dibandingkan dengan CSV (toleransi 1e-6 untuk Z dan 1e-3 untuk `pct_*`, karena CSV membulatkan `pct_*` ke 3 desimal).
- [ ] **Langkah 2:** Jalankan `.venv\Scripts\python scripts\cek_data.py`. Hasil yang diharapkan: semua LULUS. Kalau ada yang GAGAL, **jangan diperbaiki**; catat untuk laporan.
- [ ] **Langkah 3:** Commit `feat: skrip validasi data`.
- [ ] **Langkah 4: TITIK BERHENTI.** Laporkan ke Yonathan:
  - output `cek_data.py`;
  - ukuran GeoJSON sebelum dan sesudah penyederhanaan;
  - jumlah titik front MOBGOA gabungan per p;
  - jumlah pos inti per p_awal, beserta penjelasan definisi Q5(c).

  Tunggu konfirmasi sebelum Task 8.

### Task 8: Pustaka dasbor, `data_loader.py`, dan `logika.py`

**File:** `data_loader.py`, `logika.py`, `tests/test_logika.py`, `requirements.txt`.

**Antarmuka:**
- `data_loader.muat_semua(dir_olahan: Path) -> dict`, berisi `{"faskes": {kode: dict}, "geojson": dict, "hasil": {"utama|mobgoa": dict, ...}, "metrik": {...}, "opsi_skenario": list[dict]}`.
  - Kunci berformat `"<id>|<metode>"`.
  - `opsi_skenario` untuk dropdown: `{label, value}`, dikelompokkan per skenario. Eksak muncul sebelum MOBGOA.
- `logika.py` (fungsi murni):
  - `daftar_solusi(data, kunci: str, p: int) -> list[dict]`;
  - `solusi_aktif(data, kunci, p, solusi_id: int | None) -> dict` (id yang tidak ada menghasilkan solusi_id 1);
  - `warna_kelurahan(solusi, kondisi: str) -> dict[str, str]` (kode → hex);
  - `kelurahan_terendah(solusi, data, kondisi, n=10) -> list[dict]`, berisi `{nama, kecamatan, cakupan, kategori}`, diurutkan menaik berdasarkan cakupan, lalu nama;
  - `pos_inti(data, kunci, p_awal: int) -> list[tuple[str, float]]` (frekuensi ≥ `AMBANG_POS_INTI`, diurutkan menurun);
  - `detail_kelurahan(data, kunci, solusi, kode_kel) -> dict`, berisi `{nama, kecamatan, penduduk, lansia, bobot, pos_kode, pos_nama, cakupan, tercakup, kategori{lengang, biasa, sibuk}, garis: [[lat, lng], [lat, lng]]}`;
  - `ringkasan_metrik(solusi, kondisi) -> dict`, berisi `{Z1, Z2, persen_15, persen_40}`.

- [ ] **Langkah 1:**
  - Pasang `dash`, `dash-leaflet`, `plotly` (beserta `dash-extensions` hanya bila dibutuhkan).
  - Baca dokumentasi atau sumber versi yang **terpasang** untuk tiga hal: nama properti klik `dl.GeoJSON` (`clickData` di 1.x atau `click_feature` di 0.x), cara memberi fungsi gaya (`style` + `hideout` dengan fungsi JS di `assets/`), dan dukungan `className` di `dl.TileLayer`. Catat temuannya di komentar `peta.py`.
  - `pip freeze > requirements.txt`.
- [ ] **Langkah 2: Tes gagal** di `tests/test_logika.py`. Fixture-nya `muat_semua(DIR_OLAHAN)` yang asli.
  - `test_solusi_aktif_kembali_ke_default`: solusi_id 9 untuk p yang hanya punya 1 solusi menghasilkan solusi_id 1.
  - `test_warna_kelurahan_56_dan_palet`: tepat 56 kunci, semua nilai ada di `WARNA_KATEGORI`.
  - `test_kelurahan_terendah_urut`: 10 baris, cakupan menaik.
  - `test_pos_inti_kosong`: dengan ambang dinaikkan ke 101 lewat monkeypatch, hasilnya `[]`.
  - `test_detail_kelurahan_bobot_ikut_skenario`: bobot kelurahan yang sama berbeda antara `utama|eksak` dan `rho1|eksak`, dan sama dengan `bobot_kelurahan` di masing-masing file.
  - `test_detail_tidak_ada_menit`: tidak ada kunci yang mengandung "menit".
- [ ] **Langkah 3:** Jalankan pytest. Hasil: FAIL.
- [ ] **Langkah 4:** Implementasikan. Jalankan pytest. Hasil: PASS.
- [ ] **Langkah 5:** Commit `feat(dasbor): loader dan logika murni`.

### Task 9: Tampilan — aset, `peta.py`, `grafik.py`, `layout.py`, `app.py`

**File:** `assets/style.css`, `assets/peta.js`, `assets/fonts/*.woff2`, `peta.py`, `grafik.py`, `layout.py`, `app.py`, `tests/test_grafik.py`.

**Antarmuka:**
- `peta.lapisan_kelurahan(geojson, warna: dict, kode_terpilih: str | None)`: komponen `dl.GeoJSON` dengan id `"geo-kel"`. Warna dikirim lewat `hideout`, gaya dibuat oleh fungsi di `assets/peta.js`. Tooltip berisi nama dan kategori.
- `peta.lapisan_pos(solusi, data)`, `peta.lapisan_kandidat(solusi, data)`, `peta.lapisan_pos_inti(daftar)`, `peta.lapisan_garis(detail)`. Masing-masing mengembalikan `list` komponen dl.
- `grafik.figur_pareto(daftar_solusi, solusi_id_aktif) -> go.Figure`: X = Z2, Y = Z1, `customdata = solusi_id`, solusi aktif berwarna aksen dan lebih besar. Kalau hanya ada 1 solusi, muncul anotasi "Hanya satu solusi Pareto pada p ini".
- `grafik.figur_kenaikan(kenaikan, p_aktif) -> go.Figure`: garis Z1 terbaik dan batang selisih di `yaxis2`; p aktif diberi penanda aksen.
- `layout.buat_layout(data) -> html.Div`.
  - Id komponen: `dd-skenario`, `sl-p`, `rb-kondisi`, `sw-pos-inti`, `sw-kandidat`, `peta`, `geo-kel`, `lap-pos`, `lap-kandidat`, `lap-inti`, `lap-garis`, `pesan-inti`, `kartu-metrik`, `panel-detail`, `btn-tutup`, `g-pareto`, `g-kenaikan`, `tbl-terendah`, `btn-laci`, `laci`.
  - Store: `st-state` (`{kunci, p, kondisi, solusi_id, kel}`).
- `app.py`: `buat_app() -> Dash`. Dijalankan dengan `python app.py` di `127.0.0.1:8050`, `debug=False`.

- [ ] **Langkah 1:** Unduh IBM Plex Sans (400, 500, 600) dan IBM Plex Mono (400, 500) dalam format woff2 dari paket npm `@fontsource/ibm-plex-sans` dan `@fontsource/ibm-plex-mono` (jsDelivr, versi dikunci). Lisensinya OFL; sertakan `assets/fonts/OFL.txt`.
- [ ] **Langkah 2: Tes gagal** `tests/test_grafik.py`:
  - `test_figur_pareto_customdata`: `customdata` sama dengan daftar `solusi_id`.
  - `test_figur_pareto_satu_solusi_anotasi`.
  - `test_figur_kenaikan_20_titik`.
- [ ] **Langkah 3:** Implementasikan `grafik.py`. Jalankan pytest. Hasil: PASS.
- [ ] **Langkah 4:** Implementasikan `peta.py`, `layout.py`, `app.py`, dan aset. Tata letak, kartu, palet, dan tipografi mengikuti §10.
  - Filter CSS hanya untuk `.tile-osm` (`filter: grayscale(.6) contrast(.92) brightness(1.03)`).
  - Peta diberi `bounds` dari ekstensi GeoJSON, dengan padding yang memperhitungkan panel.
- [ ] **Langkah 5:** Jalankan `python app.py` lewat preview browser bawaan. Halaman tampil tanpa error konsol, dan atribusi OSM terlihat.
- [ ] **Langkah 6:** Commit `feat(dasbor): tata letak dan komponen tampilan`.

### Task 10: `callbacks.py` — interaksi (DFD 3.0, 4.0, 5.0)

**Antarmuka:** `daftarkan_callback(app, data) -> None`, dipanggil dari `buat_app`. Callback dikelompokkan dalam blok berkomentar `# === Proses 3.0 ===`, `4.0`, dan `5.0`.

- **3.0 Tampilkan Solusi**
  - Input `dd-skenario`, `sl-p`, `rb-kondisi`, `g-pareto.clickData` → mengubah `st-state`.
  - Skenario atau p berubah membuat `solusi_id` = 1. Klik Pareto memakai `customdata`.
  - `st-state` → `geo-kel.hideout`, `lap-pos`, `lap-kandidat` (bergantung `sw-kandidat`), `kartu-metrik`, `g-pareto.figure`.
- **4.0 Tampilkan Analisis**
  - `st-state` → `g-kenaikan`, `tbl-terendah`.
  - `st-state` + `sw-pos-inti` → `lap-inti`, `pesan-inti`.
  - `btn-laci` → kelas `laci` (terbuka/terlipat).
- **5.0 Tampilkan Detail Kelurahan**
  - Klik `geo-kel` → `st-state.kel`. `btn-tutup` → `kel = None`.
  - `st-state` → `panel-detail` (isi dan visibilitas), `lap-garis`, sorotan di `hideout`.
  - Label "Garis lurus (ilustrasi), bukan rute jalan".
- Semua callback memakai `prevent_initial_call=True` kecuali yang membentuk tampilan awal. Nilai None ditangani dengan `PreventUpdate` atau default.

- [ ] **Langkah 1:** Implementasikan. Logika apa pun yang belum ada di `logika.py` ditambahkan ke sana, beserta tesnya.
- [ ] **Langkah 2:** `pytest` (seluruh suite) PASS.
- [ ] **Langkah 3:** Di browser bawaan, klik satu kelurahan, satu titik Pareto, ganti skenario, lalu tutup panel. Konsol tanpa error, terminal tanpa traceback.
- [ ] **Langkah 4:** Commit `feat(dasbor): callback proses 3.0, 4.0, 5.0`.

### Task 11: Uji manual, tangkapan layar, dan cek palet

- [ ] **Langkah 1:** Jalankan 7 skenario uji §11 di browser bawaan. Tulis tabelnya (ID, skenario, input, hasil yang diharapkan, hasil, status) ke `docs/pengujian/2026-11-18-uji-manual.md`. Uji 7 memakai tiga solusi acak, seed 42, dicocokkan dengan `data/olahan`.
- [ ] **Langkah 2:** Simulasikan deuteranopia (matriks Machado 2009) pada ketiga warna kategori. Laporkan selisih kecerahan; harus jelas terbedakan.
- [ ] **Langkah 3:** Ambil tangkapan layar di 1366×768 dan 1920×1080, lalu kirim ke Yonathan untuk masukan visual.
- [ ] **Langkah 4:** Commit `test: uji manual dasbor`.

### Task 12: README dan penutup

- [ ] **Langkah 1:** Tulis `README.md` dengan isi §11:
  - instalasi, penyiapan data, cara menjalankan;
  - cara mengganti data MOBGOA atau menambah skenario;
  - struktur folder, tabel pemetaan DFD, SHA-256 file model;
  - keterbatasan: butuh internet untuk tile, garis lurus, belum ada Admin, MOBGOA hanya untuk skenario utama, pemeriksaan t̄ hanya lokal.
- [ ] **Langkah 2:** `pytest` lalu `python scripts/cek_data.py`. Keduanya harus lulus.
- [ ] **Langkah 3:** Commit `docs: README`. Tidak ada push.
