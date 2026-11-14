"""Konteks peringkat pengecam: padanan FRASA penuh pada perkataan sebelum padanan.

Penambah konteks lalai Presidio memadan setiap kata konteks sebagai SUBRENTETAN satu token lema — frasa berbilang
perkataan ("no. pendaftaran", "sdn bhd") tidak pernah padan, dan kata pendek padan di tempat salah ("ic" dalam
"invoice"/"public"). Pengecam MyPII menilai konteks sendiri melalui `enhance_using_context` (API Presidio) dan
menanda hasil sebagai sudah dinilai supaya penambah global tidak menambah skor sekali lagi.
"""

import re

from presidio_analyzer import RecognizerResult

from mypii import konfig
from mypii.pengecam.pengelas import kebarangkalian


def _ocr(teks: str, peta: dict[str, str]) -> str:
    """Seragamkan kekeliruan OCR (0/o, 1/l/i…) dalam perkataan yang ada huruf; nombor tulen tidak disentuh."""
    jadual = str.maketrans(peta)
    return " ".join(w.translate(jadual) if any(c.isalpha() for c in w) else w for w in teks.split(" "))


def _corak(frasa: list[str], peta: dict[str, str]) -> re.Pattern | None:
    if not frasa:
        return None
    alt = "|".join(re.escape(_ocr(f.lower(), peta)) for f in sorted(frasa, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alt})(?!\w)")


_PEMISAH_SEL = re.compile(r"\t|[ \t]*\|[ \t]*| {2,}")


def _sel(baris: str) -> list[tuple[int, int]]:
    """Julat (mula, tamat) setiap sel dalam satu baris jadual teks; paip di hujung baris diabaikan."""
    julat, mula = [], 0
    for m in _PEMISAH_SEL.finditer(baris):
        if m.start() > mula:
            julat.append((mula, m.start()))
        mula = m.end()
    if mula < len(baris):
        julat.append((mula, len(baris)))
    return julat


def _pengepala_lajur(text: str, mula: int) -> str | None:
    """Teks pengepala lajur bagi padanan dalam jadual teks (tab, paip atau ruang berlapis), atau None.

    Jadual = baris berturut-turut dengan bilangan sel yang sama (≥ 2); pengepala = baris pertama blok itu.
    """
    awal = text.rfind("\n", 0, mula) + 1
    akhir = text.find("\n", mula)
    baris = text[awal:akhir if akhir >= 0 else len(text)]
    sel = _sel(baris)
    lajur = next((i for i, (a, b) in enumerate(sel) if a <= mula - awal < b), None)
    if len(sel) < 2 or lajur is None:
        return None
    semua = text[:awal].split("\n")[:-1]
    kepala = None
    for atas in reversed(semua):
        if len(_sel(atas)) != len(sel):
            break
        kepala = atas
    if kepala is None:
        return None
    a, b = _sel(kepala)[lajur]
    return kepala[a:b] + " " + baris[sel[lajur][0]:mula - awal]


def _terdekat(corak: re.Pattern | None, teks: str) -> re.Match | None:
    return None if corak is None else next(reversed(list(corak.finditer(teks))), None)


