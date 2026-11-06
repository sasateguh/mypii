"""Penyemak sandaran LLM (PELAN-IAA P7, ADR-015): soalan (a)(b)(c) yang sama kepada `iaa.llm.model` melalui 9router.

    python -m mypii.iaa.llm [--bundel <fail>]   # `make iaa-llm`; cetak KIRAAN sahaja (tiada teks/jawapan)

Sumber = bundel yang sama dengan halaman semakan (`iaa.pakej`, di LUAR repo); `sampel_sha256` mesti sama dengan sampel dikomit.
Jawapan MENTAH disimpan dalam cache `iaa.llm.cache/<model>.jsonl` (kunci sha256 model+prompt+teks+span) sebelum diurai, jadi larian
semula tidak memerlukan rangkaian. Output `iaa.llm.keluar` = format eksport penyemak manusia (`eksport.baris`): jawapan yang tidak
boleh diurai/tidak lengkap = status `rosak`, panggilan gagal = `gagal` — kedua-duanya kekal dalam fail dan dikira, tidak dibuang.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from mypii import klien_llm, konfig
from mypii.iaa import eksport, pakej

AKAR = konfig.AKAR


def prompt(templat: str, dok: dict) -> str:
    span = "\n".join(f"{n}. {s['entiti']}: {dok['teks'][s['mula']:s['tamat']]}"
                     for n, s in enumerate(dok["spans"], 1)) or "(none)"
    return templat.replace("{span}", span).replace("{teks}", dok["teks"])


def kunci(model: str, p: str) -> str:
    """Prompt penuh sudah memuatkan teks + span, jadi kunci = sha256(model, prompt)."""
    return hashlib.sha256(json.dumps([model, p], ensure_ascii=False).encode()).hexdigest()


def fail_cache(k: dict, akar: Path = AKAR) -> Path:
    return akar / k["llm"]["cache"] / (re.sub(r"[^A-Za-z0-9._-]+", "_", k["llm"]["model"]) + ".jsonl")


def muat(laluan: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if laluan.exists():
        for x in laluan.read_text(encoding="utf-8").splitlines():
            try:  # baris terakhir boleh terpotong bila larian dihentikan semasa menulis
                b = json.loads(x)
                out[b["kunci"]] = b["jawapan"]
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return out


def urai(jawapan: str, n_span: int, pilihan: dict) -> dict | None:
    """Jawapan mentah → {soalan: nilai} dalam bentuk stor (`a<n>`, `b`, `c`); None = rosak (bentuk/bilangan/pilihan salah)."""
    try:
        x = klien_llm.json_dari(jawapan)
    except ValueError:
        return None
    if not isinstance(x, dict):
        return None
    a, tb, c = x.get("span"), x.get("tak_bertanda"), x.get("realistik")
    if not isinstance(a, list) or len(a) != n_span or any(v not in pilihan["a"] for v in a):
        return None
    if not isinstance(tb, list) or not all(isinstance(v, str) for v in tb) or c not in pilihan["c"]:
        return None
    tb = [v.strip() for v in tb if v.strip()]
    out = {f"a{n}": v for n, v in enumerate(a, 1)}
    out["b"] = {"pilih": pilihan["b"][1], "nilai": tb} if tb else {"pilih": pilihan["b"][0]}
    out["c"] = c
    return out


def jalankan(k: dict, dokumen: list[dict], hantar=klien_llm.hantar_9router, akar: Path = AKAR) -> tuple[list[dict], dict]:
    """Pulang (baris eksport ikut urutan, statistik kiraan). Hanya dokumen tiada dalam cache dihantar."""
    m, templat = k["llm"]["model"], k["llm"]["prompt"]
    laluan = fail_cache(k, akar)
    cache = muat(laluan)
    prompts = [prompt(templat, d) for d in dokumen]
    kunci_dok = [kunci(m, p) for p in prompts]
    hilang = {kc: p for kc, p in zip(kunci_dok, prompts) if kc not in cache}
    gagal = 0
    if hilang:
        if hantar is klien_llm.hantar_9router:
            os.nice(konfig.utama()["llm"]["nice"])

        def satu(item):
            try:
                return item[0], klien_llm.tanya([m], item[1], k["llm"]["suhu"], urai=str, hantar=hantar)[1]
            except klien_llm.GagalLLM:
                return item[0], None

        laluan.parent.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=konfig.utama()["llm"]["serentak"]) as ex, open(laluan, "a", encoding="utf-8") as f:
            for kc, hasil in ex.map(satu, hilang.items()):  # tambah serta-merta: larian terputus disambung dari cache
                if hasil is None:
                    gagal += 1
                    continue
                cache[kc] = hasil
                f.write(json.dumps({"kunci": kc, "jawapan": hasil}, ensure_ascii=False) + "\n")
                f.flush()
        laluan.write_text("".join(json.dumps({"kunci": c, "jawapan": cache[c]}, ensure_ascii=False) + "\n"
                                  for c in sorted(cache)), encoding="utf-8")   # tersusun = bait sama tanpa mengira susunan siap
    baris = []
    for kc, d in zip(kunci_dok, dokumen):
        j = urai(cache[kc], len(d["spans"]), k["pilihan"]) if kc in cache else None
        status = "gagal" if kc not in cache else ("siap" if j is not None else "rosak")
        baris.append(eksport.baris(d["urutan"], status, j))
    st = {"model": m, "dokumen": len(dokumen), "dari_cache": len(dokumen) - len(hilang), "panggilan": len(hilang),
          "gagal": gagal, "rosak": sum(b["status"] == "rosak" for b in baris), "siap": sum(b["status"] == "siap" for b in baris)}
    return baris, st


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Penyemak sandaran LLM IAA (cetak kiraan sahaja)")
    ap.add_argument("--bundel", type=Path)
    a = ap.parse_args(argv)
    k = konfig.utama()["iaa"]
    laluan = (a.bundel or pakej.laluan_lalai(k)).expanduser()
    bundel = json.loads(laluan.read_text(encoding="utf-8"))
    sha = hashlib.sha256((AKAR / k["sampel"]["fail"]).read_bytes()).hexdigest()
    if bundel["sampel_sha256"] != sha:
        print("GAGAL: bundel dibina dari sampel lain — `make iaa-pakej` dahulu", file=sys.stderr)
        return 1
    baris, st = jalankan(k, bundel["dokumen"])
    eksport.tulis(AKAR / k["llm"]["keluar"], baris)
    print(" ".join(f"{x}={v}" for x, v in st.items()))
    return 0 if st["gagal"] == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
