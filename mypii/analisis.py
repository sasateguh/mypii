"""Analisis ralat (A3 P3): senarai FP/FN MyPII atas split latih/dev + probe sintetik untuk batasan yang dev tidak uji.

    python -m mypii.analisis [--split dev latih] [--n 40] [--keluar hasil/analisis-ralat.json]

Split `ujian` TIDAK dibenarkan di sini. Probe = data/probe/ralat.yaml (tidak masuk MyPII-Bench).
"""

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from mypii import konfig
from mypii.jana import nilai_palsu

AKAR = konfig.AKAR
SLOT = re.compile(r"\{([A-Z_]+)\}")
SPLIT_DIBENARKAN = ("latih", "dev")


def kelaskan(emas: list[dict], ramal: list[dict]) -> list[dict]:
    """Ralat span tepat: fp (tiada emas bertindih), fn (tiada ramalan bertindih), sempadan (entiti sama, span lain),
    keliru (bertindih dengan entiti lain)."""
    def tindih(a, b):
        return a["mula"] < b["tamat"] and b["mula"] < a["tamat"]

    def sama(a, b):
        return (a["mula"], a["tamat"], a["entiti"]) == (b["mula"], b["tamat"], b["entiti"])

    ralat = []
    for r in ramal:
        if any(sama(r, g) for g in emas):
            continue
        t = [g for g in emas if tindih(r, g)]
        jenis = "fp" if not t else "sempadan" if any(g["entiti"] == r["entiti"] for g in t) else "keliru"
        ralat.append({"jenis": jenis, "entiti": r["entiti"], "mula": r["mula"], "tamat": r["tamat"]})
    for g in emas:
        if not any(tindih(g, r) for r in ramal):
            ralat.append({"jenis": "fn", "entiti": g["entiti"], "mula": g["mula"], "tamat": g["tamat"]})
    return ralat


def _ubah(nilai: str, jenis: str | None, cfg: dict, rng: random.Random) -> str:
    if jenis == "ocr_digit":
        c = cfg["ocr_digit"]
        calon = [i for i, ch in enumerate(nilai) if ch in c["peta"]]
        pilih = {i for i in calon if rng.random() < c["kadar"]} or {rng.choice(calon)}
        return "".join(c["peta"][ch] if i in pilih else ch for i, ch in enumerate(nilai))
    if jenis == "patah_baris":
        n = cfg["patah_baris"]["selepas_aksara"]
        return nilai[:n] + "\n" + nilai[n:]
    return nilai


def isi_probe(templat: str, probe: dict, nama: dict, rng: random.Random) -> tuple[str, list[dict]]:
    """Isi slot probe; label emas ikut `slot.<S>.label` (null = negatif, tiada span)."""
    pengisi = {
        "NAMA": lambda: f"{rng.choice(nama['nama_pertama'])} {rng.choice(nama['nama_akhir'])}",
        "SYARIKAT_BARU": lambda: rng.choice(probe["syarikat_baharu"]),
    }
    teks, spans, akhir = "", [], 0
    for m in SLOT.finditer(templat):
        teks += templat[akhir:m.start()]
        s = m.group(1)
        if s in pengisi:
            nilai, label = pengisi[s](), None
        else:
            d = probe["slot"][s]
            nilai = _ubah(getattr(nilai_palsu, d["penjana"])(rng), d.get("ubah"), probe["ubah"], rng)
            label = d["label"]
        if label:
            spans.append({"mula": len(teks), "tamat": len(teks) + len(nilai), "entiti": label})
        teks += nilai
        akhir = m.end()
    return teks + templat[akhir:], spans


def jana_probe(n: int, benih: int, fail: Path = AKAR / "data/probe/ralat.yaml") -> list[dict]:
    probe = yaml.safe_load(fail.read_text(encoding="utf-8"))
    nama = yaml.safe_load((AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    rng = random.Random(benih)
    dokumen = []
    for kat, k in probe["kategori"].items():
        for i in range(n):
            teks, spans = isi_probe(k["templat"][i % len(k["templat"])], probe, nama, rng)
            dokumen.append({"id": f"probe-{kat}-{i:03d}", "kategori": kat, "teks": teks, "spans": spans})
    return dokumen


def ringkas(dokumen: list[dict], ramalan: list[list[dict]], kunci: str) -> dict:
    """Kiraan ralat ikut `kunci` dokumen (genre/kategori) + contoh ralat pertama setiap kumpulan."""
    keluar = {}
    for d, r in zip(dokumen, ramalan):
        k = keluar.setdefault(d[kunci], {"dok": 0, "emas": 0, "ramal": 0, "tepat": 0, "ralat": Counter(), "contoh": []})
        ralat = kelaskan(d["spans"], r)
        k["dok"] += 1
        k["emas"] += len(d["spans"])
        k["ramal"] += len(r)
        k["tepat"] += len(r) - sum(1 for x in ralat if x["jenis"] != "fn")
        for x in ralat:
            k["ralat"][f"{x['jenis']}:{x['entiti']}"] += 1
            if len(k["contoh"]) < 3:
                k["contoh"].append({"id": d["id"], "teks": d["teks"], **x, "nilai": d["teks"][x["mula"]:x["tamat"]]})
    for k in keluar.values():
        k["ralat"] = dict(k["ralat"])
    return keluar


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--split", nargs="+", default=list(SPLIT_DIBENARKAN))
    p.add_argument("--n", type=int, default=40, help="dokumen probe setiap kategori")
    p.add_argument("--benih", type=int, default=20261029)
    p.add_argument("--keluar", type=Path, default=AKAR / "hasil/analisis-ralat.json")
    a = p.parse_args()
    if set(a.split) - set(SPLIT_DIBENARKAN):
        print("analisis hanya untuk latih/dev — split ujian dikunci", file=sys.stderr)
        return 2
    from mypii.nilai.harness import ramal

    hasil = {}
    for s in a.split:
        dok = [json.loads(x) for x in (AKAR / f"data/bench/{s}.jsonl").read_text(encoding="utf-8").splitlines()]
        hasil[s] = ringkas(dok, ramal("mypii", dok), "genre")
    dok = jana_probe(a.n, a.benih)
    hasil["probe"] = ringkas(dok, ramal("mypii", dok), "kategori")
    a.keluar.parent.mkdir(parents=True, exist_ok=True)
    a.keluar.write_text(json.dumps(hasil, indent=2, ensure_ascii=False) + "\n")
    print("| set | kumpulan | dok | emas | ramal | tepat | ralat |\n|---|---|---|---|---|---|---|")
    for s, kumpulan in hasil.items():
        for g, k in sorted(kumpulan.items()):
            if k["ralat"] or s == "probe":
                print(f"| {s} | {g} | {k['dok']} | {k['emas']} | {k['ramal']} | {k['tepat']} | {k['ralat']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
