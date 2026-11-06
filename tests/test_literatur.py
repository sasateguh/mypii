"""Kajian literatur (A3 P4): rujukan.bib dan RINGKASAN.md konsisten. Luar talian — kewujudan DOI = `make sahkan-rujukan`."""

import re

from mypii import konfig

LIT = konfig.AKAR / "docs/literatur"
ENTRI = re.compile(r"^@\w+\{([^,\s]+),", re.MULTILINE)


def _entri():
    teks = (LIT / "rujukan.bib").read_text(encoding="utf-8")
    bahagian = re.split(r"^(?=@)", teks, flags=re.MULTILINE)[1:]
    return {ENTRI.match(b).group(1): b for b in bahagian}


def test_setiap_entri_ada_doi_unik():
    entri = _entri()
    assert entri, "rujukan.bib kosong"
    doi = {}
    for kunci, badan in entri.items():
        m = re.search(r"^\s*doi\s*=\s*\{([^}]+)\}", badan, re.MULTILINE)
        assert m, f"{kunci}: tiada medan doi"
        assert re.fullmatch(r"10\.\d{4,9}/\S+", m.group(1)), f"{kunci}: DOI tidak sah {m.group(1)}"
        doi.setdefault(m.group(1).lower(), []).append(kunci)
    assert not {d: k for d, k in doi.items() if len(k) > 1}, "DOI pendua"


def test_kunci_unik():
    teks = (LIT / "rujukan.bib").read_text(encoding="utf-8")
    kunci = ENTRI.findall(teks)
    assert len(kunci) == len(set(kunci))


def test_petikan_ringkasan_sepadan_bib():
    dipetik = set(re.findall(r"\[@([^\]\s]+)\]", (LIT / "RINGKASAN.md").read_text(encoding="utf-8")))
    entri = set(_entri())
    assert dipetik - entri == set(), "petikan tanpa entri .bib"
    assert entri - dipetik == set(), "entri .bib tidak dipetik"
