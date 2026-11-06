"""Data v3 (PELAN-V2 P3): nilai kategori (b)–(e) betul, span emas = subrentetan tepat, split v3 boleh diulang."""

import json
import random
import re

import phonenumbers
import pytest

from mypii import konfig
from mypii.jana import jana, nilai_v3

K3 = konfig.utama()["jana_v3"]
SSM_ROB = konfig.muat("ssm_rob")
LLP = {k for k, v in SSM_ROB["kod_entiti"].items() if v["llp"]}


def test_llp_tahun_min_satu_sumber_ditambat_pada_tarikh_akta():
    """Tahun minimum LLP = tahun Akta 743 berkuat kuasa (fakta rasmi), dibaca dari ssm_rob.yaml SAHAJA — sabotaj tahun_min merah."""
    assert SSM_ROB["llp"]["tahun_min"] == int(SSM_ROB["llp"]["berkuat_kuasa"][:4]) == 2012
    assert nilai_v3.llp_tahun_min() == SSM_ROB["llp"]["tahun_min"]
    assert "llp_tahun_min" not in K3  # tiada nilai pendua dalam mypii.yaml


def test_ssm_llp_sentiasa_tahun_min_ke_atas():
    tahun_akta = int(SSM_ROB["llp"]["berkuat_kuasa"][:4])
    rng = random.Random(1)
    for _ in range(2000):
        n = nilai_v3.ssm(rng)
        assert re.fullmatch(r"\d{12}", n) and n[4:6] in SSM_ROB["kod_entiti"]
        if n[4:6] in LLP:
            assert int(n[:4]) >= tahun_akta
    for _ in range(500):
        n = nilai_v3.llp(rng)
        assert n[4:6] in LLP and int(n[:4]) >= tahun_akta


def test_rob_lama_enggan_tanpa_awalan_disahkan():
    assert SSM_ROB["rob_lama"]["awalan_disahkan"] == []
    with pytest.raises(ValueError, match="GUGUR"):
        jana.isi_v3("Reg {MY_ROB}", random.Random(0), {})


def test_talian_bs_sah_dan_kod_sabah_sarawak():
    rng = random.Random(2)
    kod = set(SSM_ROB["talian_tetap_bs"]["digit_pertama"])
    for _ in range(500):
        n = nilai_v3.talian_bs(rng)
        p = phonenumbers.parse(n, "MY")
        assert phonenumbers.is_valid_number(p)
        assert phonenumbers.number_type(p) == phonenumbers.PhoneNumberType.FIXED_LINE
        assert "0" + str(p.national_number)[:2] in kod


def test_neg12_berbentuk_mykad():
    rng = random.Random(3)
    for _ in range(300):
        d = re.sub(r"\D", "", nilai_v3.neg12(rng))
        assert len(d) == 12 and d[6:8] in konfig.kod_pb_sah()


def test_ocr_satu_aksara_diapit_digit():
    rng = random.Random(4)
    peta = K3["ocr_ganti"]
    for _ in range(300):
        asal = nilai_v3.ssm(rng)
        ocr = nilai_v3.ocr(rng, asal)
        assert ocr is not None and len(ocr) == len(asal)
        beza = [i for i, (a, b) in enumerate(zip(asal, ocr)) if a != b]
        assert len(beza) == 1 and 0 < beza[0] < len(asal) - 1
        i = beza[0]
        assert peta[asal[i]] == ocr[i] and ocr[i - 1].isdigit() and ocr[i + 1].isdigit()
    assert nilai_v3.ocr(rng, "1-2") is None  # tiada digit diapit digit
    assert nilai_v3.ocr(rng, "1-5-8-0") is None  # 5/8 diapit '-' = bukan "dalam nombor"
    assert {nilai_v3.ocr(rng, "1550") for _ in range(50)} == {"1S50", "15S0"}  # hujung (1, 0) tidak pernah diganti


def test_patah_di_sempadan_kumpulan():
    rng = random.Random(5)
    assert nilai_v3.patah(rng, "900101-14-5566", "MY_NRIC").replace("\n", "-").replace(" ", "").count("-") == 2
    for _ in range(100):
        p = nilai_v3.patah(rng, "900101145566", "MY_NRIC")
        assert "\n" in p and p.index("\n") in {6, 7, 8, 9} and re.sub(r"\s", "", p) == "900101145566"
    assert nilai_v3.patah(rng, "+60123456789", "MY_PHONE") is None  # rapat bukan-digit: tiada sempadan yakin


@pytest.mark.parametrize("slot,tanda", [("OCR_MY_NRIC", "ocr"), ("PATAH_MY_NRIC", "\n"), ("PATAH_MY_PHONE", "\n"),
                                        ("OCR_MY_SSM", "ocr"), ("MY_PHONE_BS", None), ("MY_SSM_LLP", None)])