class KonteksFrasa:
    """Campuran untuk PatternRecognizer: `self.context` = frasa positif (padanan seluruh perkataan).

    Frasa NEGATIF (`konteks_umum.negatif`: akaun, invois, tracking…) yang lebih DEKAT dengan padanan daripada frasa
    positif menjatuhkan skor ke `skor_negatif` — nombor 12 digit berbentuk MyKad/SSM sah lazim ialah no. akaun/rujukan.
    Dalam jadual teks, konteks = pengepala lajur padanan (bukan perkataan dari lajur jiran).
    Konteks entiti `bersaing` (cth SSM bagi NRIC) dikira negatif juga: 12 digit boleh sah sebagai kedua-duanya.
    """

    def enhance_using_context(self, text, raw_recognizer_results, other_raw_recognizer_results, nlp_artifacts,
                              context=None):
        k = konfig.utama()["pengecam"]["konteks_umum"]
        peta = k["ocr_seragam"]
        positif = _corak(list(self.context or []), peta)
        semua = konfig.utama()["pengecam"]
        bersaing = semua.get(self.supported_entities[0], {}).get("bersaing", [])
        negatif = _corak(k["negatif"] + [f for e in bersaing for f in semua[e]["konteks"]], peta)
        tambahan = " ".join(context or []).lower()
        for r in raw_recognizer_results:
            sebelum = _pengepala_lajur(text, r.start) or text[max(0, r.start - k["aksara_maks"]):r.start]
            sebelum = sebelum.lower().split()
            tetingkap = _ocr(" ".join(sebelum[-k["tetingkap_perkataan"]:]) + " " + tambahan, peta)
            jumpa, tolak = _terdekat(positif, tetingkap), _terdekat(negatif, tetingkap)
            frasa = "tiada"
            if tolak and (not jumpa or tolak.end() > jumpa.end()):
                frasa = "negatif"
                r.score = min(r.score, k["skor_negatif"])
            elif jumpa:
                frasa = "positif"
                r.score = min(1.0, max(r.score + k["faktor"], k["skor_min"]))
                if r.analysis_explanation:
                    r.analysis_explanation.set_supportive_context_word(jumpa.group(0))
                    r.analysis_explanation.set_improved_score(r.score)
            r.recognition_metadata[RecognizerResult.IS_SCORE_ENHANCED_BY_CONTEXT_KEY] = True
            _gabung_pengelas(text, r, k["skor_negatif"], k["skor_min"], frasa)
        return raw_recognizer_results


def _gabung_pengelas(text: str, r: RecognizerResult, skor_negatif: float, skor_min: float, frasa: str = "tiada") -> None:
    """Skor pengelas konteks tempatan digabung dengan keputusan frasa ikut config `konteks.gabung.cara`:
    tapis (P11) = p < ambang → skor_negatif, frasa memutuskan yang lain; ganti (P11, v2 = 1.0.x) = pengelas memutuskan SEMUA calon;
    frasa (v2.1, PELAN-V21) = frasa didahulukan, pengelas memutuskan baki (`_simpan_frasa`). Keputusan → ≥ skor_min atau ≤ skor_negatif."""
    p = kebarangkalian(text, r.start, r.end, r.entity_type)
    if p is None:
        return
    g = konfig.utama()["konteks"]["gabung"]
    if g["cara"] == "frasa":
        r.score = max(r.score, skor_min) if _simpan_frasa(r, p, frasa, g) else min(r.score, skor_negatif)
        return
    ambang = g["ambang"][r.entity_type]
    if p < ambang:
        r.score = min(r.score, skor_negatif)
    elif g["cara"] == "ganti":
        r.score = max(r.score, skor_min)


def _simpan_frasa(r: RecognizerResult, p: float, frasa: str, g: dict) -> bool:
    """v2.1: frasa positif terdekat → simpan kecuali pengelas hampir pasti bukan PII (p < `ambang_positif`); frasa negatif lebih dekat →
    simpan HANYA calon disahkan struktur dengan p ≥ `ambang_negatif`; tiada frasa → calon tanpa pengesahan struktur (SSM format lama)
    dibuang bila `tanpa_sah_perlu_frasa`, yang lain p ≥ `ambang_corak[<nama corak>]` atau `ambang[<entiti>]`."""
    e = r.analysis_explanation
    sah = bool(e and e.validation_result)
    if frasa == "positif":
        return p >= g["ambang_positif"]
    if frasa == "negatif":
        return sah and p >= g["ambang_negatif"]
    if not sah and g["tanpa_sah_perlu_frasa"]:
        return False
    return p >= g.get("ambang_corak", {}).get(e.pattern_name if e else None, g["ambang"][r.entity_type])
