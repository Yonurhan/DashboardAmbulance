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
            dl.LayerGroup(id="lap-garis"),
            dl.LayerGroup(id="lap-kandidat"),
            dl.LayerGroup(id="lap-inti"),
            dl.LayerGroup(id="lap-pos"),
        ])


def _tooltip_faskes(f, tambahan=""):
    jenis = "Rumah Sakit" if f["jenis"] == "RS" else "Puskesmas"
    return dl.Tooltip(f"{f['kode']} · {f['nama']} ({jenis}){tambahan}", direction="top", offset=[0, -6])


def lapisan_pos(solusi, data):
    """Penanda pos terpilih: lingkaran pekat bercincin putih."""
    out = []
    for kode in solusi["pos"]:
        f = data["faskes"][kode]
        out.append(dl.CircleMarker(center=[f["lat"], f["lng"]], radius=7,
                                   color="#FFFFFF", weight=2.5, fillColor=config.WARNA_TEKS, fillOpacity=1,
                                   children=_tooltip_faskes(f)))
    return out


def lapisan_kandidat(solusi, data):
    """Faskes kandidat yang tidak terpilih: titik abu-abu kecil."""
    terpilih = set(solusi["pos"])
    return [dl.CircleMarker(center=[f["lat"], f["lng"]], radius=3.5, color="#FFFFFF", weight=1,
                            fillColor="#8A867E", fillOpacity=0.9, children=_tooltip_faskes(f))
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
    """Garis lurus putus-putus dari centroid kelurahan ke pos yang melayani (ilustrasi)."""
    if not detail:
        return []
    awal, akhir = detail["garis"]
    return [dl.Polyline(positions=[awal, akhir], color=config.WARNA_AKSEN, weight=2.5, dashArray="6 6",
                        interactive=False),
            dl.CircleMarker(center=awal, radius=4, color="#FFFFFF", weight=2, fillColor=config.WARNA_AKSEN,
                            fillOpacity=1, interactive=False)]
