"""Laporan v2.1 `docs/BANDINGAN-V21.md` (PELAN-V21 P10) — DIJANA, bait sama setiap larian (`make bandingan-v21`).

Sumber angka (tiada rangkaian, tiada pengecam dijalankan): arkib ujian4 dalam repo (`bandingan_v21.arkib_ujian4`: RINGKASAN.json,
hasil/v21/ujian4-h5.json, ramalan harness + model luar), `hasil/v21/` (dev, dev3, dev3-h5, ayat-biasa, analisis-v2/v21), `hasil/dev-*.json`
(v1/v2 lama, tidak disentuh). Pecahan = `harness.skor`; kategori b–e = `bandingan_v2.kategori`; U1 = `luar._kelas`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mypii import konfig
from mypii.nilai import harness, luar
from mypii.nilai.bandingan_v2 import kategori
from mypii.nilai.statistik import _selang, f1_sampel, indeks_bootstrap

AKAR = konfig.AKAR


def _k() -> dict:
    return konfig.utama()["bandingan_v21"]


def _f1(skor: dict, kunci: str):
    return (skor.get(kunci) or {}).get("tepat", {}).get("f1")


def _p(x) -> str:
    return "< 0.001" if x == 0 else str(x)


def _baca(f: Path):
    return json.loads(f.read_text(encoding="utf-8"))


def _ram_luar(folder: Path, split: str, model: str, dokumen: list[dict]) -> list[list[dict]]:
    baris = {r["id"]: r for r in map(json.loads, (folder / f"{split}-{model}.jsonl").read_text(encoding="utf-8").splitlines())}
    return [[{"mula": s["mula"], "tamat": s["tamat"], "entiti": luar.PETA[model][s["label"]]}
             for s in baris[d["id"]]["spans"] if s["label"] in luar.PETA[model]] for d in dokumen]


def _ci(dokumen, ramalan, kunci="semua|*") -> dict:
    kk = konfig.utama()["nilai"]["statistik"]
    s = f1_sampel(dokumen, ramalan, indeks_bootstrap(len(dokumen), kk["ulangan"], kk["benih"]), [kunci])[kunci]
    return _selang(s, kk["aras"], kk["perpuluhan"])


def jana(arkib: Path) -> str:
    k, v21 = _k(), konfig.utama()["nilai"]["statistik"]["v21"]
    nama, sistem, model_luar = k["nama"], k["sistem"], k["luar"]
    hv = AKAR / v21["keluar"]
    rg = _baca(arkib / "RINGKASAN.json")
    h4, hd3 = _baca(arkib / "hasil/v21/ujian4-h5.json"), _baca(hv / "dev3-h5.json")
    dok = {s: harness._dokumen(s) for s in ("dev3", "ujian4")}
    folder = {"dev3": hv, "ujian4": arkib / "hasil/v21"}
    ram = {sp: {s: harness.baca_ramalan(folder[sp], sp, s, dok[sp]) for s in sistem} for sp in dok}
    skor = {sp: {s: harness.skor(dok[sp], ram[sp][s]) for s in sistem} for sp in dok}
    luar_f = {"dev3": AKAR / "hasil/luar", "ujian4": arkib / "hasil/luar"}
    ram_l = {sp: {m: _ram_luar(luar_f[sp], sp, m, dok[sp]) for m in model_luar} for sp in dok}
    o = ["# MyPII v2.1: ujian4 dimeterai (penjana keluarga baharu) + bandingan", "",
         "<!-- DIJANA oleh `make bandingan-v21` (mypii/nilai/bandingan_v21.py); jangan sunting tangan. -->", "",
         (f"ujian4 dibuka sekali (sha `{rg['sha'][:7]}`, {rg['dokumen']} dokumen; templat + nama oleh Qwen3.8-27B-FP8 dihos sendiri, "
          "keluarga yang tidak pernah menghasilkan data atau keputusan dalam kajian ini). Pra-daftar: PRA-DAFTAR pindaan 2026-11-14 (b) + (c), "
          "dikomit sebelum ujian4 dijana; pengecam v2.1 = tag `mypii-v21-beku`. dev3 = set penalaan (deskriptif)."), "",
         "## 1. Keputusan utama (ujian4, F1 tepat mikro `semua|*`, CI bootstrap 95%)", "",
         "| sistem | F1 ujian4 | CI 95% | F1 dev3 | jurang dev3 → ujian4 |", "|---|---|---|---|---|"]
    for s in sistem:
        f4, fd = _f1(skor["ujian4"][s], "semua|*"), _f1(skor["dev3"][s], "semua|*")
        c = _ci(dok["ujian4"], ram["ujian4"][s])
        o.append(f"| {nama[s]} | **{f4}** | [{c['bawah']}, {c['atas']}] | {fd} | {round(f4 - fd, 4):+} |")
    o += ["", f"## 2. Hipotesis pra-daftar H5 (Holm k = {h4['k']}, α = {h4['alfa']} sehala)", "",
          "| hipotesis | lawan | metrik | δ | F1 v2.1 | F1 lawan | ΔF1 [CI 95%] | p Holm (bootstrap) | p rawak (×k) | keputusan |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for n, x in [*h4["hipotesis"].items(), *h4["susulan"].items()]:
        kep = ("disokong" if x["disokong"] else "tidak diuji (induk tidak disokong)" if x.get("diuji") is False else "tidak disokong")
        ph = _p(x["p_holm_bootstrap"]) if "p_holm_bootstrap" in x else f"{_p(x['p_bootstrap'])} (α penuh)"
        pr = f"{x['p_rawak']}" + (f" ({x['p_rawak_bonferroni']})" if "p_rawak_bonferroni" in x else "") + \
            ("" if x["rawak_syarat"] else " deskriptif")
        o.append(f"| {n} | {nama.get(x['sistem'], x['sistem'])} | {x['metrik']} | {x['margin']:g} | {x['f1_mypii']} | {x['f1_lawan']} | "
                 f"{x['delta']:+} [{x['bawah']}, {x['atas']}] | {ph} | {pr} | {kep}"
                 f"{' (beza kecil)' if x['beza_kecil'] and x['disokong'] and not x['margin'] else ''} |")
    o += ["", "Kuasa (dari dev3, sebelum ujian4 dijana): " + "; ".join(
        f"{n} MDE {x['kuasa']['mde_ketat']}" for n, x in hd3["hipotesis"].items()) + ".", "",
          "## 3. Model PII luar (U1 = ID ∪ telefon, F1 tepat; NRIC ketat = emas MyKad sahaja)", "",
          "| sistem | split | U1 F1 [CI] | ID | telefon | NRIC ketat |", "|---|---|---|---|---|---|"]
    for sp in ("ujian4", "dev3"):
        u1d = [{**d, "spans": luar._kelas(d["spans"])} for d in dok[sp]]
        semua = {s: ram[sp][s] for s in ("mypii", "mypii-v2")} | ram_l[sp]
        for s, r in semua.items():
            rk = [luar._kelas(x) for x in r]
            su = harness.skor(u1d, rk)
            c = _ci(u1d, rk)
            nk = [luar._nric_ketat(d, x) for d, x in zip(dok[sp], r)]
            sn = harness.skor([a for a, _ in nk], [b for _, b in nk])
            o.append(f"| {nama.get(s, nama.get('luar:' + s, s))} | {sp} | {_f1(su, 'semua|*')} [{c['bawah']}, {c['atas']}] | "
                     f"{_f1(su, 'semua|ID')} | {_f1(su, 'semua|TEL')} | {_f1(sn, 'semua|N')} |")
    o += ["", "## 4. Setiap entiti (F1 tepat)", "", "| sistem | split | " + " | ".join(k["entiti"]) + " |",
          "|---|---|" + "---|" * len(k["entiti"])]
    for s in sistem:
        for sp in ("ujian4", "dev3"):
            o.append(f"| {nama[s]} | {sp} | " + " | ".join(str(_f1(skor[sp][s], f"semua|{e}")) for e in k["entiti"]) + " |")
    o += ["", "## 5. Setiap kategori v3 (ujian4)", "",
          "(b)–(d): recall span tepat bagi span emas yang bertindih kategori. (e): ramalan atas nombor negatif 12 digit (lebih rendah lebih baik).",
          "", "| sistem | (b) LLP | (c) Sabah/Sarawak | (d) OCR/patah baris | (e) FP / kawasan |", "|---|---|---|---|---|"]
    for s in sistem:
        c = kategori(dok["ujian4"], ram["ujian4"][s])
        sel = [f"{c[x]['recall']} ({c[x]['betul']}/{c[x]['emas']})" if x in c else "-" for x in "bcd"]
        e = f"{c['e']['fp']} / {c['e']['kawasan']}" if "e" in c else "-"
        o.append(f"| {nama[s]} | " + " | ".join(sel) + f" | {e} |")
    o += ["", "## 6. Setiap bahasa (ujian4, F1 tepat `*`)", "", "| sistem | " + " | ".join(k["bahasa"]) + " |",
          "|---|" + "---|" * len(k["bahasa"])]
    for s in sistem:
        o.append(f"| {nama[s]} | " + " | ".join(str(_f1(skor["ujian4"][s], f"bahasa:{b}|*")) for b in k["bahasa"]) + " |")
    o += ["", "## 7. Pembangunan v2.1 (bukan dakwaan: set penalaan + bahan sesi)", ""]
    dev = {s: _baca(f) for s, f in (("v2.1", hv / "dev-mypii.json"), ("v2 (1.0.2)", AKAR / "hasil/dev-mypii.json"),
                                    ("v1", AKAR / "hasil/dev-mypii-v1.json"))}
    o.append("- `dev` (gaya v1) F1 `*`: " + ", ".join(f"{s} {_f1(x, 'semua|*')}" for s, x in dev.items()) + ".")
    ab = _baca(hv / "ayat-biasa.json")
    o.append("- Ayat biasa (`data/probe/ayat_biasa.yaml`): " + "; ".join(
        f"{nama[s]} positif {x['positif_ditanda']}/{x['positif']}, negatif tersalah tanda {x['negatif_ditanda']}/{x['negatif']}"
        for s, x in ab.items()) + ".")
    an = {v: {kk: x for kk, x in _baca(hv / f"analisis-{v}.json")["probe"].items()} for v in ("v2", "v21")}
    o += ["- Probe luar bench `make analisis` (alat analisis A3 P3, tidak ditala):", "",
          "| probe | emas | v2 (1.0.2) betul / ramal | v2.1 betul / ramal |", "|---|---|---|---|"]
    for kat in sorted(an["v21"]):
        a2, a21 = an["v2"][kat], an["v21"][kat]
        o.append(f"| {kat} | {a21['emas']} | {a2['tepat']} / {a2['ramal']} | {a21['tepat']} / {a21['ramal']} |")
    o += ["", "## 8. Panggilan LLM dan kos", ""]
    for s, x in sorted(rg["llm"].items()):
        o.append(f"- {nama.get(s, s)} ujian4: {x['panggilan']} panggilan, {x['gagal']} gagal, {x['rosak']} jawapan rosak.")
    o.append(f"- Lejar Anthropic selepas ujian4 (arkib): USD {rg['lejar_usd_selepas']}; had keras USD 20 tidak dinaikkan.")
    o += ["", "## 9. Had kajian (lapor bersama setiap angka)", ""] + [f"{i}. {t}" for i, t in enumerate(k["had"], 1)]
    hh = h4["hipotesis"]
    o += ["", "## English summary", "", k["ringkasan_en"].format(
        v21=_f1(skor["ujian4"]["mypii"], "semua|*"), v2=_f1(skor["ujian4"]["mypii-v2"], "semua|*"),
        haiku=_f1(skor["ujian4"][k["haiku"]], "semua|*"), da=hh["H5a"]["delta"], db=hh["H5b"]["delta"], dc=hh["H5c"]["delta"],
        dd=hh["H5d"]["delta"], sok=", ".join(n for n, x in [*hh.items(), *h4["susulan"].items()] if x["disokong"]) or "none"), ""]
    return "\n".join(o)


def main() -> int:
    teks = jana(AKAR / Path(_k()["arkib_ujian4"]))
    (AKAR / _k()["laporan"]).write_text(teks, encoding="utf-8")
    print(f"{_k()['laporan']}: {len(teks)} aksara")
    return 0


if __name__ == "__main__":
    sys.exit(main())
