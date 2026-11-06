from collections.abc import Iterable
from datetime import date

from presidio_analyzer import Pattern, PatternRecognizer

from mypii import konfig
from mypii.pengecam.konteks import KonteksFrasa
from mypii.pengecam.normal import NormalOCR

# MyKad: YYMMDD-PB-###G. YYMMDD = tarikh lahir, PB = kod tempat lahir (JPN), G ganjil/genap = jantina.
# Tiada digit semak, jadi ketepatan datang daripada tarikh sah + kod PB sah + perkataan konteks.
# Corak bersela ruang menolak kumpulan digit tulen di depannya (sebahagian nombor lebih panjang), bukan digit
# dalam perkataan OCR ("N0 900101 08 1234"). Lookbehind panjang berubah: Presidio memakai modul `regex`.


class MyNricRecognizer(NormalOCR, KonteksFrasa, PatternRecognizer):
    """Recognize Malaysian NRIC (MyKad) numbers, validated by birth date and place-of-birth code."""

    COUNTRY_CODE = "my"

    def __init__(
        self,
        patterns: list[Pattern] | None = None,
        context: list[str] | None = None,
        supported_language: str = "en",
        supported_entity: str = "MY_NRIC",
        name: str | None = None,
        valid_pb_codes: Iterable[str] | None = None,
    ):
        k = konfig.utama()["pengecam"]["MY_NRIC"]
        skor = k["skor"]
        nl = konfig.utama()["pengecam"]["normal"]["patah_baris"]   # P9: sempadan kumpulan boleh dipecah baris
        patterns = patterns or [
            Pattern("NRIC (dashed)", rf"(?<![\d-])\d{{6}}(?:-|{nl})\d{{2}}(?:-|{nl})\d{{4}}(?![\d-])", skor["bersempang"]),
            Pattern("NRIC (spaced)", rf"(?<!\d)(?<!(?:^|\W)\d+ )\d{{6}}(?: |{nl})\d{{2}}(?: |{nl})\d{{4}}(?! ?\d)", skor["bersempang"]),
            Pattern("NRIC (compact)", rf"(?<!\d)\d{{6}}(?:{nl})?\d{{2}}(?:{nl})?\d{{4}}(?!\d)", skor["rapat"]),
        ]
        self.valid_pb_codes = set(valid_pb_codes) if valid_pb_codes else konfig.kod_pb_sah()
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context or k["konteks"],
            supported_language=supported_language,
            name=name,
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        digits = "".join(c for c in pattern_text if c.isdigit())
        if len(digits) != 12:
            return False
        if digits[6:8] not in self.valid_pb_codes:
            return False
        yy, mm, dd = int(digits[0:2]), int(digits[2:4]), int(digits[4:6])
        for abad in (1900, 2000):
            try:
                if date(abad + yy, mm, dd) <= date.today():
                    return True
            except ValueError:
                continue  # cth 000229: 1900 bukan tahun lompat, 2000 ya
        return False
