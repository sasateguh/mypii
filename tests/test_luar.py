"""Pemetaan + pandangan skor model luar (pindaan PRA-DAFTAR 2026-11-14) atas data mainan; tiada rangkaian/Modal."""
from mypii.nilai import harness, luar


def _d(spans, teks="x" * 60):
    return {"id": "t", "bahasa": "en", "teks": teks, "spans": spans}


def test_kelas_u1_satukan_nric_dan_ssm():
    assert [s["entiti"] for s in luar._kelas([{"mula": 0, "tamat": 1, "entiti": "MY_SSM"},
                                              {"mula": 2, "tamat": 3, "entiti": "MY_NRIC"},
                                              {"mula": 4, "tamat": 5, "entiti": "MY_PHONE"}])] == ["ID", "ID", "TEL"]


def test_nric_ketat_abaikan_ramalan_atas_ssm_bukan_fp():
    d = _d([{"mula": 0, "tamat": 12, "entiti": "MY_NRIC"}, {"mula": 20, "tamat": 32, "entiti": "MY_SSM"}])
    r = [{"mula": 0, "tamat": 12, "entiti": "ID"}, {"mula": 20, "tamat": 32, "entiti": "ID"}]
    emas, p = luar._nric_ketat(d, r)
    s = harness.skor([emas], [p])["semua|N"]["tepat"]
    assert (s["p"], s["r"]) == (1.0, 1.0)


def test_peta_meddies_tiada_ssm_dan_label_lain_diabaikan():
    assert set(luar.PETA["meddies"].values()) == {"ID", "MY_PHONE"}
    assert "company_name" not in luar.PETA["meddies"]


def test_kategori_e_kira_ramalan_sebagai_fp():
    d = {**_d([]), "kategori": [{"kategori": "e", "mula": 5, "tamat": 17}]}
    assert luar._kategori([d], [[{"mula": 5, "tamat": 17, "entiti": "ID"}]]) == {"e": {"n": 1, "kena": 1}}
