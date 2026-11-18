"""Tes kenaikan cakupan dan frekuensi pos inti (olah/metrik.py)."""
import pytest

from olah import metrik


def s(p, z1, pos):
    return {"p": p, "Z1": z1, "pos": pos}


def test_kenaikan_selisih():
    sol = [s(1, 0.6, ["A"]), s(2, 0.7, ["A", "B"]), s(2, 0.65, ["A", "C"]), s(3, 0.75, ["A", "B", "C"])]
    k = metrik.kenaikan_cakupan(sol)
    assert [r["p"] for r in k] == [1, 2, 3]
    assert k[0]["selisih"] is None
    assert k[1]["Z1_terbaik"] == pytest.approx(0.7)
    assert k[1]["selisih"] == pytest.approx(0.1)
    assert k[2]["selisih"] == pytest.approx(0.05)


def test_frekuensi_bobot_p_sama():
    sol = [s(1, 0.5, ["A"])] + [s(2, 0.6, ["A", x]) for x in "BCDE"]
    f = metrik.frekuensi_faskes(sol, ["A", "B", "C", "D", "E"])
    assert f["1"]["A"] == pytest.approx(100.0)
    # p_awal 1: B ada di 0% solusi p=1 dan 25% solusi p=2 -> rata-rata 12,5
    assert f["1"]["B"] == pytest.approx(12.5)
    assert f["2"]["B"] == pytest.approx(25.0)

    sol2 = [s(2, 0.6, ["A", "B"]), s(2, 0.5, ["A", "C"])]
    assert metrik.frekuensi_faskes(sol2, ["A", "B", "C"])["2"]["B"] == pytest.approx(50.0)


def test_frekuensi_semua_faskes_ada():
    f = metrik.frekuensi_faskes([s(1, 0.5, ["A"])], ["A", "B", "Z"])
    assert f["1"] == {"A": 100.0, "B": 0.0, "Z": 0.0}
