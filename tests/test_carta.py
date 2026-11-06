"""PELAN-C C2b (ADR-006 §Iterasi): carta `hasil/kemajuan.svg` — data sintetik, tiada spaCy/Presidio/rangkaian."""

import xml.etree.ElementTree as ET

from mypii.nilai import carta

NS = "{http://www.w3.org/2000/svg}"


def _b(dev: str, f1: str, status: str = "simpan", ket: str = "x") -> dict:
    return {"tarikh": "2026-10-30", "komit": "abc1234", "dev_sha8": dev, "f1": f1, "status": status,
            "baris_kod": "+0/-0", "keterangan": ket}


def _akar(baris):
    return ET.fromstring(carta.lukis(baris))


def _titik(akar):
    return [g for g in akar.iter(f"{NS}g") if g.get("class") == "titik"]


def _garis(akar):
    return [p for p in akar.iter(f"{NS}path") if p.get("class") == "best s-simpan" and p.get("data-segmen")]


def test_xml_sah_dan_titik_sama_dengan_baris():
    baris = [_b("aaaaaaaa", "0.8"), _b("aaaaaaaa", "0.9", "buang"), _b("aaaaaaaa", "", "crash"),
             _b("aaaaaaaa", "0.85", "ukur"), _b("bbbbbbbb", "", "ukur")]
    akar = _akar(baris)
    assert akar.tag == f"{NS}svg"
    t = _titik(akar)
    assert len(t) == len(baris)
    assert [g.get("data-status") for g in t] == [b["status"] for b in baris]


def test_segmen_dipecah_bila_dev_berubah():
    sama = [_b("aaaaaaaa", v) for v in ("0.80", "0.85", "0.90", "0.95")]
    assert len(_garis(_akar(sama))) == 1
    beza = sama[:2] + [_b("bbbbbbbb", v) for v in ("0.70", "0.75")]
    g = _garis(_akar(beza))
    assert [p.get("data-segmen") for p in g] == ["1", "3"]
    assert carta.segmen(beza) == [[0, 1], [2, 3]]


def test_dev_tidak_diketahui_tidak_disambung():
    baris = [_b("?", "0.8"), _b("?", "0.9"), _b("aaaaaaaa", "0.7"), _b("aaaaaaaa", "0.75")]
    assert carta.segmen(baris) == [[0], [1], [2, 3]]
    assert [p.get("data-segmen") for p in _garis(_akar(baris))] == ["3"]
    assert carta.larian_label(baris) == [0, 2]


def test_terbaik_simpan_sahaja():
    baris = [_b("a", "0.8"), _b("a", "0.99", "buang"), _b("a", "0.95", "ukur"), _b("a", "0.7"), _b("a", "0.9")]
    assert carta.terbaik(baris, [0, 1, 2, 3, 4]) == [(0, 0.8), (4, 0.9)]


def test_crash_dan_tiada_f1_di_lorong_dasar():
    baris = [_b("a", "0.8"), _b("a", "", "crash"), _b("a", "", "ukur"), _b("a", "0.9")]
    t = _titik(_akar(baris))
    y = [float(g.get("transform").split(",")[1].rstrip(")")) for g in t]
    assert y[1] == y[2] > max(y[0], y[3])


def test_teks_dilepaskan_dan_bait_sama(tmp_path):
    baris = [_b("a", "0.8", ket="<script>&\"'"), _b("a", "0.9")]
    assert carta.lukis(baris) == carta.lukis(baris)
    _akar(baris)  # XML sah walaupun keterangan berisi < & "
    masuk = tmp_path / "i.tsv"
    lajur = list(baris[0])
    masuk.write_text("\t".join(lajur) + "\n" + "".join("\t".join(b[k] for k in lajur) + "\n" for b in baris))
    k1, k2 = tmp_path / "1.svg", tmp_path / "2.svg"
    assert carta.main(["--masuk", str(masuk), "--keluar", str(k1)]) == 0
    assert carta.main(["--masuk", str(masuk), "--keluar", str(k2)]) == 0
    assert k1.read_bytes() == k2.read_bytes()


def test_fail_kosong_tidak_crash():
    assert _titik(_akar([])) == []
