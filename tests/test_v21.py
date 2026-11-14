"""PELAN-V21: peraturan gabung `frasa` (setiap cabang), sistem beku `mypii-v2`, gerbang split belum dibuka, statistik H5."""

import pytest
from presidio_analyzer import AnalysisExplanation, RecognizerResult

from mypii import konfig
from mypii.nilai import harness, pradaftar, statistik_v21, v1_worktree
from mypii.pengecam import konteks

K = konfig.utama()
KK = K["pengecam"]["konteks_umum"]


def _r(sah: bool | None, corak: str = "NRIC (compact)", entiti: str = "MY_NRIC", skor: float = 1.0):
    e = AnalysisExplanation(recognizer="x", original_score=skor, pattern_name=corak, pattern="", validation_result=sah)
    return RecognizerResult(entiti, 0, 12, skor, analysis_explanation=e, recognition_metadata={})


def _gabung(monkeypatch, r, p, frasa):
    monkeypatch.setitem(K["konteks"]["gabung"], "cara", "frasa")
    monkeypatch.setattr(konteks, "kebarangkalian", lambda *a: p)
    konteks._gabung_pengelas("900101081234", r, KK["skor_negatif"], KK["skor_min"], frasa)
    return r.score >= KK["skor_min"]


@pytest.mark.parametrize("frasa,sah,p,simpan", [
    ("positif", True, 0.06, True),     # frasa positif menang atas pengelas yang ragu ("My IC is …", p 0.49)
    ("positif", True, 0.04, False),    # … kecuali pengelas hampir pasti bukan PII
    ("positif", None, 0.5, True),      # SSM lama + frasa positif = disimpan (seperti v1)
    ("negatif", True, 0.89, False),    # frasa negatif lebih dekat: perlu p ≥ ambang_negatif
    ("negatif", True, 0.95, True),
    ("negatif", None, 0.99, False),    # calon tanpa pengesahan struktur + frasa negatif = buang
    ("tiada", True, 0.5, True),        # tiada frasa: pengelas memutuskan pada ambang entiti
    ("tiada", True, 0.49, False),
    ("tiada", None, 0.99, False),      # SSM lama tanpa frasa = buang (kod produk berkurung, dev 142 FP)
])
def test_simpan_frasa_setiap_cabang(monkeypatch, frasa, sah, p, simpan):
    assert _gabung(monkeypatch, _r(sah), p, frasa) is simpan


def test_ambang_corak_bersempang_lebih_rendah(monkeypatch):
    assert _gabung(monkeypatch, _r(True, "NRIC (dashed)"), 0.35, "tiada")
    assert not _gabung(monkeypatch, _r(True, "NRIC (compact)"), 0.35, "tiada")


def test_tanpa_pengesahan_boleh_dimatikan(monkeypatch):
    monkeypatch.setitem(K["konteks"]["gabung"], "tanpa_sah_perlu_frasa", False)
    assert _gabung(monkeypatch, _r(None, "SSM (old company)", "MY_SSM", 0.1), 0.9, "tiada")


def test_ganti_kekal_tingkah_laku_v2(monkeypatch):
    """Undur v2.1 = `cara: ganti`: frasa diabaikan, pengelas memutuskan (rekod 1.0.x)."""
    monkeypatch.setitem(K["konteks"]["gabung"], "cara", "ganti")
    monkeypatch.setattr(konteks, "kebarangkalian", lambda *a: 0.49)
    r = _r(True)
    konteks._gabung_pengelas("x", r, KK["skor_negatif"], KK["skor_min"], "positif")
    assert r.score <= KK["skor_negatif"]


def test_sistem_beku_mypii_v2_ke_tag(monkeypatch):
    dipanggil = {}
    monkeypatch.setattr(v1_worktree, "ramal_tag", lambda d, tag: dipanggil.setdefault("tag", tag) and [[] for _ in d])
    assert harness.ramal("mypii-v2", [{"id": "a", "teks": "x"}]) == [[]]
    assert dipanggil["tag"] == K["nilai"]["sistem_beku"]["mypii-v2"] == "mypii-v2-beku"


