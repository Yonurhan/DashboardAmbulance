"""Generator DFD (Data Flow Diagram) Dashboard Lokasi Pos Gawat Darurat Kota Bekasi.

Satu sumber untuk tiga diagram: Diagram Konteks (level 0), DFD Level 1, dan DFD Level 2 Proses 2.0.
Setiap diagram ditulis dua kali:
- <nama>.svg    : gambar siap tempel ke skripsi (Word/LaTeX bisa memakai SVG langsung);
- <nama>.drawio : file draw.io (app.diagrams.net) yang bisa dibuka, diedit, dan diekspor ke PNG/PDF.

Notasi bawaan Yourdon/DeMarco (proses = lingkaran). Notasi Gane–Sarson (proses = persegi
bersudut tumpul dengan pita nomor) tersedia lewat argumen:
    python docs/dfd/buat_dfd.py              # Yourdon/DeMarco
    python docs/dfd/buat_dfd.py gane-sarson  # Gane–Sarson
"""
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

FOLDER = Path(__file__).resolve().parent
FONT = "Arial, Helvetica, sans-serif"
TINTA = "#111111"
ABU = "#555555"


# ============================================================ bentuk
def entitas(id_, label, x, y, w=160, h=64):
    return {"id": id_, "jenis": "entitas", "label": label, "x": x, "y": y, "w": w, "h": h}


def proses(id_, nomor, nama, cx, cy, r=78, putus=False):
    return {"id": id_, "jenis": "proses", "nomor": nomor, "label": nama, "cx": cx, "cy": cy, "r": r,
            "putus": putus}


def simpan(id_, kode, nama, x, y, w=240, h=40):
    return {"id": id_, "jenis": "simpan", "kode": kode, "label": nama, "x": x, "y": y, "w": w, "h": h}


def alir(dari, ke, label, geser=0, posisi=0.5, label_dx=0, label_dy=-9, lewat=()):
    """Aliran data dari bentuk `dari` ke bentuk `ke`.

    geser  : pergeseran sejajar (px) agar beberapa aliran antara dua bentuk yang sama tidak menumpuk;
             arahnya tegak lurus terhadap garis antar-pusat (urutan id), sehingga + dan − konsisten.
    posisi : letak label sepanjang segmen terpanjang (0 = awal, 1 = akhir).
    lewat  : titik belok [(x, y), ...] bila garis perlu dibelokkan.
    """
    return {"dari": dari, "ke": ke, "label": label, "geser": geser, "posisi": posisi,
            "dx": label_dx, "dy": label_dy, "lewat": list(lewat)}


def pusat(b):
    if b["jenis"] == "proses":
        return b["cx"], b["cy"]
    return b["x"] + b["w"] / 2, b["y"] + b["h"] / 2


def kotak(b, notasi):
    """Kotak pembatas bentuk (dipakai draw.io dan uji titik)."""
    if b["jenis"] == "proses":
        if notasi == "gane-sarson":
            w, h = b["r"] * 2, b["r"] * 1.45
            return b["cx"] - w / 2, b["cy"] - h / 2, w, h
        return b["cx"] - b["r"], b["cy"] - b["r"], 2 * b["r"], 2 * b["r"]
    return b["x"], b["y"], b["w"], b["h"]


def di_dalam(b, p, notasi):
    x, y = p
    if b["jenis"] == "proses" and notasi == "yourdon":
        return math.hypot(x - b["cx"], y - b["cy"]) <= b["r"]
    bx, by, bw, bh = kotak(b, notasi)
    return bx <= x <= bx + bw and by <= y <= by + bh


def potong_tepi(b, dalam, luar, notasi):
    """Titik pada tepi bentuk b di segmen dalam→luar (bisection)."""
    a, c = dalam, luar
    for _ in range(40):
        m = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
        if di_dalam(b, m, notasi):
            a = m
        else:
            c = m
    return c


def jalur(f, bentuk, notasi):
    """Titik-titik garis aliran, sudah dipotong di tepi kedua bentuk."""
    A, B = bentuk[f["dari"]], bentuk[f["ke"]]
    pa, pb = pusat(A), pusat(B)
    # arah tegak lurus dihitung dari pasangan id yang diurutkan agar geser +/− konsisten dua arah
    p1, p2 = (pa, pb) if f["dari"] < f["ke"] else (pb, pa)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(dx, dy) or 1
    tx, ty = -dy / n * f["geser"], dx / n * f["geser"]
    titik = [(pa[0] + tx, pa[1] + ty)] + f["lewat"] + [(pb[0] + tx, pb[1] + ty)]
    titik[0] = potong_tepi(A, titik[0], titik[1], notasi)
    titik[-1] = potong_tepi(B, titik[-1], titik[-2], notasi)
    return titik


