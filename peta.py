"""Lapisan peta dash-leaflet (DFD 3.0 dan 5.0).

Catatan API (dash-leaflet 1.1.3, dash-extensions 2.0.6, dicek dari versi terpasang):
- dl.GeoJSON: klik dibaca lewat `n_clicks` + `clickData` (fitur yang diklik);
  gaya per fitur lewat `style` = fungsi JS di assets/peta.js dan `hideout`.
- dl.TileLayer mendukung `className`, dipakai untuk filter CSS khusus tile.
"""
import dash_leaflet as dl
from dash_extensions.javascript import Namespace

import config

NS = Namespace("dasbor", "peta")


def batas_wilayah(geojson):
    """[[lat_min, lng_min], [lat_maks, lng_maks]] dari seluruh poligon."""
    lat, lng = [], []

    def jelajah(k):
        if isinstance(k[0], (int, float)):
            lng.append(k[0])
            lat.append(k[1])
        else:
            for x in k:
                jelajah(x)

    for f in geojson["features"]:
        jelajah(f["geometry"]["coordinates"])
    return [[min(lat), min(lng)], [max(lat), max(lng)]]


def hideout_kelurahan(solusi, kondisi, kode_terpilih):
    """Isi hideout GeoJSON: warna, label kategori, kelurahan terpilih."""
    warna, kat = {}, {}
    for kel, v in solusi["hasil_kelurahan"].items():
        k = v["kategori"][kondisi]
        warna[kel] = config.WARNA_KATEGORI[k]
        kat[kel] = config.LABEL_KATEGORI[k]
    return {"warna": warna, "kategori": kat, "terpilih": kode_terpilih, "aksen": config.WARNA_AKSEN}


def peta_dasar(geojson, hideout):
    """Komponen peta lengkap dengan semua lapisan kosong yang diisi callback."""
    b = batas_wilayah(geojson)
    pusat = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]
    # center + zoom wajib ada di dash-leaflet 1.1.3 (tanpa itu muncul galat "reading 'equals'").
    # Penyesuaian ke batas wilayah dilakukan callback klien (callbacks.py) lewat prop viewport,
    # agar padding panel diperhitungkan.
    return dl.Map(
        id="peta", center=pusat, zoom=11.5, zoomSnap=0.25,
        zoomControl=False, attributionControl=True, className="peta",
        children=[
            dl.TileLayer(url=config.TILE_URL, attribution=config.TILE_ATRIBUSI, className="tile-osm",
                         maxZoom=19),
            dl.ZoomControl(position="topright"),
            dl.GeoJSON(id="geo-kel", data=geojson, hideout=hideout, style=NS("gaya"),
                       onEachFeature=NS("tooltip"), hoverStyle={"weight": 2.5, "color": "#1C1B19"}),
            # Poligon kelurahan ada di overlayPane (zIndex 400). Rute di pane sendiri di atasnya, lalu
            # titik kandidat dan cincin pos inti; ikon pos (DivMarker) ada di markerPane (600) paling atas.
            dl.Pane(name="pane-rute", style={"zIndex": 450}, children=[dl.LayerGroup(id="lap-garis")]),
            dl.Pane(name="pane-faskes", style={"zIndex": 460}, children=[
                dl.LayerGroup(id="lap-kandidat"), dl.LayerGroup(id="lap-inti")]),
            dl.LayerGroup(id="lap-pos"),
        ])


def _tooltip_faskes(f, tambahan=""):
    jenis = "Rumah Sakit" if f["jenis"] == "RS" else "Puskesmas"
    return dl.Tooltip(f"{f['kode']} · {f['nama']} ({jenis}){tambahan}", direction="top", offset=[0, -6])


# Logo rumah sakit: palang putih di kotak bersudut membulat (ukuran tetap saat peta di-zoom).
_SVG_RS = ('<svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true">'
           '<rect x="1" y="1" width="18" height="18" rx="5" fill="{warna}" stroke="#FFFFFF" stroke-width="2"/>'
           '<path d="M8.5 5h3v3.5H15v3h-3.5V15h-3v-3.5H5v-3h3.5z" fill="#FFFFFF"/></svg>')


def ikon_faskes(f):
    """DivMarker logo rumah sakit untuk satu faskes (RS dan Puskesmas memakai logo yang sama)."""
    return dl.DivMarker(position=[f["lat"], f["lng"]], children=_tooltip_faskes(f), iconOptions={
        "className": f"ikon-faskes ikon-{f['jenis'].lower()}", "html": _SVG_RS.format(warna=config.WARNA_TEKS),
        "iconSize": [20, 20], "iconAnchor": [10, 10]})


def lapisan_pos(solusi, data):
    """Penanda pos terpilih: logo rumah sakit."""
    return [ikon_faskes(data["faskes"][kode]) for kode in solusi["pos"]]


def lapisan_kandidat(solusi, data):
    """Faskes kandidat yang tidak terpilih: logo rumah sakit abu-abu, lebih kecil."""
    terpilih = set(solusi["pos"])
    return [dl.DivMarker(position=[f["lat"], f["lng"]], children=_tooltip_faskes(f), iconOptions={
                "className": "ikon-faskes ikon-kandidat", "html": _SVG_RS.format(warna="#8A867E"),
                "iconSize": [14, 14], "iconAnchor": [7, 7]})
            for kode, f in data["faskes"].items() if kode not in terpilih]


def lapisan_pos_inti(daftar, data):
    """Pos inti: cincin ganda berwarna aksen; tooltip berisi frekuensi."""
    out = []
    for kode, frek in daftar:
        f = data["faskes"][kode]
        teks = f" — pos inti {frek:.0f}%".replace(".", ",")
        out.append(dl.CircleMarker(center=[f["lat"], f["lng"]], radius=12, color=config.WARNA_AKSEN, weight=2,
                                   fill=False, children=_tooltip_faskes(f, teks)))
        out.append(dl.CircleMarker(center=[f["lat"], f["lng"]], radius=16, color=config.WARNA_AKSEN, weight=1,
                                   opacity=0.6, fill=False, interactive=False))
    return out


def lapisan_garis(detail):
    """Jalur dari pos (mulai) ke centroid kelurahan (selesai), magenta agar kontras dengan wilayah.

    Mulai: cincin magenta mengelilingi ikon pos. Selesai: titik putih bergaris magenta di centroid.
    Rute jalan OSRM (garis utuh) kalau sudah diambil; kalau belum, garis lurus putus-putus (ilustrasi).
    """
    if not detail:
        return []
    centroid, pos = detail["garis"]
    if detail.get("rute"):
        jalur = detail["rute"]                       # OSRM: pos -> kelurahan
        garis = [dl.Polyline(positions=jalur, color="#FFFFFF", weight=8, opacity=0.95, interactive=False),
                 dl.Polyline(positions=jalur, color=config.WARNA_RUTE, weight=4.5, interactive=False)]
    else:
        jalur = [pos, centroid]
        garis = [dl.Polyline(positions=jalur, color=config.WARNA_RUTE, weight=3, dashArray="6 6",
                             interactive=False)]
    return garis + [
        dl.CircleMarker(center=jalur[0], radius=15, color=config.WARNA_RUTE, weight=3, fill=False,
                        interactive=False),
        dl.CircleMarker(center=jalur[-1], radius=5, color=config.WARNA_RUTE, weight=3, fillColor="#FFFFFF",
                        fillOpacity=1, interactive=False),
    ]
