"""Probe format garis dasar EKSPLORASI (PRA-DAFTAR pindaan 2026-11-03, PELAN-MODEL-LAIN P3/P4, ADR-017) — `make probe-llm`.

Setiap model `garis_dasar.llm.eksplorasi` dipanggil atas N dokumen PERTAMA split (config `garis_dasar.llm.probe`: saiz + split yang
dibenarkan; split dikunci ditolak SEBELUM fail dibaca) MELALUI `garis.ramal_llm` — prompt, suhu, parameter dan kunci cache sama dengan
larian penuh, jadi jawapan probe disambung oleh larian dev (bukan larian kedua). Lulus = N/N jawapan diterima DAN N/N diurai
(`span_dari_jawapan` ≠ None). **F1 tidak dikira**: output = kiraan + jenis ralat sahaja (tiada teks, tiada span, tiada kunci).
API Anthropic menolak permintaan (`TolakAPI`, cth 400 parameter) = model itu GUGUR; tiada cubaan kedua dengan parameter lain.
"""

import argparse
import json
import sys
from pathlib import Path

from mypii import klien_llm, konfig
from mypii.nilai import garis


def _k() -> dict:
    return konfig.utama()["garis_dasar"]["llm"]


def semak_split(split: str) -> None:
    if split in konfig.utama()["nilai"]["split_dikunci"] or split not in _k()["probe"]["split"]:
        raise SystemExit(f"split {split}: probe hanya untuk {_k()['probe']['split']} (split dikunci ditolak)")


def satu_model(model: str, dokumen: list[dict], hantar_9router=klien_llm.hantar_9router,
               hantar_anthropic=None, akar: Path = konfig.AKAR) -> dict:
    """Satu calon → {diterima, diurai, lulus, jenis_ralat, …kiraan}. `hantar_anthropic` None = SDK sebenar (jalan ramal_llm biasa)."""
    hantar = hantar_9router
    if garis.ialah_anthropic(model) and hantar_anthropic is not None:
        hantar = hantar_anthropic
    try:
        _, st = garis.ramal_llm(model, dokumen, hantar=hantar, akar=akar)
    except garis.TolakAPI as e:
        return {"dokumen": len(dokumen), "diterima": 0, "diurai": 0, "lulus": False, "jenis_ralat": [f"TolakAPI: {e}"]}
    diterima = st["dokumen"] - st["gagal"]
    diurai = diterima - st["rosak"]
    jenis = list(st.get("ralat", []))
    if st["rosak"]:
        jenis.append(f"jawapan tidak diurai: {st['rosak']}")
    if st.get("had_dicapai"):
        jenis.append("had belanja lejar dicapai")
    keluar = {"dokumen": st["dokumen"], "diterima": diterima, "diurai": diurai, "lulus": diurai == st["dokumen"] == diterima,
              "jenis_ralat": jenis, "panggilan": st["panggilan"], "dari_cache": st["dari_cache"]}
    if "usd" in st:
        keluar["usd"] = st["usd"]
    return keluar


def jalankan(dokumen_split: list[dict], split: str, akar: Path = konfig.AKAR, **hantar) -> dict:
    n = _k()["probe"]["dokumen"]
    dok = dokumen_split[:n]  # susunan FAIL, bukan diisih (pindaan)
    model = {m: satu_model(m, dok, akar=akar, **hantar) for m in _k().get("eksplorasi", [])}
    return {"split": split, "dokumen": len(dok), "id": [d["id"] for d in dok], "model": model,
            "lulus": [m for m, v in model.items() if v["lulus"]], "gugur": [m for m, v in model.items() if not v["lulus"]]}


def fail_hasil(split: str, akar: Path | None = None) -> Path:
    return (akar or konfig.AKAR) / _k()["probe"]["fail"].format(split=split)  # AKAR dibaca semasa panggilan (ujian menindihnya)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--split", default="dev")
    a = p.parse_args(argv)
    semak_split(a.split)
    from mypii.nilai.harness import (
        _dokumen,  # selepas semak_split: split dikunci tidak pernah dibaca
    )

    h = jalankan(_dokumen(a.split), a.split)
    fail = fail_hasil(a.split)
    fail.parent.mkdir(parents=True, exist_ok=True)
    fail.write_text(json.dumps(h, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print("| model | diterima | diurai | lulus | jenis ralat |\n|---|---|---|---|---|")
    for m, v in h["model"].items():
        print(f"| {m} | {v['diterima']}/{v['dokumen']} | {v['diurai']}/{v['dokumen']} | {'ya' if v['lulus'] else 'GUGUR'} | "
              f"{'; '.join(v['jenis_ralat']) or '—'} |")
    print(f"lulus {len(h['lulus'])}, gugur {len(h['gugur'])} ({fail.relative_to(konfig.AKAR)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
