"""Laporan bandingan dev (PELAN-B B4, ADR-012): jadual + ralat utama setiap sistem → blok jana dalam `docs/BANDINGAN.md`.

    python -m mypii.nilai.bandingan               # skor + ralat (LLM dari cache DIKOMIT, tiada rangkaian) → tulis blok jana
    python -m mypii.nilai.bandingan --ukur-masa   # juga ukur masa sistem tempatan + latensi LLM sampel (perlu 9router) → fail masa

Skor = `harness.skor()` (fungsi sama dengan harness). Masa berubah setiap larian, jadi ia disimpan dalam fail berasingan
(`bandingan.fail_masa`, dikomit) dan hanya dibaca semasa menjana — tanpa `--ukur-masa`, blok jana sama bait demi bait.
Hanya split dev: split dikunci ditolak.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime

from mypii import klien_llm, konfig
from mypii.nilai import garis, harness

AKAR = konfig.AKAR
JENIS = ("palsu", "sempadan", "salah_jenis", "terlepas")


def _k() -> dict:
    return konfig.utama()["bandingan"]


def _tiada_rangkaian(model, prompt, suhu):
    raise OSError("bandingan membaca cache LLM sahaja — jalankan `make nilai-garis` dengan 9router dahulu")


def ramal_semua(dokumen: list[dict], sistem: list[str]) -> dict[str, list[list[dict]]]:
    keluar = {}
    for s in sistem:
        if s.startswith("llm:"):
            r, st = garis.ramal_llm(s[4:], dokumen, hantar=_tiada_rangkaian)
            if st["panggilan"]:
                raise SystemExit(f"{s}: {st['panggilan']} dokumen tiada dalam cache — `make nilai-garis` dahulu")
            keluar[s] = r
        else:
            keluar[s] = harness.ramal(s, dokumen)
    return keluar


def label(teks: str, mula: int) -> str:
    """Label sebelum span dalam baris yang sama (≤ 3 token terakhir, huruf kecil) — cth 'no. akaun' — untuk mengumpul ralat."""
    baris = teks[teks.rfind("\n", 0, mula) + 1:mula]
    token = re.findall(r"[^\W\d_][\w.'/-]*", baris.lower())[-_k()["token_label"]:]
    return " ".join(t.rstrip(".") for t in token) or "(tiada label)"


def petikan(teks: str, mula: int, tamat: int) -> str:
    w = _k()["lebar_petikan"]
    a, b = max(0, mula - w), min(len(teks), tamat + w)
    s = ("…" if a else "") + teks[a:mula] + "«" + teks[mula:tamat] + "»" + teks[tamat:b] + ("…" if b < len(teks) else "")
    return s.replace("\n", " ⏎ ")


def kelaskan(dokumen: list[dict], ramalan: list[list[dict]]) -> list[dict]:
    """Setiap ralat padanan TEPAT: ramalan tanpa emas bertindih = palsu; bertindih emas entiti sama = sempadan; bertindih emas entiti
    lain sahaja = salah_jenis; emas tanpa ramalan bertindih langsung = terlepas. (Emas yang hanya dipotong sempadan/jenis tidak dikira
    dua kali sebagai terlepas.)"""
    keluar = []
    for d, r in zip(dokumen, ramalan):
        emas = d["spans"]
        sama = lambda a, b: a["entiti"] == b["entiti"] and a["mula"] == b["mula"] and a["tamat"] == b["tamat"]
        tindih = lambda a, b: a["mula"] < b["tamat"] and b["mula"] < a["tamat"]
        for s in r:
            if any(sama(s, g) for g in emas):
                continue
            t = [g for g in emas if tindih(s, g)]
            jenis = "palsu" if not t else "sempadan" if any(g["entiti"] == s["entiti"] for g in t) else "salah_jenis"
            keluar.append({"jenis": jenis, "entiti": s["entiti"], "dok": d, "span": s})
        for g in emas:
            if not any(tindih(s, g) for s in r):
                keluar.append({"jenis": "terlepas", "entiti": g["entiti"], "dok": d, "span": g})
    return keluar


def ringkas_ralat(ralat: list[dict]) -> dict:
    kira = Counter((x["jenis"], x["entiti"]) for x in ralat)
    neg = [x for x in ralat if x["jenis"] == "palsu" and not x["dok"]["spans"]]
    utama = {}
    for jenis in ("palsu", "terlepas"):
        kump = defaultdict(list)
        for x in sorted((x for x in ralat if x["jenis"] == jenis), key=lambda x: (x["dok"]["id"], x["span"]["mula"])):
            kump[label(x["dok"]["teks"], x["span"]["mula"])].append(x)
        teratas = sorted(kump.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:_k()["label_teratas"]]
        utama[jenis] = [{"label": lb, "bil": len(xs), "entiti": dict(sorted(Counter(x["entiti"] for x in xs).items())),
                         "contoh": [petikan(x["dok"]["teks"], x["span"]["mula"], x["span"]["tamat"]) + f" ({x['dok']['id']})"
                                    for x in xs[:_k()["contoh_setiap_label"]]]} for lb, xs in teratas]
    return {"kira": {f"{j}|{e}": n for (j, e), n in sorted(kira.items())},
            "dok_negatif": {"dok": len({x["dok"]["id"] for x in neg}), "span": len(neg)}, "utama": utama}


def kos_llm(model: str, dokumen: list[dict]) -> dict:
    """Saiz masuk/keluar dari cache dikomit (aksara; token bergantung pada tokenizer setiap model — tidak dianggar)."""
    k = konfig.utama()["garis_dasar"]["llm"]
    cache = garis._muat_cache(garis.fail_cache(model))
    jawapan = [cache[garis.kunci_dok(model, d["teks"])] for d in dokumen]
    return {"aksara_masuk": sum(len(k["prompt"].replace("{teks}", d["teks"])) for d in dokumen),
            "aksara_keluar": sum(len(j) for j in jawapan)}


def ukur_masa(dokumen: list[dict], sistem: list[str], hantar=klien_llm.hantar_9router) -> dict:
    keluar = {"diukur": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "sistem": {}, "llm": {}}
    for s in sistem:
        if s.startswith("llm:"):
            continue
        t = time.perf_counter()
        harness.ramal(s, dokumen)
        keluar["sistem"][s] = {"dokumen": len(dokumen), "saat": round(time.perf_counter() - t, 2)}
    k = konfig.utama()["garis_dasar"]["llm"]
    sampel = sorted(dokumen, key=lambda d: d["id"])[:_k()["sampel_latensi"]]
    if hantar is klien_llm.hantar_9router and any(s.startswith("llm:") for s in sistem):
        os.nice(konfig.utama()["llm"]["nice"])
    for s in (s for s in sistem if s.startswith("llm:")):
        masa, gagal = [], 0
        for d in sampel:  # bersiri (bukan serentak) supaya latensi satu panggilan tidak bercampur giliran; cache TIDAK ditulis
            t = time.perf_counter()
            try:
                hantar(s[4:], k["prompt"].replace("{teks}", d["teks"]), k["suhu"])
                masa.append(time.perf_counter() - t)
            except (OSError, ValueError, KeyError, IndexError, TypeError):
                gagal += 1
        masa.sort()
        keluar["llm"][s] = {"sampel": len(sampel), "gagal": gagal,
                            "median_s": round(masa[len(masa) // 2], 2) if masa else None,
                            "maks_s": round(masa[-1], 2) if masa else None}
    return keluar


def kira(dokumen: list[dict], sistem: list[str]) -> dict:
    ramalan = ramal_semua(dokumen, sistem)
    hasil = {"dokumen": len(dokumen), "dok_negatif": sum(not d["spans"] for d in dokumen), "sistem": {}}
    for s, r in ramalan.items():
        h = {"skor": harness.skor(dokumen, r), "ralat": ringkas_ralat(kelaskan(dokumen, r))}
        if s == "pii-guard":
            h["skor_disokong"] = harness.skor(garis.gold_disokong(dokumen), r)
        if s.startswith("llm:"):
            h["kos"] = kos_llm(s[4:], dokumen)
        hasil["sistem"][s] = h
    return hasil


def tulis_blok(laluan, blok: str, penanda: list[str] | None = None) -> None:
    mula, tamat = penanda or _k()["penanda"]
    teks = laluan.read_text(encoding="utf-8")
    a, b = teks.find(mula), teks.find(tamat)
    if a < 0 or b < a:
        raise SystemExit(f"{laluan}: penanda blok jana tiada ({mula} … {tamat})")
    laluan.write_text(teks[:a + len(mula)] + "\n" + blok + teks[b:], encoding="utf-8")


def main() -> int:
    from mypii.nilai import bandingan_md

    p = argparse.ArgumentParser()
    p.add_argument("--split", default="dev")
    p.add_argument("--ukur-masa", action="store_true")
    a = p.parse_args()
    if a.split in konfig.utama()["nilai"]["split_dikunci"]:
        print(f"split {a.split} dikunci — laporan bandingan untuk dev sahaja", file=sys.stderr)
        return 2
    fail = AKAR / "data/bench" / f"{a.split}.jsonl"
    dokumen = [json.loads(x) for x in fail.read_text(encoding="utf-8").splitlines()]
    sistem = harness.senarai_sistem(["semua"])
    fail_masa = AKAR / _k()["fail_masa"]
    if a.ukur_masa:
        fail_masa.parent.mkdir(parents=True, exist_ok=True)
        fail_masa.write_text(json.dumps(ukur_masa(dokumen, sistem), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    hasil = kira(dokumen, sistem) | {"split": a.split, "sha256": hashlib.sha256(fail.read_bytes()).hexdigest()}
    masa = json.loads(fail_masa.read_text(encoding="utf-8")) if fail_masa.exists() else None
    (AKAR / "hasil").mkdir(exist_ok=True)
    (AKAR / "hasil" / f"{a.split}-bandingan.json").write_text(json.dumps(hasil, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tulis_blok(AKAR / _k()["laporan"], bandingan_md.blok(hasil, masa))
    for s, h in hasil["sistem"].items():
        print(f"{s}: F1 * tepat {h['skor']['semua|*']['tepat']['f1']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
