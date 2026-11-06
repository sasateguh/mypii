"""PELAN-B B3: garis dasar pesaing (ADR-011) — luar talian: klien LLM palsu, enjin pii-guard palsu (pustaka sebenar hanya bila dipasang)."""

import json
from types import SimpleNamespace

import pytest

from mypii import konfig
from mypii.nilai import garis, harness

MODEL = konfig.utama()["garis_dasar"]["llm"]["model"][0]
DOK = [
    {"id": "a", "bahasa": "ms", "teks": "IC 900101-14-5678, tel 012-3456789. Ulang IC 900101-14-5678.",
     "spans": [{"mula": 3, "tamat": 17, "entiti": "MY_NRIC"}, {"mula": 23, "tamat": 34, "entiti": "MY_PHONE"},
               {"mula": 45, "tamat": 59, "entiti": "MY_NRIC"}]},
    {"id": "b", "bahasa": "en", "teks": "Invoice 202201234567 paid.", "spans": []},
]


class Palsu:
    def __init__(self, jawapan):
        self.jawapan, self.panggil = jawapan, []

    def __call__(self, model, prompt, suhu):
        self.panggil.append((model, prompt, suhu))
        return self.jawapan(prompt) if callable(self.jawapan) else self.jawapan


def test_span_semua_kejadian_dan_entiti_luar_diabaikan():
    j = json.dumps([{"teks": "900101-14-5678", "entiti": "MY_NRIC"}, {"teks": "012-3456789", "entiti": "MY_PHONE"},
                    {"teks": "Invoice", "entiti": "EMAIL"}, {"teks": "tiada-di-sini", "entiti": "MY_SSM"}, "rentetan", {"teks": ""}])
    s = garis.span_dari_jawapan(DOK[0]["teks"], "```json\n" + j + "\n```")
    assert s == sorted(DOK[0]["spans"], key=lambda x: x["mula"])


@pytest.mark.parametrize("jawapan", ["maaf, tiada", '{"teks": "x"}', "[1, 2"])
def test_jawapan_rosak_none(jawapan):
    assert garis.span_dari_jawapan("x", jawapan) is None


def test_llm_cache_tiada_rangkaian_kali_kedua(tmp_path):
    def jawab(prompt):
        return "[]" if "Invoice" in prompt else json.dumps([{"teks": "012-3456789", "entiti": "MY_PHONE"}])

    h = Palsu(jawab)
    r1, st1 = garis.ramal_llm(MODEL, DOK, hantar=h, akar=tmp_path)
    assert st1 == {"dokumen": 2, "dari_cache": 0, "panggilan": 2, "gagal": 0, "rosak": 0}
    assert all(p[2] == konfig.utama()["garis_dasar"]["llm"]["suhu"] and DOK[0]["teks"] in h.panggil[0][1] + h.panggil[1][1]
               for p in h.panggil)
    cache = garis.fail_cache(MODEL, tmp_path)
    bait = cache.read_bytes()
    assert "/" not in cache.name and len(bait.splitlines()) == 2
    h2 = Palsu(AssertionError)
    r2, st2 = garis.ramal_llm(MODEL, DOK, hantar=h2, akar=tmp_path)
    assert r2 == r1 == [[{"mula": 23, "tamat": 34, "entiti": "MY_PHONE"}], []]
    assert st2["panggilan"] == 0 and st2["dari_cache"] == 2 and h2.panggil == [] and cache.read_bytes() == bait


def test_kunci_cache_berubah_ikut_model_prompt_teks():
    asas = garis.kunci_cache("m", "p", "t")
    assert len({asas, garis.kunci_cache("m2", "p", "t"), garis.kunci_cache("m", "p2", "t"), garis.kunci_cache("m", "p", "t2")}) == 4


def test_llm_rosak_dikira_tiada_ramalan(tmp_path):
    r, st = garis.ramal_llm(MODEL, DOK, hantar=Palsu("bukan json"), akar=tmp_path)
    assert r == [[], []] and st["rosak"] == 2 and st["gagal"] == 0


