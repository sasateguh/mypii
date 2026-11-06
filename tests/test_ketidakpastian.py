"""PELAN-C C3b (ADR-013): blok "Ketidakpastian" BANDINGAN dijana dari output statistik — data sintetik, tiada spaCy/rangkaian."""

import json
import re
import sys

import pytest

from mypii import konfig
from mypii.nilai import ketidakpastian, statistik
from tests.test_statistik import _data


@pytest.fixture(scope="module")
def h():
    """Output `statistik.jalankan` sebenar: mypii baik, 'lemah' sedikit lebih buruk, 'kosong' tiada ramalan."""
    dok, baik = _data(n=60, ralat=0.1)
    _, lemah = _data(n=60, benih=9, ralat=0.4)
    k = dict(konfig.utama()["nilai"]["statistik"], ulangan=200)
    return {"split": "dev", **statistik.jalankan(dok, {"mypii": baik, "lemah": lemah, "kosong": [[] for _ in dok]}, k)}


def test_setiap_angka_blok_dari_json(h):
    b = ketidakpastian.blok(h)
    teks_json = json.dumps(h)
    for x in set(re.findall(r"\b0\.\d+\b|\b1\.0\b", b)):
        if x != "0.95":  # aras config, juga dalam JSON
            assert x in teks_json, x
    for s, ks in h["banding"].items():
        assert re.search(rf"\| {s} \| `\*`( †)? \| {ks['semua|*']['delta']} \|", b), s


def test_tanda_tiada_ramalan_dan_ringkasan(h):
    b = ketidakpastian.blok(h)
    assert all(f"| kosong | `{e}` †" in b for e in konfig.utama()["nilai"]["entiti"])
    assert "| lemah | `*` |" in b and "| lemah | `*` †" not in b
    assert "Selang Δ yang menyentuh atau melepasi 0:" in b and "garis dasar" in b


def test_bertindih():
    assert ketidakpastian.bertindih({"bawah": 0.1, "atas": 0.3}, {"bawah": 0.3, "atas": 0.5})
    assert not ketidakpastian.bertindih({"bawah": 0.1, "atas": 0.29}, {"bawah": 0.3, "atas": 0.5})


def test_lantai_p_rawak_dibundar(h):
    """Regresi: p rawak disimpan dibundar (0.001) > 1/1001 tidak dibundar — perbandingan mesti atas nilai dibundar."""
    g = json.loads(json.dumps(h))
    g["config"]["ulangan"] = 1000
    for ks in g["banding"].values():
        for v in ks.values():
            v["p_rawak"] = 0.001
    jumlah = sum(len(ks) for ks in g["banding"].values())
    assert f"{jumlah}/{jumlah} perbandingan berada di lantai" in ketidakpastian.blok(g)


def test_blok_tentu(h):
    assert ketidakpastian.blok(h) == ketidakpastian.blok(json.loads(json.dumps(h)))


def test_main_tulis_antara_penanda_sendiri(tmp_path, monkeypatch, h):
    k = konfig.utama()["nilai"]["statistik"]
    (tmp_path / "hasil").mkdir()
    (tmp_path / "hasil/dev-statistik.json").write_text(json.dumps(h), encoding="utf-8")
    lap = tmp_path / k["laporan"]
    lap.parent.mkdir(parents=True)
    lap.write_text("atas\n<!-- jana:mula -->\nJANA\n<!-- jana:tamat -->\n" + "\n".join(k["penanda"]) + "\nbawah\n", encoding="utf-8")
    monkeypatch.setattr(ketidakpastian, "AKAR", tmp_path)
    monkeypatch.setattr(sys, "argv", ["x"])
    assert ketidakpastian.main() == 0
    t = lap.read_text(encoding="utf-8")
    assert "\nJANA\n" in t and t.startswith("atas\n") and t.endswith(k["penanda"][1] + "\nbawah\n")
    assert "Ringkasan mekanikal" in t.split(k["penanda"][0])[1]


def test_split_dikunci_ditolak(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x", "--split", konfig.utama()["nilai"]["split_dikunci"][0]])
    assert ketidakpastian.main() == 2
