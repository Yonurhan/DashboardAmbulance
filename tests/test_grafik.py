"""Tes figur Plotly (grafik.py)."""
import pytest

import config
import data_loader
import grafik
import logika


@pytest.fixture(scope="module")
def data():
    return data_loader.muat_semua(config.DIR_OLAHAN)


def _titik(fig):
    return [tr for tr in fig.data if tr.type == "scatter" and tr.mode == "markers"]


def test_figur_pareto_customdata(data):
    daftar = logika.daftar_solusi(data, "utama|eksak", 4)
    fig = grafik.figur_pareto(daftar, 3)
    ids = sorted(int(c) for tr in _titik(fig) for c in tr.customdata)
    assert ids == [s["solusi_id"] for s in daftar]
    aktif = [tr for tr in _titik(fig) if list(tr.customdata) == [3]]
    assert aktif and aktif[0].marker.color == config.WARNA_AKSEN
    assert fig.layout.xaxis.title.text.startswith("Z2")


def test_figur_pareto_satu_solusi_anotasi(data):
    daftar = logika.daftar_solusi(data, "utama|eksak", 2)
    assert len(daftar) == 1
    fig = grafik.figur_pareto(daftar, 1)
    assert any("satu solusi" in a.text for a in fig.layout.annotations)


def test_figur_kenaikan_20_titik(data):
    k = data["metrik"]["utama|eksak"]["kenaikan_cakupan"]
    fig = grafik.figur_kenaikan(k, 10)
    garis = [tr for tr in fig.data if tr.type == "scatter" and tr.mode and "lines" in tr.mode][0]
    assert list(garis.x) == list(range(1, 21))
    # satu sumbu saja (tanpa sumbu kedua); selisih ada di tooltip
    assert not any(tr.type == "bar" for tr in fig.data)
    assert "yaxis2" not in fig.layout.to_plotly_json()
    assert garis.customdata[0][0] == "—" and garis.customdata[1][0].startswith("+")
    assert any(tr.type == "scatter" and list(tr.x) == [10] for tr in fig.data)


def test_figur_pareto_dua_solusi_tetap_ada_garis(data):
    daftar = logika.daftar_solusi(data, "utama|eksak", 1)
    assert len(daftar) == 2
    fig = grafik.figur_pareto(daftar, 1)
    assert any(tr.mode == "lines" for tr in fig.data)
