"""Ayat biasa (`data/probe/ayat_biasa.yaml`, BAHAN PEMBANGUNAN PELAN-V21) untuk setiap sistem → `hasil/v21/ayat-biasa.json`.

    python -m mypii.nilai.ayat_biasa [--sistem mypii mypii-v2 mypii-v1]

Positif = span tepat + entiti ditanda; negatif = tiada ramalan bertindih nilai. Bukan dakwaan (ditulis sesi yang sama yang membaiki
pengecam); dilapor dalam BANDINGAN-V21 §Pembangunan sahaja. Sistem beku melalui worktree (`harness.ramal`).
"""

from __future__ import annotations

import argparse
import json
import sys

import yaml

from mypii import konfig
from mypii.nilai import harness


def nilai(sistem: list[str]) -> dict:
    p = yaml.safe_load((konfig.AKAR / "data/probe/ayat_biasa.yaml").read_text(encoding="utf-8"))
    kes = [("positif", x) for x in p["positif"]] + [("negatif", x) for x in p["negatif"]]
    dok = [{"id": str(i), "teks": x["teks"]} for i, (_, x) in enumerate(kes)]
    keluar = {}
    for s in sistem:
        ram = harness.ramal(s, dok)
        terlepas, tersalah = [], []
        for (jenis, x), r in zip(kes, ram, strict=True):
            a = x["teks"].index(x["nilai"])
            b = a + len(x["nilai"])
            if jenis == "positif" and not any((y["mula"], y["tamat"], y["entiti"]) == (a, b, x["entiti"]) for y in r):
                terlepas.append(x["teks"])
            if jenis == "negatif" and any(y["mula"] < b and a < y["tamat"] for y in r):
                tersalah.append(x["teks"])
        keluar[s] = {"positif": len(p["positif"]), "positif_ditanda": len(p["positif"]) - len(terlepas),
                     "negatif": len(p["negatif"]), "negatif_ditanda": len(tersalah), "terlepas": terlepas, "tersalah": tersalah}
    return keluar


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--sistem", nargs="+", default=["mypii", "mypii-v2", "mypii-v1"])
    h = nilai(a.parse_args().sistem)
    f = konfig.AKAR / konfig.utama()["nilai"]["statistik"]["v21"]["keluar"] / "ayat-biasa.json"
    f.write_text(json.dumps(h, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for s, x in h.items():
        print(f"{s}: positif {x['positif_ditanda']}/{x['positif']}, negatif ditanda {x['negatif_ditanda']}/{x['negatif']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
