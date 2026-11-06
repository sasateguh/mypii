from datetime import date

from presidio_analyzer import Pattern, PatternRecognizer

from mypii import konfig
from mypii.pengecam.konteks import KonteksFrasa
from mypii.pengecam.normal import NormalOCR, digit

# SSM (Suruhanjaya Syarikat Malaysia), sejak 11 Okt 2019: 12 digit YYYY TT NNNNNN
# (tahun daftar, kod jenis entiti 01–06, nombor siri). Format lama syarikat: 1234567-A (skor rendah, perlu konteks);
# dalam kurungan selepas nama, "Nama Syarikat (123456-X)", ialah konvensyen tetap — skor lebih tinggi.


class MySsmRecognizer(NormalOCR, KonteksFrasa, PatternRecognizer):
    """Recognize Malaysian SSM business/company registration numbers."""

    COUNTRY_CODE = "my"

    def __init__(
        self,
        patterns: list[Pattern] | None = None,
        context: list[str] | None = None,
        supported_language: str = "en",
        supported_entity: str = "MY_SSM",
        name: str | None = None,
    ):
        k = konfig.utama()["pengecam"]["MY_SSM"]
        self.tahun_min = k["tahun_min"]
        self.kod_jenis = set(k["kod_jenis"])
        rob = konfig.muat("ssm_rob")   # P9: LLP (kod llp: true) wujud hanya dari tahun Akta 743 — satu sumber fakta
        self.kod_llp = {kod for kod, x in rob["kod_entiti"].items() if x["llp"]}
        self.llp_tahun_min = rob["llp"]["tahun_min"]
        nl = konfig.utama()["pengecam"]["normal"]["patah_baris"]   # P9: patah baris di sempadan tahun | kod | siri
        patterns = patterns or [
            Pattern("SSM (new)", rf"(?<!\d)(?:18|19|20)\d{{2}}(?:{nl})?0[1-6](?:{nl})?\d{{6}}(?!\d)", k["skor"]["baharu"]),
            Pattern("SSM (old company)", r"(?<![\w-])\d{1,7}-[A-Z](?![\w-])", k["skor"]["lama"]),
            Pattern("SSM (old, bracketed)", r"(?<=\(\s?)\d{1,7}-[A-Z](?=\s?\))", k["skor"]["lama_berkurung"]),
        ]
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context or k["konteks"],
            supported_language=supported_language,
            name=name,
        )

    def validate_result(self, pattern_text: str) -> bool | None:
        if "-" in pattern_text:
            return None  # format lama: tiada struktur untuk disemak, biar konteks yang memutuskan
        d = digit(pattern_text)   # P9: teks padanan boleh mengandungi patah baris
        tahun = int(d[:4])
        if d[4:6] in self.kod_llp and tahun < self.llp_tahun_min:
            return False
        return self.tahun_min <= tahun <= date.today().year and d[4:6] in self.kod_jenis
