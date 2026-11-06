"""Ketidakpastian skor: selang bootstrap, ujian berpasangan, pembetulan Holm (PELAN-C C3a, ADR-006 §Statistik).

Unit sampel semula = DOKUMEN (bukan span): span dalam dokumen yang sama berkorelasi (templat, gaya dan konteks sama), jadi
menyampel span akan menyempitkan selang secara palsu. Setiap sampel dinilai dengan `harness.skor()` SEDIA ADA — metrik
tidak disalin di sini (gerbang §4 mengunci AST fungsi itu). Ulangan/benih/aras/kaedah = config `nilai.statistik:`.

- `selang_bootstrap` — persentil (interpolasi linear) F1 tepat atas `ulangan` sampel semula dokumen dengan ganti.
- `berpasangan` — A lawan B atas indeks sampel YANG SAMA: ΔF1, selang Δ, p bootstrap sehala (Berg-Kirkpatrick et al.
  2012: pecahan δ* > 2δ; δ ≤ 0 → p = 1) dan ujian rawak anggaran (tukar ramalan A/B per dokumen dengan kebarangkalian ½,
  p = (b+1)/(R+1), b = bilangan δ_r ≥ δ).
- `holm` — nilai-p terlaras Holm-Bonferroni (langkah turun) atas k perbandingan.

Garis dasar EKSPLORASI (`garis_dasar.llm.eksplorasi`, PRA-DAFTAR pindaan 2026-11-03, ADR-017): Δ + CI + p mentah dikira seperti
sistem lain, tetapi sistem itu TIDAK masuk keluarga Holm (`p_holm_*` = None, `eksplorasi: true`); k = garis dasar pengesahan sahaja.
"""

import random

from mypii import konfig
from mypii.nilai import harness


def _k() -> dict:
    return konfig.utama()["nilai"]["statistik"]


def sistem_eksplorasi(c: dict | None = None) -> set[str]:
    """Nama sistem (`llm:<model>`) garis dasar eksplorasi dari config; tiada kunci = set kosong (tingkah laku lama)."""
    c = c or konfig.utama()
    return {f"llm:{m}" for m in c["garis_dasar"]["llm"].get("eksplorasi") or []}


def senarai_kunci(k: dict | None = None) -> list[str]:
    """Kunci utama dahulu, kemudian `semua|<entiti>` untuk setiap `nilai.entiti` (sekunder)."""
    k = k or _k()
    return [k["kunci_utama"]] + [f"semua|{e}" for e in konfig.utama()["nilai"]["entiti"]]


def persentil(nilai: list[float], q: float) -> float:
    """Persentil q ∈ [0, 1] dengan interpolasi linear antara titik tertib (kaedah lalai numpy)."""
    x = sorted(nilai)
    if not x:
        raise ValueError("persentil atas senarai kosong")
    pos = q * (len(x) - 1)
    i = int(pos)
    j = min(i + 1, len(x) - 1)
    return x[i] + (x[j] - x[i]) * (pos - i)


def indeks_bootstrap(n: int, ulangan: int, benih: int) -> list[list[int]]:
    """`ulangan` sampel n indeks dokumen dengan ganti; benih sama → indeks sama (dikongsi oleh semua sistem)."""
    rng = random.Random(benih)
    return [[rng.randrange(n) for _ in range(n)] for _ in range(ulangan)]


def _f1(skor: dict, kunci: str) -> float | None:
    """F1 tepat; None bila kunci tiada (tiada emas DAN tiada ramalan entiti itu dalam sampel — F1 tidak tertakrif)."""
    b = skor.get(kunci)
    return b["tepat"]["f1"] if b else None


def f1_sampel(dokumen: list[dict], ramalan: list[list[dict]], indeks: list[list[int]], kunci: list[str]) -> dict:
    """{kunci: [F1 setiap sampel atau None]} — satu panggilan `harness.skor` setiap sampel."""
    keluar = {x: [] for x in kunci}
    for ix in indeks:
        s = harness.skor([dokumen[i] for i in ix], [ramalan[i] for i in ix])
        for x in kunci:
            keluar[x].append(_f1(s, x))
    return keluar


def _selang(sampel: list[float | None], aras: float, dp: int) -> dict:
    sah = [v for v in sampel if v is not None]
    if not sah:
        return {"bawah": None, "atas": None, "n_sah": 0}
    a = (1 - aras) / 2
    return {"bawah": round(persentil(sah, a), dp), "atas": round(persentil(sah, 1 - a), dp), "n_sah": len(sah)}


