"""Alat analisis ralat (A3 P3): pengelasan ralat + probe sintetik. Tidak menjalankan enjin Presidio."""

import random

import pytest
import yaml

from mypii import analisis, konfig


def _s(mula, tamat, entiti="MY_NRIC"):
    return {"mula": mula, "tamat": tamat, "entiti": entiti}


def test_kelaskan_semua_jenis():
    emas = [_s(0, 12), _s(20, 30, "MY_SSM"), _s(40, 50), _s(60, 70)]
    ramal = [_s(0, 12), _s(20, 30, "MY_NRIC"), _s(40, 48), _s(80, 90, "MY_PHONE")]
    jenis = sorted((r["jenis"], r["entiti"]) for r in analisis.kelaskan(emas, ramal))
    assert jenis == [("fn", "MY_NRIC"), ("fp", "MY_PHONE"), ("keliru", "MY_NRIC"), ("sempadan", "MY_NRIC")]


def test_kelaskan_tiada_ralat():
    assert analisis.kelaskan([_s(0, 5)], [_s(0, 5)]) == []


@pytest.fixture(scope="module")
def probe():
    return yaml.safe_load((konfig.AKAR / "data/probe/ralat.yaml").read_text(encoding="utf-8"))


def test_probe_span_menunjuk_nilai_berlabel(probe):
    dok = analisis.jana_probe(n=6, benih=1)
    assert {d["kategori"] for d in dok} == set(probe["kategori"])
    for d in dok:
        for s in d["spans"]:
            nilai = d["teks"][s["mula"]:s["tamat"]]
            assert nilai and nilai == nilai.strip(), d
            assert sum(ch.isdigit() for ch in nilai) >= 4, d  # SSM lama boleh 4 digit


def test_probe_negatif_tiada_label(probe):
    for d in analisis.jana_probe(n=4, benih=2):
        if d["kategori"] in ("negatif_berkurung", "negatif_tanpa_kata", "telefon_bukan_telefon"):
            assert d["spans"] == [], d


def test_ubah_ocr_sentiasa_menukar_dan_patah_baris(probe):
    rng = random.Random(3)
    for _ in range(50):
        asal = "800101-14-5023"
        baru = analisis._ubah(asal, "ocr_digit", probe["ubah"], rng)
        assert baru != asal and len(baru) == len(asal)
    assert "\n" in analisis._ubah("800101145023", "patah_baris", probe["ubah"], rng)


def test_syarikat_probe_tiada_dalam_senarai_bench(probe):
    nama = yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    assert not set(probe["syarikat_baharu"]) & set(nama["syarikat"])


def test_split_ujian_ditolak(monkeypatch):
    monkeypatch.setattr("sys.argv", ["analisis", "--split", "ujian"])
    assert analisis.main() == 2
