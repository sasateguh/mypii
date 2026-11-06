"""PELAN-B B4 (ADR-012): laporan bandingan — luar talian, tiada spaCy/Presidio/9router (ramalan dan klien dipalsukan)."""

import json
import sys

import pytest

from mypii.nilai import bandingan, bandingan_md, harness

E = lambda m, t, e: {"mula": m, "tamat": t, "entiti": e}
DOK = [
    {"id": "a", "bahasa": "ms", "teks": "No. KP: 900101-14-5678\nTel: 012-3456789\nNo. Ahli: 202201234567",
     "spans": [E(8, 22, "MY_NRIC"), E(28, 39, "MY_PHONE")]},
    {"id": "b", "bahasa": "en", "teks": "Invoice No: 202201234567 paid.", "spans": []},
    {"id": "c", "bahasa": "en", "teks": "SSM: 123456-X", "spans": [E(5, 13, "MY_SSM")]},
]


def test_kelaskan_setiap_jenis():
    ramalan = [
        [E(8, 22, "MY_NRIC"), E(28, 36, "MY_PHONE"), E(50, 62, "MY_NRIC")],  # tepat, sempadan, palsu
        [E(12, 24, "MY_SSM")],                                               # palsu dalam dok negatif
        [E(5, 13, "MY_NRIC")],                                               # salah jenis (emas SSM tidak dikira terlepas)
    ]
    r = bandingan.kelaskan(DOK, ramalan)
    assert sorted((x["dok"]["id"], x["jenis"], x["entiti"]) for x in r) == [
        ("a", "palsu", "MY_NRIC"), ("a", "sempadan", "MY_PHONE"), ("b", "palsu", "MY_SSM"), ("c", "salah_jenis", "MY_NRIC")]
    assert [x["jenis"] for x in bandingan.kelaskan(DOK, [[], [], []])] == ["terlepas"] * 3


def test_label_dan_petikan():
    t = DOK[0]["teks"]
    assert bandingan.label(t, 50) == "no ahli"
    assert bandingan.label("202201234567", 0) == "(tiada label)"
    p = bandingan.petikan(t, 8, 22)
    assert "«900101-14-5678»" in p and "\n" not in p and "⏎" in p


def test_ringkas_ralat_kumpul_ikut_label_dan_dok_negatif():
    r = bandingan.ringkas_ralat(bandingan.kelaskan(DOK, [[E(50, 62, "MY_NRIC")], [E(12, 24, "MY_SSM")], []]))
    assert r["kira"] == {"palsu|MY_NRIC": 1, "palsu|MY_SSM": 1, "terlepas|MY_NRIC": 1, "terlepas|MY_PHONE": 1, "terlepas|MY_SSM": 1}
    assert r["dok_negatif"] == {"dok": 1, "span": 1}
    assert {x["label"] for x in r["utama"]["palsu"]} == {"no ahli", "invoice no"}
    assert r["utama"]["palsu"][0]["contoh"][0].endswith("(b)")  # seri bil → ikut abjad label ("invoice no" < "no ahli"), tentu


def _kira(monkeypatch, ramalan):
    monkeypatch.setattr(bandingan, "ramal_semua", lambda dok, sistem: ramalan)
    monkeypatch.setattr(bandingan, "kos_llm", lambda model, dok: {"aksara_masuk": 1, "aksara_keluar": 2})
    return bandingan.kira(DOK, list(ramalan)) | {"split": "dev", "sha256": "0" * 64}


def test_kira_guna_skor_harness_dan_blok_tentu(monkeypatch):
    ramalan = {"mypii": [d["spans"] for d in DOK], "pii-guard": [[DOK[0]["spans"][0]], [], []], "llm:x": [[], [], []]}
    h = _kira(monkeypatch, ramalan)
    assert h["sistem"]["mypii"]["skor"] == harness.skor(DOK, ramalan["mypii"])
    assert h["sistem"]["mypii"]["skor"]["semua|*"]["tepat"]["f1"] == 1.0
    assert "skor_disokong" in h["sistem"]["pii-guard"] and "kos" in h["sistem"]["llm:x"]
    md = bandingan_md.blok(h, None)
    assert md == bandingan_md.blok(json.loads(json.dumps(h)), None)  # sama selepas JSON (fail hasil) — tiada susunan rawak
    assert "| `mypii` | 1.0 | 1.0 | 1.0 |" in md and "Masa belum diukur" in md and "(disokong: MY_NRIC, MY_PHONE)" in md
    masa = {"diukur": "T", "sistem": {"mypii": {"dokumen": 3, "saat": 0.3}}, "llm": {"llm:x": {"sampel": 2, "gagal": 0,
                                                                                                 "median_s": 1.0, "maks_s": 2.0}}}
    assert "| `mypii` | 3 | 0.3 | 100.0 |" in bandingan_md.blok(h, masa)


def test_tulis_blok_hanya_antara_penanda(tmp_path):
    mula, tamat = bandingan._k()["penanda"]
    f = tmp_path / "B.md"
    f.write_text(f"prosa\n{mula}\nlama\n{tamat}\nekor\n")
    bandingan.tulis_blok(f, "baharu\n")
    assert f.read_text() == f"prosa\n{mula}\nbaharu\n{tamat}\nekor\n"
    f.write_text("tiada penanda")
    with pytest.raises(SystemExit):
        bandingan.tulis_blok(f, "x")


def test_llm_tanpa_cache_ditolak_tanpa_rangkaian(tmp_path, monkeypatch):
    from mypii.nilai import garis

    model = bandingan.konfig.utama()["garis_dasar"]["llm"]["model"][0]
    monkeypatch.setattr(garis, "fail_cache", lambda m, akar=None: tmp_path / "tiada.jsonl")
    with pytest.raises(SystemExit, match="tiada dalam cache"):
        bandingan.ramal_semua(DOK, [f"llm:{model}"])


def test_ukur_masa_klien_palsu_tidak_tulis_cache(monkeypatch):
    panggil = []
    monkeypatch.setattr(harness, "ramal", lambda s, dok: [[] for _ in dok])

    def hantar(model, prompt, suhu):
        panggil.append(model)
        if len(panggil) == 2:
            raise OSError("putus")
        return "[]"

    m = bandingan.ukur_masa(DOK, ["mypii", "llm:x"], hantar=hantar)
    assert m["sistem"]["mypii"]["dokumen"] == 3
    assert m["llm"]["llm:x"]["sampel"] == 3 and m["llm"]["llm:x"]["gagal"] == 1 and len(panggil) == 3


def test_split_dikunci_ditolak(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["bandingan", "--split", "ujian2"])
    assert bandingan.main() == 2
