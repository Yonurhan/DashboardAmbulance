# Tampilan HP dan grafik tanpa zoom — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dasbor terbaca di HP (peta penuh, panel dibuka saat perlu) dan grafik Front Pareto / Kenaikan cakupan tidak bisa di-zoom.

**Architecture:** Satu blok `@media (max-width: 640px)` di `assets/style.css` untuk tata letak HP; tombol ⚙ dan "Legenda" (hanya tampil di HP) menukar kelas `terbuka` lewat callback klien; laci memakai callback klien yang menentukan keadaan awal dari lebar layar.

**Tech Stack:** Dash 4.5, dash-leaflet 1.1.3, plotly 7.1, CSS.

**Spec:** `docs/superpowers/specs/2026-11-24-tampilan-hp-design.md`

## Global Constraints
- Batas HP: lebar ≤ 640 px. Tampilan desktop tidak berubah selain zoom grafik.
- Atribusi "© OpenStreetMap contributors" selalu terlihat.
- Teks UI berbahasa Indonesia.

## Review Focus
- Layar HP diputar (landscape, tinggi kecil): lembar Analisis dan detail tetap bisa digulir, tidak terpotong.
- Kontrol dan detail terbuka bersamaan: keduanya tetap bisa ditutup.
- Desktop dengan jendela sempit (< 640 px) mendapat tampilan HP — diterima.
- Klik kelurahan saat laci Analisis terbuka di HP: detail tampil di atas laci.
- Grafik: hover tetap menampilkan tooltip setelah zoom dikunci.

---

### Task 1: Kunci zoom grafik

**Files:** Modify `grafik.py` (dict `sumbu` di tata letak dasar); Test `tests/test_grafik.py`

- [ ] Tes `test_grafik_tidak_bisa_dizoom`: untuk `figur_pareto(...)` dan `figur_kenaikan(...)` (argumen seperti tes yang ada), `fig.layout.xaxis.fixedrange is True` dan `fig.layout.yaxis.fixedrange is True`.
- [ ] Jalankan → FAIL. Tambah `"fixedrange": True` ke `sumbu`. Jalankan `pytest -q` → semua PASS.

### Task 2: Kerangka HP (layout + callback klien)

**Files:** Modify `layout.py` (`buat_layout`, `_legenda`, `_laci`), `callbacks.py` (blok "Kerangka tampilan"); Test `tests/test_tampilan.py`

- [ ] Tes: layout berisi tombol `btn-kontrol` dan `btn-legenda`, `kolom-kiri` ber-id `kolom-kiri`, legenda ber-id `legenda`; judul punya span `judul-panjang` dan `judul-pendek`.
- [ ] Bilah: `html.H1([Span("Dashboard Lokasi Pos Gawat Darurat Kota Bekasi", className="judul-panjang"), Span("Pos Gawat Darurat Bekasi", className="judul-pendek")])` + `html.Button("⚙", id="btn-kontrol", className="btn-hp", title="Pengaturan")`.
- [ ] Legenda: `id="legenda"`, tombol pertama `html.Button("Legenda", id="btn-legenda", className="btn-hp btn-legenda")`.
- [ ] Callback klien `toggle(n, kelas)` → menambah/menghapus ` terbuka`; dipakai untuk (`btn-kontrol` → `kolom-kiri.className`) dan (`btn-legenda` → `legenda.className`), `prevent_initial_call=True`.
- [ ] Ganti `lipat_laci` (server) dengan callback klien dari `btn-laci.n_clicks` (tanpa prevent_initial_call): n=0 → `"laci"` bila `innerWidth <= 640` selain itu `"laci terbuka"`; n>0 → tukar.
- [ ] Callback paskan peta: bila `innerWidth <= 640` padding `[10, 70]` / `[10, 60]`, selain itu tetap seperti sekarang.
- [ ] `pytest -q` → semua PASS.

### Task 3: CSS HP

**Files:** Modify `assets/style.css`

- [ ] `.btn-hp` tersembunyi di desktop; `.judul-pendek` tersembunyi di desktop.
- [ ] `@media (max-width: 640px)`: judul pendek; ⚙ tampil di kanan bilah; `.kolom-kiri` tersembunyi kecuali `.terbuka` (lebar penuh di bawah bilah, maks `100dvh - 90px`, bisa digulir); legenda hanya tombol kecuali `.terbuka`; laci lebar penuh, saat terbuka tinggi ±80dvh dengan `.laci-isi` satu kolom bisa digulir, grafik 260 px; `.panel-detail` jadi lembar bawah (left/right 8px, bottom 8px, maks 55dvh, z-index di atas laci); `.leaflet-control-zoom` disembunyikan; atribusi tetap terlihat di atas tombol Analisis.
- [ ] Cek visual 375×812: awal (peta terlihat penuh), ⚙ terbuka, legenda terbuka, Analisis terbuka & digulir, klik kelurahan → detail. Cek desktop sama seperti sebelumnya.
- [ ] Commit, push, cek di https://dashboard-ambulance.vercel.app (HP emulasi).
