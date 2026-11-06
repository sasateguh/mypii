"""Pensampel IAA berstrata (PELAN-IAA P2, ADR-015, pindaan PRA-DAFTAR 2026-10-31).

    python -m mypii.iaa.sampel          # `make iaa-sampel`; tulis iaa.sampel.fail, cetak KIRAAN strata + sha256

Setiap split × bahasa × (berspan | negatif) = `setiap_strata` dokumen, dipilih dengan `random.Random(benih)` atas id terisih.
Urutan paparan dikocok (benih sama) merentas split — buta split. Fail split hanya dibaca untuk id, bahasa dan BILANGAN span;
teks tidak disimpan, dicetak atau dipulangkan (ujian2 dimeterai, pengecualian §14 hanya untuk halaman + LLM).
"""

import hashlib
import json
import random
import sys
from pathlib import Path

from mypii import konfig

AKAR = konfig.AKAR


def baca_meta(laluan: Path) -> list[dict]:
    """id + bahasa + berspan setiap dokumen; medan lain dibuang serta-merta."""
    out = []
    with open(laluan, encoding="utf-8") as f:
        for baris in f:
            if baris.strip():
                r = json.loads(baris)
                out.append({"id": r["id"], "bahasa": r["bahasa"], "berspan": len(r["spans"]) > 0})
    return out


def pilih(meta: dict[str, list[dict]], bahasa: list[str], setiap: int, benih: int) -> list[dict]:
    """Sampel berstrata + kocok urutan. `meta` = {split: [meta…]} mengikut urutan config. Strata kurang = ValueError."""
    rng = random.Random(benih)
    dipilih = []
    for split, dok in meta.items():
        for b in bahasa:
            for berspan in (True, False):
                calon = sorted(d["id"] for d in dok if d["bahasa"] == b and d["berspan"] is berspan)
                if len(calon) < setiap:
                    jenis = "berspan" if berspan else "negatif"
                    raise ValueError(f"strata {split}/{b}/{jenis} hanya {len(calon)} dokumen (perlu {setiap})")
                dipilih += [{"id": i, "split": split, "bahasa": b, "berspan": berspan}
                            for i in rng.sample(calon, setiap)]
    rng.shuffle(dipilih)
    return [{"urutan": n, **d} for n, d in enumerate(dipilih, 1)]


def kiraan(sampel: list[dict]) -> dict[str, int]:
    k: dict[str, int] = {}
    for d in sampel:
        kunci = f"{d['split']}/{d['bahasa']}/{'berspan' if d['berspan'] else 'negatif'}"
        k[kunci] = k.get(kunci, 0) + 1
    return dict(sorted(k.items()))


def jana(k: dict, akar: Path = AKAR) -> tuple[dict, bytes]:
    """Config `iaa.sampel` → (objek fail, bait JSON). Tiada tulis."""
    meta = {s: baca_meta(akar / p) for s, p in k["split"].items()}
    sampel = pilih(meta, k["bahasa"], k["setiap_strata"], k["benih"])
    obj = {"benih": k["benih"], "setiap_strata": k["setiap_strata"], "n": len(sampel),
           "kiraan": kiraan(sampel), "dokumen": sampel}
    return obj, (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode()


def main() -> int:
    k = konfig.utama()["iaa"]["sampel"]
    try:
        obj, bait = jana(k, AKAR)
    except ValueError as e:
        print(f"GAGAL: {e}", file=sys.stderr)
        return 1
    keluar = AKAR / k["fail"]
    keluar.parent.mkdir(parents=True, exist_ok=True)
    keluar.write_bytes(bait)
    for kunci, n in obj["kiraan"].items():
        print(f"{kunci}\t{n}")
    print(f"n={obj['n']} sha256={hashlib.sha256(bait).hexdigest()} → {k['fail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