def selang_bootstrap(dokumen, ramalan, kunci="semua|*", ulangan=None, benih=None, aras=None, sampel=None) -> dict:
    """{f1, bawah, atas, n_sah}: F1 tepat penuh + selang persentil `aras` atas sampel semula dokumen.

    `sampel` = output `f1_sampel` yang sudah dikira (harness berkongsi sampel antara selang dan perbandingan).
    """
    k = _k()
    ulangan, benih, aras = ulangan or k["ulangan"], k["benih"] if benih is None else benih, aras or k["aras"]
    if sampel is None:
        sampel = f1_sampel(dokumen, ramalan, indeks_bootstrap(len(dokumen), ulangan, benih), [kunci])
    return {"f1": _f1(harness.skor(dokumen, ramalan), kunci), **_selang(sampel[kunci], aras, k["perpuluhan"])}


def _p_bootstrap(delta: float, sampel_d: list[float]) -> float:
    """Berg-Kirkpatrick 2012: p = #(δ* > 2δ) / B. δ ≤ 0 = tiada bukti A > B → 1.0 (ujian sehala)."""
    if delta <= 0 or not sampel_d:
        return 1.0
    return sum(1 for d in sampel_d if d > 2 * delta) / len(sampel_d)


def _rawak(dokumen, ra, rb, kunci: list[str], delta: dict, ulangan: int, benih: int) -> dict:
    """Ujian rawak anggaran: tukar ramalan A/B per dokumen (½); p = (b+1)/(R+1), b = #(δ_r ≥ δ)."""
    rng = random.Random(benih)
    b = {x: 0 for x in kunci}
    r_sah = {x: 0 for x in kunci}
    for _ in range(ulangan):
        tukar = [rng.random() < 0.5 for _ in dokumen]
        sa = harness.skor(dokumen, [y if t else x for x, y, t in zip(ra, rb, tukar)])
        sb = harness.skor(dokumen, [x if t else y for x, y, t in zip(ra, rb, tukar)])
        for x in kunci:
            fa, fb = _f1(sa, x), _f1(sb, x)
            if fa is None or fb is None or delta[x] is None:
                continue
            r_sah[x] += 1
            b[x] += (fa - fb) >= delta[x] - 1e-12
    return {x: (b[x] + 1) / (r_sah[x] + 1) for x in kunci}


def berpasangan(dokumen, ramalan_a, ramalan_b, kunci="semua|*", ulangan=None, benih=None, aras=None,
                sampel_a=None, sampel_b=None) -> dict:
    """A lawan B. `kunci` = satu kunci → satu dict; senarai kunci → {kunci: dict}.

    Setiap dict: {delta, bawah, atas, n_sah, p_bootstrap, p_rawak}. Bootstrap memakai indeks yang SAMA untuk A dan B
    (`indeks_bootstrap(n, ulangan, benih)`), jadi `sampel_a/sampel_b` dari `f1_sampel` dengan indeks itu boleh dikongsi.
    """
    k = _k()
    ulangan, benih, aras = ulangan or k["ulangan"], k["benih"] if benih is None else benih, aras or k["aras"]
    senarai = [kunci] if isinstance(kunci, str) else list(kunci)
    if sampel_a is None or sampel_b is None:
        ix = indeks_bootstrap(len(dokumen), ulangan, benih)
        sampel_a = f1_sampel(dokumen, ramalan_a, ix, senarai)
        sampel_b = f1_sampel(dokumen, ramalan_b, ix, senarai)
    sa, sb = harness.skor(dokumen, ramalan_a), harness.skor(dokumen, ramalan_b)
    dp = k["perpuluhan"]
    delta = {}
    for x in senarai:
        fa, fb = _f1(sa, x), _f1(sb, x)
        delta[x] = None if fa is None or fb is None else round(fa - fb, dp)
    p_rawak = _rawak(dokumen, ramalan_a, ramalan_b, senarai, delta, ulangan, benih)
    keluar = {}
    for x in senarai:
        d_sampel = [a - b for a, b in zip(sampel_a[x], sampel_b[x]) if a is not None and b is not None]
        keluar[x] = {"delta": delta[x], **_selang(d_sampel, aras, dp),
                     "p_bootstrap": round(_p_bootstrap(delta[x], d_sampel), dp) if delta[x] is not None else None,
                     "p_rawak": round(p_rawak[x], dp)}
    return keluar[kunci] if isinstance(kunci, str) else keluar


def holm(p: dict) -> dict:
    """Holm-Bonferroni langkah turun: p_(i) terlaras = max_{j ≤ i} min(1, (k − j + 1) · p_(j)). Nilai None dilangkau."""
    sah = sorted(((v, n) for n, v in p.items() if v is not None), key=lambda t: (t[0], t[1]))
    k, terlaras, maks = len(sah), {n: None for n in p}, 0.0
    for j, (v, n) in enumerate(sah):
        maks = max(maks, min(1.0, (k - j) * v))
        terlaras[n] = maks
    return terlaras


