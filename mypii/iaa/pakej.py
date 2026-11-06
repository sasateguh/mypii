"""Pemakej bundel IAA (PELAN-IAA P3, ADR-015): sampel + fail split → bundel JSON di LUAR repo.

    python -m mypii.iaa.pakej [--keluar <fail>]   # `make iaa-pakej`; lalai iaa.pakej.folder/bundel; cetak KIRAAN + sha256 sahaja

Bundel = `dokumen` (300, ikut urutan sampel) + `uji` (dokumen dev di LUAR sampel, `iaa.uji.dokumen`, untuk penyemak `uji`).
Setiap dokumen membawa id/split untuk eksport; pelayan TIDAK menghantarnya ke halaman. Teks tidak pernah dicetak
(ujian2 dimeterai — pengecualian PRA-DAFTAR §14 hanya untuk halaman semakan + penyemak LLM).
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

from mypii import konfig

AKAR = konfig.AKAR


def _baca(laluan: Path, perlu: set[str] | None) -> dict[str, dict]:
    """id → {teks, spans} untuk id dalam `perlu` (None = semua). Medan lain dibuang."""
    out = {}
    with open(laluan, encoding="utf-8") as f:
        for baris in f:
            if baris.strip():
                r = json.loads(baris)
                if perlu is None or r["id"] in perlu:
                    out[r["id"]] = {"bahasa": r["bahasa"], "teks": r["teks"],
                                    "spans": [{"mula": s["mula"], "tamat": s["tamat"], "entiti": s["entiti"]}
                                              for s in sorted(r["spans"], key=lambda s: s["mula"])]}
    return out


def bina(k: dict, akar: Path = AKAR) -> dict:
    """Config `iaa` → objek bundel. Id sampel yang tiada dalam fail split = ValueError (sampel basi)."""
    sampel = json.loads((akar / k["sampel"]["fail"]).read_text(encoding="utf-8"))
    split = k["sampel"]["split"]
    dokumen = []
    for s in split:
        perlu = {d["id"] for d in sampel["dokumen"] if d["split"] == s}
        ada = _baca(akar / split[s], perlu)
        hilang = perlu - ada.keys()
        if hilang:
            raise ValueError(f"{len(hilang)} id sampel {s} tiada dalam fail split — jana semula sampel")
        dokumen += [{"urutan": d["urutan"], "id": d["id"], "split": s, **ada[d["id"]]}
                    for d in sampel["dokumen"] if d["split"] == s]
    dokumen.sort(key=lambda d: d["urutan"])
    dalam = {d["id"] for d in sampel["dokumen"]}
    dev = _baca(akar / split["dev"], None)
    calon = sorted(i for i in dev if i not in dalam)
    uji = random.Random(k["sampel"]["benih"]).sample(calon, k["uji"]["dokumen"])
    uji_dok = [{"urutan": n, "id": i, "split": "dev", **dev[i]} for n, i in enumerate(uji, 1)]
    return {"sampel_sha256": hashlib.sha256((akar / k["sampel"]["fail"]).read_bytes()).hexdigest(),
            "n": len(dokumen), "dokumen": dokumen, "uji": uji_dok}


def laluan_lalai(k: dict) -> Path:
    return Path(k["pakej"]["folder"]).expanduser() / k["pakej"]["bundel"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bundel dokumen semakan IAA (di luar repo)")
    ap.add_argument("--keluar", type=Path)
    a = ap.parse_args(argv)
    k = konfig.utama()["iaa"]
    keluar = (a.keluar or laluan_lalai(k)).expanduser().resolve()
    if keluar.is_relative_to(AKAR):
        print(f"GAGAL: bundel mesti di LUAR repo ({keluar})", file=sys.stderr)
        return 2
    try:
        obj = bina(k, AKAR)
    except ValueError as e:
        print(f"GAGAL: {e}", file=sys.stderr)
        return 1
    bait = json.dumps(obj, ensure_ascii=False).encode()
    keluar.parent.mkdir(parents=True, exist_ok=True)
    keluar.write_bytes(bait)
    keluar.chmod(0o640)
    span = sum(len(d["spans"]) for d in obj["dokumen"])
    print(f"dokumen={obj['n']} span={span} uji={len(obj['uji'])} sha256={hashlib.sha256(bait).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