def test_llm_gagal_rangkaian_tidak_dicache(tmp_path, monkeypatch):
    monkeypatch.setitem(konfig.utama()["llm"], "jeda_saat", 0)

    def putus(model, prompt, suhu):
        raise OSError("putus")

    r, st = garis.ramal_llm(MODEL, DOK, hantar=putus, akar=tmp_path)
    assert r == [[], []] and st["gagal"] == 2 and st["rosak"] == 0
    assert not garis.fail_cache(MODEL, tmp_path).exists()  # dibuka malas: tiada jawapan = tiada fail (penyemak P2)


def test_model_tidak_disenarai_ditolak(tmp_path):
    with pytest.raises(SystemExit):
        garis.ramal_llm("ag/gemini-3.8-flash", DOK, hantar=Palsu("[]"), akar=tmp_path)


def _f(e, a, b, sk):
    return SimpleNamespace(entity_type=e, start=a, end=b, score=sk)


def test_pii_guard_peta_dan_selesai():
    temuan = {DOK[0]["teks"]: [_f("MY_NRIC", 3, 17, 1.0), _f("PHONE_NUMBER", 23, 34, 0.9), _f("MY_BANK_ACCOUNT", 23, 34, 0.5),
                               _f("EMAIL_ADDRESS", 0, 2, 1.0)],
              DOK[1]["teks"]: [_f("MY_BANK_ACCOUNT", 8, 20, 0.6)]}
    enjin = SimpleNamespace(analyze=lambda teks, score_threshold: temuan[teks])
    dipanggil = []

    def selesai(f):
        dipanggil.append(len(f))
        return [x for x in f if x.entity_type != "MY_BANK_ACCOUNT"]

    r = garis.ramal_pii_guard(DOK, enjin=enjin, selesai=selesai)
    assert dipanggil == [4, 1]
    assert r == [[{"mula": 3, "tamat": 17, "entiti": "MY_NRIC"}, {"mula": 23, "tamat": 34, "entiti": "MY_PHONE"}], []]


def test_gold_disokong_buang_ssm_sahaja():
    d = [{"id": "x", "bahasa": "ms", "teks": "", "spans": [{"mula": 0, "tamat": 1, "entiti": "MY_SSM"},
                                                         {"mula": 2, "tamat": 3, "entiti": "MY_PHONE"}]}]
    assert garis.gold_disokong(d)[0]["spans"] == [{"mula": 2, "tamat": 3, "entiti": "MY_PHONE"}]
    assert len(d[0]["spans"]) == 2


def test_harness_senarai_semua_dan_nama_fail():
    s = harness.senarai_sistem(["semua"])
    dijalankan = [m for m in konfig.utama()["garis_dasar"]["llm"]["model"]  # anthropic/ tanpa cache dilangkau (PELAN-CLAUDE P4)
                  if not m.startswith("anthropic/") or garis.fail_cache(m).exists()]
    assert s[:3] == ["mypii", "presidio-asal", "pii-guard"] and s[3:] == [f"llm:{m}" for m in dijalankan]
    assert harness.senarai_sistem(["mypii"]) == ["mypii"]
    assert harness.nama_fail("dev", "mypii") == "dev-mypii.json"
    assert "/" not in harness.nama_fail("dev", "llm:" + MODEL)


def test_pii_guard_sebenar_bila_dipasang():
    pytest.importorskip("malaysia_pii_guard")
    teks = "Nama: Ali. No. IC: 900101-14-5678. Telefon bimbit: 012-345 6789."
    r = garis.ramal_pii_guard([{"teks": teks}])[0]
    assert {"mula": teks.index("900101"), "tamat": teks.index("900101") + 14, "entiti": "MY_NRIC"} in r
    assert all(s["entiti"] in ("MY_NRIC", "MY_PHONE") for s in r)


def test_cache_baris_terpotong_diabaikan(tmp_path):
    h = Palsu("[]")
    garis.ramal_llm(MODEL, DOK, hantar=h, akar=tmp_path)
    laluan = garis.fail_cache(MODEL, tmp_path)
    baris = laluan.read_text().splitlines()
    laluan.write_text(baris[0] + "\n" + baris[1][:20])
    _, st = garis.ramal_llm(MODEL, DOK, hantar=h, akar=tmp_path)
    assert st["dari_cache"] == 1 and st["panggilan"] == 1 and len(h.panggil) == 3
