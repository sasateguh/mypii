"""PELAN-V21 P1: ayat biasa (`data/probe/ayat_biasa.yaml`, bahan pembangunan) — v2.1 (`konteks.gabung.cara: frasa`) menanda setiap
positif dan tiada negatif; `cara: ganti` (v2 = 1.0.x) terlepas ayat berfrasa "IC" (rekod regresi yang dibaiki)."""

import pytest
import yaml
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from mypii import konfig, semua_pengecam

# Tanpa model spaCy (pokok eksport: `uv sync` tanpa kumpulan `nilai`), Presidio MEMUAT TURUN model secara automatik — langkau.
pytest.importorskip("en_core_web_sm")

K = konfig.utama()
PROBE = yaml.safe_load((konfig.AKAR / "data/probe/ayat_biasa.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def enjin():
    nlp = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]}).create_engine()
    e = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
    for p in semua_pengecam("en"):
        e.registry.add_recognizer(p)
    return e


def _span(enjin, teks):
    r = enjin.analyze(text=teks, language="en", score_threshold=K["nilai"]["ambang_skor"])
    return {(x.start, x.end, x.entity_type) for x in r if x.entity_type in K["nilai"]["entiti"]}


def test_probe_sah_struktur_dan_nilai_subrentetan():
    assert len(PROBE["positif"]) >= 20 and len(PROBE["negatif"]) >= 10
    for x in PROBE["positif"] + PROBE["negatif"]:
        assert x["nilai"] in x["teks"]


@pytest.mark.parametrize("x", PROBE["positif"], ids=lambda x: x["teks"][:40])
def test_positif_ditanda(enjin, x):
    a = x["teks"].index(x["nilai"])
    assert (a, a + len(x["nilai"]), x["entiti"]) in _span(enjin, x["teks"])


@pytest.mark.parametrize("x", PROBE["negatif"], ids=lambda x: x["teks"][:40])
def test_negatif_tidak_ditanda(enjin, x):
    a = x["teks"].index(x["nilai"])
    b = a + len(x["nilai"])
    assert not any(m < b and a < t for m, t, _ in _span(enjin, x["teks"]))


def test_cara_ganti_v2_terlepas_ic_biasa(enjin, monkeypatch):
    """Rekod regresi 1.0.x: pengelas memutuskan semua calon → "My IC is …" (p ≈ 0.49) tidak ditanda."""
    monkeypatch.setitem(K["konteks"]["gabung"], "cara", "ganti")
    assert not any(e == "MY_NRIC" for _, _, e in _span(enjin, "My IC is 900101-08-1234"))
