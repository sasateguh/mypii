"""Pensampel IAA (PELAN-IAA P2, ADR-015): strata tepat, benih → bait sama, strata kurang → ralat, tiada teks dalam output."""

import json

import pytest

from mypii.iaa import sampel

RAHSIA = "TEKS-RAHSIA-JANGAN-BOCOR"


def _tulis(laluan, split, bilangan):
    """bilangan dokumen setiap (bahasa, berspan) untuk ms/en."""
    with open(laluan, "w", encoding="utf-8") as f:
        n = 0
        for b in ("ms", "en"):
            for berspan in (True, False):
                for _ in range(bilangan):
                    n += 1
                    spans = [{"mula": 0, "tamat": 4, "entiti": "MY_PHONE"}] if berspan else []
                    f.write(json.dumps({"id": f"{split}-{n:04d}", "bahasa": b, "genre": "x",
                                        "teks": f"{RAHSIA} {n}", "spans": spans}) + "\n")


@pytest.fixture
def k(tmp_path):
    _tulis(tmp_path / "dev.jsonl", "dev", 9)
    _tulis(tmp_path / "u2.jsonl", "u2", 7)
    return {"benih": 7, "setiap_strata": 3, "bahasa": ["ms", "en"],
            "split": {"dev": "dev.jsonl", "ujian2": "u2.jsonl"}}


def test_strata_tepat(k, tmp_path):
    obj, _ = sampel.jana(k, tmp_path)
    assert obj["n"] == 2 * 2 * 2 * 3
    assert len(obj["kiraan"]) == 8 and set(obj["kiraan"].values()) == {3}
    assert [d["urutan"] for d in obj["dokumen"]] == list(range(1, 25))
    assert len({d["id"] for d in obj["dokumen"]}) == 24
    for d in obj["dokumen"]:
        assert d["id"].startswith("dev-" if d["split"] == "dev" else "u2-")


def test_benih_sama_bait_sama_benih_lain_berbeza(k, tmp_path):
    _, a = sampel.jana(k, tmp_path)
    _, b = sampel.jana(k, tmp_path)
    assert a == b
    c, _ = sampel.jana({**k, "benih": 8}, tmp_path)
    assert c["dokumen"] != json.loads(a)["dokumen"]


def test_urutan_dikocok_merentas_split(k, tmp_path):
    obj, _ = sampel.jana(k, tmp_path)
    splits = [d["split"] for d in obj["dokumen"]]
    assert splits != sorted(splits) and splits != sorted(splits, reverse=True)


def test_berspan_dan_bahasa_betul(k, tmp_path):
    obj, _ = sampel.jana(k, tmp_path)
    meta = {m["id"]: m for f in ("dev.jsonl", "u2.jsonl") for m in sampel.baca_meta(tmp_path / f)}
    for d in obj["dokumen"]:
        assert meta[d["id"]]["berspan"] is d["berspan"] and meta[d["id"]]["bahasa"] == d["bahasa"]


def test_strata_kurang_ralat_jelas(k, tmp_path):
    with pytest.raises(ValueError, match=r"ujian2/ms/berspan hanya 7 dokumen \(perlu 8\)"):
        sampel.jana({**k, "setiap_strata": 8}, tmp_path)


def test_tiada_teks_dalam_output(k, tmp_path):
    obj, bait = sampel.jana(k, tmp_path)
    assert RAHSIA.encode() not in bait
    assert {tuple(sorted(d)) for d in obj["dokumen"]} == {("bahasa", "berspan", "id", "split", "urutan")}


def test_main_cetak_kiraan_tanpa_teks(k, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sampel, "AKAR", tmp_path)
    monkeypatch.setattr(sampel.konfig, "utama", lambda: {"iaa": {"sampel": {**k, "fail": "o/s.json"}}})
    assert sampel.main() == 0
    keluar = capsys.readouterr().out
    assert RAHSIA not in keluar and "n=24" in keluar
    assert json.loads((tmp_path / "o/s.json").read_text())["n"] == 24