def letak_label(f, titik):
    segmen = max(zip(titik, titik[1:]), key=lambda s: math.dist(*s))
    (x1, y1), (x2, y2) = segmen
    t = f["posisi"]
    return x1 + (x2 - x1) * t + f["dx"], y1 + (y2 - y1) * t + f["dy"]


# ============================================================ SVG
def _teks(x, y, baris, ukuran=13, tebal=False, warna=TINTA, halo=False, anchor="middle"):
    baris = baris.split("\n")
    tinggi = ukuran * 1.22
    y0 = y - (len(baris) - 1) * tinggi / 2
    gaya = f'font-family="{FONT}" font-size="{ukuran}" fill="{warna}" text-anchor="{anchor}"'
    if tebal:
        gaya += ' font-weight="bold"'
    if halo:
        gaya += ' stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'
    isi = "".join(f'<tspan x="{x:.1f}" y="{y0 + i * tinggi:.1f}" dominant-baseline="middle">{escape(b)}</tspan>'
                  for i, b in enumerate(baris))
    return f"<text {gaya}>{isi}</text>"


def svg_bentuk(b, notasi):
    if b["jenis"] == "entitas":
        return (f'<rect x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" fill="#FFFFFF" '
                f'stroke="{TINTA}" stroke-width="2"/>' + _teks(*pusat(b), b["label"], 14, tebal=True))
    if b["jenis"] == "simpan":
        x, y, w, h = b["x"], b["y"], b["w"], b["h"]
        kode_w = 46
        return (f'<path d="M{x + w},{y} H{x} V{y + h} H{x + w}" fill="none" stroke="{TINTA}" stroke-width="2"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFFFF" stroke="none" opacity="0"/>'
                f'<line x1="{x + kode_w}" y1="{y}" x2="{x + kode_w}" y2="{y + h}" stroke="{TINTA}" stroke-width="1.5"/>'
                + _teks(x + kode_w / 2, y + h / 2, b["kode"], 13, tebal=True)
                + _teks(x + kode_w + 10, y + h / 2, b["label"], 13, anchor="start"))
    garis = f'stroke="{ABU if b["putus"] else TINTA}" stroke-width="2"' + (' stroke-dasharray="7 5"' if b["putus"] else "")
    cx, cy = b["cx"], b["cy"]
    if notasi == "gane-sarson":
        x, y, w, h = kotak(b, notasi)
        pita = 26
        return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="#FFFFFF" {garis}/>'
                f'<line x1="{x:.1f}" y1="{y + pita:.1f}" x2="{x + w:.1f}" y2="{y + pita:.1f}" {garis}/>'
                + _teks(cx, y + pita / 2, b["nomor"], 13, tebal=True)
                + _teks(cx, y + pita + (h - pita) / 2, b["label"], 13))
    return (f'<circle cx="{cx}" cy="{cy}" r="{b["r"]}" fill="#FFFFFF" {garis}/>'
            + _teks(cx, cy - b["r"] * 0.42, b["nomor"], 13, tebal=True)
            + f'<line x1="{cx - b["r"] * 0.72:.1f}" y1="{cy - b["r"] * 0.24:.1f}" x2="{cx + b["r"] * 0.72:.1f}" '
              f'y2="{cy - b["r"] * 0.24:.1f}" stroke="{TINTA}" stroke-width="1"/>'
            + _teks(cx, cy + b["r"] * 0.22, b["label"], 13))


def buat_svg(diagram, notasi):
    bentuk = {b["id"]: b for b in diagram["bentuk"]}
    W, H = diagram["ukuran"]
    bagian = ['<?xml version="1.0" encoding="UTF-8"?>',
              f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
              f'<title>{escape(diagram["judul"])}</title>',
              '<defs><marker id="panah" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="9" markerHeight="9" '
              f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{TINTA}"/></marker></defs>',
              f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    label = []
    for f in diagram["alir"]:
        titik = jalur(f, bentuk, notasi)
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in titik)
        bagian.append(f'<path d="{d}" fill="none" stroke="{TINTA}" stroke-width="1.4" marker-end="url(#panah)"/>')
        label.append(_teks(*letak_label(f, titik), f["label"], 12, halo=True))
    bagian += [svg_bentuk(b, notasi) for b in diagram["bentuk"]]
    bagian += label                                   # label terakhir agar selalu di atas garis dan bentuk
    bagian.append("</svg>")
    return "\n".join(bagian)


