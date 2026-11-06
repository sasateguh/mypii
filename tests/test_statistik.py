"""PELAN-C C3a (ADR-006 §Statistik): bootstrap dokumen, ujian berpasangan, Holm — data sintetik, tiada spaCy/Presidio/rangkaian."""

import json
import random
import sys

import pytest

from mypii.nilai import harness, statistik

ULANG = 200


def _data(n: int = 40, benih: int = 7, ralat: float = 0.3):
    """n dokumen, satu span emas setiap satu; ramalan 'baik' tepat kecuali pecahan `ralat` (span terganjak)."""
    rng = random.Random(benih)
    entiti = ["MY_NRIC", "MY_SSM", "MY_PHONE"]
    dok, baik = [], []
    for i in range(n):
        s = {"mula": 5, "tamat": 19, "entiti": entiti[i % 3]}
        dok.append({"id": f"d{i:03d}", "bahasa": ["bm", "en"][i % 2], "spans": [s]})
        baik.append([dict(s, tamat=18)] if rng.random() < ralat else [dict(s)])
    return dok, baik


def test_persentil_interpolasi_linear():
    x = list(range(1, 102))  # 1..101
    assert statistik.persentil(x, 0.025) == pytest.approx(3.5)
    assert statistik.persentil(x, 0.975) == pytest.approx(98.5)
    assert statistik.persentil([4, 1, 3, 2], 0.5) == pytest.approx(2.5)
    with pytest.raises(ValueError):
        statistik.persentil([], 0.5)


def test_selang_mengandungi_anggaran_dan_julat_sah():
    dok, baik = _data()
    r = statistik.selang_bootstrap(dok, baik, "semua|*", ulangan=ULANG, benih=1, aras=0.95)
    assert r["f1"] == harness.skor(dok, baik)["semua|*"]["tepat"]["f1"]
    assert 0 <= r["bawah"] < r["f1"] < r["atas"] <= 1 and r["n_sah"] == ULANG


def test_selang_ikut_persentil_sampel():
    # sabotaj (persentil ditukar / aras diabaikan) → selang tidak sama dengan persentil sampel yang dikira semula di sini
    dok, baik = _data()
    ix = statistik.indeks_bootstrap(len(dok), ULANG, 3)
    sampel = statistik.f1_sampel(dok, baik, ix, ["semua|*"])
    r = statistik.selang_bootstrap(dok, baik, "semua|*", ULANG, 3, 0.9, sampel)
    xs = sorted(sampel["semua|*"])
    assert r["bawah"] == round(statistik.persentil(xs, 0.05), 4) and r["atas"] == round(statistik.persentil(xs, 0.95), 4)
    assert r["bawah"] != round(statistik.persentil(xs, 0.025), 4)


def test_banding_diri_sendiri_delta_sifar_p_satu():
    dok, baik = _data()
    r = statistik.berpasangan(dok, baik, baik, "semua|*", ulangan=ULANG, benih=1, aras=0.95)
    assert (r["delta"], r["bawah"], r["atas"], r["p_bootstrap"], r["p_rawak"]) == (0.0, 0.0, 0.0, 1.0, 1.0)


def test_sempurna_lawan_kosong_signifikan():
    dok, _ = _data()
    emas = [d["spans"] for d in dok]
    r = statistik.berpasangan(dok, emas, [[] for _ in dok], "semua|*", ulangan=ULANG, benih=1, aras=0.95)
    assert r["delta"] == 1.0 and r["p_bootstrap"] < 0.01 and r["p_rawak"] < 0.01
    assert r["p_rawak"] == round(1 / (ULANG + 1), 4)  # tiada pilih atur mencapai δ = 1 (2^-40)
    terbalik = statistik.berpasangan(dok, [[] for _ in dok], emas, "semua|*", ulangan=ULANG, benih=1, aras=0.95)
    assert terbalik["delta"] == -1.0 and terbalik["p_bootstrap"] == 1.0 and terbalik["p_rawak"] > 0.5  # sehala


def test_p_bootstrap_berg_kirkpatrick():
    assert statistik._p_bootstrap(0.1, [0.25, 0.15, 0.21, 0.0]) == 0.5  # 0.25, 0.21 > 0.2
    assert statistik._p_bootstrap(0.0, [0.5]) == 1.0 and statistik._p_bootstrap(-0.1, [0.5]) == 1.0


def test_holm():
    p = statistik.holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": None})
    # tertib 0.01, 0.03, 0.04 → 3·0.01, max(0.03, 2·0.03), max(0.06, 1·0.04)
    assert p["a"] == pytest.approx(0.03) and p["c"] == pytest.approx(0.06) and p["b"] == pytest.approx(0.06)
    assert p["d"] is None
    assert statistik.holm({"a": 0.6, "b": 0.7}) == {"a": 1.0, "b": 1.0}


