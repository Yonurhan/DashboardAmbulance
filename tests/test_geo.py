"""Tes pembentukan faskes.json dan kelurahan.geojson (olah/geo.py)."""
import pandas as pd
import pytest

import config
from olah import geo, model_io


@pytest.fixture(scope="module")
def d():
    return model_io.muat_model("rho1")


def test_buat_faskes_99(d):
    f = geo.buat_faskes(config.PATH_FASKES_CSV, d["fas"])
    assert len(f) == 99
    assert sum(x["jenis"] == "RS" for x in f) == 44
    assert sum(x["jenis"] == "PKM" for x in f) == 55
    assert [x["kode"] for x in f] == d["fas"]
    assert set(f[0]) == {"kode", "nama", "jenis", "kecamatan", "lat", "lng"}


@pytest.mark.skipif(not config.PATH_GDB.exists(), reason="GDB tidak tersedia")
def test_kelurahan_56_epsg4326(d):
    fc, lap = geo.buat_kelurahan(config.PATH_GDB, config.PATH_CENTROID_CSV, d, toleransi=0.0001)
    fitur = fc["features"]
    assert len(fitur) == 56
    assert {f["properties"]["kode"] for f in fitur} == set(d["kel"])
    c = pd.read_csv(config.PATH_CENTROID_CSV).set_index("kode_kelurahan")
    for f in fitur:
        pr = f["properties"]
        assert "bobot" not in pr
        assert pr["centroid_lat"] == c.loc[pr["kode"], "lat"]
        assert pr["centroid_lng"] == c.loc[pr["kode"], "lon"]
        koord = f["geometry"]["coordinates"]
        while isinstance(koord[0], list):
            koord = koord[0]
        assert len(koord) == 2 and 106 < koord[0] < 108 and -7 < koord[1] < -6
    assert lap["tidak_cocok"] == []
    assert lap["ukuran_sesudah_kb"] < lap["ukuran_sebelum_kb"]
