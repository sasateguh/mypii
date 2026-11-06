"""Nilai sistem atas MyPII-Bench: precision/recall/F1 span TEPAT dan SEPARA, setiap entiti, setiap bahasa.

    python -m mypii.nilai.harness --split dev [--sistem mypii presidio-asal pii-guard llm:<model> | semua] [--keluar hasil/]
        [--iterasi simpan|buang|ukur --keterangan TEKS]
    python -m mypii.nilai.harness --split dev --sistem semua --statistik

`--iterasi` menambah satu baris `hasil/iterasi.tsv` (`mypii/nilai/iterasi.py`, ADR-006); larian yang gagal → baris `crash` + exit ≠ 0.

Garis dasar pesaing (`pii-guard`, `llm:<model>`) = `mypii/nilai/garis.py` (ADR-011); `semua` = mypii, presidio-asal, pii-guard dan
setiap model `garis_dasar.llm.model`.

Setiap larian menyimpan ramalan per dokumen `<keluar>/ramalan/<split>-<sistem>.jsonl` (`{id, spans}`); `--statistik` membaca
fail itu SAHAJA (tiada Presidio/rangkaian) → `<keluar>/<split>-statistik.json` + jadual markdown (`mypii/nilai/statistik.py`,
ADR-006 §Statistik).

Split `latih3`/`dev3`/`ujian3` (PELAN-V2 P4) dibaca dari `nilai.split_fail`; selain itu `data/bench/<split>.jsonl`.
Split `ujian`/`ujian2` (config `nilai.split_dikunci`) hanya boleh dibaca dengan --benarkan-ujian (gelung automatik TIDAK menggunakannya)
DAN bila `docs/PRA-DAFTAR.md` dikomit + bersih dalam git HEAD (`mypii/nilai/pradaftar.py`, ADR-014); sha komitnya dicetak dan ditulis
sebagai `_pradaftar` dalam setiap fail hasil split itu. `ujian3` (juga dalam `split_dikunci`) menuntut syarat sama DAN tajuk
pindaan "MyPII v2" ≥ `pindaan_split.ujian3.min` dalam fail itu di HEAD (`pradaftar.semak_pindaan`).
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from mypii import konfig
from mypii.nilai import garis, iterasi, pradaftar

AKAR = konfig.AKAR


def _enjin(sistem: str):
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    nlp = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }).create_engine()
    enjin = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
    if sistem == "mypii":
        from mypii import semua_pengecam
        for p in semua_pengecam("en"):
            enjin.registry.add_recognizer(p)
    return enjin


def ramal(sistem: str, dokumen: list[dict]) -> list[list[dict]]:
    if sistem == "mypii-v1":   # PRA-DAFTAR §7-v2: kod + config tag v1 dari git worktree sementara
        from mypii.nilai import v1_worktree
        return v1_worktree.ramal(dokumen)
    if sistem == "pii-guard":
        return garis.ramal_pii_guard(dokumen)
    if sistem.startswith("llm:"):
        ramalan, st = garis.ramal_llm(sistem[4:], dokumen)
        print(f"{sistem}: {json.dumps(st)}", file=sys.stderr)
        return ramalan
    k = konfig.utama()["nilai"]
    peta = k["peta_garis_dasar"] if sistem == "presidio-asal" else {}
    enjin = _enjin(sistem)
    hasil = []
    for d in dokumen:
        # Teks BM/Manglish juga dianalisis sebagai "en": pengecam corak tidak bergantung bahasa;
        # perkataan konteks BM ada dalam senarai konteks.
        r = enjin.analyze(text=d["teks"], language="en", score_threshold=k["ambang_skor"])
        spans = []
        for x in r:
            e = peta.get(x.entity_type, x.entity_type)
            if e in k["entiti"]:
                spans.append({"mula": x.start, "tamat": x.end, "entiti": e})
        hasil.append(spans)
    return hasil


def _bertindih(a: dict, b: dict) -> bool:
    return a["entiti"] == b["entiti"] and a["mula"] < b["tamat"] and b["mula"] < a["tamat"]


def _sama(a: dict, b: dict) -> bool:
    return a["entiti"] == b["entiti"] and a["mula"] == b["mula"] and a["tamat"] == b["tamat"]


def skor(dokumen: list[dict], ramalan: list[list[dict]]) -> dict:
    """Precision dikira dari sisi ramalan, recall dari sisi emas (span tepat dan span bertindih)."""
    kira = defaultdict(lambda: defaultdict(int))
    for d, r in zip(dokumen, ramalan):
        emas = d["spans"]
        for kumpulan in ("semua", f"bahasa:{d['bahasa']}"):
            for e in {s["entiti"] for s in emas} | {s["entiti"] for s in r} | {"*"}:
                g = [s for s in emas if e in ("*", s["entiti"])]
                p = [s for s in r if e in ("*", s["entiti"])]
                c = kira[f"{kumpulan}|{e}"]
                c["emas"] += len(g)
                c["ramal"] += len(p)
                for jenis, padan in (("tepat", _sama), ("separa", _bertindih)):
                    c[f"p_{jenis}"] += sum(1 for s in p if any(padan(s, x) for x in g))
                    c[f"g_{jenis}"] += sum(1 for x in g if any(padan(s, x) for s in p))
    keluar = {}
    for kunci, c in sorted(kira.items()):
        baris = {"emas": c["emas"], "ramal": c["ramal"]}
        for jenis in ("tepat", "separa"):
            pr = c[f"p_{jenis}"] / c["ramal"] if c["ramal"] else 0.0
            rc = c[f"g_{jenis}"] / c["emas"] if c["emas"] else 0.0
            f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
            baris[jenis] = {"p": round(pr, 4), "r": round(rc, 4), "f1": round(f1, 4)}
        keluar[kunci] = baris
    return keluar


def senarai_sistem(diminta: list[str]) -> list[str]:
    """`semua` = mypii, presidio-asal, pii-guard + setiap `garis_dasar.llm.model`, KECUALI `anthropic/<id>` yang belum pernah
    dijalankan (tiada fail cache — sebelum PELAN-CLAUDE P4): dilangkau dengan amaran, supaya `make statistik`/`bandingan` tidak
    memanggil API berbayar atau gagal. Cache separa tetap dimuatkan (bandingan berhenti "tiada dalam cache" — tiada angka separa)."""
    if diminta != ["semua"]:
        return diminta
    llm = []
    for m in konfig.utama()["garis_dasar"]["llm"]["model"]:
        if m.startswith("anthropic/") and not garis.fail_cache(m).exists():
            print(f"llm:{m}: belum dijalankan (tiada cache) — dilangkau dari `semua` (PELAN-CLAUDE P4)", file=sys.stderr)
            continue
        llm.append(f"llm:{m}")
    return ["mypii", "presidio-asal", "pii-guard"] + llm


def nama_fail(split: str, sistem: str) -> str:
    return f"{split}-" + re.sub(r"[^A-Za-z0-9._-]+", "_", sistem) + ".json"


def _dokumen(split: str) -> list[dict]:
    fail = AKAR / konfig.fail_split(split)  # v3 (latih3/dev3/ujian3) = config nilai.split_fail
    return [json.loads(x) for x in fail.read_text(encoding="utf-8").splitlines()]


def fail_ramalan(keluar: Path, split: str, sistem: str) -> Path:
    folder = konfig.utama()["nilai"]["statistik"]["folder_ramalan"]
    return keluar / folder / (Path(nama_fail(split, sistem)).stem + ".jsonl")


def simpan_ramalan(keluar: Path, split: str, sistem: str, dokumen: list[dict], ramalan: list[list[dict]]) -> Path:
    f = fail_ramalan(keluar, split, sistem)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("".join(json.dumps({"id": d["id"], "spans": r}, ensure_ascii=False, sort_keys=True) + "\n"
                         for d, r in zip(dokumen, ramalan)), encoding="utf-8")
    return f


def baca_ramalan(keluar: Path, split: str, sistem: str, dokumen: list[dict]) -> list[list[dict]]:
    """Ramalan tersimpan disusun ikut susunan `dokumen`; id hilang/lebih = ralat (bukan diam-diam dianggap kosong)."""
    f = fail_ramalan(keluar, split, sistem)
    if not f.exists():
        raise FileNotFoundError(f"{f} tiada — jalankan harness tanpa --statistik untuk sistem {sistem!r} dahulu")
    ikut_id = {}
    for x in f.read_text(encoding="utf-8").splitlines():
        b = json.loads(x)
        ikut_id[b["id"]] = b["spans"]
    ids = [d["id"] for d in dokumen]
    if set(ikut_id) != set(ids) or len(ikut_id) != len(ids):
        raise ValueError(f"{f}: id ramalan tidak sepadan dengan split {split} ({len(ikut_id)} lawan {len(ids)} dokumen)")
    return [ikut_id[i] for i in ids]


def _pd(a: argparse.Namespace) -> dict:
    return {"_pradaftar": a.pradaftar} if getattr(a, "pradaftar", None) else {}


def statistik(a: argparse.Namespace) -> dict:
    from mypii.nilai import (
        statistik as st,  # import lewat: statistik.py mengimport modul ini (harness.skor)
    )

    dokumen = _dokumen(a.split)
    ramalan = {s: baca_ramalan(a.keluar, a.split, s, dokumen) for s in senarai_sistem(a.sistem)}
    v2 = konfig.utama()["nilai"]["statistik"]["v2"]
    if a.split in v2["split"]:   # PRA-DAFTAR v2: Holm = hipotesis H4a/H4b; selain itu deskriptif (eksplorasi)
        eks = set(ramalan) - {x["sistem"] for x in v2["hipotesis"].values()} - {konfig.utama()["nilai"]["statistik"]["rujukan"]}
        h = {"split": a.split, **st.jalankan(dokumen, ramalan, eksplorasi=eks), **_pd(a)}
        from mypii.nilai import statistik_v2
        h["v2"] = statistik_v2.h4(h, dokumen, ramalan)
    else:
        h = {"split": a.split, **st.jalankan(dokumen, ramalan), **_pd(a)}
    (a.keluar / f"{a.split}-statistik.json").write_text(json.dumps(h, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(st.jadual_md(h))
    if "v2" in h:
        from mypii.nilai import statistik_v2
        print("\n" + statistik_v2.jadual_md(h["v2"]))
    return h


def nilai(a: argparse.Namespace) -> dict:
    dokumen = _dokumen(a.split)
    a.keluar.mkdir(parents=True, exist_ok=True)
    semua = {}
    for s in senarai_sistem(a.sistem):
        r = ramal(s, dokumen)
        simpan_ramalan(a.keluar, a.split, s, dokumen, r)
        semua[s] = skor(dokumen, r)
        if s == "pii-guard":  # tiada SSM: `*` juga atas entiti yang ia sokong sahaja
            semua["pii-guard (disokong)"] = skor(garis.gold_disokong(dokumen), r)
    for s, h in semua.items():
        (a.keluar / nama_fail(a.split, s.replace(" (disokong)", "-disokong"))).write_text(json.dumps({**h, **_pd(a)}, indent=2) + "\n")
    print("| sistem | entiti | P tepat | R tepat | F1 tepat | F1 separa |\n|---|---|---|---|---|---|")
    for s, h in semua.items():
        for kunci, b in h.items():
            if kunci.startswith("semua|"):
                print(f"| {s} | {kunci[6:]} | {b['tepat']['p']} | {b['tepat']['r']} | {b['tepat']['f1']} | {b['separa']['f1']} |")
    return semua


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--split", default="dev")
    p.add_argument("--sistem", nargs="+", default=["mypii", "presidio-asal"])
    p.add_argument("--keluar", type=Path, default=AKAR / "hasil")
    p.add_argument("--benarkan-ujian", action="store_true")
    p.add_argument("--iterasi", metavar="STATUS", help="catat satu baris hasil/iterasi.tsv (config nilai.iterasi.status)")
    p.add_argument("--keterangan", default="", help="keterangan baris iterasi (hipotesis/perubahan)")
    p.add_argument("--statistik", action="store_true", help="selang bootstrap + ujian berpasangan dari ramalan tersimpan")
    a = p.parse_args()
    if a.split in konfig.utama()["nilai"]["split_dikunci"] and not a.benarkan_ujian:
        print(f"split {a.split} dikunci — guna --benarkan-ujian (manusia sahaja, sekali sebelum terbit)", file=sys.stderr)
        return 2
    a.pradaftar = None
    if a.split in konfig.utama()["nilai"]["split_dikunci"]:
        try:  # SEBELUM fail split dibaca
            a.pradaftar = pradaftar.semak(AKAR)
            pradaftar.semak_pindaan(AKAR, a.split)  # v3: ujian3 menuntut pindaan v2 (P2 + P13) dalam HEAD
        except pradaftar.Ditolak as e:
            print(f"split {a.split} ditolak: {e}", file=sys.stderr)
            return 2
        print(f"pra-daftar {a.pradaftar['fail']} @ komit {a.pradaftar['komit']} (blob {a.pradaftar['blob']})", file=sys.stderr)
    if a.statistik:
        if a.iterasi is not None:
            print("--statistik tidak menilai semula — jangan gabung dengan --iterasi", file=sys.stderr)
            return 2
        statistik(a)
        return 0
    if a.iterasi is None:
        nilai(a)
        return 0
    ki = konfig.utama()["nilai"]["iterasi"]
    if a.iterasi not in ki["status"] or a.iterasi == "crash":
        print(f"--iterasi {a.iterasi!r} tidak sah — pilih {[x for x in ki['status'] if x != 'crash']}", file=sys.stderr)
        return 2
    try:
        semua = nilai(a)
    except Exception as e:  # crash tetap direkod (corak results.tsv), kemudian gagal seperti biasa
        ralat = f"{type(e).__name__}: {e}"  # baris terakhir traceback
        iterasi.catat("crash", f"{ralat} ({a.keterangan})" if a.keterangan else ralat, split=a.split)
        raise
    b = semua.get(ki["sistem_f1"], {}).get(ki["kunci_f1"])
    iterasi.catat(a.iterasi, a.keterangan, b["tepat"]["f1"] if b else None, split=a.split)
    return 0

if __name__ == "__main__":
    sys.exit(main())
