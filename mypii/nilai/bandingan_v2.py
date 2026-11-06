"""Laporan v2 `docs/BANDINGAN-V2.md` (PELAN-V2 P16) — DIJANA, bait sama setiap larian (`make bandingan-v2`, 2× `cmp`).

Sumber angka (tiada rangkaian, tiada pengecam dijalankan):
- dev3: `hasil/dev3-statistik.json` (dikomit) + ramalan `hasil/ramalan/dev3-*.jsonl`;
- ujian3: `<arkib>/RINGKASAN.json` + ramalan `<arkib>/hasil/ramalan/ujian3-*.jsonl` (salinan arkib dalam repo `hasil/arkib/`, config `bandingan_v2.arkib_ujian3`).
Pecahan entiti × bahasa = `harness.skor`; kategori (b)–(e) = recall span emas yang bertindih kategori, (e) = ramalan bertindih (FP).
`docs/BANDINGAN.md` v1 TIDAK disentuh.
"""

import json
import sys
from pathlib import Path

from mypii import konfig
from mypii.nilai import harness

AKAR = konfig.AKAR


def _k() -> dict:
    return konfig.utama()["bandingan_v2"]


def _ramalan(folder: Path, split: str, sistem: str, dokumen: list[dict]) -> list[list[dict]]:
    return harness.baca_ramalan(folder, split, sistem, dokumen)


def _tindih(a0: int, a1: int, b0: int, b1: int) -> bool:
    return a0 < b1 and b0 < a1


def kategori(dokumen: list[dict], ramalan: list[list[dict]]) -> dict[str, dict]:
    """{kategori: {emas, betul, recall}} untuk (b)–(d) (span emas bertindih kategori, betul = span tepat diramal);
    (e) = {kawasan, fp} (ramalan bertindih kawasan negatif)."""
    out: dict[str, dict] = {}
    for d, r in zip(dokumen, ramalan):
        tepat = {(s["mula"], s["tamat"], s["entiti"]) for s in r}
        for k in d.get("kategori", []):
            c = out.setdefault(k["kategori"], {"emas": 0, "betul": 0, "kawasan": 0, "fp": 0})
            if k["kategori"] == "e":
                c["kawasan"] += 1
                c["fp"] += sum(1 for s in r if _tindih(s["mula"], s["tamat"], k["mula"], k["tamat"]))
                continue
            for s in d["spans"]:
                if _tindih(s["mula"], s["tamat"], k["mula"], k["tamat"]):
                    c["emas"] += 1
                    c["betul"] += (s["mula"], s["tamat"], s["entiti"]) in tepat
    for c in out.values():
        c["recall"] = round(c["betul"] / c["emas"], 4) if c["emas"] else None
    return dict(sorted(out.items()))


def _f1(skor: dict, kunci: str):
    return (skor.get(kunci) or {}).get("tepat", {}).get("f1")


