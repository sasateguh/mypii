"""PELAN-MODEL-LAIN P2 (ADR-017, PRA-DAFTAR pindaan 2026-11-03): garis dasar EKSPLORASI di luar keluarga Holm.

Data sintetik sahaja (tiada spaCy/Presidio/rangkaian). Sifat yang dikunci:
- menambah sistem eksplorasi TIDAK mengubah satu bait pun output sistem pengesahan (termasuk `p_holm_*`);
- sistem eksplorasi: Δ + CI + p mentah ada, `p_holm_*` None, `eksplorasi: true`;
- k kuasa = garis dasar pengesahan sahaja; config tanpa `eksplorasi` = tingkah laku lama.
"""

import copy
import json

import pytest

from mypii import konfig
from mypii.nilai import bandingan_md, garis, ketidakpastian, kuasa, statistik
from tests.test_statistik import _data, _k

EKS = "llm:x/eksplorasi"


@pytest.fixture(scope="module")
def ramalan():
    dok, baik = _data()
    _, lain = _data(benih=8, ralat=0.6)
    _, eks = _data(benih=11, ralat=0.5)
    return dok, {"a": baik, "b": lain, "c": [[] for _ in dok]}, eks


def _json(h: dict) -> str:
    return json.dumps(h, sort_keys=True)


def test_eksplorasi_tidak_mengubah_sistem_pengesahan_bait_sama(ramalan):
    dok, asas, eks = ramalan
    lama = statistik.jalankan(dok, asas, _k(), eksplorasi=set())
    baru = statistik.jalankan(dok, {**asas, EKS: eks}, _k(), eksplorasi={EKS})
    for s in ("b", "c"):
        assert _json(baru["banding"][s]) == _json(lama["banding"][s]), s
    for s in ("a", "b", "c"):
        assert _json(baru["sistem"][s]) == _json(lama["sistem"][s]), s
    assert "eksplorasi" not in lama and baru["eksplorasi"] == [EKS]


def test_eksplorasi_tiada_p_holm_tetapi_p_mentah_dan_ci_ada(ramalan):
    dok, asas, eks = ramalan
    h = statistik.jalankan(dok, {**asas, EKS: eks}, _k(), eksplorasi={EKS})
    for x, v in h["banding"][EKS].items():
        assert v["p_holm_bootstrap"] is None and v["p_holm_rawak"] is None, x
        assert v["eksplorasi"] is True and v["p_rawak"] is not None and v["delta"] is not None, x
        assert v["bawah"] is not None and v["atas"] is not None
    assert all("eksplorasi" not in v for s in ("b", "c") for v in h["banding"][s].values())
    assert set(statistik.pengesahan(h)) == {"b", "c"}
    assert "| llm:x/eksplorasi (eksplorasi) |" in statistik.jadual_md(h)


def test_tanpa_eksplorasi_dalam_ramalan_output_lama(ramalan):
    """Sistem eksplorasi dalam config tetapi belum dijalankan = output sama bait-demi-bait (dev-statistik tidak berubah)."""
    dok, asas, _ = ramalan
    assert _json(statistik.jalankan(dok, asas, _k(), eksplorasi={EKS})) == _json(
        statistik.jalankan(dok, asas, _k(), eksplorasi=set()))


def test_sistem_eksplorasi_dari_config():
    c = copy.deepcopy(konfig.utama())
    assert statistik.sistem_eksplorasi(c) == {f"llm:{m}" for m in c["garis_dasar"]["llm"]["eksplorasi"]}
    model, eks = c["garis_dasar"]["llm"]["model"], set(c["garis_dasar"]["llm"]["eksplorasi"])
    dalam = [m for m in model if m in eks]  # PELAN-MODEL-LAIN P6: eksplorasi masuk `model` di HUJUNG, hanya bersama cachenya
    assert model[len(model) - len(dalam):] == dalam, "model eksplorasi mesti di HUJUNG garis_dasar.llm.model"
    dev = [json.loads(x) for x in (konfig.AKAR / "data/bench/dev.jsonl").read_text(encoding="utf-8").splitlines()]
    for m in dalam:  # cache dev LENGKAP dikomit — `make bandingan`/Depot CI tidak pernah memanggil rangkaian
        cache = garis._muat_cache(garis.fail_cache(m))
        assert all(garis.kunci_dok(m, d["teks"]) in cache for d in dev), f"{m}: cache dev tidak lengkap"
    del c["garis_dasar"]["llm"]["eksplorasi"]
    assert statistik.sistem_eksplorasi(c) == set()


def test_kuasa_k_kekal_bilangan_pengesahan(ramalan):
    dok, asas, eks = ramalan
    lama = statistik.jalankan(dok, asas, _k(), eksplorasi=set())
    baru = statistik.jalankan(dok, {**asas, EKS: eks}, _k(), eksplorasi={EKS})
    for h in (lama, baru):
        h["dokumen"] = len(dok)
    assert kuasa.kira(baru, 0.05, 0.8, 1000, 6) == kuasa.kira(lama, 0.05, 0.8, 1000, 6)
    assert len(statistik.pengesahan(baru)) == 2


@pytest.fixture(scope="module")
def blok_ketidakpastian(ramalan):
    dok, asas, eks = ramalan
    k = _k(rujukan="a")
    lama = {"split": "dev", **statistik.jalankan(dok, asas, k, eksplorasi=set())}
    baru = {"split": "dev", **statistik.jalankan(dok, {**asas, EKS: eks}, k, eksplorasi={EKS})}
    return ketidakpastian.blok(lama), ketidakpastian.blok(baru)


def test_ketidakpastian_label_dan_ringkasan_holm_tidak_berubah(blok_ketidakpastian):
    lama, baru = blok_ketidakpastian
    assert "eksplorasi" not in lama
    assert "pembetulan holm atas 2 garis dasar" in baru and "1 garis dasar eksplorasi di luar keluarga Holm" in baru
    assert f"| {EKS} (eksplorasi) |" in baru
    def holm(b):
        return [x for x in b.split("### Ringkasan mekanikal")[1].splitlines() if x.startswith("- ") and EKS not in x]

    assert holm(baru) == holm(lama)
    eks = [x for x in baru.splitlines() if x.startswith("- Eksplorasi")]
    assert len(eks) == 1 and "di luar keluarga Holm" in eks[0]
    for kata in ("menang", "kalah", "signifikan", "mengatasi"):
        assert kata not in eks[0]


def test_bandingan_md_label_eksplorasi(monkeypatch):
    monkeypatch.setattr(statistik, "sistem_eksplorasi", lambda c=None: {EKS})
    sk = {"semua|*": {"tepat": {"p": 1, "r": 1, "f1": 1}, "separa": {"p": 1, "r": 1, "f1": 1}, "emas": 1, "ramal": 1}}
    hasil = {"sistem": {"a": {"skor": sk}, EKS: {"skor": sk}}}
    md = bandingan_md.ringkasan(hasil)
    assert f"| `{EKS}` (eksplorasi) |" in md and "| `a` |" in md and "`a` (eksplorasi)" not in md
    assert f"<code>{EKS}</code> (eksplorasi)</summary>" in bandingan_md.terperinci(hasil)
