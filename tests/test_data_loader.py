import base64
import gzip
import json

import config
import data_loader

MENIT = {"fas": ["F1"], "kel": ["K1"], "opt": [[3.0]], "bg": [[4.0]], "pes": [[5.0]]}


def test_menit_dibaca_dari_env_kalau_tidak_ada_file(tmp_path, monkeypatch):
    isi = base64.b64encode(gzip.compress(json.dumps(MENIT).encode())).decode()
    monkeypatch.setenv(config.ENV_MENIT, isi)
    m = data_loader.muat_menit(tmp_path)
    assert m["fas"] == {"F1": 0} and m["bg"] == [[4.0]]


def test_file_lokal_didahulukan_dari_env(tmp_path, monkeypatch):
    (tmp_path / config.FILE_MENIT).write_text(json.dumps(MENIT), encoding="utf-8")
    monkeypatch.setenv(config.ENV_MENIT, "bukan-base64")
    assert data_loader.muat_menit(tmp_path)["opt"] == [[3.0]]


def test_menit_none_kalau_tidak_ada_file_maupun_env(tmp_path, monkeypatch):
    monkeypatch.delenv(config.ENV_MENIT, raising=False)
    assert data_loader.muat_menit(tmp_path) is None
