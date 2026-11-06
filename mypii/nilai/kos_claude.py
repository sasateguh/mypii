"""Anggaran kos garis dasar Claude SEBELUM larian (PELAN-CLAUDE P3, ADR-016) — `make kos-claude`.

Token MASUK = sebenar dari `messages.count_tokens` (percuma, tiada penjanaan) untuk setiap dokumen split × setiap model `anthropic/`
dalam `garis_dasar.llm.model`, dengan prompt dan `parameter` yang SAMA seperti larian (`klien_anthropic.tetapan`). Token KELUAR belum
boleh diukur tanpa memanggil model → dianggar dari panjang jawapan cache LLM sedia ada (9router) bagi dokumen yang sama:
`jangka` = median aksara, `atas` = maksimum aksara (÷ `aksara_setiap_token`, dibundar ke atas), `terburuk` = `max_tokens` penuh.

Split yang dibenarkan = config `garis_dasar.llm.anthropic.kos.split` (dev sahaja); split dalam `nilai.split_dikunci` ditolak SEBELUM
fail dibaca. Output `hasil/<split>-kos-claude.json` = kiraan + USD sahaja (tiada teks, tiada kunci). Exit 3 bila jumlah terburuk
melepasi baki had lejar (pemilik memilih: kurangkan model atau naikkan had).

`--rancang` (PRA-DAFTAR pindaan 2026-11-03, PELAN-MODEL-LAIN P5, ADR-017): calon Claude EKSPLORASI yang lulus probe
(`hasil/<split>-probe-llm.json`). Satu split = token masuk `count_tokens` × harga masuk + purata token keluar SEBENAR setiap panggilan
(lejar, dari probe) × dokumen × `kos.margin` × harga keluar. Perlu = Σ Claude pengesahan (2 × USD lejar dev: ujian + ujian2) + Σ calon
(3 × satu split − belanja probe). Perlu > baki lejar → gugur ikut `kos.gugur` (config), kira semula; had TIDAK dinaikkan. Ditulis sebagai
blok `kos.blok_rancang` dalam fail kos yang sama (`dipilih`, `digugurkan` + sebab, `perlu_ujian_usd` = ujian + ujian2 SEMUA Claude yang
akan dijalankan — dibaca skrip ujian muktamad). Exit 3 bila set pengesahan sahaja pun tidak muat.
"""

import argparse
import json
import math
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from mypii import klien_anthropic, konfig
from mypii.nilai import garis

KELUAR_MELEPASI = 3


def _k() -> dict:
    return konfig.utama()["garis_dasar"]["llm"]


def model_anthropic() -> list[str]:
    return [m for m in _k()["model"] if klien_anthropic.ialah(m)]


def semak_split(split: str) -> None:
    if split in konfig.utama()["nilai"]["split_dikunci"] or split not in _k()["anthropic"]["kos"]["split"]:
        raise SystemExit(f"split {split}: anggaran kos Claude hanya untuk {_k()['anthropic']['kos']['split']} (split dikunci ditolak)")


def kira_token_api(model_id: str, prompt: str, parameter: dict) -> int:
    """`messages.count_tokens` (SDK rasmi, import malas). Mesej ralat tidak memuatkan kunci atau prompt."""
    a = _k()["anthropic"]
    kunci = os.environ.get(a["env_kunci"])
    if not kunci:
        raise SystemExit(f"env {a['env_kunci']} tiada — `set -a; . ~/ops/mypii/anthropic.env; set +a` dahulu")
    import anthropic  # selepas semakan kunci: mesej jelas walaupun extra `garis` tiada (CI)

    try:
        r = klien_anthropic._klien(kunci, a["had_masa_saat"], a["ulang_sdk"]).messages.count_tokens(
            model=model_id, messages=[{"role": "user", "content": prompt}], **parameter)
    except anthropic.RateLimitError as e:
        raise OSError(f"RateLimitError {e.status_code}") from None
    except anthropic.APIStatusError as e:
        if e.status_code < 500 and e.status_code not in (408, 409):
            raise klien_anthropic.TolakAPI(f"{model_id}: HTTP {e.status_code} {type(e).__name__}: {e.message}") from None
        raise OSError(f"{type(e).__name__} {e.status_code}") from None
    except anthropic.APIConnectionError as e:
        raise OSError(type(e).__name__) from None
    return r.input_tokens


def _dengan_ulang(kira, model_id: str, prompt: str, parameter: dict, kos: dict, tidur=time.sleep) -> int:
    """Ralat sementara (OSError) diulang `kos.ulang` kali dengan jeda linear; `TolakAPI` terus dibangkitkan."""
    for cubaan in range(kos["ulang"] + 1):
        try:
            return kira(model_id, prompt, parameter)
        except OSError:
            if cubaan == kos["ulang"]:
                raise
            tidur(kos["jeda_saat"] * (cubaan + 1))
    raise AssertionError("tidak tercapai")