# ============================================================ draw.io
def _sel(id_, nilai, gaya, x, y, w, h):
    nilai = escape(nilai, {'"': "&quot;", "\n": "&#xa;"})
    return (f'<mxCell id="{id_}" value="{nilai}" style="{gaya}" vertex="1" parent="1">'
            f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>')


def buat_drawio(diagram, notasi):
    bentuk = {b["id"]: b for b in diagram["bentuk"]}
    sel = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    teks = f"fontFamily=Arial;fontSize=13;fontColor={TINTA};strokeColor={TINTA};strokeWidth=2;whiteSpace=wrap;html=0;"
    for b in diagram["bentuk"]:
        x, y, w, h = kotak(b, notasi)
        if b["jenis"] == "entitas":
            sel.append(_sel(b["id"], b["label"], teks + "rounded=0;fillColor=#FFFFFF;fontStyle=1;fontSize=14;", x, y, w, h))
        elif b["jenis"] == "simpan":
            gaya = teks + "shape=partialRectangle;right=0;fillColor=#FFFFFF;align=left;spacingLeft=56;"
            sel.append(_sel(b["id"], b["label"], gaya, x, y, w, h))
            sel.append(_sel(b["id"] + "_kode", b["kode"], teks + "shape=partialRectangle;top=0;bottom=0;left=0;"
                            "fillColor=none;fontStyle=1;strokeWidth=1.5;", x, y, 46, h))
        else:
            putus = "dashed=1;strokeColor=#555555;" if b["putus"] else ""
            bentuk_gaya = "rounded=1;arcSize=12;" if notasi == "gane-sarson" else "ellipse;"
            sel.append(_sel(b["id"], f'{b["nomor"]}\n{b["label"]}', teks + bentuk_gaya + "fillColor=#FFFFFF;" + putus,
                            x, y, w, h))
    for i, f in enumerate(diagram["alir"]):
        titik = jalur(f, bentuk, notasi)
        A, B = bentuk[f["dari"]], bentuk[f["ke"]]
        ax, ay, aw, ah = kotak(A, notasi)
        bx, by, bw, bh = kotak(B, notasi)
        (sx, sy), (ex, ey) = titik[0], titik[-1]
        gaya = (f"endArrow=block;endFill=1;html=0;strokeColor={TINTA};strokeWidth=1.4;fontFamily=Arial;fontSize=12;"
                f"labelBackgroundColor=#FFFFFF;exitX={(sx - ax) / aw:.3f};exitY={(sy - ay) / ah:.3f};exitPerimeter=0;"
                f"entryX={(ex - bx) / bw:.3f};entryY={(ey - by) / bh:.3f};entryPerimeter=0;")
        tengah = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in f["lewat"])
        lx, ly = letak_label(f, titik)
        nilai = escape(f["label"], {'"': "&quot;", "\n": "&#xa;"})
        sel.append(f'<mxCell id="a{i}" value="{nilai}" style="{gaya}" edge="1" parent="1" source="{f["dari"]}" '
                   f'target="{f["ke"]}"><mxGeometry relative="1" as="geometry">'
                   + (f'<Array as="points">{tengah}</Array>' if tengah else "")
                   + '</mxGeometry></mxCell>')
    W, H = diagram["ukuran"]
    return ('<mxfile host="app.diagrams.net"><diagram name="' + escape(diagram["judul"]) + '">'
            f'<mxGraphModel dx="{W}" dy="{H}" grid="1" gridSize="10" guides="1" page="1" pageWidth="{W}" '
            f'pageHeight="{H}"><root>' + "".join(sel) + "</root></mxGraphModel></diagram></mxfile>")


# ============================================================ isi diagram
# Nama aliran dibuat SAMA di semua level agar DFD seimbang (balancing).
ADMIN_MASUK_LOGIN, ADMIN_KELUAR_LOGIN = "data login admin", "status login"
ADMIN_MASUK_FILE, ADMIN_KELUAR_LAPORAN = "berkas hasil optimasi\ndan data pendukung", "laporan validasi data"
P_PILIHAN = "pilihan skenario, jumlah pos,\nkondisi lalu lintas, solusi"
P_SAKELAR, P_KELURAHAN = "sakelar pos inti", "kelurahan dipilih"
P_PETA, P_ANALISIS, P_DETAIL = ("peta solusi dan\nringkasan metrik", "grafik analisis\ndan pos inti",
                                "detail kelurahan\ndan rute jalan")
OSRM_MINTA, OSRM_RUTE = "permintaan rute", "geometri rute jalan"


