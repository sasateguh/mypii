"""Garis dasar pesaing untuk harness (PELAN-B B3, ADR-011): `pii-guard` dan `llm:<model>` sifar-tembak.

pii-guard: enjin `malaysia_pii_guard` (extra `garis`) dengan ambang skor yang sama seperti sistem lain; pertindihan diselesaikan oleh
`resolve()` pustaka itu sendiri (cara ia memutuskan semasa menyamarkan), kemudian jenis entiti dipeta ke entiti MyPII.

llm: prompt tetap dari config; jawapan JSON `[{teks, entiti}]` → span = SEMUA kejadian `teks` tepat dalam dokumen. Jawapan mentah
disimpan dalam cache (kunci sha256 model+prompt+teks) sebelum diurai, jadi larian semula tidak memerlukan rangkaian; jawapan yang tidak
boleh diurai = tiada ramalan untuk dokumen itu dan dikira (`rosak`).

Model `anthropic/<id>` (PELAN-CLAUDE, ADR-016) dihala ke API Anthropic terus (`klien_anthropic`), bukan 9router: kunci cache juga
memuatkan parameter permintaan, dan setiap panggilan ditempah dahulu dalam lejar belanja (had keras config).
"""

import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path

from mypii import klien_anthropic, klien_llm, konfig

# Modul lain (probe_llm) menyentuh Anthropic MELALUI garis sahaja — gerbang autopilot §17 hanya membenarkan import klien di sini.
ialah_anthropic = klien_anthropic.ialah
TolakAPI = klien_anthropic.TolakAPI


def _k() -> dict:
    return konfig.utama()["garis_dasar"]


def ramal_pii_guard(dokumen: list[dict], enjin=None, selesai=None) -> list[list[dict]]:
    nilai = konfig.utama()["nilai"]
    if enjin is None:
        from malaysia_pii_guard import AnalyzerEngine
        from malaysia_pii_guard.anonymizer import resolve

        enjin, selesai = AnalyzerEngine(score_threshold=nilai["ambang_skor"]), resolve
    peta = _k()["pii_guard"]["peta"]
    hasil = []
    for d in dokumen:
        spans = []
        for x in selesai(enjin.analyze(d["teks"], score_threshold=nilai["ambang_skor"])):
            e = peta.get(x.entity_type)
            if e in nilai["entiti"]:
                spans.append({"mula": x.start, "tamat": x.end, "entiti": e})
        hasil.append(sorted(spans, key=lambda s: (s["mula"], s["tamat"], s["entiti"])))
    return hasil


def gold_disokong(dokumen: list[dict]) -> list[dict]:
    """Salinan dokumen dengan span emas entiti yang pii-guard sokong SAHAJA (laporan `*` adil untuk sistem tanpa SSM)."""
    sokong = set(_k()["pii_guard"]["entiti_disokong"])
    return [d | {"spans": [s for s in d["spans"] if s["entiti"] in sokong]} for d in dokumen]


def kunci_cache(model: str, prompt: str, teks: str, permintaan: dict | None = None) -> str:
    """Tanpa `permintaan` = kunci asal (cache 9router kekal sah); dengan = parameter berubah tidak memakai jawapan lama."""
    x = [model, prompt, teks] if permintaan is None else [model, prompt, json.dumps(permintaan, sort_keys=True), teks]
    return hashlib.sha256(json.dumps(x, ensure_ascii=False).encode()).hexdigest()


def kunci_dok(model: str, teks: str) -> str:
    """Kunci cache satu dokumen untuk model garis dasar (termasuk parameter permintaan bagi `anthropic/`)."""
    permintaan = klien_anthropic.tetapan(model)["permintaan"] if klien_anthropic.ialah(model) else None
    return kunci_cache(model, _k()["llm"]["prompt"], teks, permintaan)


def fail_cache(model: str, akar: Path = konfig.AKAR) -> Path:
    return akar / _k()["llm"]["cache"] / (re.sub(r"[^A-Za-z0-9._-]+", "_", model) + ".jsonl")


def _muat_cache(laluan: Path) -> dict[str, str]:
    if not laluan.exists():
        return {}
    cache = {}
    for x in laluan.read_text(encoding="utf-8").splitlines():
        try:  # baris terakhir boleh terpotong bila larian dihentikan semasa menulis
            b = json.loads(x)
        except json.JSONDecodeError:
            continue
        cache[b["kunci"]] = b["jawapan"]
    return cache


def _tulis_cache(laluan: Path, cache: dict[str, str]) -> None:
    laluan.parent.mkdir(parents=True, exist_ok=True)
    teks = "".join(json.dumps({"kunci": k, "jawapan": cache[k]}, ensure_ascii=False) + "\n" for k in sorted(cache))
    laluan.write_text(teks, encoding="utf-8")


def span_dari_jawapan(teks: str, jawapan: str) -> list[dict] | None:
    """None = jawapan rosak (bukan senarai JSON). Item tanpa medan sah / entiti di luar senarai diabaikan."""
    try:
        x = klien_llm.json_dari(jawapan)
    except ValueError:
        return None
    if not isinstance(x, list):
        return None
    entiti = set(konfig.utama()["nilai"]["entiti"])
    spans = set()
    for item in x:
        if not isinstance(item, dict):
            continue
        t, e = item.get("teks"), item.get("entiti")
        if not isinstance(t, str) or not t or e not in entiti:
            continue
        for m in re.finditer(re.escape(t), teks):
            spans.add((m.start(), m.end(), e))
    return [{"mula": a, "tamat": b, "entiti": e} for a, b, e in sorted(spans)]


