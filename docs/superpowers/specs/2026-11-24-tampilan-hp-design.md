# Tampilan HP dan grafik tanpa zoom — desain singkat

**Tanggal:** 2026-11-24 · **Ukuran:** perubahan kecil

## Maksud
Dosen membuka link Vercel di HP. Saat ini (lebar 375 px) kartu kontrol, legenda, dan laci Analisis menutupi peta,
dan 4 kartu analisis terjepit dalam satu baris. Di desktop, grafik Front Pareto dan Kenaikan cakupan bisa di-zoom
masuk tetapi tidak bisa kembali.

## Tujuan / bukan tujuan
- Tujuan: di HP peta terlihat penuh; kontrol, legenda, detail kelurahan, dan Analisis bisa dibuka saat perlu dan
  terbaca nyaman. Kedua grafik tidak bisa di-zoom/di-drag (desktop dan HP); tooltip tetap ada.
- Bukan tujuan: mengubah tampilan desktop (selain zoom grafik), menambah fitur atau data.
- Anti-tujuan: peta tertutup permanen; teks/angka terpotong; atribusi OSM hilang.

## Pendekatan (dipilih: A)
- **A. Peta penuh + lembar (dipilih).** Panel disembunyikan, dibuka lewat tombol. Sama dengan konsep desktop.
- B. Halaman bergulir. Paling sedikit kode, tetapi peta "menangkap" jari saat menggulir dan detail harus dicari.
- C. Tab bawah (Peta/Pengaturan/Analisis). Terasa seperti aplikasi, tetapi kodenya paling banyak.

## Desain (HP = lebar ≤ 640 px; desktop tidak berubah)
- **Bilah judul:** judul pendek "Pos Gawat Darurat Bekasi" + tombol ⚙ (hanya di HP).
- **Kontrol:** tersembunyi; ⚙ membukanya sebagai panel di bawah bilah judul (bisa digulir), ⚙ lagi menutupnya.
- **Legenda:** jadi tombol kecil "Legenda" di kiri bawah; ditekan → isi legenda muncul bertumpuk.
- **Analisis:** awalnya terlipat (desktop tetap terbuka). Dibuka → lembar ±80% tinggi layar, kartu bertumpuk satu
  kolom dan bisa digulir; tiap grafik ±260 px tinggi.
- **Detail kelurahan:** lembar di bawah layar (lebar penuh, maks ±55% tinggi, bisa digulir), di atas laci.
- **Peta:** tombol +/− disembunyikan (cubit untuk zoom); padding fitBounds disesuaikan untuk HP.
- **Grafik:** sumbu `fixedrange` di `grafik.py` (berlaku desktop dan HP).

## Keputusan teknis (dari saya)
- Buka/tutup kontrol dan legenda lewat satu callback klien yang menukar kelas `terbuka`.
- Laci: callback server `lipat_laci` diganti callback klien, supaya keadaan awal bisa mengikuti lebar layar
  (HP terlipat, desktop terbuka).
- Hampir semua tata letak HP lewat satu blok `@media (max-width: 640px)` di `assets/style.css`.
- Uji: tes `grafik.py` (fixedrange), lalu cek visual di 375×812 dan desktop, lalu di Vercel.
