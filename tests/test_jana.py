"""Penjana P1: negatif keras mesti benar-benar negatif, dan slot alias dilabel dengan entiti yang betul."""

import random
import re

import phonenumbers
import yaml

from mypii import konfig
from mypii.jana import jana, nilai_palsu


def test_telefon_tidak_sah_ditolak_libphonenumber():
    rng = random.Random(1)
    for _ in range(200):
        assert not phonenumbers.is_valid_number(phonenumbers.parse(nilai_palsu.telefon_tidak_sah(rng), "MY"))


def test_ssm_lama_bentuk_lama():
    rng = random.Random(2)
    for _ in range(100):
        assert re.fullmatch(r"\d{4,7}-[A-Z]", nilai_palsu.ssm_lama(rng))


def test_slot_alias_dilabel_entiti_asal():
    teks, spans = jana.isi("Reg {MY_SSM_LAMA}", random.Random(3), {})
    assert spans == [{"mula": 4, "tamat": len(teks), "entiti": "MY_SSM"}]


def test_slot_negatif_p1_tiada_label():
    rng = random.Random(4)
    for slot in jana.NEGATIF_P1:
        _, spans = jana.isi(f"x {{{slot}}} y", rng, {})
        assert spans == []


def test_akaun_bank_separuh_berbentuk_mykad():
    """Negatif paling sukar mesti wujud: 12 digit dengan tarikh + kod PB sah (hanya konteks membezakannya)."""
    rng = random.Random(5)
    nilai = [re.sub(r"\D", "", nilai_palsu.akaun_bank(rng)) for _ in range(400)]
    assert 100 < sum(len(n) == 12 for n in nilai) < 300


def test_no_ahli12_rapat_dan_separuh_berbentuk_mykad():
    rng = random.Random(6)
    nilai = [nilai_palsu.no_ahli12(rng) for _ in range(400)]
    assert all(re.fullmatch(r"\d{12}", n) for n in nilai)
    assert 150 < sum(n[6:8] in konfig.kod_pb_sah() for n in nilai)


def test_templat_berawalan_llm_digabung_ke_bahasa(tmp_path):
    (tmp_path / "ms.yaml").write_text("genre: {a: [satu]}\n")
    (tmp_path / "llm_ms.yaml").write_text("genre: {b: [dua]}\n")
    assert jana._templat(tmp_path) == {"ms": [("b", "dua"), ("a", "satu")]}


def test_gabung_nama_latih_sahaja_dan_tanpa_fail_tiada_rng(tmp_path):
    lama = {"nama_pertama": ["Ali"], "nama_akhir": ["bin Abu"], "syarikat": ["A Sdn Bhd"], "bandar": ["Tapah"]}
    assert jana.gabung_nama(lama, tmp_path / "tiada.yaml") is lama
    f = tmp_path / "t.yaml"
    f.write_text(yaml.safe_dump({"syarikat": ["A Sdn Bhd", "B Trading"], "bandar": ["Jasin"], "pertama_cina": ["Jun Hao"]}))
    g = jana.gabung_nama(lama, f)
    assert g["syarikat"] == ["A Sdn Bhd", "B Trading"] and g["bandar"] == ["Tapah", "Jasin"] and "syarikat" in g[jana.TAMBAHAN]
    assert lama["syarikat"] == ["A Sdn Bhd"]   # nama.yaml v1 tidak diubah di tempat
    a, b = random.Random(1), random.Random(1)
    jana.nama_orang(a, lama)
    b.choice(lama["nama_pertama"]), b.choice(lama["nama_akhir"])
    assert a.random() == b.random()   # tiada TAMBAHAN = jujukan rng v1 tepat
