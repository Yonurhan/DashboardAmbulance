"""Tes isi panel detail (layout.panel_detail) dan lapisan rute (peta.lapisan_rute)."""
import config
import layout
import peta

DETAIL = {
    "kode": "K1", "nama": "Bojong Rawalumbu", "kecamatan": "Rawalumbu", "penduduk": 80505, "lansia": 4409,
    "bobot": 0.0306, "pos_kode": "PKM-51", "pos_nama": "Puskesmas Mustika Sari", "cakupan": 0.978,
    "tercakup": True, "kategori": {"lengang": "<=15", "biasa": "<=15", "sibuk": "<=15"},
    "garis": [[-6.27, 106.99], [-6.28, 107.00]],
    "menit": {"lengang": {"menit": 8.2, "pos": "RS-18"}, "biasa": {"menit": 9.6, "pos": "PKM-51"},
              "sibuk": {"menit": 13.5, "pos": "PKM-51"}},
    "rute": [[-6.28, 107.00], [-6.275, 106.995], [-6.27, 106.99]],
}


def _semua(komp):
    """Kumpulkan semua komponen Dash secara rekursif."""
    out = [komp]
    anak = getattr(komp, "children", None)
    if isinstance(anak, (list, tuple)):
        for a in anak:
            out += _semua(a)
    elif anak is not None and not isinstance(anak, (str, int, float)):
        out += _semua(anak)
    return out


def _teks(komponen):
    hasil = []
    for k in komponen:
        for x in _semua(k) if not isinstance(k, str) else [k]:
            if isinstance(x, str):
                hasil.append(x)
            elif isinstance(getattr(x, "children", None), str):
                hasil.append(x.children)
    return " ".join(hasil)


def _kelas(komponen, nama):
    return [x for k in komponen for x in _semua(k) if nama in (getattr(x, "className", "") or "").split()]


def test_menit_besar_mengikuti_kondisi_terpilih():
    for kondisi, harap in (("lengang", "8,2"), ("biasa", "9,6"), ("sibuk", "13,5")):
        isi = layout.panel_detail(DETAIL, kondisi)
        besar = _kelas(isi, "menit-besar")
        assert len(besar) == 1, kondisi
        assert harap in _teks([besar[0]])
        assert DETAIL["menit"][kondisi]["pos"] in _teks(isi)


def test_panel_tanpa_catatan_sumber():
    teks = _teks(layout.panel_detail(DETAIL, "biasa"))
    assert "Google (03.00" not in teks and "Rute: OSRM" not in teks and "Garis lurus" not in teks


def test_panel_tanpa_data_menit_tidak_ada_menit_besar():
    isi = layout.panel_detail({**DETAIL, "menit": None}, "biasa")
    assert _kelas(isi, "menit-besar") == []


def test_rute_warna_kontras_tanpa_label_teks():
    lap = peta.lapisan_rute(DETAIL)
    garis = [x for x in lap if type(x).__name__ == "Polyline"]
    assert any(g.color == config.WARNA_RUTE for g in garis)
    assert config.WARNA_RUTE not in config.WARNA_KATEGORI.values()
    # tidak ada label teks Mulai/Selesai lagi
    assert not any(type(x).__name__ == "DivMarker" for x in lap)
    # ujung selesai (centroid kelurahan) ditandai titik kecil; ujung mulai (pos) cincin magenta di sekitar ikon
    titik = [x for x in lap if type(x).__name__ == "CircleMarker"]
    assert any(t.center == DETAIL["rute"][-1] and t.radius <= 6 for t in titik)
    # tidak ada lingkaran di logo rumah sakit (ujung mulai): logo pos sendiri sudah jadi penandanya
    assert not any(t.center == DETAIL["rute"][0] for t in titik)


def _cari(komp, nama_tipe):
    hasil = [komp] if type(komp).__name__ == nama_tipe else []
    anak = getattr(komp, "children", None)
    for a in (anak if isinstance(anak, (list, tuple)) else [anak] if anak is not None else []):
        if not isinstance(a, (str, int, float)):
            hasil += _cari(a, nama_tipe)
    return hasil


def test_rute_berada_di_pane_di_atas_poligon():
    """Rute di pane tersendiri (zIndex > 400 overlayPane tempat poligon), di bawah ikon pos."""
    m = peta.peta_dasar({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [107.0, -6.3]}}]},
        [[-6.3, 107.0], [-6.3, 107.0]])
    panes = {p.name: p for p in _cari(m, "Pane")}
    assert "pane-rute" in panes and panes["pane-rute"].style["zIndex"] > 400
    assert "lap-rute" in [g.id for g in _cari(panes["pane-rute"], "LayerGroup")]


def test_pos_terpilih_memakai_ikon_rumah_sakit():
    data = {"faskes": {"RS-01": {"kode": "RS-01", "nama": "RS A", "jenis": "RS", "lat": -6.2, "lng": 107.0},
                       "PKM-01": {"kode": "PKM-01", "nama": "PKM B", "jenis": "PKM", "lat": -6.3, "lng": 107.1}}}
    lap = peta.lapisan_pos({"pos": ["RS-01", "PKM-01"]}, data)
    assert len(lap) == 2 and all(type(x).__name__ == "DivMarker" for x in lap)
    assert all("ikon-faskes" in x.iconOptions["className"] and "<svg" in x.iconOptions["html"] for x in lap)
    assert sorted(x.position for x in lap) == sorted([[-6.2, 107.0], [-6.3, 107.1]])


def test_kandidat_lain_logo_abu_abu_kecil():
    data = {"faskes": {"RS-01": {"kode": "RS-01", "nama": "RS A", "jenis": "RS", "lat": -6.2, "lng": 107.0},
                       "PKM-01": {"kode": "PKM-01", "nama": "PKM B", "jenis": "PKM", "lat": -6.3, "lng": 107.1}}}
    lap = peta.lapisan_kandidat({"pos": ["RS-01"]}, data)
    assert len(lap) == 1 and type(lap[0]).__name__ == "DivMarker"
    assert "ikon-kandidat" in lap[0].iconOptions["className"] and lap[0].iconOptions["iconSize"] == [14, 14]


def test_catatan_saat_pos_tercepat_berbeda_dari_pos_melayani():
    """Lengang: pos tercepat RS-18 ≠ pos melayani PKM-51 → catatan tampil; Biasa: sama → tidak ada."""
    beda = _kelas(layout.panel_detail(DETAIL, "lengang"), "beda-pos")
    assert len(beda) == 1 and "RS-18" in _teks(beda) and "PKM-51" in _teks(beda)
    assert _kelas(layout.panel_detail(DETAIL, "biasa"), "beda-pos") == []


def test_kerangka_punya_tombol_hp():
    """Tombol ⚙ (kontrol) dan Legenda untuk HP, serta judul panjang/pendek."""
    import data_loader
    akar = layout.buat_layout(data_loader.muat_semua(config.DIR_OLAHAN))
    semua = _semua(akar)
    ids = {getattr(x, "id", None) for x in semua}
    assert {"btn-kontrol", "btn-legenda", "kolom-kiri", "legenda", "btn-laci"} <= ids
    assert _kelas([akar], "judul-panjang") and _kelas([akar], "judul-pendek")
    assert "Pos Gawat Darurat Bekasi" in _teks(_kelas([akar], "judul-pendek"))
