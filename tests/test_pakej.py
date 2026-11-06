"""Pakej wheel (`pip install mypii`): config + model dibaca dari mypii/_data bila ada, jika tidak dari akar klon."""

import tomllib

import mypii
from mypii import konfig


def test_klon_guna_akar(monkeypatch, tmp_path):
    monkeypatch.setattr(konfig, "DATA_PAKEJ", tmp_path / "tiada")
    assert konfig.akar_data() == konfig.AKAR


def test_wheel_guna_data_pakej(monkeypatch, tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "mypii.yaml").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(konfig, "DATA_PAKEJ", tmp_path)
    monkeypatch.delenv("MYPII_KONFIG", raising=False)
    assert konfig.akar_data() == tmp_path
    assert konfig.folder_konfig() == tmp_path / "config"


def test_force_include_membawa_config_dan_artifak():
    """Artifak pengelas yang dirujuk config mesti dibawa wheel — nama artifak baharu tanpa kemas pyproject = gagal di sini."""
    projek = tomllib.loads((konfig.AKAR / "pyproject.toml").read_text(encoding="utf-8"))
    fi = projek["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    assert fi["config"] == "mypii/_data/config"
    artifak = konfig.utama()["konteks"]["artifak"]
    assert fi[artifak] == f"mypii/_data/{artifak}"


def test_alias_inggeris():
    assert mypii.all_recognizers is mypii.semua_pengecam
    assert "all_recognizers" in mypii.__all__
