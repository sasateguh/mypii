"""Eksport jawapan IAA (PELAN-IAA P7, ADR-015): SQLite → `iaa.skor.jawapan/<penyemak>.jsonl` (TANPA token).

    python -m mypii.iaa.eksport [--penyemak p1 ...]   # `make iaa-eksport`; lalai = semua penyemak dalam stor kecuali `uji`

Satu baris setiap dokumen sampel yang ada sekurang-kurangnya satu jawapan, ikut urutan:
`{"urutan": n, "status": "siap|separa|rosak|gagal", "jawapan": {"a1": …, "b": {"pilih", "nilai"?}, "c": …} | null}`.
Penyemak LLM (`llm.py`) menulis format yang SAMA (`baris`), jadi `skor` membaca satu bentuk sahaja. Id/split dokumen tidak ditulis —
`skor` menyambung `urutan` dengan `data/iaa/sampel.json`.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from mypii import konfig
from mypii.iaa import pakej
from mypii.iaa.stor import Stor, siap

AKAR = konfig.AKAR
STATUS = ("siap", "separa", "rosak", "gagal")


def baris(urutan: int, status: str, jawapan: dict | None) -> dict:
    if status not in STATUS:
        raise ValueError(f"status tidak dikenali: {status}")
    return {"urutan": urutan, "status": status, "jawapan": jawapan}


def tulis(laluan: Path, semua: list[dict]) -> None:
    laluan.parent.mkdir(parents=True, exist_ok=True)
    laluan.write_text("".join(json.dumps(b, ensure_ascii=False, sort_keys=True) + "\n"
                              for b in sorted(semua, key=lambda b: b["urutan"])), encoding="utf-8")


def dari_stor(stor: Stor, penyemak: str, dokumen: list[dict]) -> list[dict]:
    """Dokumen sampel → baris eksport bagi dokumen yang dijawab (siap / separa). Jawapan untuk urutan di luar sampel diabaikan."""
    j = stor.jawapan(penyemak)
    return [baris(d["urutan"], "siap" if siap(d, j[d["urutan"]]) else "separa", j[d["urutan"]])
            for d in dokumen if d["urutan"] in j]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Eksport jawapan penyemak IAA (tanpa token)")
    ap.add_argument("--penyemak", nargs="*")
    ap.add_argument("--bundel", type=Path)
    a = ap.parse_args(argv)
    k = konfig.utama()["iaa"]
    folder = Path(k["pakej"]["folder"]).expanduser()
    dokumen = json.loads((a.bundel or pakej.laluan_lalai(k)).expanduser().read_text(encoding="utf-8"))["dokumen"]
    stor = Stor(folder / k["pakej"]["stor"])
    try:
        ids = a.penyemak if a.penyemak is not None else [p for p in stor.penyemak() if p != "uji"]
        for p in ids:
            if not re.fullmatch(r"[a-z0-9_-]+", p) or p == "llm":
                print(f"GAGAL: id penyemak tidak sah: {p!r}", file=sys.stderr)
                return 2
            semua = dari_stor(stor, p, dokumen)
            tulis(AKAR / k["skor"]["jawapan"] / f"{p}.jsonl", semua)
            print(f"{p}: siap={sum(b['status'] == 'siap' for b in semua)} separa={sum(b['status'] == 'separa' for b in semua)}"
                  f" n={len(dokumen)}")
    finally:
        stor.tutup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