def test_skor_harness_dipanggil_bukan_disalin(monkeypatch):
    dok, baik = _data(n=12)
    asal, kira = harness.skor, []

    def palsu(d, r):
        kira.append(1)
        return asal(d, r)

    monkeypatch.setattr(harness, "skor", palsu)
    statistik.selang_bootstrap(dok, baik, "semua|*", ulangan=30, benih=1, aras=0.95)
    assert len(kira) == 30 + 1  # satu setiap sampel + anggaran penuh
    kira.clear()
    statistik.berpasangan(dok, baik, [[] for _ in dok], "semua|*", ulangan=30, benih=1, aras=0.95)
    assert len(kira) == 2 * 30 + 2 + 2 * 30  # bootstrap A+B, penuh A+B, rawak A'+B'
    monkeypatch.setattr(harness, "skor", lambda d, r: {"semua|*": {"tepat": {"f1": 0.5}}})
    r = statistik.selang_bootstrap(dok, baik, "semua|*", ulangan=10, benih=1, aras=0.95)
    assert (r["f1"], r["bawah"], r["atas"]) == (0.5, 0.5, 0.5)


def _k(**ganti):
    return {"ulangan": 100, "benih": 2026, "aras": 0.95, "kaedah": "holm", "rujukan": "a", "kunci_utama": "semua|*",
            "folder_ramalan": "ramalan", "perpuluhan": 4, **ganti}


def test_jalankan_benih_sama_bait_sama_dan_holm():
    dok, baik = _data()
    _, lain = _data(benih=8, ralat=0.6)
    ramalan = {"a": baik, "b": lain, "c": [[] for _ in dok]}
    h1 = json.dumps(statistik.jalankan(dok, ramalan, _k()), sort_keys=True)
    assert h1 == json.dumps(statistik.jalankan(dok, ramalan, _k()), sort_keys=True)
    assert h1 != json.dumps(statistik.jalankan(dok, ramalan, _k(benih=1)), sort_keys=True)
    h = json.loads(h1)
    assert set(h["sistem"]) == {"a", "b", "c"} and set(h["banding"]) == {"b", "c"}
    assert sorted(h["sistem"]["a"]) == sorted(statistik.senarai_kunci(_k()))
    for s in ("b", "c"):
        v = h["banding"][s]["semua|*"]
        assert v["p_holm_rawak"] >= v["p_rawak"] and v["p_holm_bootstrap"] >= v["p_bootstrap"]
    assert "| a lawan |" in statistik.jadual_md(h)
    with pytest.raises(ValueError):
        statistik.jalankan(dok, ramalan, _k(kaedah="bonferroni"))
    with pytest.raises(ValueError):
        statistik.jalankan(dok, ramalan, _k(rujukan="tiada"))


@pytest.fixture
def akar_tmp(tmp_path, monkeypatch):
    dok, baik = _data()
    (tmp_path / "data/bench").mkdir(parents=True)
    (tmp_path / "data/bench/dev.jsonl").write_text("".join(json.dumps(d) + "\n" for d in dok))
    monkeypatch.setattr(harness, "AKAR", tmp_path)
    monkeypatch.setattr(harness, "ramal", lambda s, d: baik if s == "mypii" else [[] for _ in d])
    return tmp_path, dok, baik


def test_harness_simpan_ramalan_kemudian_statistik(akar_tmp, monkeypatch, capsys):
    akar, dok, baik = akar_tmp
    keluar = akar / "hasil"
    monkeypatch.setattr(sys, "argv", ["h", "--keluar", str(keluar), "--sistem", "mypii", "presidio-asal"])
    assert harness.main() == 0
    f = keluar / "ramalan/dev-mypii.jsonl"
    baris = [json.loads(x) for x in f.read_text().splitlines()]
    assert [b["id"] for b in baris] == [d["id"] for d in dok] and [b["spans"] for b in baris] == baik
    monkeypatch.setattr(harness, "ramal", lambda *a: pytest.fail("--statistik tidak boleh meramal semula"))
    monkeypatch.setattr(sys, "argv", ["h", "--keluar", str(keluar), "--sistem", "mypii", "presidio-asal", "--statistik"])
    assert harness.main() == 0
    pertama = (keluar / "dev-statistik.json").read_bytes()
    assert harness.main() == 0 and (keluar / "dev-statistik.json").read_bytes() == pertama
    h = json.loads(pertama)
    assert h["split"] == "dev" and h["banding"]["presidio-asal"]["semua|*"]["delta"] > 0
    assert "presidio-asal" in capsys.readouterr().out


def test_harness_statistik_id_tidak_sepadan_dan_fail_tiada(akar_tmp, monkeypatch):
    akar, dok, baik = akar_tmp
    keluar = akar / "hasil"
    harness.simpan_ramalan(keluar, "dev", "mypii", dok[:-1], baik[:-1])
    with pytest.raises(ValueError):
        harness.baca_ramalan(keluar, "dev", "mypii", dok)
    with pytest.raises(FileNotFoundError):
        harness.baca_ramalan(keluar, "dev", "presidio-asal", dok)


def test_harness_statistik_split_dikunci_dan_iterasi_ditolak(akar_tmp, monkeypatch):
    akar, *_ = akar_tmp
    monkeypatch.setattr(harness, "statistik", lambda a: pytest.fail("tidak boleh berjalan"))
    monkeypatch.setattr(sys, "argv", ["h", "--split", "ujian2", "--statistik", "--keluar", str(akar / "hasil")])
    assert harness.main() == 2
    monkeypatch.setattr(sys, "argv", ["h", "--statistik", "--iterasi", "ukur", "--keluar", str(akar / "hasil")])
    assert harness.main() == 2
    assert not (akar / "hasil").exists()