def panjang_jawapan_sedia(dokumen: list[dict], akar: Path = konfig.AKAR) -> list[int]:
    """Aksara jawapan cache LLM bukan-Anthropic PENGESAHAN bagi dokumen INI sahaja (kunci model+prompt+teks) — asas anggaran token
    keluar. Model eksplorasi (`garis_dasar.llm.eksplorasi`, masuk `model` pada PELAN-MODEL-LAIN P6) TIDAK dikira: asas kekal seperti P3."""
    n, eks = [], set(_k().get("eksplorasi") or [])
    for m in _k()["model"]:
        if klien_anthropic.ialah(m) or m in eks:
            continue
        cache = garis._muat_cache(garis.fail_cache(m, akar))
        n += [len(cache[kc]) for kc in (garis.kunci_dok(m, d["teks"]) for d in dokumen) if kc in cache]
    return n


def _token_masuk(model: str, dokumen: list[dict], kira, tidur) -> list[int]:
    """Token masuk SEBENAR setiap dokumen (prompt + parameter sama seperti larian; `max_tokens` tidak diterima count_tokens)."""
    t, kos = klien_anthropic.tetapan(model), _k()["anthropic"]["kos"]
    parameter = {x: v for x, v in t["permintaan"].items() if x != "max_tokens"}
    prompts = [_k()["prompt"].replace("{teks}", d["teks"]) for d in dokumen]
    with ThreadPoolExecutor(max_workers=kos["serentak"]) as ex:
        return list(ex.map(lambda p: _dengan_ulang(kira, t["id"], p, parameter, kos, tidur), prompts))


def anggar(dokumen: list[dict], split: str, kira=kira_token_api, lejar: klien_anthropic.Lejar | None = None,
           akar: Path = konfig.AKAR, tidur=time.sleep) -> dict:
    a = _k()["anthropic"]
    nisbah = a["aksara_setiap_token"]
    lejar = lejar or klien_anthropic.Lejar.dari_config(akar)
    panjang = panjang_jawapan_sedia(dokumen, akar)
    if not panjang:
        raise SystemExit("tiada jawapan cache LLM sedia ada untuk dokumen split ini — token keluar tidak boleh dianggar")
    keluar = {"jangka": math.ceil(statistics.median(panjang) / nisbah), "atas": math.ceil(max(panjang) / nisbah),
              "terburuk": a["max_tokens"]}
    hasil = {"split": split, "dokumen": len(dokumen), "model": {},
             "keluar_setiap_dokumen": {**keluar, "asas_jawapan": len(panjang), "aksara_median": statistics.median(panjang),
                                       "aksara_maks": max(panjang), "aksara_setiap_token": nisbah}}
    for m in model_anthropic():
        t = klien_anthropic.tetapan(m)
        masuk = _token_masuk(m, dokumen, kira, tidur)
        jm = sum(masuk)
        hasil["model"][m] = {
            "token_masuk": jm, "token_masuk_median": statistics.median(masuk), "token_masuk_maks": max(masuk),
            **{f"usd_{x}": round(klien_anthropic.kos({"masuk": jm, "keluar": n * len(dokumen)}, t["harga"]), 6)
               for x, n in keluar.items()},
            "harga": t["harga"]}
    jum = {x: round(sum(v[f"usd_{x}"] for v in hasil["model"].values()), 6) for x in keluar}
    baki = round(lejar.had - lejar.data["jumlah_usd"], 6)
    hasil |= {"jumlah_usd": jum, "had_usd": lejar.had, "lejar_usd": lejar.data["jumlah_usd"], "baki_usd": baki,
              "muat_terburuk": jum["terburuk"] <= baki}
    return hasil