def jalankan(dokumen: list[dict], ramalan: dict[str, list[list[dict]]], k: dict | None = None,
             eksplorasi: set[str] | None = None) -> dict:
    """Selang setiap sistem × kunci + rujukan lawan SETIAP sistem lain (Holm per kunci atas k garis dasar PENGESAHAN).

    `eksplorasi` (lalai: `sistem_eksplorasi()`) = sistem di luar keluarga Holm: p mentah dilapor, `p_holm_*` None,
    `eksplorasi: true`. Kunci atas `eksplorasi` hanya ditulis bila sistem itu hadir — output tanpanya sama bait-demi-bait.
    """
    k = k or _k()
    eksplorasi = sistem_eksplorasi() if eksplorasi is None else set(eksplorasi)
    if k["kaedah"] != "holm":
        raise ValueError(f"nilai.statistik.kaedah {k['kaedah']!r} tidak disokong (holm sahaja)")
    if k["rujukan"] not in ramalan:
        raise ValueError(f"tiada ramalan sistem rujukan {k['rujukan']!r}")
    kunci, dp = senarai_kunci(k), k["perpuluhan"]
    ix = indeks_bootstrap(len(dokumen), k["ulangan"], k["benih"])
    sampel = {s: f1_sampel(dokumen, r, ix, kunci) for s, r in ramalan.items()}
    sistem = {s: {x: selang_bootstrap(dokumen, r, x, k["ulangan"], k["benih"], k["aras"], sampel[s]) for x in kunci}
              for s, r in ramalan.items()}
    rj = k["rujukan"]
    banding = {s: berpasangan(dokumen, ramalan[rj], r, kunci, k["ulangan"], k["benih"], k["aras"], sampel[rj], sampel[s])
               for s, r in ramalan.items() if s != rj}
    eks = sorted(s for s in banding if s in eksplorasi)
    for x in kunci:
        for jenis in ("bootstrap", "rawak"):
            terlaras = holm({s: banding[s][x][f"p_{jenis}"] for s in banding if s not in eks})
            for s in banding:
                v = terlaras.get(s)
                banding[s][x][f"p_holm_{jenis}"] = None if v is None else round(v, dp)
        for s in eks:
            banding[s][x]["eksplorasi"] = True
    return {"dokumen": len(dokumen), "unit": "dokumen", "rujukan": rj, "kunci_utama": k["kunci_utama"],
            "config": {x: k[x] for x in ("ulangan", "benih", "aras", "kaedah")}, "sistem": sistem, "banding": banding,
            **({"eksplorasi": eks} if eks else {})}


def pengesahan(h: dict) -> dict:
    """`banding` tanpa sistem eksplorasi = keluarga Holm (k = len)."""
    eks = set(h.get("eksplorasi", []))
    return {s: ks for s, ks in h["banding"].items() if s not in eks}


def _p(v, ulangan: int) -> str:
    return "—" if v is None else (f"< {1 / ulangan:.3g}" if v == 0 else f"{v}")


def jadual_md(h: dict) -> str:
    """Dua jadual markdown: F1 + selang setiap sistem × kunci; rujukan lawan setiap garis dasar (kunci utama dahulu)."""
    pct = round(h["config"]["aras"] * 100)
    b = [f"| sistem | kunci | F1 tepat | CI {pct}% |", "|---|---|---|---|"]
    for s, ks in h["sistem"].items():
        for x, v in ks.items():
            b.append(f"| {s}{' (eksplorasi)' if s in set(h.get('eksplorasi', [])) else ''} | {x} | {v['f1']} | [{v['bawah']}, {v['atas']}] |")
    b += ["", f"| {h['rujukan']} lawan | kunci | ΔF1 | CI {pct}% Δ | p bootstrap | p rawak | p Holm (bootstrap) | p Holm (rawak) |",
          "|---|---|---|---|---|---|---|---|"]
    u = h["config"]["ulangan"]
    eks = set(h.get("eksplorasi", []))
    for s, ks in h["banding"].items():
        for x, v in ks.items():
            b.append(f"| {s}{' (eksplorasi)' if s in eks else ''} | {x} | {v['delta']} | [{v['bawah']}, {v['atas']}] | {_p(v['p_bootstrap'], u)} | "
                     f"{_p(v['p_rawak'], u)} | {_p(v['p_holm_bootstrap'], u)} | {_p(v['p_holm_rawak'], u)} |")
    return "\n".join(b)
