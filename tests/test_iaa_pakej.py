"""Pemakej bundel IAA (PELAN-IAA P3, ADR-015): urutan sampel, teks + span emas, uji = dev di luar sampel, keluar di luar repo."""

import json

import pytest

from mypii.iaa import pakej


def _jsonl(laluan, awalan, n):
    with open(laluan, "w", encoding="utf-8") as f:
        for i in range(n):
            spans = [{"mula": 4, "tamat": 8, "entiti": "MY_SSM"}, {"mula": 0, "tamat": 3, "entiti": "MY_PHONE"}] \
                if i % 2 else []
            f.write(json.dumps({"id": f"{awalan}-{i:03d}", "bahasa": "ms", "genre": "g",
                                "teks": f"012 1234 dok {awalan}{i}", "spans": spans}) + "\n")


@pytest.fixture
def k(tmp_path):
    _jsonl(tmp_path / "dev.jsonl", "dev", 20)
    _jsonl(tmp_path / "u2.jsonl", "u2", 10)
    dok = [{"urutan": 1, "id": "u2-001", "split": "ujian2", "bahasa": "ms", "berspan": True},
           {"urutan": 2, "id": "dev-004", "split": "dev", "bahasa": "ms", "berspan": False},
           {"urutan": 3, "id": "dev-003", "split": "dev", "bahasa": "ms", "berspan": True}]
    (tmp_path / "sampel.json").write_text(json.dumps({"dokumen": dok}))
    return {"sampel": {"fail": "sampel.json", "benih": 5, "split": {"dev": "dev.jsonl", "ujian2": "u2.jsonl"}},
            "uji": {"dokumen": 4}, "pakej": {"folder": str(tmp_path / "luar"), "bundel": "dokumen.json"}}


def test_urutan_teks_span(k, tmp_path):
    b = pakej.bina(k, tmp_path)
    assert b["n"] == 3 and [d["urutan"] for d in b["dokumen"]] == [1, 2, 3]
    assert [(d["id"], d["split"]) for d in b["dokumen"]] == [("u2-001", "ujian2"), ("dev-004", "dev"),
                                                             ("dev-003", "dev")]
    d = b["dokumen"][0]
    assert d["teks"] == "012 1234 dok u21" and [s["mula"] for s in d["spans"]] == [0, 4]   # span diisih ikut mula
    assert set(d) == {"urutan", "id", "split", "bahasa", "teks", "spans"}                    # genre dll dibuang
    assert len(b["sampel_sha256"]) == 64


def test_uji_dev_luar_sampel_tetap(k, tmp_path):
    a, b = pakej.bina(k, tmp_path), pakej.bina(k, tmp_path)
    assert a["uji"] == b["uji"] and len(a["uji"]) == 4
    assert all(d["split"] == "dev" and d["id"].startswith("dev-") for d in a["uji"])
    assert not {d["id"] for d in a["uji"]} & {"dev-003", "dev-004"}
    assert [d["urutan"] for d in a["uji"]] == [1, 2, 3, 4]


def test_sampel_basi_ralat(k, tmp_path):
    s = json.loads((tmp_path / "sampel.json").read_text())
    s["dokumen"][0]["id"] = "u2-999"
    (tmp_path / "sampel.json").write_text(json.dumps(s))
    with pytest.raises(ValueError, match="tiada dalam fail split"):
        pakej.bina(k, tmp_path)


def test_keluar_dalam_repo_ditolak(capsys):
    assert pakej.main(["--keluar", str(pakej.AKAR / "data" / "iaa" / "x.json")]) == 2
    assert not (pakej.AKAR / "data" / "iaa" / "x.json").exists()
    assert "LUAR repo" in capsys.readouterr().err


def test_uji_tidak_bertindih_sampel_walau_penuh(k, tmp_path):
    k["uji"]["dokumen"] = 18          # 20 dev − 2 dalam sampel = semua calon mesti dipilih
    ids = {d["id"] for d in pakej.bina(k, tmp_path)["uji"]}
    assert ids == {f"dev-{i:03d}" for i in range(20)} - {"dev-003", "dev-004"}
