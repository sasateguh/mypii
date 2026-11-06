"""Analisis kuasa pra-daftar (PELAN-C C4a, ADR-007): SE dari lebar CI Δ, MDE = (z_{1-α'} + z_kuasa)·SE."""

import json
from statistics import NormalDist

import pytest

from mypii.nilai import kuasa

Z = NormalDist()


def _h(lebar_se: float, k: int = 4, dokumen: int = 1000, split: str = "dev") -> dict:
    """CI Δ dibina supaya SE sebenar = lebar_se (aras 0.95)."""
    z = Z.inv_cdf(0.975)
    v = {"delta": 0.1, "bawah": 0.1 - z * lebar_se, "atas": 0.1 + z * lebar_se}
    return {"split": split, "dokumen": dokumen, "config": {"aras": 0.95},
            "banding": {f"g{i}": {"semua|*": dict(v)} for i in range(k)}}


def test_se_dan_mde_formula():
    b = kuasa.kira(_h(0.01), alfa=0.05, kuasa=0.8, n_sasaran=1000, perpuluhan=6)
    assert len(b) == 4
    assert b[0]["se"] == pytest.approx(0.01, abs=1e-6)
    assert b[0]["mde_ketat"] == pytest.approx((Z.inv_cdf(1 - 0.05 / 4) + Z.inv_cdf(0.8)) * 0.01, abs=1e-6)
    assert b[0]["mde_longgar"] == pytest.approx((Z.inv_cdf(0.95) + Z.inv_cdf(0.8)) * 0.01, abs=1e-6)
    assert b[0]["mde_ketat"] > b[0]["mde_longgar"]


def test_k_mengikut_bilangan_garis_dasar():
    satu = kuasa.kira(_h(0.01, k=1), 0.05, 0.8, 1000, 6)[0]
    empat = kuasa.kira(_h(0.01, k=4), 0.05, 0.8, 1000, 6)[0]
    assert satu["mde_ketat"] == satu["mde_longgar"]
    assert empat["mde_ketat"] > satu["mde_ketat"]


def test_skala_saiz_sampel():
    b = kuasa.kira(_h(0.01), 0.05, 0.8, n_sasaran=4000, perpuluhan=6)[0]
    assert b["se"] == pytest.approx(0.005, abs=1e-6)  # √(1000/4000) = ½


def test_kuasa_lebih_tinggi_mde_lebih_besar():
    a = kuasa.kira(_h(0.01), 0.05, 0.8, 1000, 6)[0]
    b = kuasa.kira(_h(0.01), 0.05, 0.9, 1000, 6)[0]
    assert b["mde_ketat"] > a["mde_ketat"]


def test_split_dikunci_ditolak(tmp_path, capsys):
    f = tmp_path / "s.json"
    f.write_text(json.dumps(_h(0.01, split="ujian2")))
    import sys
    lama = sys.argv
    sys.argv = ["kuasa", "--fail", str(f)]
    try:
        assert kuasa.main() == 2
    finally:
        sys.argv = lama
    assert "dikunci" in capsys.readouterr().err


def test_jadual_md_satu_baris_setiap_perbandingan():
    b = kuasa.kira(_h(0.01, k=3), 0.05, 0.8, 1000)
    md = kuasa.jadual_md(b, 3, 0.05, 0.8)
    assert md.count("\n| g") == 3 and "k = 3" in md
