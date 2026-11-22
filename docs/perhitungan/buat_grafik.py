"""Buat SVG kurva sigmoid φ(t) dan contoh TFN untuk halaman penjelasan perhitungan.

Nilai α dan γ dihitung dengan fungsi model (data_bersama.alpha_gamma), bukan diketik ulang.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model"))
import data_bersama as db  # noqa: E402

A, G = db.alpha_gamma(db.T_BAIK, db.PHI_BAIK, db.T_BURUK, db.PHI_BURUK)
TL, TM, TU = 9.867, 9.867, 13.5            # Bojong Rawalumbu -> PKM-51 (setelah koreksi TFN)
KAPPA = 0.9782422295297826

W, H, KIRI, KANAN, ATAS, BAWAH = 720, 340, 56, 20, 18, 46
T_MAKS = 60.0


def sx(t):
    return KIRI + (W - KIRI - KANAN) * t / T_MAKS


def sy(v):
    return ATAS + (H - ATAS - BAWAH) * (1 - v)


t = np.linspace(0, T_MAKS, 241)
kurva = " ".join(f"{'M' if k == 0 else 'L'}{sx(a):.1f},{sy(b):.1f}" for k, (a, b) in enumerate(zip(t, db.phi(t, A, G))))
bag = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Kurva sigmoid derajat cakupan terhadap waktu tempuh">']
for v in (0, .25, .5, .75, 1):
    bag.append(f'<line x1="{KIRI}" x2="{W - KANAN}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" class="grid"/>'
               f'<text x="{KIRI - 8}" y="{sy(v) + 4:.1f}" class="tik" text-anchor="end">{str(v).replace(".", ",")}</text>')
for m in range(0, 61, 10):
    bag.append(f'<text x="{sx(m):.1f}" y="{H - BAWAH + 18}" class="tik" text-anchor="middle">{m}</text>')
bag.append(f'<text x="{(KIRI + W - KANAN) / 2:.1f}" y="{H - 6}" class="judul-sumbu" text-anchor="middle">waktu tempuh t (menit)</text>')
bag.append(f'<text x="14" y="{(ATAS + H - BAWAH) / 2:.1f}" class="judul-sumbu" text-anchor="middle" '
           f'transform="rotate(-90 14 {(ATAS + H - BAWAH) / 2:.1f})">φ(t)</text>')
# TFN contoh (segitiga μ, diskalakan ke tinggi 0,35 agar terlihat di bawah kurva)
tinggi = 0.35
bag.append(f'<path d="M{sx(TL):.1f},{sy(0):.1f} L{sx(TL):.1f},{sy(tinggi):.1f} L{sx(TU):.1f},{sy(0):.1f} Z" class="tfn"/>')
bag.append(f'<text x="{sx(TU) + 6:.1f}" y="{sy(0.12):.1f}" class="anot">μ(t): TFN (9,867; 9,867; 13,5)</text>')
bag.append(f'<path d="{kurva}" class="kurva"/>')
for tt, vv, teks, dx, anchor in ((15, 0.95, "φ(15) = 0,95", 8, "start"), (40, 0.05, "φ(40) = 0,05", -8, "end"),
                                 (G, 0.5, "γ = 27,5 → φ = 0,5", 8, "start")):
    bag.append(f'<circle cx="{sx(tt):.1f}" cy="{sy(vv):.1f}" r="4.5" class="titik"/>'
               f'<text x="{sx(tt) + dx:.1f}" y="{sy(vv) - 8:.1f}" class="anot" text-anchor="{anchor}">{teks}</text>')
bag.append(f'<line x1="{sx(TL):.1f}" x2="{sx(TU):.1f}" y1="{sy(KAPPA):.1f}" y2="{sy(KAPPA):.1f}" class="kappa"/>'
           f'<text x="{sx(TU) + 6:.1f}" y="{sy(KAPPA) + 14:.1f}" class="anot">κ = 0,978</text>')
bag.append("</svg>")
(Path(__file__).with_name("grafik_sigmoid.svg")).write_text("\n".join(bag), encoding="utf-8")
print(f"alpha={A:.6f} gamma={G:.4f}")
