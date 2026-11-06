"""Markdown blok jana `docs/BANDINGAN.md` dari output `bandingan.kira()` + fail masa (ADR-012). Tiada pengiraan skor di sini.

Sistem dalam `garis_dasar.llm.eksplorasi` (ADR-017) berlabel "(eksplorasi)" dalam setiap jadual."""

from mypii import konfig

BAHASA = ("en", "ms", "manglish")


def _e() -> list[str]:
    return konfig.utama()["nilai"]["entiti"]


def _eks(s: str) -> str:
    """" (eksplorasi)" bagi garis dasar eksplorasi (di luar keluarga Holm), "" bagi yang lain."""
    from mypii.nilai.statistik import sistem_eksplorasi  # lewat: statistik → harness → modul berat

    return " (eksplorasi)" if s in sistem_eksplorasi() else ""


def _n(s: str) -> str:
    return f"`{s}`{_eks(s)}"


def _sel(x) -> str:
    return "–" if x is None else str(x).replace("|", "\\|")


def _jadual(kepala: list[str], baris: list[list]) -> str:
    return "\n".join(["| " + " | ".join(kepala) + " |", "|" + "---|" * len(kepala)]
                     + ["| " + " | ".join(_sel(x) for x in b) + " |" for b in baris]) + "\n"


def _f1(skor: dict, kunci: str, jenis: str = "tepat"):
    return skor[kunci][jenis]["f1"] if kunci in skor else None


def _baris_sistem(hasil: dict):
    for s, h in hasil["sistem"].items():
        yield s, h["skor"]
        if "skor_disokong" in h:
            yield f"{s} (disokong: {', '.join(konfig.utama()['garis_dasar']['pii_guard']['entiti_disokong'])})", h["skor_disokong"]


def ringkasan(hasil: dict) -> str:
    baris = []
    for s, sk in _baris_sistem(hasil):
        t = sk["semua|*"]["tepat"]
        baris.append([_n(s), t["p"], t["r"], t["f1"], _f1(sk, "semua|*", "separa")] + [_f1(sk, f"semua|{e}") for e in _e()])
    return _jadual(["sistem", "P `*`", "R `*`", "**F1 `*` tepat**", "F1 `*` separa"] + [f"F1 {e}" for e in _e()], baris)


def per_bahasa(hasil: dict) -> str:
    baris = []
    for s, sk in _baris_sistem(hasil):
        for e in ["*"] + _e():
            if f"semua|{e}" in sk:
                baris.append([_n(s), e] + [f"{_f1(sk, f'bahasa:{b}|{e}')} / {_f1(sk, f'bahasa:{b}|{e}', 'separa')}"
                                               for b in BAHASA])
    return _jadual(["sistem", "entiti"] + [f"{b} (tepat / separa)" for b in BAHASA], baris)


def terperinci(hasil: dict) -> str:
    keluar = []
    for s, sk in _baris_sistem(hasil):
        baris = [[k.replace("|", " · "), v["emas"], v["ramal"], v["tepat"]["p"], v["tepat"]["r"], v["tepat"]["f1"],
                  v["separa"]["p"], v["separa"]["r"], v["separa"]["f1"]] for k, v in sk.items()]
        keluar.append(f"<details><summary><code>{s}</code>{_eks(s)}</summary>\n\n"
                      + _jadual(["kumpulan · entiti", "emas", "ramal", "P tepat", "R tepat", "F1 tepat", "P separa", "R separa",
                                 "F1 separa"], baris) + "\n</details>\n")
    return "\n".join(keluar)


def ralat(hasil: dict) -> str:
    from mypii.nilai.bandingan import JENIS

    baris = []
    for s, h in hasil["sistem"].items():
        k = h["ralat"]["kira"]
        sel = [f"{sum(k.get(f'{j}|{e}', 0) for e in _e())} ("
               + " · ".join(f"{e[3:]} {k.get(f'{j}|{e}', 0)}" for e in _e()) + ")" for j in JENIS]
        n = h["ralat"]["dok_negatif"]
        baris.append([_n(s)] + sel + [f"{n['dok']} / {n['span']}"])
    return _jadual(["sistem", "palsu", "sempadan", "salah jenis", "terlepas",
                    f"dok negatif berisi ramalan / span (daripada {hasil['dok_negatif']})"], baris)


def ralat_utama(hasil: dict) -> str:
    keluar = []
    for s, h in hasil["sistem"].items():
        keluar.append(f"#### {_n(s)}\n")
        for jenis, tajuk in (("palsu", "Ramalan palsu (tiada emas bertindih)"), ("terlepas", "Emas terlepas")):
            u = h["ralat"]["utama"][jenis]
            if not u:
                keluar.append(f"*{tajuk}: tiada.*\n")
                continue
            keluar.append(f"*{tajuk} — label sebelum span, kumpulan teratas:*\n")
            keluar.append(_jadual(["label", "bil", "entiti", "contoh (dev)"],
                                  [[f"`{x['label']}`", x["bil"], ", ".join(f"{e} {n}" for e, n in x["entiti"].items()),
                                    "<br>".join(x["contoh"])] for x in u]))
    return "\n".join(keluar)


def masa_kos(hasil: dict, masa: dict | None) -> str:
    keluar = []
    if masa is None:
        keluar.append("*Masa belum diukur (`make bandingan-masa`).*\n")
    else:
        keluar.append(f"Diukur {masa['diukur']} (hos dikongsi — angka kasar, bukan penanda aras prestasi).\n")
        keluar.append(_jadual(["sistem", "dokumen", "saat (termasuk memuat enjin)", "ms / dok"],
                              [[_n(s), m["dokumen"], m["saat"], round(1000 * m["saat"] / m["dokumen"], 1)]
                               for s, m in masa["sistem"].items()]))
        keluar.append("Latensi LLM — sampel dokumen dev pertama ikut `id`, bersiri, satu panggilan setiap dokumen (cache tidak ditulis):\n")
        keluar.append(_jadual(["sistem", "sampel", "gagal", "median s", "maks s"],
                              [[_n(s), m["sampel"], m["gagal"], m["median_s"], m["maks_s"]] for s, m in masa["llm"].items()]))
    kos = [[_n(s), h["kos"]["aksara_masuk"], h["kos"]["aksara_keluar"]] for s, h in hasil["sistem"].items() if "kos" in h]
    if kos:
        keluar.append(f"Saiz panggilan LLM atas {hasil['dokumen']} dok (dari cache dikomit; aksara, bukan token):\n")
        keluar.append(_jadual(["sistem", "aksara masuk", "aksara keluar"], kos))
    return "\n".join(keluar)


def blok(hasil: dict, masa: dict | None) -> str:
    return "\n".join([
        "<!-- dijana `make bandingan` (mypii/nilai/bandingan.py) — JANGAN sunting dengan tangan -->\n",
        f"Split `{hasil['split']}`: {hasil['dokumen']} dok ({hasil['dok_negatif']} tanpa PII), sha256 `{hasil['sha256'][:16]}…`.\n",
        "### Ringkasan — semua bahasa\n", ringkasan(hasil),
        "### Setiap bahasa — F1 tepat / separa\n", per_bahasa(hasil),
        "### Jadual penuh setiap sistem\n", terperinci(hasil),
        "### Ralat (padanan tepat) — kiraan\n", ralat(hasil),
        "### Ralat utama setiap sistem\n", ralat_utama(hasil),
        "### Masa dan saiz panggilan\n", masa_kos(hasil, masa),
    ])