def diagram_konteks():
    b = [entitas("admin", "Admin", 50, 240, 170, 140),
         proses("p0", "0", "Sistem Dashboard\nLokasi Pos\nGawat Darurat\nKota Bekasi", 680, 310, r=130),
         entitas("perencana", "Perencana\n(Dinkes / PSC 119)", 1190, 190, 200, 240),
         entitas("osrm", "Layanan Rute\n(OSRM)", 585, 560, 190, 64)]
    f = [alir("admin", "p0", ADMIN_MASUK_LOGIN, geser=48),
         alir("p0", "admin", ADMIN_KELUAR_LOGIN, geser=16),
         alir("admin", "p0", ADMIN_MASUK_FILE.replace("\n", " "), geser=-16),
         alir("p0", "admin", ADMIN_KELUAR_LAPORAN, geser=-48),
         alir("perencana", "p0", P_PILIHAN.replace("\n", " "), geser=-80),
         alir("perencana", "p0", P_SAKELAR, geser=-48),
         alir("perencana", "p0", P_KELURAHAN, geser=-16),
         alir("p0", "perencana", P_PETA.replace("\n", " "), geser=16),
         alir("p0", "perencana", P_ANALISIS.replace("\n", " "), geser=48),
         alir("p0", "perencana", P_DETAIL.replace("\n", " "), geser=80),
         alir("p0", "osrm", OSRM_MINTA, geser=-36, label_dx=-62, label_dy=0),
         alir("osrm", "p0", OSRM_RUTE, geser=36, label_dx=72, label_dy=0)]
    return {"nama": "dfd-0-konteks", "judul": "Diagram Konteks", "ukuran": (1440, 650), "bentuk": b, "alir": f}


def diagram_level1():
    b = [entitas("admin", "Admin", 30, 330, 150, 64),
         proses("p1", "1.0", "Kelola Login\nAdmin", 360, 150, r=74),
         proses("p2", "2.0", "Kelola Data\nHasil Optimasi", 360, 590, r=84),
         simpan("d1", "D1", "Admin", 560, 60, 220),
         simpan("d5", "D5", "Metrik Analisis", 640, 280),
         simpan("d2", "D2", "Faskes", 640, 400),
         simpan("d4", "D4", "Solusi Optimasi", 640, 520),
         simpan("d3", "D3", "Kelurahan", 640, 640),
         simpan("d6", "D6", "Waktu Tempuh dan Rute", 640, 760),
         proses("p4", "4.0", "Tampilkan\nAnalisis", 1150, 230, r=80),
         proses("p3", "3.0", "Tampilkan\nSolusi", 1150, 560, r=80),
         proses("p5", "5.0", "Tampilkan Detail\nKelurahan", 1150, 890, r=80),
         entitas("perencana", "Perencana\n(Dinkes / PSC 119)", 1370, 528, 190, 64),
         entitas("osrm", "Layanan Rute\n(OSRM)", 60, 870, 170, 64)]
    f = [alir("admin", "p1", ADMIN_MASUK_LOGIN, geser=-12, label_dx=-48),
         alir("p1", "admin", ADMIN_KELUAR_LOGIN, geser=12, label_dx=40, label_dy=14),
         alir("d1", "p1", "data akun admin", label_dy=-12),
         alir("p1", "p2", "hak akses admin", label_dx=58, label_dy=0),
         alir("admin", "p2", ADMIN_MASUK_FILE, geser=12, label_dx=-60, label_dy=12),
         alir("p2", "admin", ADMIN_KELUAR_LAPORAN, geser=-12, label_dx=58, label_dy=-14),
         alir("p2", "d5", "metrik analisis", posisi=0.62),
         alir("p2", "d2", "data faskes", posisi=0.66),
         alir("p2", "d4", "solusi Pareto", posisi=0.62, label_dy=-10),
         alir("p2", "d3", "data kelurahan", posisi=0.62, label_dy=12),
         alir("p2", "d6", "menit tempuh dan rute", posisi=0.55, label_dy=12),
         alir("p2", "osrm", OSRM_MINTA, geser=-12, label_dx=-58, label_dy=0),
         alir("osrm", "p2", OSRM_RUTE, geser=12, label_dx=72, label_dy=6),
         alir("d5", "p4", "kenaikan cakupan dan\nfrekuensi faskes", posisi=0.5, label_dy=-18),
         alir("d2", "p4", "lokasi faskes", posisi=0.55, label_dy=10),
         alir("d2", "p3", "lokasi faskes", posisi=0.45, label_dy=-10),
         alir("d4", "p3", "solusi Pareto", posisi=0.5, label_dy=-9),
         alir("d3", "p3", "batas kelurahan", posisi=0.5, label_dy=10),
         alir("d3", "p5", "data kelurahan", posisi=0.5, label_dy=-12),
         alir("d6", "p5", "menit tempuh dan rute", posisi=0.5, label_dy=12),
         alir("p3", "p4", "solusi aktif", label_dx=-44, label_dy=0),
         alir("p3", "p5", "solusi aktif", label_dx=-44, label_dy=0),
         alir("perencana", "p3", P_PILIHAN, geser=-16, label_dy=-26),
         alir("p3", "perencana", P_PETA, geser=16, label_dy=26),
         alir("perencana", "p4", P_SAKELAR, geser=18, label_dx=62, label_dy=-2),
         alir("p4", "perencana", P_ANALISIS, geser=-18, label_dx=-72, label_dy=6),
         alir("perencana", "p5", P_KELURAHAN, geser=-18, label_dx=66, label_dy=2),
         alir("p5", "perencana", P_DETAIL, geser=18, label_dx=-74, label_dy=-4)]
    return {"nama": "dfd-1-level1", "judul": "DFD Level 1", "ukuran": (1590, 1000), "bentuk": b, "alir": f}