def jana(arkib: Path) -> str:
    k = _k()
    sistem = k["sistem"]
    nama = k["nama"]
    rg = json.loads((arkib / "RINGKASAN.json").read_text(encoding="utf-8"))
    st3 = json.loads((AKAR / "hasil/dev3-statistik.json").read_text(encoding="utf-8"))
    dok = {s: harness._dokumen(s) for s in ("dev3", "ujian3")}
    folder = {"dev3": AKAR / "hasil", "ujian3": arkib / "hasil"}
    ram = {sp: {s: _ramalan(folder[sp], sp, s, dok[sp]) for s in sistem} for sp in dok}
    skor = {sp: {s: harness.skor(dok[sp], ram[sp][s]) for s in sistem} for sp in dok}
    ku = rg["kunci"]
    o = ["# MyPII v2: bandingan dev3 + ujian3", "",
         "<!-- DIJANA oleh `make bandingan-v2` (mypii/nilai/bandingan_v2.py); jangan sunting tangan. -->", "",
         (f"Ujian3 dibuka sekali (sha `{rg['sha'][:7]}`, {rg['dokumen']} dokumen, penjana templat B = Claude Sonnet 5.5). "
          "dev3 ialah set penalaan (penjana A = Nemotron, sama dengan latih3), jadi angka dev3 deskriptif dan dijangka optimis."), "",
         "## 1. Keputusan utama (ujian3, F1 tepat mikro `semua|*`, CI bootstrap 95%)", "",
         "| sistem | F1 ujian3 | CI 95% | F1 dev3 | jurang dev3 → ujian3 |", "|---|---|---|---|---|"]
    for s in sistem:
        f3, fd = rg["f1"][s], st3["sistem"][s][ku]["f1"]
        o.append(f"| {nama[s]} | **{f3['f1']}** | [{f3['bawah']}, {f3['atas']}] | {fd} | {round(f3['f1'] - fd, 4):+} |")
    o += ["", "## 2. Hipotesis pra-daftar (Holm k = 2, α = 0.05 sehala)", "",
          "| hipotesis | lawan | δ | ΔF1 | CI 95% | p Holm (bootstrap) | p rawak × 2 | keputusan |", "|---|---|---|---|---|---|---|---|"]
    for h, x in rg["hipotesis"].items():
        p = "< 0.001" if x["p_holm_bootstrap"] == 0 else x["p_holm_bootstrap"]
        rawak = f"{x['p_rawak_bonferroni']}" + ("" if x["rawak_syarat"] else " (deskriptif)")
        o.append(f"| {h} | {nama[x['sistem']]} | {x['margin']:g} | {x['delta']:+} | [{x['bawah']}, {x['atas']}] | {p} | {rawak} | "
                 f"{'disokong' if x['disokong'] else 'tidak disokong'}{' (beza kecil)' if x['beza_kecil'] else ''} |")
    o += ["", "## 3. Setiap entiti (F1 tepat)", "", "| sistem | split | " + " | ".join(k["entiti"]) + " |",
          "|---|---|" + "---|" * len(k["entiti"])]
    for s in sistem:
        for sp in ("ujian3", "dev3"):
            o.append(f"| {nama[s]} | {sp} | " + " | ".join(str(_f1(skor[sp][s], f"semua|{e}")) for e in k["entiti"]) + " |")
    o += ["", "## 4. Setiap kategori v3 (ujian3)", "",
          ("Kategori (a) ROB lama digugurkan (tiada sumber rasmi, pindaan 2026-11-04). (b)–(d): recall span tepat bagi span emas yang "
           "bertindih kategori. (e): bilangan ramalan yang jatuh atas nombor negatif 12 digit (positif palsu; lebih rendah lebih baik)."), "",
          "| sistem | (b) LLP | (c) Sabah/Sarawak | (d) OCR/patah baris | (e) FP / kawasan |", "|---|---|---|---|---|"]
    for s in sistem:
        c = kategori(dok["ujian3"], ram["ujian3"][s])
        sel = [f"{c[x]['recall']} ({c[x]['betul']}/{c[x]['emas']})" if x in c else "-" for x in "bcd"]
        e = f"{c['e']['fp']} / {c['e']['kawasan']}" if "e" in c else "-"
        o.append(f"| {nama[s]} | " + " | ".join(sel) + f" | {e} |")
    o += ["", "## 5. Setiap bahasa (ujian3, F1 tepat `*`)", "", "| sistem | " + " | ".join(k["bahasa"]) + " |",
          "|---|" + "---|" * len(k["bahasa"])]
    for s in sistem:
        o.append(f"| {nama[s]} | " + " | ".join(str(_f1(skor["ujian3"][s], f"bahasa:{b}|*")) for b in k["bahasa"]) + " |")
    o += ["", "## 6. Panggilan LLM dan kos", ""]
    for s, x in sorted(rg["llm"].items()):
        o.append(f"- {nama.get(s, s)} ujian3: {x['panggilan']} panggilan, {x['gagal']} gagal, {x['rosak']} jawapan rosak.")
    o.append(f"- Lejar Anthropic selepas ujian3 (arkib): USD {rg['lejar_usd_selepas']}; had keras USD 20 tidak dinaikkan.")
    o += ["", "## 7. Had kajian (lapor bersama setiap angka)", ""] + [f"{i}. {t}" for i, t in enumerate(k["had"], 1)]
    o += ["", "## English summary", "", k["ringkasan_en"].format(
        v2=rg["f1"]["mypii"]["f1"], haiku=rg["f1"][k["haiku"]]["f1"], v1=rg["f1"]["mypii-v1"]["f1"],
        da=rg["hipotesis"]["H4a"]["delta"], db=rg["hipotesis"]["H4b"]["delta"]), ""]
    return "\n".join(o)


def main() -> int:
    arkib = AKAR / Path(_k()["arkib_ujian3"]).expanduser()  # relatif = dari akar repo; mutlak dipakai terus
    teks = jana(arkib)
    (AKAR / _k()["laporan"]).write_text(teks, encoding="utf-8")
    print(f"{_k()['laporan']}: {len(teks)} aksara")
    return 0


if __name__ == "__main__":
    sys.exit(main())
