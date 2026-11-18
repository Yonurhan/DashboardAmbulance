# Uji Manual Dasbor — 19 November 2026

**Lingkungan**
- Browser bawaan aplikasi Claude (Chromium), viewport 1366 × 768 dan 1920 × 1080.
- Server `python app.py` di `127.0.0.1:8050`, `debug=False`.
- Data olahan hasil `scripts/siapkan_data.py`, lulus `scripts/cek_data.py` 55/55.

Pemeriksaan otomatis memakai skrip di halaman: jumlah penanda pos dihitung dari elemen SVG berwarna `#1C1B19`, dan galat JavaScript dicatat lewat `window.onerror`.

| ID | Skenario uji | Input | Hasil yang diharapkan | Hasil | Status |
|---|---|---|---|---|---|
| UJI-1 | Geser slider p | Utama · MOBGOA. Slider dari p = 1 sampai 20 dengan tombol panah, satu langkah per kali. | Jumlah titik pos selalu sama dengan p. | 20/20 langkah cocok, misalnya p = 1 → 1 pos dan p = 20 → 20 pos. Tidak ada galat JS. | LULUS |
| UJI-2 | Ganti kondisi lalu lintas | p = 20, Biasa → Sibuk | Warna kelurahan berubah, lokasi pos tidak berubah. | Geometri 20 penanda pos identik. Warna 3 kelurahan berubah. Ringkasan metrik berganti ke kondisi sibuk. | LULUS |
| UJI-3 | Ganti skenario | Utama · MOBGOA → Tanpa bobot lansia · Eksak | Semua komponen ikut berubah. | Penanda pos, warna peta, kartu metrik, front Pareto, grafik kenaikan, dan tabel terendah semuanya berubah. | LULUS |
| UJI-4 | Klik titik front Pareto | ρ = 1 · Eksak, p = 20, klik solusi 4 | Peta, metrik, dan tabel mengikuti solusi itu. | Kartu menunjukkan "4 dari 19". Pos dan tabel berubah. Z1 0,9909, Z2 6,33, ≤ 15 menit 96,7% (sibuk), sama dengan `hasil_rho1_eksak.json`. | LULUS |
| UJI-5 | Klik kelurahan, lalu tutup panel | Klik Bojong Rawalumbu, lalu tombol × | Panel detail dan garis muncul. Setelah ditutup, keduanya hilang. | Panel menampilkan nama, kecamatan, penduduk, lansia, bobot, pos melayani PKM-51, cakupan 0,978, kategori 3 kondisi, dan label "Garis lurus (ilustrasi)". 1 garis putus-putus dan sorotan tepi muncul. Setelah ×: panel tersembunyi, 0 garis, 0 sorotan. | LULUS* |
| UJI-6 | Nyalakan dan matikan pos inti | Utama · MOBGOA, p = 10 | Penanda pos inti muncul dan hilang. | Menyala: 7 cincin pos inti dan pesan "7 pos inti … p = 10–20" (sama dengan `cek_data.py`). Mati: 0 cincin, pesan hilang. Sakelar kandidat lain menampilkan 89 titik (99 − 10). | LULUS |
| UJI-7 | Z1/Z2 ringkasan = data olahan | 3 solusi: (Utama · MOBGOA, p 10, id 1, biasa), (Utama · MOBGOA, p 20, id 1, sibuk), (ρ = 1 · Eksak, p 20, id 4, sibuk) | Nilai sama dengan JSON olahan. | 0,9769 / 9,65 / 98,4% / 100,0%; 0,9910 / 6,51 / 99,4% / 100,0%; 0,9909 / 6,33 / 96,7% / 100,0%. Ketiganya cocok setelah pembulatan tampilan. | LULUS |

\* **Catatan UJI-5.** Pada otomasi browser, klik pertama tanpa gerakan kursor sebelumnya tidak sampai ke lapisan Leaflet. Dengan kursor digerakkan dulu ke poligon, seperti pengguna sungguhan, klik selalu berhasil, termasuk klik ulang pada kelurahan yang sama.

**Pemeriksaan tambahan**
- Laci analisis bisa dilipat dan dibuka. Kolom kiri dan legenda ikut bergeser.
- Atribusi © OpenStreetMap contributors terlihat (dicek dengan elementFromPoint) saat laci terbuka maupun terlipat.
- Konsol browser bersih. Tidak ada traceback di terminal server.
- **Palet buta warna** (validator dataviz, mode terang): ketiga warna kategori `#1F6FB0` / `#E0A33A` / `#9E2A2B` lulus pemeriksaan lightness, chroma, separasi CVD (ΔE terburuk 29,1, protan), dan floor penglihatan normal. Amber berkontras < 3:1 terhadap latar, sehingga selalu didampingi label teks (legenda, tooltip, tabel, chip).
- **pytest**: 34 tes lulus (`pytest -q`).

**Tangkapan layar**
- `tampilan-awal-1366.jpg`
- `tampilan-detail-1366.jpg`