def test_span_emas_subrentetan_tepat(slot, tanda):
    rng = random.Random(6)
    huruf = set(K3["ocr_ganti"].values())
    ditanda = 0
    for _ in range(50):
        teks, spans, kategori = jana.isi_v3(f"Nombor: {{{slot}}} ok", rng, {})
        assert len(spans) == 1
        s = spans[0]
        nilai = teks[s["mula"]:s["tamat"]]
        assert teks == f"Nombor: {nilai} ok" and nilai == nilai.strip()
        d = {"kategori": "d", "mula": s["mula"], "tamat": s["tamat"]} in kategori
        if tanda == "ocr":
            assert d == bool(set(nilai) & huruf)
        elif tanda:
            assert d == (tanda in nilai)
        else:
            assert kategori[0]["kategori"] == ("c" if slot == "MY_PHONE_BS" else "b")
        ditanda += d
    assert ditanda >= (40 if tanda else 0)  # nilai tanpa kedudukan layak (cth +60 rapat) dilangkau, bukan dilabel salah


def test_neg12_tanpa_dicatat_hanya_tanpa_kata_negatif():
    teks, spans, kategori = jana.isi_v3("No. ahli {NEG12_TANPA} aktif", random.Random(7), {})
    assert spans == [] and [k["kategori"] for k in kategori] == ["e"]
    assert not nilai_v3.ada_kata_negatif(teks)
    teks, spans, kategori = jana.isi_v3("No. akaun {NEG12_TANPA}", random.Random(7), {})
    assert spans == [] and kategori == [] and nilai_v3.ada_kata_negatif(teks)


def test_ada_kata_negatif_sempadan_perkataan():
    assert nilai_v3.ada_kata_negatif("Sila semak Invoice no 3")
    assert not nilai_v3.ada_kata_negatif("prefer bordered referral")  # 'ref'/'order' dalam perkataan lain


@pytest.fixture(scope="module")
def v3(tmp_path_factory):
    keluar = tmp_path_factory.mktemp("v3")
    return keluar, jana.jana_v3(keluar)


def test_jana_v3_saiz_config_ujian3_hanya_bila_templat_wujud_dan_boleh_diulang(v3, tmp_path):
    """P3: tanpa templat ujian3 → latih3/dev3 sahaja. P6 (5 Nov): templat + nama ujian3 dikomit → ujian3 juga, KUNCI3 berasingan
    daripada CINCANGAN3. Kandungan ujian3 TIDAK dibaca (kiraan + kewujudan fail sahaja)."""
    keluar, r = v3
    ada3 = bool(jana._templat(jana.AKAR / K3["templat_ujian3"])) and (jana.AKAR / K3["nama_ujian3"]).exists()
    jangka = {"latih3": K3["bilangan"]["latih3"], "dev3": K3["bilangan"]["dev3"]} | ({"ujian3": K3["bilangan"]["ujian3"]} if ada3 else {})
    assert {s: r[s]["dokumen"] for s in r} == jangka
    assert json.loads((keluar / "CINCANGAN3.json").read_text()) == {s: r[s] for s in ("latih3", "dev3")}
    assert (keluar / "KUNCI3.json").exists() == ada3 == (keluar / "ujian3.jsonl").exists()
    if ada3:
        assert json.loads((keluar / "KUNCI3.json").read_text()) == {"ujian3": r["ujian3"]}
        assert json.loads((jana.AKAR / "data/bench_v3/KUNCI3.json").read_text()) == {"ujian3": r["ujian3"]}   # repo = jana semula
    assert jana.jana_v3(tmp_path) == r


def test_jana_v3_kategori_dalam_span_emas_dan_e_tanpa_kata_negatif(v3):
    keluar, _ = v3
    kiraan = {k: 0 for k in "abcde"}
    for baris in (keluar / "dev3.jsonl").read_text(encoding="utf-8").splitlines():
        d = json.loads(baris)
        emas = {(s["mula"], s["tamat"]) for s in d["spans"]}
        for k in d["kategori"]:
            kiraan[k["kategori"]] += 1
            if k["kategori"] == "e":
                assert (k["mula"], k["tamat"]) not in emas and not nilai_v3.ada_kata_negatif(d["teks"])
            else:
                assert (k["mula"], k["tamat"]) in emas
        for s in d["spans"]:
            assert d["teks"][s["mula"]:s["tamat"]].strip() == d["teks"][s["mula"]:s["tamat"]]
    assert kiraan["a"] == 0 and all(kiraan[k] > 0 for k in "bcde")
