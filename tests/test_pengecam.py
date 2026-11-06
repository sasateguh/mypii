import pytest

from mypii.pengecam import MyNricRecognizer, MyPhoneRecognizer, MySsmRecognizer


@pytest.fixture(scope="module")
def nric():
    return MyNricRecognizer()


@pytest.mark.parametrize("nilai", ["900101-08-1234", "900101 08 1234", "900101081234", "000229-14-0001", "851231-82-5678"])
def test_nric_sah(nric, nilai):
    assert nric.validate_result(nilai) is True


@pytest.mark.parametrize("nilai,sebab", [
    ("901301-08-1234", "bulan 13"), ("900230-08-1234", "30 Feb"), ("900101-00-1234", "PB 00"),
    ("900101-17-1234", "PB 17 tiada"), ("900101-70-1234", "PB 70 tiada"), ("900101-95-1234", "PB 95 tiada"),
    ("90010108123", "11 digit"), ("050229-14-0001", "2005 bukan tahun lompat"),
])
def test_nric_tolak(nric, nilai, sebab):
    assert nric.validate_result(nilai) is False, sebab


def test_semua_kod_pb_jpn_diterima(nric):
    # 86 kod dari jpn.gov.my/my/kod-negeri + /kod-negara (disemak 28 Okt 2026)
    assert len(nric.valid_pb_codes) == 86
    for pb in ["01", "16", "21", "59", "60", "68", "71", "72", "74", "79", "82", "83", "93", "98", "99"]:
        assert pb in nric.valid_pb_codes


@pytest.mark.parametrize("nilai,dijangka", [
    ("201901000005", True), ("199801123456", True), ("202603999999", True),
    ("201907000005", False), ("189901000001", False), ("209901000001", False), ("1312525-A", None),
])
def test_ssm(nilai, dijangka):
    assert MySsmRecognizer().validate_result(nilai) is dijangka


@pytest.mark.parametrize("nilai,dijangka", [
    ("012-345 6789", True), ("+60 12-345 6789", True), ("011-1234 5678", True), ("03-2123 4567", True),
    ("012-345", False), ("+65 9123 4567", False),
])
def test_telefon(nilai, dijangka):
    assert MyPhoneRecognizer().validate_result(nilai) is dijangka


@pytest.mark.parametrize("teks,dijangka", [
    ("lC N0 900101 08 1234 HP", ["900101 08 1234"]),   # digit dalam perkataan OCR bukan sebahagian nombor
    ("acc 12 900101 08 1234", []), ("RM 1,200 900101 08 1234", []),
])
def test_nric_bersela_ruang_sempadan(nric, teks, dijangka):
    assert [teks[r.start:r.end] for r in nric.analyze(teks, ["MY_NRIC"])] == dijangka


# P2-10 diundur 29 Okt 2026: kurungan SAHAJA bukan bukti SSM — probe 40/40 FP kod produk "(560578-W)". Bentuk berkurung perlu
# konteks (Sdn Bhd, no. pendaftaran…) seperti SSM lama lain; lihat test_konteks.test_frasa_berbilang_perkataan_dipadan.
@pytest.mark.parametrize("teks", ["Warisan Katering (115948-H) dokumen", "Model penapis air (560578-W) habis stok", "kod produk 115948-H"])
def test_ssm_lama_dalam_kurungan_perlu_konteks(teks):
    assert all(x.score < 0.4 for x in MySsmRecognizer().analyze(teks, ["MY_SSM"]))
