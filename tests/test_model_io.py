"""Tes pemuatan model per skenario (olah/model_io.py)."""
import os

import numpy as np
import pandas as pd
import pytest

import config
from olah import model_io


@pytest.fixture(scope="module")
def d_rho1():
    return model_io.muat_model("rho1")


def test_muat_model_rho1_cocok_matriks(d_rho1):
    m = pd.read_csv(config.SKENARIO["rho1"]["matriks_kappa"], index_col=0)
    m = m.loc[d_rho1["fas"], d_rho1["kel"]].to_numpy(float)
    assert d_rho1["K"].shape == (99, 56)
    np.testing.assert_allclose(d_rho1["K"], m, atol=1e-8)
    assert d_rho1["param"]["RHO"] == 1.0


def test_muat_model_cwd_kembali(monkeypatch):
    sebelum = os.getcwd()

    def gagal(**kw):
        raise SystemExit(1)

    monkeypatch.setattr(model_io.db, "siapkan", gagal)
    with pytest.raises(RuntimeError):
        model_io.muat_model("utama")
    assert os.getcwd() == sebelum


def test_idx_faskes(d_rho1):
    idx = model_io.idx_faskes(d_rho1, ["RS-01", "PKM-01"])
    assert [d_rho1["fas"][i] for i in idx] == ["RS-01", "PKM-01"]
    with pytest.raises(KeyError):
        model_io.idx_faskes(d_rho1, ["XX-99"])
