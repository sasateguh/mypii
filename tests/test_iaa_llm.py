"""Penyemak LLM + eksport IAA (PELAN-IAA P7, ADR-015): urai betul/rosak, cache tanpa rangkaian, format eksport = format llm.
Klien palsu sahaja — tiada rangkaian, tiada kunci."""

import json

import pytest

from mypii import konfig
from mypii.iaa import eksport, llm
from mypii.iaa.stor import Stor

PILIHAN = konfig.utama()["iaa"]["pilihan"]


@pytest.fixture
def k(tmp_path):
    base = konfig.utama()["iaa"]
    return {"pilihan": base["pilihan"],
            "llm": base["llm"] | {"cache": "cache/iaa", "prompt": "SPAN:\n{span}\nDOK:\n{teks}"}}


DOK = [{"urutan": 1, "teks": "Tel 012-3456789 ok", "spans": [{"mula": 4, "tamat": 15, "entiti": "MY_PHONE"}]},
       {"urutan": 2, "teks": "tiada apa", "spans": []},
       {"urutan": 3, "teks": "rosak di sini", "spans": []}]


def _palsu(panggil):
    def hantar(model, p, suhu):
        panggil.append((model, p, suhu))
        if "rosak" in p:
            return "maaf, saya tidak pasti"
        if "012-3456789" in p:
            return '```json\n{"span": ["betul"], "tak_bertanda": [" 0198765432 "], "realistik": "ya"}\n```'
        return '{"span": [], "tak_bertanda": [], "realistik": "janggal"}'
    return hantar


def test_prompt_span_bernombor_dan_kosong(k):
    assert "1. MY_PHONE: 012-3456789" in llm.prompt(k["llm"]["prompt"], DOK[0])
    assert "(none)" in llm.prompt(k["llm"]["prompt"], DOK[1]) and "{teks}" not in llm.prompt(k["llm"]["prompt"], DOK[1])


@pytest.mark.parametrize("jawapan", [
    "bukan json", '["betul"]', '{"span": ["betul", "betul"], "tak_bertanda": [], "realistik": "ya"}',   # bilangan span salah
    '{"span": ["mungkin"], "tak_bertanda": [], "realistik": "ya"}', '{"span": ["betul"], "tak_bertanda": [], "realistik": "x"}',
    '{"span": ["betul"], "tak_bertanda": "0123", "realistik": "ya"}', '{"span": ["betul"], "realistik": "ya"}'])
def test_urai_rosak(jawapan):
    assert llm.urai(jawapan, 1, PILIHAN) is None


def test_urai_betul_bentuk_stor():
    assert llm.urai('{"span": ["salah", "jenis_lain"], "tak_bertanda": ["", " 9 "], "realistik": "ya"}', 2, PILIHAN) == \
        {"a1": "salah", "a2": "jenis_lain", "b": {"pilih": "ada", "nilai": ["9"]}, "c": "ya"}
    assert llm.urai('{"span": [], "tak_bertanda": [" "], "realistik": "janggal"}', 0, PILIHAN)["b"] == {"pilih": "tiada"}


def test_jalankan_rosak_dikira_dan_cache_tanpa_rangkaian(k, tmp_path):
    panggil = []
    baris, st = llm.jalankan(k, DOK, hantar=_palsu(panggil), akar=tmp_path)
    assert [b["status"] for b in baris] == ["siap", "siap", "rosak"]          # rosak kekal dalam output, tidak dibuang
    assert baris[0]["jawapan"] == {"a1": "betul", "b": {"pilih": "ada", "nilai": ["0198765432"]}, "c": "ya"}
    assert st | {"model": None} == {"model": None, "dokumen": 3, "dari_cache": 0, "panggilan": 3, "gagal": 0, "rosak": 1, "siap": 2}
    assert {p[2] for p in panggil} == {k["llm"]["suhu"]} and {p[0] for p in panggil} == {k["llm"]["model"]}
    cache = llm.fail_cache(k, tmp_path)
    assert cache.name == "cbcn_glm-5.3.jsonl" and "ujian" not in str(cache.relative_to(tmp_path))
    bait = cache.read_bytes()

    def tiada_rangkaian(*_):
        raise AssertionError("rangkaian dipanggil walaupun cache penuh")
    baris2, st2 = llm.jalankan(k, list(reversed(DOK)), hantar=tiada_rangkaian, akar=tmp_path)
    assert st2["panggilan"] == 0 and st2["dari_cache"] == 3 and cache.read_bytes() == bait
    assert sorted(baris2, key=lambda b: b["urutan"]) == baris


def test_gagal_tidak_masuk_cache(k, tmp_path, monkeypatch):
    monkeypatch.setattr("mypii.klien_llm.time.sleep", lambda _: None)

    def putus(*_):
        raise OSError("putus")
    baris, st = llm.jalankan(k, DOK[:1], hantar=putus, akar=tmp_path)
    assert st["gagal"] == 1 and baris[0] == {"urutan": 1, "status": "gagal", "jawapan": None}
    assert llm.muat(llm.fail_cache(k, tmp_path)) == {}


def test_cache_baris_terpotong_diabaikan(tmp_path):
    f = tmp_path / "c.jsonl"
    f.write_text('{"kunci": "a", "jawapan": "x"}\n{"kunci": "b", "jaw')
    assert llm.muat(f) == {"a": "x"}


def test_eksport_format_sama_dengan_llm(k, tmp_path):
    stor = Stor(tmp_path / "j.sqlite")
    stor.simpan("p1", 1, "a1", "betul")
    stor.simpan("p1", 1, "b", {"pilih": "ada", "nilai": ["0198765432"]})
    stor.simpan("p1", 1, "c", "ya")
    stor.simpan("p1", 2, "c", "janggal")                                     # separa: (b) belum
    stor.simpan("p1", 99, "c", "ya")                                         # di luar sampel → diabaikan
    stor.simpan("uji", 1, "c", "ya")
    manusia = eksport.dari_stor(stor, "p1", DOK)
    assert stor.penyemak() == ["p1", "uji"]
    stor.tutup()
    mesin, _ = llm.jalankan(k, DOK[:1], hantar=_palsu([]), akar=tmp_path)
    assert manusia[0] == mesin[0]                                            # bentuk + nilai sama untuk jawapan sama
    assert manusia[1] == {"urutan": 2, "status": "separa", "jawapan": {"c": "janggal"}}
    assert [b["urutan"] for b in manusia] == [1, 2]
    keluar = tmp_path / "jawapan" / "p1.jsonl"
    eksport.tulis(keluar, list(reversed(manusia)))
    teks = keluar.read_text()
    assert [json.loads(x)["urutan"] for x in teks.splitlines()] == [1, 2] and "token" not in teks


def test_status_tidak_dikenali():
    with pytest.raises(ValueError):
        eksport.baris(1, "entah", None)
