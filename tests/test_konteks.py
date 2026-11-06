"""Lapisan FRASA KonteksFrasa (v1). Pengelas konteks P11 dimatikan di sini — ia diuji dalam test_pengelas_konteks.py."""

import pytest
from presidio_analyzer import RecognizerResult

from mypii import konfig
from mypii.pengecam import MyNricRecognizer, MySsmRecognizer


@pytest.fixture(autouse=True)
def tanpa_pengelas(monkeypatch):
    monkeypatch.setitem(konfig.utama()["konteks"], "aktif", False)
    from mypii.pengecam import pengelas
    pengelas._model.cache_clear()
    yield
    pengelas._model.cache_clear()


def _skor(pengecam, teks: str, nilai: str, skor: float) -> float:
    mula = teks.index(nilai)
    r = RecognizerResult(pengecam.supported_entities[0], mula, mula + len(nilai), skor,
                         recognition_metadata={RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: pengecam.id})
    pengecam.enhance_using_context(teks, [r], [], None)
    assert r.recognition_metadata[RecognizerResult.IS_SCORE_ENHANCED_BY_CONTEXT_KEY] is True
    return r.score


def test_frasa_berbilang_perkataan_dipadan():
    assert _skor(MySsmRecognizer(), "Kedai Runcit Sdn Bhd (859836-X)", "859836-X", 0.1) >= 0.4
    assert _skor(MySsmRecognizer(), "No. Pendaftaran: 859836-X", "859836-X", 0.1) >= 0.4


def test_kata_pendek_tidak_padan_dalam_perkataan_lain():
    # Presidio lalai memadan "ic" sebagai subrentetan "basic"/"public"
    assert _skor(MyNricRecognizer(), "basic 900101081234", "900101081234", 0.3) == 0.3
    assert _skor(MyNricRecognizer(), "Public Bank 900101081234", "900101081234", 0.3) == 0.3
    assert _skor(MyNricRecognizer(), "no. ic 900101081234", "900101081234", 0.3) >= 0.4


def test_konteks_jauh_di_luar_tetingkap_diabaikan():
    teks = "IC: satu dua tiga empat lima enam tujuh 900101081234"
    assert _skor(MyNricRecognizer(), teks, "900101081234", 0.3) == 0.3


def test_frasa_negatif_terdekat_membuang_hasil():
    assert _skor(MyNricRecognizer(), "bank in ke akaun 900101 08 1234 ya", "900101 08 1234", 0.5) == 0.0
    assert _skor(MySsmRecognizer(), "parcel tracking 201901000005 esok", "201901000005", 0.4) == 0.0


def test_frasa_positif_lebih_dekat_mengatasi_negatif():
    assert _skor(MyNricRecognizer(), "akaun pemohon, no. kp 900101 08 1234", "900101 08 1234", 0.5) >= 0.85


def test_konteks_ssm_terdekat_membatalkan_nric():
    # 201103258714 sah sebagai MyKad (tarikh 110325, PB 87) DAN SSM baharu (2011, jenis 03)
    assert _skor(MyNricRecognizer(), "Company No. 201103258714", "201103258714", 0.3) == 0.0
    assert _skor(MySsmRecognizer(), "Company No. 201103258714", "201103258714", 0.4) >= 0.75


def test_kata_tunggal_ssm_lama():
    assert _skor(MySsmRecognizer(), "co. Delima Trading reg 643792-K, pic", "643792-K", 0.1) >= 0.4
    assert _skor(MySsmRecognizer(), "kod produk 643792-K", "643792-K", 0.1) == 0.1


def test_kekeliruan_ocr_dalam_kata_konteks():
    assert _skor(MySsmRecognizer(), "lNVOICE  201901000005  DATE", "201901000005", 0.4) == 0.0
    assert _skor(MyNricRecognizer(), "lC N0 900101 08 1234 HP", "900101 08 1234", 0.5) >= 0.85


def test_jadual_teks_memakai_pengepala_lajur():
    teks = "Syarikat\tNo. SSM\tPengarah\tIC Pengarah\nKedai Runcit\t201103258714\tHui Min\t821229545327"
    assert _skor(MyNricRecognizer(), teks, "821229545327", 0.3) >= 0.4
    assert _skor(MyNricRecognizer(), teks, "201103258714", 0.3) == 0.0   # lajur "No. SSM", bukan "IC Pengarah"
    teks = "Acct No           Amount\n900101 08 1234    RM 1,200"
    assert _skor(MyNricRecognizer(), teks, "900101 08 1234", 0.5) == 0.0


def test_baris_tunggal_berjarak_bukan_jadual():
    assert _skor(MySsmRecognizer(), "lNVOICE  201901000005   DATE  30-07", "201901000005", 0.4) == 0.0
