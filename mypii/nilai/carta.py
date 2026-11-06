"""Carta kemajuan gelung `hasil/kemajuan.svg` dari `hasil/iterasi.tsv` (PELAN-C C2b, ADR-006 §Iterasi).

SVG statik, stdlib sahaja, bait sama setiap larian (tiada cap masa). Paksi-x = nombor iterasi (baris TSV), titik F1
diwarna DAN dibentuk ikut status; tanpa F1 (crash / pengukuran tanpa skor) = penanda di lorong dasar bawah paksi.
Garis "terbaik setakat ini" hanya dari baris `simpan`, dan tidak pernah merentas segmen: segmen baharu bila `dev_sha8`
berubah atau `?` (dev tidak diketahui — dua baris `?` mungkin dev berlainan, jadi tidak disambung). Teks, saiz, warna
(terang + gelap ikut `prefers-color-scheme`) = config `nilai.iterasi.carta`; palet = skil dataviz.
"""

import argparse
import csv
import math
from pathlib import Path
from xml.sax.saxutils import escape

from mypii import konfig

TIDAK_DIKETAHUI = "?"


def _k() -> dict:
    return konfig.utama()["nilai"]["iterasi"]


def baca(laluan: Path) -> list[dict]:
    with open(laluan, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def segmen(baris: list[dict]) -> list[list[int]]:
    """Indeks baris dikumpul ikut segmen dev: baru bila `dev_sha8` berubah atau `?`."""
    hasil: list[list[int]] = []
    for i, b in enumerate(baris):
        d = b["dev_sha8"]
        if not hasil or d == TIDAK_DIKETAHUI or d != baris[i - 1]["dev_sha8"]:
            hasil.append([])
        hasil[-1].append(i)
    return hasil


def larian_label(baris: list[dict]) -> list[int]:
    """Indeks permulaan setiap larian `dev_sha8` sama (termasuk larian `?`) — tempat pemisah + label dev."""
    return [i for i, b in enumerate(baris) if i == 0 or b["dev_sha8"] != baris[i - 1]["dev_sha8"]]


def _f1(b: dict) -> float | None:
    return float(b["f1"]) if b.get("f1") and b["status"] != "crash" else None


def julat_y(baris: list[dict], langkah: float) -> tuple[float, float]:
    nilai = [v for b in baris if (v := _f1(b)) is not None]
    if not nilai:
        return 0.0, 1.0
    lo = round(math.floor(min(nilai) / langkah + 1e-9) * langkah, 6)
    hi = round(min(1.0, math.ceil(max(nilai) / langkah - 1e-9) * langkah), 6)
    return (lo, hi) if hi > lo else (round(lo - langkah, 6), hi)


def terbaik(baris: list[dict], seg: list[int]) -> list[tuple[int, float]]:
    """Langkah naik F1 terbaik dalam satu segmen: [(indeks, f1)] dari baris `simpan` sahaja."""
    out: list[tuple[int, float]] = []
    for i in seg:
        v = _f1(baris[i])
        if baris[i]["status"] == "simpan" and v is not None and (not out or v > out[-1][1]):
            out.append((i, v))
    return out


def _n(x: float) -> str:
    return f"{x:.1f}"


def _bentuk(nama: str, kelas: str) -> str:
    if nama == "bulat":
        return f'<circle r="5" class="{kelas}"/>'
    if nama == "segiempat":
        return f'<rect x="-4.5" y="-4.5" width="9" height="9" rx="1" class="{kelas}"/>'
    if nama == "berlian":
        return f'<path d="M0,-6L6,0L0,6L-6,0Z" class="{kelas}"/>'
    return f'<path d="M-4,-4L4,4M-4,4L4,-4" class="{kelas}"/>'  # pangkah


def _gaya(warna: dict, status: list[str]) -> str:
    def blok(w: dict) -> str:
        r = [f".bg{{fill:{w['permukaan']}}}", f".t1{{fill:{w['dakwat']}}}", f".t2{{fill:{w['dakwat2']}}}",
             f".t3{{fill:{w['senyap']}}}", f".grid{{stroke:{w['grid']}}}", f".paksi{{stroke:{w['paksi']}}}"]
        for s in status:
            r.append(f".p-{s}{{fill:{w[s]};stroke:{w['permukaan']}}}")
            r.append(f".h-{s}{{fill:{w['permukaan']};stroke:{w[s]}}}")
            r.append(f".x-{s}{{fill:none;stroke:{w[s]}}}")
        return "".join(r)
    asas = ("text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif}"
            ".grid,.paksi{stroke-width:1;fill:none}.pisah{stroke-dasharray:3 3}"
            ".best{fill:none;stroke-width:2;stroke-linejoin:round}"
            "[class^=p-],[class^=h-]{stroke-width:2}[class^=x-]{stroke-width:2;stroke-linecap:round}")
    terang = blok(warna["terang"]) + "".join(f".best.s-{s}{{stroke:{warna['terang'][s]}}}" for s in status)
    gelap = blok(warna["gelap"]) + "".join(f".best.s-{s}{{stroke:{warna['gelap'][s]}}}" for s in status)
    return f"<style>{asas}{terang}@media (prefers-color-scheme:dark){{{gelap}}}</style>"


def _tooltip(i: int, b: dict, had: int) -> str:
    ket = b.get("keterangan", "")
    ket = ket if len(ket) <= had else ket[: had - 1] + "…"
    f1 = b["f1"] or "—"
    return f"#{i + 1} · {b['status']} · F1 {f1} · dev {b['dev_sha8']} · {b['komit']} · {b['tarikh']} — {ket}"


def lukis(baris: list[dict], c: dict | None = None) -> str:
    """SVG lengkap (rentetan). `c` = config `nilai.iterasi.carta` (lalai dari config)."""
    c = c or _k()["carta"]
    status = list(c["label_status"])
    W, H, j = c["lebar"], c["tinggi"], c["jidar"]
    kiri, kanan, atas, bawah = j["kiri"], W - j["kanan"], j["atas"], H - j["bawah"]
    n = max(len(baris), 1)
    langkah_px = (kanan - kiri) / n
    lo, hi = julat_y(baris, c["langkah_y"])

    def x(i: float) -> float:
        return kiri + langkah_px * (i + 0.5)

    def y(v: float) -> float:
        return bawah - (v - lo) / (hi - lo) * (bawah - atas)

    lorong = bawah + 14
    o: list[str] = [
        (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-labelledby="tajuk desk">'),
        f'<title id="tajuk">{escape(c["tajuk"])}</title>',
        f'<desc id="desk">{escape(" ".join(c["sari_kata"]))} · n = {len(baris)}</desc>',
        _gaya(c["warna"], status),
        f'<rect class="bg" width="{W}" height="{H}"/>',
        f'<text class="t1" x="{kiri}" y="26" font-size="16" font-weight="600">{escape(c["tajuk"])}</text>',
    ]
    for k, teks in enumerate(c["sari_kata"]):
        o.append(f'<text class="t2" x="{kiri}" y="{46 + 15 * k}" font-size="12">{escape(teks)}</text>')

    # legenda — hanya unsur yang ada dalam carta; balut ke baris baharu bila melepasi lebar
    ada = {b["status"] for b in baris}
    item = [(c["label_status"][s], _bentuk(c["bentuk"][s], (f"x-{s}" if c["bentuk"][s] == "pangkah" else f"p-{s}")))
            for s in status if s in ada]
    if any(_f1(b) is None and b["status"] != "crash" for b in baris):
        item.append((c["label_tiada_f1"], _bentuk(c["bentuk"]["ukur"], "h-ukur")))
    if any(len(terbaik(baris, seg)) and terbaik(baris, seg)[0][0] != seg[-1] for seg in segmen(baris)):
        item.append((c["label_terbaik"], '<path d="M-8,0H8" class="best s-simpan"/>'))
    lx, ly = kiri, atas - 40
    o.append('<g class="legenda">')
    for teks, simbol in item:
        lebar_item = 20 + 6.4 * len(teks) + 18
        if lx > kiri and lx + lebar_item > kanan:
            lx, ly = kiri, ly + 18
        o.append(f'<g transform="translate({_n(lx + 8)},{ly})">{simbol}</g>'
                 f'<text class="t2" x="{_n(lx + 20)}" y="{ly + 4}" font-size="12">{escape(teks)}</text>')
        lx += lebar_item
    o.append("</g>")

    # grid + paksi
    k = 0
    while (v := round(lo + k * c["langkah_y"], 6)) <= hi + 1e-9:
        o.append(f'<line class="grid" x1="{kiri}" x2="{kanan}" y1="{_n(y(v))}" y2="{_n(y(v))}"/>'
                 f'<text class="t3" x="{kiri - 8}" y="{_n(y(v) + 4)}" font-size="11" text-anchor="end">{v:.2f}</text>')
        k += 1
    o.append(f'<line class="paksi" x1="{kiri}" x2="{kanan}" y1="{bawah}" y2="{bawah}"/>')
    o.append(f'<text class="t3" x="{kiri - 8}" y="{lorong + 4}" font-size="11" text-anchor="end">'
             f'{escape(c["label_lorong"])}</text>')
    for i in range(len(baris)):
        if (i + 1) % c["langkah_x"] == 0 or i == 0:
            o.append(f'<text class="t3" x="{_n(x(i))}" y="{bawah + 32}" font-size="11" text-anchor="middle">{i + 1}</text>')
    o.append(f'<text class="t2" x="{(kiri + kanan) / 2:.1f}" y="{H - 8}" font-size="12" text-anchor="middle">'
             f'{escape(c["paksi_x"])}</text>')
    o.append(f'<text class="t2" transform="translate(16,{(atas + bawah) / 2:.1f}) rotate(-90)" font-size="12" '
             f'text-anchor="middle">{escape(c["paksi_y"])}</text>')

    # pemisah + label dev
    for i in larian_label(baris):
        xp = kiri + langkah_px * i
        if i:
            o.append(f'<line class="paksi pisah" x1="{_n(xp)}" x2="{_n(xp)}" y1="{atas}" y2="{lorong + 6}"/>')
        o.append(f'<text class="t3" x="{_n(xp + 4)}" y="{atas + 12}" font-size="11">'
                 f'{escape(c["label_dev"])} {escape(baris[i]["dev_sha8"])}</text>')

    # garis terbaik setakat ini — satu laluan setiap segmen (tidak pernah merentas segmen)
    for seg in segmen(baris):
        t = terbaik(baris, seg)
        if not t or t[0][0] == seg[-1]:
            continue
        d = f"M{_n(x(t[0][0]))},{_n(y(t[0][1]))}"
        for i, v in t[1:]:
            d += f"H{_n(x(i))}V{_n(y(v))}"
        d += f"H{_n(x(seg[-1]))}"
        o.append(f'<path class="best s-simpan" data-segmen="{seg[0] + 1}" d="{d}"/>')

    # titik — satu setiap baris TSV
    o.append('<g class="titik-semua">')
    for i, b in enumerate(baris):
        s = b["status"] if b["status"] in status else "ukur"
        v = _f1(b)
        if s == "crash":
            kelas, yp = f"x-{s}", lorong
        elif v is None:
            kelas, yp = f"h-{s}", lorong
        else:
            kelas, yp = f"p-{s}", y(v)
        o.append(f'<g class="titik" data-status="{s}" transform="translate({_n(x(i))},{_n(yp)})">'
                 f'<title>{escape(_tooltip(i, b, c["had_tooltip"]))}</title>'
                 f'<circle r="9" fill="transparent"/>{_bentuk(c["bentuk"][s], kelas)}</g>')
    o.append("</g></svg>\n")
    return "\n".join(o)


def main(argv: list[str] | None = None) -> int:
    k = _k()
    ap = argparse.ArgumentParser(description="Carta kemajuan gelung → SVG (PELAN-C C2b)")
    ap.add_argument("--masuk", type=Path, default=konfig.AKAR / k["fail"])
    ap.add_argument("--keluar", type=Path, default=konfig.AKAR / k["carta"]["fail"])
    a = ap.parse_args(argv)
    baris = baca(a.masuk)
    a.keluar.parent.mkdir(parents=True, exist_ok=True)
    a.keluar.write_text(lukis(baris), encoding="utf-8")
    print(f"{a.keluar}: {len(baris)} titik, {len(segmen(baris))} segmen dev")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