def diagram_level2_p2():
    b = [proses("p1", "1.0", "Kelola Login\nAdmin", 380, 70, r=52, putus=True),
         entitas("admin", "Admin", 30, 340, 150, 64),
         proses("p21", "2.1", "Terima Berkas\nHasil Optimasi", 380, 250, r=76),
         proses("p22", "2.2", "Validasi\nData", 380, 540, r=72),
         proses("p23", "2.3", "Olah Data\nTampilan", 760, 540, r=80),
         proses("p24", "2.4", "Ambil Rute\nJalan", 760, 820, r=72),
         entitas("osrm", "Layanan Rute\n(OSRM)", 300, 790, 170, 64),
         simpan("d5", "D5", "Metrik Analisis", 1000, 260),
         simpan("d2", "D2", "Faskes", 1000, 380),
         simpan("d4", "D4", "Solusi Optimasi", 1000, 500),
         simpan("d3", "D3", "Kelurahan", 1000, 620),
         simpan("d6", "D6", "Waktu Tempuh dan Rute", 1000, 740)]
    f = [alir("p1", "p21", "hak akses admin", label_dx=58, label_dy=0),
         alir("admin", "p21", ADMIN_MASUK_FILE, label_dx=-34, label_dy=-22),
         alir("p21", "p22", "berkas hasil optimasi", label_dx=74, label_dy=0),
         alir("p22", "admin", ADMIN_KELUAR_LAPORAN, label_dx=-30, label_dy=18),
         alir("p22", "p23", "data tervalidasi", label_dy=-10),
         alir("p23", "d5", "metrik analisis", posisi=0.6),
         alir("p23", "d2", "data faskes", posisi=0.6),
         alir("p23", "d4", "solusi Pareto", posisi=0.55),
         alir("p23", "d3", "data kelurahan", posisi=0.55, label_dy=12),
         alir("p23", "d6", "menit tempuh", posisi=0.6, label_dy=12),
         alir("p23", "p24", "pasangan\nkelurahan–pos", label_dx=-56, label_dy=0),
         alir("p24", "osrm", OSRM_MINTA, geser=16, label_dy=18),
         alir("osrm", "p24", OSRM_RUTE, geser=-16, label_dy=-18),
         alir("p24", "d6", "rute jalan", posisi=0.55, label_dy=14)]
    return {"nama": "dfd-2-proses2", "judul": "DFD Level 2 Proses 2.0", "ukuran": (1270, 920), "bentuk": b,
            "alir": f}


def main():
    notasi = sys.argv[1] if len(sys.argv) > 1 else "yourdon"
    if notasi not in ("yourdon", "gane-sarson"):
        sys.exit("notasi harus 'yourdon' atau 'gane-sarson'")
    akhiran = "" if notasi == "yourdon" else "-gane-sarson"
    for diagram in (diagram_konteks(), diagram_level1(), diagram_level2_p2()):
        (FOLDER / f'{diagram["nama"]}{akhiran}.svg').write_text(buat_svg(diagram, notasi), encoding="utf-8")
        (FOLDER / f'{diagram["nama"]}{akhiran}.drawio').write_text(buat_drawio(diagram, notasi), encoding="utf-8")
        print("ditulis:", diagram["nama"] + akhiran, "(.svg, .drawio)")


if __name__ == "__main__":
    main()
