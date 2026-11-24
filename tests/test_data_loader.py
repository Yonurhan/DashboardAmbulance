import json

import config
import data_loader

MENIT = {"fas": ["F1"], "kel": ["K1"], "opt": [[3.0]], "bg": [[4.0]], "pes": [[5.0]]}


def test_menit_dibaca_dari_folder_cadangan_kalau_tidak_ada_di_olahan(tmp_path, monkeypatch):
    olahan, rahasia = tmp_path / "olahan", tmp_path / "rahasia"
    olahan.mkdir(), rahasia.mkdir()
    (rahasia / config.FILE_MENIT).write_text(json.dumps(MENIT), encoding="utf-8")
    monkeypatch.setattr(config, "DIR_MENIT_CADANGAN", rahasia)
    m = data_loader.muat_menit(olahan)
    assert m["fas"] == {"F1": 0} and m["bg"] == [[4.0]]


def test_menit_none_kalau_tidak_ada_di_mana_pun(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DIR_MENIT_CADANGAN", tmp_path / "tidak_ada")
    assert data_loader.muat_menit(tmp_path) is None
