"""PELAN-V2 P12/P14: H4a (bukan-inferioriti, Δ dianjak δ) + H4b (keunggulan + p rawak × k), Holm k = 2; sistem mypii-v1 dari worktree tag."""

import json
import subprocess

import pytest

from mypii import konfig
from mypii.nilai import statistik as st
from mypii.nilai import statistik_v2

V2 = konfig.utama()["nilai"]["statistik"]["v2"]
HA, HB = V2["hipotesis"]["H4a"]["sistem"], V2["hipotesis"]["H4b"]["sistem"]


def _dok(n):
    return [{"id": str(i), "bahasa": "ms", "teks": "x" * 20, "spans": [{"mula": 0, "tamat": 12, "entiti": "MY_NRIC"}]} for i in range(n)]


def _betul(dok, kadar):
    """Ramalan yang betul untuk `kadar` pertama dokumen, salah span untuk selebihnya."""
    cut = int(len(dok) * kadar)
    return [[{"mula": 0, "tamat": 12, "entiti": "MY_NRIC"}] if i < cut else [{"mula": 1, "tamat": 12, "entiti": "MY_NRIC"}]
            for i in range(len(dok))]


def _jalan(ramalan, dok, monkeypatch):
    monkeypatch.setitem(konfig.utama()["nilai"]["statistik"], "ulangan", 200)
    h = st.jalankan(dok, ramalan, eksplorasi=set())
    return statistik_v2.h4(h, dok, ramalan)["hipotesis"]


def test_v2_lebih_baik_kedua_disokong(monkeypatch):
    dok = _dok(80)
    r = _jalan({"mypii": _betul(dok, 1.0), HA: _betul(dok, 0.6), HB: _betul(dok, 0.3)}, dok, monkeypatch)
    assert r["H4a"]["disokong"] and r["H4b"]["disokong"] and not r["H4b"]["beza_kecil"]


def test_sama_bukan_inferior_tetapi_bukan_unggul(monkeypatch):
    dok = _dok(80)
    sama = _betul(dok, 0.7)
    r = _jalan({"mypii": sama, HA: sama, HB: sama}, dok, monkeypatch)
    assert r["H4a"]["disokong"]            # Δ = 0 > −δ: bukan-inferior
    assert not r["H4b"]["disokong"] and r["H4b"]["p_bootstrap"] == 1.0


def test_lebih_teruk_melebihi_margin_tidak_bukan_inferior(monkeypatch):
    dok = _dok(80)
    r = _jalan({"mypii": _betul(dok, 0.5), HA: _betul(dok, 0.9), HB: _betul(dok, 0.1)}, dok, monkeypatch)
    assert not r["H4a"]["disokong"] and r["H4a"]["p_bootstrap"] == 1.0


def test_p_rawak_syarat_hanya_h4b(monkeypatch):
    dok = _dok(80)
    r = _jalan({"mypii": _betul(dok, 1.0), HA: _betul(dok, 0.6), HB: _betul(dok, 0.3)}, dok, monkeypatch)
    assert r["H4b"]["rawak_syarat"] and not r["H4a"]["rawak_syarat"]
    assert r["H4b"]["p_rawak_bonferroni"] == round(min(1.0, r["H4b"]["p_rawak"] * 2), 4)


def test_mypii_v1_worktree_kod_tag_dan_dibuang(monkeypatch):
    pytest.importorskip("en_core_web_sm")
    from mypii.nilai import v1_worktree
    sebelum = subprocess.run(["git", "worktree", "list"], cwd=konfig.AKAR, capture_output=True, text=True, check=True).stdout
    monkeypatch.setenv("GIT_DIR", "/tiada")   # dari cangkuk git: mesti dibuang oleh modul
    dok = [{"id": "a", "teks": "IC: 45O325-13-1339 ok"}, {"id": "b", "teks": "No. IC 900101-08-1234"}]
    r = v1_worktree.ramal(dok)
    monkeypatch.delenv("GIT_DIR")
    assert r[0] == [] and r[1] == [{"mula": 7, "tamat": 21, "entiti": "MY_NRIC"}]   # v1 tiada normalisasi OCR
    assert subprocess.run(["git", "worktree", "list"], cwd=konfig.AKAR, capture_output=True, text=True, check=True).stdout == sebelum
    assert json.dumps(r)
