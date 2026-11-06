"""Skor IAA (PELAN-IAA P9, ADR-015 §Skor): κ buku teks, F1 span, normalisasi, pasangan tersedia sahaja, kadar ralat, bait sama.
Fixture beku sahaja — tiada fail data/iaa dibaca."""

import json

import pytest

from mypii import konfig
from mypii.iaa import skor
from mypii.nilai.bandingan import tulis_blok

K = konfig.utama()["iaa"]
ST = {"ulangan": 200, "benih": 7, "aras": 0.95, "perpuluhan": 4}


def test_kappa_buku_teks():
    # Contoh Cohen klasik (Wikipedia "Cohen's kappa"): 50 item, ya/ya 20, ya/tidak 5, tidak/ya 10, tidak/tidak 15 → po 0.7, pe 0.5, κ 0.4
    p = [("ya", "ya")] * 20 + [("ya", "tak")] * 5 + [("tak", "ya")] * 10 + [("tak", "tak")] * 15
    assert skor.kappa(p) == pytest.approx(0.4)
    assert skor.setuju(p) == pytest.approx(0.7)


def test_kappa_sempurna_dan_tidak_tertakrif():
    assert skor.kappa([("a", "a"), ("b", "b")]) == pytest.approx(1.0)
    assert skor.kappa([("a", "a")] * 5) is None   # pe = 1 → κ tidak tertakrif, bukan 1 atau 0
    assert skor.kappa([]) is None and skor.setuju([]) is None


def test_normal():
    assert skor.normal("880101-14-5678") == "880101145678"
    assert skor.normal(" 012-345 6789 ") == "0123456789"
    assert skor.normal("123456-x") == "123456X"
    assert skor.normal("2019 0101 2345") == "201901012345"


def test_f1_span():
    assert skor._f1([(1, 4)]) == pytest.approx(0.5)            # A={x,y}, B={y,z}
    assert skor._f1([(1, 2), (0, 2)]) == pytest.approx(0.5)    # mikro atas dokumen
    assert skor._f1([(0, 0)]) is None


def _j(a, b, c):
    out = {f"a{n}": v for n, v in enumerate(a, 1)}
    out["b"] = {"pilih": "ada", "nilai": b} if b else {"pilih": "tiada"}
    return out | {"c": c}


def _baris(urutan, jaw, status="siap"):
    return {"urutan": urutan, "status": status, "jawapan": jaw}


SAMPEL = {"n": 4, "sha256": "x", "dokumen": [{"urutan": 1, "split": "dev"}, {"urutan": 2, "split": "dev"},
                                              {"urutan": 3, "split": "ujian2"}, {"urutan": 4, "split": "ujian2"}]}
LLM = {1: _baris(1, _j(["betul", "betul"], [], "ya")), 2: _baris(2, _j([], ["012-345 6789"], "janggal")),
       3: _baris(3, _j(["salah"], [], "ya")), 4: _baris(4, None, "rosak")}
P1 = {1: _baris(1, _j(["betul", "salah"], [], "ya")), 2: _baris(2, _j([], ["0123456789", "880101145678"], "janggal")),
      3: _baris(3, _j(["salah"], [], "ya"), "separa")}


def test_menunggu_bila_penyemak_tiada():
    h = skor.kira(SAMPEL, {"p1": None, "llm": LLM, "p2": None}, K, ST)
    assert h["pasangan"]["p1×llm"] == {"keadaan": "menunggu p1 (0/4)", "utama": True}
    assert h["pasangan"]["p1×p2"]["keadaan"] == "menunggu p1 (0/4), p2 (0/4)"
    assert h["penyemak"]["llm"] == {"siap": 3, "separa": 0, "rosak": 1, "gagal": 0, "n": 4}
    assert list(h["ralat"]) == ["llm"]


def test_pasangan_dokumen_siap_kedua_sahaja():
    h = skor.kira(SAMPEL, {"p1": P1, "llm": LLM, "p2": None}, K, ST)
    r = h["pasangan"]["p1×llm"]
    assert r["keadaan"] == "separa" and r["dokumen"] == 2 and r["span"] == 2   # urutan 3 separa (p1), 4 rosak (llm)
    assert r["a"]["setuju"]["nilai"] == 0.5 and r["c"]["setuju"]["nilai"] == 1.0
    assert r["c"]["kappa"]["nilai"] == 1.0
    assert r["b"]["f1"]["nilai"] == pytest.approx(round(2 * 1 / 3, 4))           # {0123456789} vs {0123456789, 880101145678}
    assert r["b"]["kedua_tiada"] == 1 and r["b"]["nilai_a"] == 2 and r["b"]["nilai_b"] == 1
    assert r["a"]["kappa"]["bawah"] <= r["a"]["kappa"]["atas"] or r["a"]["kappa"]["bawah"] is None


def test_kadar_ralat_setiap_split():
    h = skor.kira(SAMPEL, {"p1": None, "llm": LLM, "p2": None}, K, ST)
    r = h["ralat"]["llm"]
    assert (r["dev"]["dokumen"], r["dev"]["span"], r["ujian2"]["dokumen"], r["ujian2"]["span"]) == (2, 2, 1, 1)
    assert r["dev"]["span_salah"]["nilai"] == 0.0 and r["ujian2"]["span_salah"]["nilai"] == 1.0
    assert r["dev"]["tak_bertanda"]["nilai"] == 0.5 and r["dev"]["janggal"]["nilai"] == 0.5
    assert r["dev-ujian2"]["span_salah"]["nilai"] == -1.0
    assert r["dev-ujian2"]["janggal"]["nilai"] == 0.5


def test_bait_sama_dan_blok(tmp_path):
    a = json.dumps(skor.kira(SAMPEL, {"p1": P1, "llm": LLM, "p2": None}, K, ST), sort_keys=True)
    b = json.dumps(skor.kira(SAMPEL, {"p1": P1, "llm": LLM, "p2": None}, K, ST), sort_keys=True)
    assert a == b
    h = json.loads(a)
    f = tmp_path / "B.md"
    f.write_text("x\n<!-- iaa:mula -->\nlama\n<!-- iaa:tamat -->\ny\n", encoding="utf-8")
    tulis_blok(f, skor.blok(h, "hasil/iaa.json"), K["skor"]["penanda"])
    t = f.read_text(encoding="utf-8")
    assert "lama" not in t and "| **p1×llm** (utama) | separa | 2 | 2 |" in t and "p1×p2: menunggu p2 (0/4)" in t
    assert "{" not in t.split("<!-- iaa:mula -->")[1].split("-->", 1)[1]   # tiada dict mentah dalam jadual


def test_utama_p1_p2_bila_p2_ada():
    h = skor.kira(SAMPEL, {"p1": P1, "llm": LLM, "p2": LLM}, K, ST)
    assert h["pasangan"]["p1×p2"]["utama"] and not h["pasangan"]["p1×llm"]["utama"]
