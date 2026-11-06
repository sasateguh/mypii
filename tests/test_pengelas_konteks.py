"""PELAN-V2 P9–P11: normalisasi OCR + patah baris + kurungan kod kawasan + LLP, ciri bertopeng, pengelas konteks (gabung, sha, split)."""

import hashlib
import json

import pytest
from presidio_analyzer import RecognizerResult

from mypii import konfig
from mypii.pengecam import (
    MyNricRecognizer,
    MyPhoneRecognizer,
    MySsmRecognizer,
    ciri,
    konteks,
    normal,
    pengelas,
)

K = konfig.utama()


def _jumpa(p, teks):
    return [teks[r.start:r.end] for r in p.analyze(teks, p.supported_entities)]


# --- P9 normalisasi ---

def test_ocr_hanya_bila_diapit_digit_dan_panjang_sama():
    t = "45O325131339 B2B O12 2O23 0S48"
    n = normal.ocr(t)
    assert len(n) == len(t) and n == "450325131339 B2B O12 2023 0548"


def test_ocr_dan_patah_baris_dikesan_dengan_span_asal():
    assert _jumpa(MyNricRecognizer(), "IC: 45O325-13-1339 ok") == ["45O325-13-1339"]
    assert _jumpa(MyNricRecognizer(), "IC 900101\n08-1234 ok") == ["900101\n08-1234"]
    assert _jumpa(MyPhoneRecognizer(), "Tel: 013\n6727285 ok") == ["013\n6727285"]
    assert _jumpa(MySsmRecognizer(), "SSM: 202206\n  784775.") == ["202206\n  784775"]


def test_kod_kawasan_berkurung_span_termasuk_kurungan():
    assert _jumpa(MyPhoneRecognizer(), "Office line: (082) 771667.") == ["(082) 771667"]


def test_llp_sebelum_tahun_akta_ditolak_dari_ssm_rob():
    s = MySsmRecognizer()
    tahun = konfig.muat("ssm_rob")["llp"]["tahun_min"]
    assert s.validate_result(f"{tahun - 1}04123456") is False
    assert s.validate_result(f"{tahun + 1}04123456") is True
    assert s.validate_result(f"{tahun - 1}01123456") is True   # bukan LLP


# --- P10 ciri ---

def test_ciri_menopeng_digit_dan_boleh_diulang():
    t = "No rujukan 12345 pelanggan IC 900101081234 sila semak"
    m = t.index("900101081234")
    f = ciri.ciri(t, m, m + 12, K["konteks"]["ciri"])
    assert f == ciri.ciri(t, m, m + 12, K["konteks"]["ciri"]) and f == sorted(f)
    assert not any(c in x.split(":", 1)[1] for x in f for c in "123456789")   # nilai ciri ditopeng (awalan k2:/n2: bukan nombor)
    assert "b:000000000000" in f and "k:0000+" in f and "k0:ic" in f


# --- P11 gabung + artifak ---

def _r(entiti, mula, tamat, skor):
    return RecognizerResult(entiti, mula, tamat, skor, recognition_metadata={})


@pytest.mark.parametrize("cara,p,skor_awal,jangka", [
    ("ganti", 0.9, 0.0, "naik"), ("ganti", 0.1, 0.9, "turun"), ("tapis", 0.9, 0.0, "kekal"), ("tapis", 0.1, 0.9, "turun")])
def test_gabung_pengelas_ikut_cara(monkeypatch, cara, p, skor_awal, jangka):
    monkeypatch.setitem(K["konteks"]["gabung"], "cara", cara)
    monkeypatch.setattr(konteks, "kebarangkalian", lambda *a: p)
    r = _r("MY_NRIC", 0, 12, skor_awal)
    kk = K["pengecam"]["konteks_umum"]
    konteks._gabung_pengelas("900101081234", r, kk["skor_negatif"], kk["skor_min"])
    assert {"naik": r.score >= kk["skor_min"], "turun": r.score <= kk["skor_negatif"], "kekal": r.score == skor_awal}[jangka]


def test_artifak_sha_tidak_sama_ditolak(monkeypatch):
    pengelas._model.cache_clear()
    monkeypatch.setitem(K["konteks"], "sha256", "0" * 64)
    with pytest.raises(RuntimeError, match="sha256"):
        pengelas.kebarangkalian("IC 900101081234", 3, 15, "MY_NRIC")
    pengelas._model.cache_clear()


def test_artifak_dikomit_sha_config_saiz_dan_tiada_digit():
    k = K["konteks"]
    data = (konfig.AKAR / k["artifak"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == k["sha256"] and len(data) < 2 * 1024 * 1024
    m = json.loads(data)
    assert m["split"] == k["split_latih"] and set(m["entiti"]) == {"MY_NRIC", "MY_SSM", "MY_PHONE"}
    assert not any(c in f.split(":", 1)[1] for e in m["entiti"].values() for f in e["vocab"] for c in "123456789")   # ditopeng


def test_kebarangkalian_konteks_negatif_lebih_rendah():
    pengelas._model.cache_clear()
    pos = "Nama: Ali. No. IC: 900101081234. Terima kasih."
    neg = "No. akaun bank: 900101081234. Terima kasih."
    a, b = pos.index("9"), neg.index("9")
    assert pengelas.kebarangkalian(pos, a, a + 12, "MY_NRIC") > pengelas.kebarangkalian(neg, b, b + 12, "MY_NRIC")


# --- P10 kod latih ---

@pytest.mark.parametrize("split", ["dev3", "ujian3", "ujian2", "ujian", "dev", "tiada"])
def test_latih_menolak_split_lain_sebelum_fail_dibaca(monkeypatch, split):
    from mypii import konteks_latih
    monkeypatch.setattr(konfig, "fail_split", lambda s: pytest.fail("fail split dibaca"))
    with pytest.raises(SystemExit, match="split_latih"):
        konteks_latih.semak_split(split)


def test_latih_bait_sama_atas_data_kecil():
    pytest.importorskip("sklearn")
    from mypii import konteks_latih
    dok = [{"teks": f"IC pelanggan: 9001010812{i:02d}. Akaun bank: 8501010812{i:02d}.",
            "spans": [{"mula": 14, "tamat": 26, "entiti": "MY_NRIC"}]} for i in range(30)]
    a, b = konteks_latih.latih(konteks_latih.calon(dok)), konteks_latih.latih(konteks_latih.calon(dok))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["entiti"]["MY_NRIC"]["positif"] == 30 and a["entiti"]["MY_NRIC"]["calon"] == 60
