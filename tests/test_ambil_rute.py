"""Tes fungsi murni pengambil rute OSRM (scripts/ambil_rute.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ambil_rute  # noqa: E402


def test_pasangan_rute_unik_dari_semua_solusi():
    hasil = [{"solusi": [
        {"hasil_kelurahan": {"K1": {"pos_melayani": "RS-01"}, "K2": {"pos_melayani": "PKM-02"}}},
        {"hasil_kelurahan": {"K1": {"pos_melayani": "RS-01"}, "K2": {"pos_melayani": "RS-01"}}},
    ]}]
    assert ambil_rute.pasangan_rute(hasil) == [("K1", "RS-01"), ("K2", "PKM-02"), ("K2", "RS-01")]


def test_url_rute_dari_pos_ke_kelurahan_lng_lat():
    url = ambil_rute.url_rute((-6.29, 106.96), (-6.24, 106.95))
    assert url.startswith("https://router.project-osrm.org/route/v1/driving/106.96,-6.29;106.95,-6.24?")
    assert "geometries=geojson" in url and "overview=full" in url


def test_ubah_geometri_ke_lat_lng_dan_disederhanakan():
    resp = {"code": "Ok", "routes": [{"geometry": {"coordinates": [[106.96, -6.29], [106.9601, -6.2901],
                                                                   [106.955, -6.27], [106.95, -6.24]]}}]}
    jalur = ambil_rute.ubah_geometri(resp, toleransi=0.0)
    assert jalur[0] == [-6.29, 106.96] and jalur[-1] == [-6.24, 106.95]
    assert len(ambil_rute.ubah_geometri(resp, toleransi=0.001)) < 4


def test_ubah_geometri_gagal_mengembalikan_none():
    assert ambil_rute.ubah_geometri({"code": "NoRoute", "routes": []}) is None
