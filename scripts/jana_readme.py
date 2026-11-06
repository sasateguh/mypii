"""Jana blok jadual dev README dari `hasil/` (PELAN-SEDIA-TERBIT P1). `make readme`.

Sumber TUNGGAL: `hasil/dev-statistik.json` (dikomit; senarai sistem, F1 + selang bootstrap, Δ berpasangan vs MyPII, label
eksplorasi). `hasil/dev-<sistem>.json` (P/R) diabaikan git, jadi tidak wujud di klon bersih/Depot CI: P/R kekal dalam
`docs/BANDINGAN.md`. Tiada pengiraan skor di sini: setiap nombor disalin dari fail hasil.
Blok ditulis antara penanda `MULA` dan `TAMAT`; teks lain README tidak disentuh. `--semak` = keluar 1 jika README basi.
"""

import argparse
import json
import sys
from pathlib import Path

MULA = "<!-- jadual-dev:mula -->"
TAMAT = "<!-- jadual-dev:tamat -->"
AKAR = Path(__file__).resolve().parents[1]
SPLIT = "dev"  # README memaparkan dev sahaja; ujian/ujian2 = tempat kosong dalam kertas


def _baca(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _f(x) -> str:
    return "–" if x is None else f"{x:.4f}"


def _selang(d: dict | None) -> str:
    return "–" if not d else f"[{_f(d['bawah'])}, {_f(d['atas'])}]"


def _nama(s: str) -> str:
    return s.removeprefix("llm:")


def jadual(hasil: Path) -> str:
    """Markdown blok (tanpa penanda) dari folder `hasil`. Deterministik: urutan = MyPII dahulu, kemudian `sistem` statistik."""
    st = _baca(hasil / f"{SPLIT}-statistik.json")
    split, kunci, rujuk = st["split"], st["kunci_utama"], st["rujukan"]
    eks = set(st.get("eksplorasi") or [])
    c = st["config"]
    sistem = [rujuk] + [s for s in st["sistem"] if s != rujuk]
    baris = []
    for s in sistem:
        b = st.get("banding", {}).get(s, {}).get(kunci)
        delta = "rujukan / reference" if s == rujuk else f"{b['delta']:+.4f} {_selang(b)}"
        label = f"`{_nama(s)}`" + (" (eksplorasi / exploratory)" if s in eks else "")
        f1 = st["sistem"][s].get(kunci)
        baris.append(f"| {label} | **{_f(f1 and f1['f1'])}** | {_selang(f1)} | {delta} |")
    kepala = [
        f"<!-- dijana `make readme` (scripts/jana_readme.py) dari hasil/{split}-*.json; jangan sunting dengan tangan -->",
        "",
        (f"Split `{split}`, {st['dokumen']} dokumen / documents, padanan tepat / exact match, `{kunci}`. "
         f"Selang = bootstrap {round(c['aras'] * 100)}% ({c['ulangan']} ulangan / resamples, unit `{st['unit']}`). "
         "Δ = F1 MyPII tolak F1 sistem / MyPII minus system (negatif = sistem lebih baik / negative = system is better). "
         "P/R: `docs/BANDINGAN.md`."),
        "",
        "| Sistem / System | F1 | Selang F1 / F1 interval | Δ F1 [selang / interval] |",
        "|---|---|---|---|",
    ]
    return "\n".join(kepala + baris) + "\n"


def ganti(readme: str, blok: str) -> str:
    if readme.count(MULA) != 1 or readme.count(TAMAT) != 1 or readme.index(MULA) > readme.index(TAMAT):
        raise ValueError(f"README mesti ada tepat satu {MULA} sebelum satu {TAMAT}")
    awal, baki = readme.split(MULA)
    _, akhir = baki.split(TAMAT)
    return f"{awal}{MULA}\n{blok}{TAMAT}{akhir}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--readme", type=Path, default=AKAR / "README.md")
    ap.add_argument("--hasil", type=Path, default=AKAR / "hasil")
    ap.add_argument("--semak", action="store_true", help="jangan tulis; keluar 1 jika blok README basi")
    a = ap.parse_args(argv)
    lama = a.readme.read_text(encoding="utf-8")
    baru = ganti(lama, jadual(a.hasil))
    if a.semak:
        if baru != lama:
            print("README: blok jadual-dev basi; jalankan `make readme`", file=sys.stderr)
            return 1
        return 0
    if baru != lama:
        a.readme.write_text(baru, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
