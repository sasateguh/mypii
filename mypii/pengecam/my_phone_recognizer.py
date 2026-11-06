
import phonenumbers
from presidio_analyzer import Pattern, PatternRecognizer

from mypii import konfig
from mypii.pengecam.konteks import KonteksFrasa
from mypii.pengecam.normal import NormalOCR, pemisah

# Corak menangkap calon; kesahan sebenar (awalan operator/kawasan, panjang) diputuskan oleh libphonenumber
# untuk rantau MY — kebergantungan yang sudah dibawa Presidio.


class MyPhoneRecognizer(NormalOCR, KonteksFrasa, PatternRecognizer):
    """Recognize Malaysian mobile and landline numbers, validated with libphonenumber (region MY)."""

    COUNTRY_CODE = "my"

    def __init__(
        self,
        patterns: list[Pattern] | None = None,
        context: list[str] | None = None,
        supported_language: str = "en",
        supported_entity: str = "MY_PHONE",
        name: str | None = None,
    ):
        k = konfig.utama()["pengecam"]["MY_PHONE"]
        sep = pemisah(r"[ \-.]")   # P9: pemisah biasa ATAU patah baris (config pengecam.normal)
        patterns = patterns or [
            Pattern("MY phone (+60)", rf"(?<![\w+])\+?60{sep}1\d{sep}\d{{3,4}}{sep}\d{{4}}(?!\d)",
                    k["skor"]["antarabangsa"]),
            Pattern("MY mobile (01x)", rf"(?<![\w+])01\d{sep}\d{{3,4}}{sep}\d{{4}}(?!\d)",
                    k["skor"]["tempatan"]),
            Pattern("MY landline", rf"(?<![\w+])(?:\+?60{sep}|0)[3-9]\d?{sep}\d{{3,4}}{sep}\d{{3,4}}(?!\d)",
                    k["skor"]["tempatan"]),
            # P9 (kategori c): kod kawasan dalam kurungan "(082) 771667" — span termasuk kurungan
            Pattern("MY landline (bracketed area)", rf"(?<![\w+(])\(0[3-9]\d?\){sep}\d{{3,4}}{sep}\d{{3,4}}(?!\d)",
                    k["skor"]["tempatan"]),
        ]
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context or k["konteks"],
            supported_language=supported_language,
            name=name,
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        try:
            nombor = phonenumbers.parse(" ".join(pattern_text.split()), "MY")   # patah baris → satu ruang
        except phonenumbers.NumberParseException:
            return False
        return nombor.country_code == 60 and phonenumbers.is_valid_number(nombor)