def ramal_llm(model: str, dokumen: list[dict], hantar=klien_llm.hantar_9router, akar: Path = konfig.AKAR) -> tuple[list, dict]:
    """Pulang (ramalan, statistik). Panggilan hanya untuk dokumen yang tiada dalam cache; setiap jawapan ditambah serta-merta, dan
    cache ditulis semula tersusun ikut kunci di hujung (bait sama tanpa mengira susunan siap)."""
    k = _k()["llm"]
    if model not in k["model"] and model not in k.get("eksplorasi", []):  # eksplorasi: probe + larian dev sebelum masuk `model` (P6)
        raise SystemExit(f"model {model} bukan garis dasar yang disenarai (config garis_dasar.llm.model / eksplorasi)")
    laluan = fail_cache(model, akar)
    cache = _muat_cache(laluan)
    kunci = [kunci_dok(model, d["teks"]) for d in dokumen]
    hilang = {kc: d["teks"] for kc, d in zip(kunci, dokumen) if kc not in cache}
    gagal, lejar = [], None
    if hilang:
        if hantar is klien_llm.hantar_9router:
            os.nice(konfig.utama()["llm"]["nice"])

        def satu(item):
            kc, teks = item
            try:
                return kc, klien_llm.tanya([model], k["prompt"].replace("{teks}", teks), k["suhu"], urai=str, hantar=hantar)[1]
            except klien_llm.GagalLLM as e:
                return kc, e

        if klien_anthropic.ialah(model):
            lejar = klien_anthropic.Lejar.dari_config(akar)
            satu = _satu_anthropic(model, k["prompt"], lejar,
                                   klien_anthropic.hantar if hantar is klien_llm.hantar_9router else hantar)

        f = None
        with ExitStack() as tindan, ThreadPoolExecutor(max_workers=konfig.utama()["llm"]["serentak"]) as ex:
            for kc, j in ex.map(satu, hilang.items()):  # tambah serta-merta: larian terputus disambung dari cache
                if isinstance(j, Exception):
                    gagal.append(str(j))
                    continue
                if f is None:  # dibuka MALAS: tiada jawapan = tiada fail baharu (bandingan luar talian, tree kekal bersih)
                    laluan.parent.mkdir(parents=True, exist_ok=True)
                    f = tindan.enter_context(open(laluan, "a", encoding="utf-8"))
                cache[kc] = j
                f.write(json.dumps({"kunci": kc, "jawapan": j}, ensure_ascii=False) + "\n")
                f.flush()
        if f is not None:
            _tulis_cache(laluan, cache)
    ramalan, rosak = [], 0
    for kc, d in zip(kunci, dokumen):
        s = span_dari_jawapan(d["teks"], cache[kc]) if kc in cache else None
        rosak += s is None and kc in cache
        ramalan.append(s or [])
    st = {"dokumen": len(dokumen), "dari_cache": len(dokumen) - len(hilang), "panggilan": len(hilang),
          "gagal": len(gagal), "rosak": rosak}
    if lejar is not None:
        st |= {"usd": round(lejar.usd_larian, 6), "jumlah_usd": lejar.data["jumlah_usd"], "had_dicapai": lejar.dicapai}
        if lejar.dicapai:
            print(f"{model}: had belanja USD {lejar.had:g} dicapai — panggilan selebihnya TIDAK dibuat", file=sys.stderr)
    if gagal:  # jenis ralat sahaja (nama kelas / mesej klien — tiada teks dokumen, tiada kunci); tiada kunci bila 0 = output lama sama
        st["ralat"] = sorted(set(gagal))
        print(f"{model}: {len(gagal)} panggilan gagal (tiada dalam cache; jalankan semula) — {gagal[0]}", file=sys.stderr)
    return ramalan, st


def _satu_anthropic(model: str, prompt: str, lejar: "klien_anthropic.Lejar", hantar):
    """Penghantar satu dokumen untuk `anthropic/`: tempah kos terburuk → panggil (`hantar(id, prompt, permintaan)` → (teks, usage))
    → rekod kos sebenar. Had dicapai / gagal = Exception dipulangkan (dokumen itu gagal, tiada dalam cache). `TolakAPI` dibangkitkan."""
    t = klien_anthropic.tetapan(model)

    def satu(item):
        kc, teks = item
        p = prompt.replace("{teks}", teks)
        usd = klien_anthropic.kos_terburuk(p, t)
        if lejar.henti:
            return kc, klien_llm.GagalLLM(f"{model}: dihentikan selepas API menolak permintaan")
        if not lejar.tempah(usd):
            return kc, klien_anthropic.HadDicapai(f"had belanja USD {lejar.had:g} dicapai")
        try:
            jawapan, usage = hantar(t["id"], p, t["permintaan"])
        except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
            lejar.lepas(usd)
            return kc, klien_llm.GagalLLM(f"{model}: {type(e).__name__}")
        except BaseException:
            lejar.lepas(usd)
            lejar.henti = True
            raise
        lejar.rekod(model, usage, t["harga"], usd)
        return kc, jawapan

    return satu
