"""SEKALI (PELAN-C C2a): isi semula `hasil/iterasi.tsv` dari jadual `docs/LOG-ITERASI.md`, kronologi.

    uv run python scripts/iterasi_dari_log.py [--log docs/LOG-ITERASI.md] [--keluar hasil/iterasi.tsv]

Enggan menulis bila fail keluar sudah berisi (selepas C2a fail itu TAMBAH-SAHAJA melalui `make nilai`). Peraturan pemetaan (ADR-006):
- status: kata kunci TERAWAL dalam lajur Keputusan — simpan → `simpan`; buang/undur → `buang`; ukur, atau tiada (garis dasar,
  dokumen, kod/proses) → `ukur`.
- f1: lajur `F1 *` bila baris berformat 9 lajur DAN nombor; selain itu kosong (tidak dipetik dari prosa).
- komit: `-` (LOG tiada lajur komit — tidak direka).
- dev_sha8: `?` sehingga baris PERTAMA yang menyebut cincangan dev (`dev-v2 \\`xxxxxxxx…\\``); dibawa ke baris seterusnya sehingga baris
  lain menyebut cincangan dev baharu (dev hanya berubah pada baris yang menyatakannya).
"""

import argparse
import re
import sys
from pathlib import Path

from mypii import konfig
from mypii.nilai import iterasi

DEV_SHA = re.compile(r"dev(?:-v\d+)?\s+`([0-9a-f]{8})")
NOMBOR = re.compile(r"\d+(?:\.\d+)?")


def sel(baris: str) -> list[str]:
    """Pecah baris jadual markdown pada `|` yang bukan `\\|` dan bukan dalam `kod`."""
    keluar, semasa, kod, i = [], "", False, 0
    while i < len(baris):
        c = baris[i]
        if c == "\\" and baris[i + 1:i + 2] == "|":
            semasa += "|"
            i += 2
            continue
        if c == "`":
            kod = not kod
        if c == "|" and not kod:
            keluar.append(semasa.strip())
            semasa = ""
        else:
            semasa += c
        i += 1
    keluar.append(semasa.strip())
    return keluar[1:-1]  # buang sel kosong sebelum `|` pertama dan selepas `|` terakhir


STATUS_LOG = {"simpan": "simpan", "buang": "buang", "undur": "buang", "ukur": "ukur"}


def status(keputusan: str) -> str:
    """Kata kunci TERAWAL dalam Keputusan menang ("ukur (… tiada keputusan simpan/buang)" = ukur); tiada = `ukur`."""
    k = keputusan.lower()
    jumpa = [(k.find(x), x) for x in STATUS_LOG if x in k]
    return STATUS_LOG[min(jumpa)[1]] if jumpa else "ukur"


def tukar(log: str) -> list[dict]:
    rekod, dev = [], "?"
    for b in log.splitlines():
        if not re.match(r"\|\s*\d{4}-\d{2}-\d{2}\s*\|", b):
            continue
        s = sel(b)
        tarikh, nombor, perubahan = s[0], s[1], s[2]
        keputusan = s[-1] if len(s) >= 4 else ""
        f1 = s[3] if len(s) == 9 and NOMBOR.fullmatch(s[3]) else ""
        m = DEV_SHA.search(perubahan)
        dev = m.group(1) if m else dev
        rekod.append({"tarikh": tarikh, "komit": "-", "dev_sha8": dev, "f1": f1, "status": status(keputusan),
                      "baris_kod": "", "keterangan": _ringkas(f"LOG {nombor}: {perubahan}")})
    return rekod


def _ringkas(teks: str) -> str:
    had = konfig.utama()["nilai"]["iterasi"]["had_keterangan"]
    t = iterasi.bersih(teks)
    return t if len(t) <= had else t[: had - 1] + "…"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--log", type=Path, default=konfig.AKAR / "docs/LOG-ITERASI.md")
    p.add_argument("--keluar", type=Path, default=konfig.AKAR / konfig.utama()["nilai"]["iterasi"]["fail"])
    a = p.parse_args()
    if a.keluar.exists() and a.keluar.stat().st_size:
        print(f"{a.keluar} sudah berisi — isi semula sekali sahaja (fail tambah-sahaja)", file=sys.stderr)
        return 2
    rekod = tukar(a.log.read_text(encoding="utf-8"))
    iterasi.tambah(a.keluar, rekod)
    kira = {s: sum(r["status"] == s for r in rekod) for s in ("simpan", "buang", "ukur")}
    print(f"{len(rekod)} baris LOG → {a.keluar} ({kira}; dev_sha8 '?' {sum(r['dev_sha8'] == '?' for r in rekod)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
