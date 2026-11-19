"""Tes isi panel detail (layout.panel_detail) dan lapisan rute (peta.lapisan_garis)."""
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


def test_rute_warna_kontras_dan_penanda_mulai_selesai():
    lap = peta.lapisan_garis(DETAIL)
    garis = [x for x in lap if type(x).__name__ == "Polyline"]
    assert any(g.color == config.WARNA_RUTE for g in garis)
    assert config.WARNA_RUTE not in config.WARNA_KATEGORI.values()
    penanda = [x for x in lap if type(x).__name__ == "DivMarker"]
    kelas = sorted(m.iconOptions["className"] for m in penanda)
    assert kelas == ["penanda-rute penanda-mulai", "penanda-rute penanda-selesai"]
    mulai = [m for m in penanda if "mulai" in m.iconOptions["className"]][0]
    selesai = [m for m in penanda if "selesai" in m.iconOptions["className"]][0]
    assert mulai.position == DETAIL["rute"][0] and selesai.position == DETAIL["rute"][-1]