def rancang(dokumen: list[dict], probe: dict, kira=kira_token_api, lejar: klien_anthropic.Lejar | None = None,
            akar: Path = konfig.AKAR, tidur=time.sleep) -> dict:
    """Blok `rancang_eksplorasi` (lihat docstring modul). Tiada nilai model/margin/susunan dalam kod — semuanya config."""
    k, a = _k(), _k()["anthropic"]
    kos, eks = a["kos"], k.get("eksplorasi", [])
    lejar = lejar or klien_anthropic.Lejar.dari_config(akar)
    lm = lejar.data["model"]
    pengesahan = [m for m in model_anthropic() if m not in eks]
    calon = [m for m in eks if klien_anthropic.ialah(m)]
    digugurkan: dict[str, str] = {}
    for m in calon:
        v = probe["model"].get(m)
        if v is None or not v["lulus"]:
            digugurkan[m] = "probe: " + ("tidak diprobe" if v is None else "; ".join(v["jenis_ralat"]) or "tidak lulus")
    lama = {}
    for m in pengesahan:
        if m not in lm:
            raise SystemExit(f"{m}: tiada dalam lejar — larian dev garis dasar pengesahan belum dijalankan")
        lama[m] = round(2 * lm[m]["usd"], 6)
    model = {}
    for m in calon:
        if m in digugurkan:
            continue
        if not lm.get(m, {}).get("panggilan"):
            raise SystemExit(f"{m}: tiada panggilan dalam lejar — probe (`make probe-llm`) belum dijalankan dengan kunci")
        t, x = klien_anthropic.tetapan(m), lm[m]
        jm = sum(_token_masuk(m, dokumen, kira, tidur))
        purata = x["keluar"] / x["panggilan"]
        satu = (jm * t["harga"]["masuk"] + purata * len(dokumen) * kos["margin"] * t["harga"]["keluar"]) / 1e6
        model[m] = {"token_masuk": jm, "purata_keluar_probe": round(purata, 2), "usd_probe": x["usd"],
                    "usd_satu_split": round(satu, 6), "usd_perlu": round(3 * satu - x["usd"], 6), "harga": t["harga"]}
    baki = round(lejar.had - lejar.data["jumlah_usd"], 6)
    dipilih = list(model)

    def perlu(ds):
        return round(sum(lama.values()) + sum(model[d]["usd_perlu"] for d in ds), 6)

    for g in kos["gugur"]:
        if perlu(dipilih) <= baki:
            break
        if g in dipilih:
            digugurkan[g] = f"kos: perlu USD {perlu(dipilih)} > baki USD {baki}"
            dipilih.remove(g)
    return {"dipilih": dipilih, "digugurkan": digugurkan, "pengesahan_ujian_usd": lama, "model": model, "perlu_usd": perlu(dipilih),
            "perlu_ujian_usd": round(sum(lama.values()) + sum(2 * model[d]["usd_satu_split"] for d in dipilih), 6),
            "baki_usd": baki, "had_usd": lejar.had, "lejar_usd": lejar.data["jumlah_usd"], "margin": kos["margin"],
            "dokumen": len(dokumen), "muat": perlu(dipilih) <= baki}


def _tulis(fail: Path, h: dict) -> None:
    fail.parent.mkdir(parents=True, exist_ok=True)
    fail.write_text(json.dumps(h, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main_rancang(split: str) -> int:
    from mypii.nilai import probe_llm
    from mypii.nilai.harness import _dokumen  # dipanggil selepas semak_split

    fp = probe_llm.fail_hasil(split)
    if not fp.exists():
        raise SystemExit(f"{fp.relative_to(konfig.AKAR)} tiada — `make probe-llm` dahulu")
    r = rancang(_dokumen(split), json.loads(fp.read_text(encoding="utf-8")))
    fail = konfig.AKAR / _k()["anthropic"]["kos"]["fail"].format(split=split)
    h = json.loads(fail.read_text(encoding="utf-8")) if fail.exists() else {}
    h[_k()["anthropic"]["kos"]["blok_rancang"]] = r
    _tulis(fail, h)
    print(f"dipilih: {', '.join(r['dipilih']) or '—'}")
    for m, sebab in r["digugurkan"].items():
        print(f"digugurkan: {m} — {sebab}")
    print(f"perlu USD {r['perlu_usd']} (ujian+ujian2 {r['perlu_ujian_usd']}), baki {r['baki_usd']} → "
          f"{'MUAT' if r['muat'] else 'TIDAK MUAT'} ({fail.relative_to(konfig.AKAR)})")
    return 0 if r["muat"] else KELUAR_MELEPASI


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--split", default="dev")
    p.add_argument("--rancang", action="store_true", help="keputusan kos calon Claude eksplorasi (pindaan 2026-11-03)")
    a = p.parse_args(argv)
    semak_split(a.split)
    if a.rancang:
        return main_rancang(a.split)
    from mypii.nilai.harness import (
        _dokumen,  # selepas semak_split: split dikunci tidak pernah dibaca
    )

    h = anggar(_dokumen(a.split), a.split, kira=kira_token_api, akar=konfig.AKAR)
    fail = konfig.AKAR / _k()["anthropic"]["kos"]["fail"].format(split=a.split)
    blok = _k()["anthropic"]["kos"]["blok_rancang"]
    if fail.exists() and blok in (lama := json.loads(fail.read_text(encoding="utf-8"))):
        h[blok] = lama[blok]  # anggaran semula tidak memadam keputusan `--rancang`
    _tulis(fail, h)
    print("| model | token masuk | USD jangka | USD atas | USD terburuk |\n|---|---|---|---|---|")
    for m, v in h["model"].items():
        print(f"| {m} | {v['token_masuk']} | {v['usd_jangka']} | {v['usd_atas']} | {v['usd_terburuk']} |")
    j = h["jumlah_usd"]
    print(f"| jumlah | | {j['jangka']} | {j['atas']} | {j['terburuk']} |")
    print(f"had USD {h['had_usd']:g}, lejar {h['lejar_usd']}, baki {h['baki_usd']} → terburuk "
          f"{'MUAT' if h['muat_terburuk'] else 'MELEPASI baki'} ({fail.relative_to(konfig.AKAR)})")
    return 0 if h["muat_terburuk"] else KELUAR_MELEPASI


if __name__ == "__main__":
    sys.exit(main())