def test_gerbang_belum_dibuka(monkeypatch, tmp_path):
    pradaftar.gerbang_belum_dibuka("dev3", False, tmp_path)   # split biasa: tiada semakan
    pradaftar.gerbang_belum_dibuka("ujian3", False, tmp_path)  # sudah dibuka (langkah B): tidak berubah
    with pytest.raises(SystemExit, match="benarkan-ujian"):
        pradaftar.gerbang_belum_dibuka("ujian4", False, tmp_path)
    with pytest.raises(SystemExit, match="ditolak"):
        pradaftar.gerbang_belum_dibuka("ujian4", True, tmp_path)   # tmp_path bukan repo git → pra-daftar tidak boleh disahkan


# --- statistik H5 atas data kecil ---

def _dok(n):
    return [{"id": str(i), "bahasa": "ms", "teks": "x" * 40,
             "spans": [{"mula": 0, "tamat": 12, "entiti": "MY_NRIC"}, {"mula": 20, "tamat": 32, "entiti": "MY_SSM"}]}
            for i in range(n)]


def _ram(dok, kena_nric, kena_ssm, label_ssm="MY_SSM"):
    out = []
    for i, _ in enumerate(dok):
        r = []
        if i < kena_nric:
            r.append({"mula": 0, "tamat": 12, "entiti": "MY_NRIC"})
        if i < kena_ssm:
            r.append({"mula": 20, "tamat": 32, "entiti": label_ssm})
        out.append(r)
    return out


def test_h5_holm_bukan_inferioriti_u1_dan_susulan(monkeypatch):
    monkeypatch.setitem(K["nilai"]["statistik"], "ulangan", 200)
    d = _dok(60)
    ram = {"mypii": _ram(d, 60, 60), "mypii-v2": _ram(d, 60, 60), "llm:anthropic/claude-haiku-5-5": _ram(d, 30, 60),
           "luar:meddies": _ram(d, 60, 60, "MY_NRIC"), "luar:gliner": _ram(d, 20, 20)}
    v = statistik_v21.h5("dev3", d, ram)
    h = v["hipotesis"]
    assert v["k"] == 4 and set(h) == {"H5a", "H5b", "H5c", "H5d"}
    assert h["H5a"]["delta"] == 0 and h["H5a"]["disokong"]          # sama = bukan-inferior (margin 0.01)
    assert h["H5b"]["delta"] > 0 and h["H5b"]["disokong"]
    assert h["H5c"]["metrik"] == "u1" and h["H5c"]["delta"] == 0     # U1: SSM berlabel MY_NRIC = kelas ID yang sama
    assert not h["H5c"]["disokong"] and h["H5d"]["disokong"]
    s = v["susulan"]["H5a+"]
    assert s["diuji"] and not s["disokong"]                           # Δ 0 → keunggulan tidak disokong
    assert all("mde_ketat" in x["kuasa"] for x in h.values())


def test_h5_susulan_tidak_diuji_bila_induk_gagal(monkeypatch):
    monkeypatch.setitem(K["nilai"]["statistik"], "ulangan", 200)
    d = _dok(60)
    ram = {"mypii": _ram(d, 20, 20), "mypii-v2": _ram(d, 60, 60), "llm:anthropic/claude-haiku-5-5": _ram(d, 60, 60),
           "luar:meddies": _ram(d, 0, 0), "luar:gliner": _ram(d, 0, 0)}
    v = statistik_v21.h5("dev3", d, ram)
    assert not v["hipotesis"]["H5a"]["disokong"] and v["susulan"]["H5a+"]["diuji"] is False
    assert "tidak diuji" in statistik_v21.jadual_md(v)
