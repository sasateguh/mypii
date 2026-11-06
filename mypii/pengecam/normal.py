"""Normalisasi sebelum padanan corak (PELAN-V2 P9, PRA-DAFTAR §3.1 kategori (d)).

- OCR: aksara dalam `pengecam.normal.ocr_digit` yang DIAPIT digit kiri dan kanan diganti digitnya ("45O325" → "450325").
  Penggantian 1:1, jadi kedudukan mula/tamat dalam teks asal kekal sama — span dilapor atas teks ASAL (termasuk aksara OCR).
- Patah baris: `pemisah(...)` membina pemisah sempadan kumpulan = pemisah biasa ATAU `pengecam.normal.patah_baris`.

Semua nilai dari config; tiada rangkaian.
"""

from functools import lru_cache

import regex as re

from mypii import konfig


def _k() -> dict:
    return konfig.utama()["pengecam"]["normal"]


@lru_cache(maxsize=8)
def _corak_ocr(aksara: str) -> re.Pattern:
    return re.compile(rf"(?<=\d)[{re.escape(aksara)}](?=\d)")


def ocr(teks: str) -> str:
    peta = _k()["ocr_digit"]
    if not peta:
        return teks
    return _corak_ocr("".join(sorted(peta))).sub(lambda m: peta[m.group(0)], teks)


def pemisah(biasa: str) -> str:
    """Pemisah sempadan kumpulan pilihan: `biasa` (kelas aksara regex, cth `[ \\-.]`) atau patah baris config."""
    return rf"(?:{biasa}|{_k()['patah_baris']})?"


def digit(teks: str) -> str:
    return "".join(c for c in teks if c.isdigit())


class NormalOCR:
    """Mixin PatternRecognizer: corak dipadan atas teks dinormal OCR (panjang sama) — `validate_result` menerima teks dinormal."""

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):
        return super().analyze(ocr(text), entities, nlp_artifacts, regex_flags)
