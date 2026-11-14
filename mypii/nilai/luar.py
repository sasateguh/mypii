"""Skor DESKRIPTIF model PII luar atas MyPII-Bench (pindaan PRA-DAFTAR 2026-11-14; langkah B KAJIAN-HF-MODAL-V3).

    python -m mypii.nilai.luar            # hasil/luar/<split>-<model>.jsonl + MyPII v2 → hasil/luar/ringkasan.json + docs/BANDINGAN-LUAR.md

Ramalan mentah = `scripts/luar_modal.py` (Modal). Pemetaan label + metrik = pindaan itu, tidak ditala selepas melihat keputusan.
`harness.skor` dipakai tanpa ubah; tiada nilai p (deskriptif selepas kejadian).
"""

from __future__ import annotations

import json

from mypii import konfig
from mypii.nilai import harness
from mypii.nilai.statistik import _k, _selang, f1_sampel, indeks_bootstrap

AKAR = konfig.AKAR
SPLIT = ["ujian3", "ujian2", "ujian"]
# label mentah model → entiti MyPII (pra-daftar). Meddies tiada label SSM: `id_number` = kelas ID sahaja.
PETA = {
    "meddies": {"id_number": "ID", "phone_number": "MY_PHONE"},
    "gliner": {"identity card number": "MY_NRIC", "registration number": "MY_SSM", "phone number": "MY_PHONE"},
}
NAMA = {"mypii": "MyPII v2 (1.0.x)", "meddies": "Meddies PII v2", "gliner": "GLiNER multi PII v1 ‡"}
KELAS = {"MY_NRIC": "ID", "MY_SSM": "ID", "ID": "ID", "MY_PHONE": "TEL"}
TIDAK_DIJALANKAN = {"PII Engineer Multi-NER v2.1": "pelayan rasmi memulangkan HTTP 500 (Reshape span_rep) untuk setiap input"}


def _dokumen(split: str) -> list[dict]:
    return [json.loads(x) for x in (AKAR / konfig.fail_split(split)).read_text(encoding="utf-8").splitlines() if x.strip()]


def ramalan_luar(model: str, split: str, dokumen: list[dict]) -> list[list[dict]]:
    baris = {r["id"]: r for r in map(json.loads, (AKAR / f"hasil/luar/{split}-{model}.jsonl").read_text(encoding="utf-8").splitlines())}
    keluar = []
    for d in dokumen:
        keluar.append([{"mula": s["mula"], "tamat": s["tamat"], "entiti": PETA[model][s["label"]]}
                       for s in baris[d["id"]]["spans"] if s["label"] in PETA[model]])
    return keluar


def _kelas(spans: list[dict]) -> list[dict]:
    return [{**s, "entiti": KELAS[s["entiti"]]} for s in spans]


def _nric_ketat(d: dict, r: list[dict]) -> tuple[dict, list[dict]]:
    """Emas MyKad sahaja; ramalan ID yang bertindih span emas SSM diabaikan (bukan FP)."""
    ssm = [s for s in d["spans"] if s["entiti"] == "MY_SSM"]
    emas = [{**s, "entiti": "N"} for s in d["spans"] if s["entiti"] == "MY_NRIC"]
    p = [{**s, "entiti": "N"} for s in _kelas(r) if s["entiti"] == "ID"
         and not any(s["mula"] < x["tamat"] and x["mula"] < s["tamat"] for x in ssm)]
    return {**d, "spans": emas}, p


def _kategori(dokumen: list[dict], ramalan: list[list[dict]]) -> dict:
    """ujian3: dapatan semula span emas yang bertindih kategori b–d; ramalan ID/TEL yang bertindih kategori e (= FP)."""
    k = {x: [0, 0] for x in "bcde"}
    for d, r in zip(dokumen, ramalan):
        for kat in d.get("kategori") or []:
            x = kat["kategori"]
            def tindih(s, kat=kat):
                return s["mula"] < kat["tamat"] and kat["mula"] < s["tamat"]
            if x == "e":
                k[x][0] += 1
                k[x][1] += any(tindih(s) for s in r)
            else:
                for g in (s for s in d["spans"] if tindih(s)):
                    k[x][0] += 1
                    k[x][1] += any(tindih(s) and KELAS[s["entiti"]] == KELAS[g["entiti"]] for s in r)
    return {x: {"n": n, "kena": c} for x, (n, c) in k.items() if n}


def nilai_split(split: str, model_ada: list[str]) -> dict:
    dokumen = _dokumen(split)
    ram = {"mypii": harness.ramal("mypii", dokumen)} | {m: ramalan_luar(m, split, dokumen) for m in model_ada}
    k = _k()
    ix = indeks_bootstrap(len(dokumen), k["ulangan"], k["benih"])
    u1_d = [{**d, "spans": _kelas(d["spans"])} for d in dokumen]
    pandangan = {"U1": (u1_d, {m: [_kelas(r) for r in rr] for m, rr in ram.items()}, ["semua|*", "semua|ID", "semua|TEL"])}
    nk = {m: [_nric_ketat(d, r) for d, r in zip(dokumen, rr)] for m, rr in ram.items()}
    pandangan["NRIC_ketat"] = ([x[0] for x in nk["mypii"]], {m: [x[1] for x in v] for m, v in nk.items()}, ["semua|N"])
    bertipe = {m: rr for m, rr in ram.items() if m != "meddies"}
    pandangan["bertipe"] = (dokumen, bertipe, ["semua|*", "semua|MY_NRIC", "semua|MY_SSM", "semua|MY_PHONE"])
    keluar = {"split": split, "dokumen": len(dokumen), "sistem": {}}
    for nama_p, (dd, rr, kunci) in pandangan.items():
        sampel = {m: f1_sampel(dd, r, ix, kunci) for m, r in rr.items()}
        for m, r in rr.items():
            s = harness.skor(dd, r)
            for x in kunci:
                b = s.get(x)
                rek = {"f1": b["tepat"]["f1"] if b else None, "p": b["tepat"]["p"] if b else None,
                       "r": b["tepat"]["r"] if b else None, "f1_separa": b["separa"]["f1"] if b else None,
                       **_selang(sampel[m][x], k["aras"], k["perpuluhan"])}
                if m != "mypii":
                    dl = [a - c for a, c in zip(sampel["mypii"][x], sampel[m][x]) if a is not None and c is not None]
                    f_m = (harness.skor(dd, rr["mypii"]).get(x) or {}).get("tepat", {}).get("f1")
                    rek["delta_mypii"] = None if f_m is None or rek["f1"] is None else round(f_m - rek["f1"], 4)
                    rek["delta_ci"] = _selang(dl, k["aras"], k["perpuluhan"])
                keluar["sistem"].setdefault(m, {})[f"{nama_p}:{x}"] = rek
        if nama_p == "U1":
            for m, r in rr.items():
                bahasa = {kk.split("|")[0]: v["tepat"]["f1"] for kk, v in harness.skor(dd, r).items()
                          if kk.startswith("bahasa:") and kk.endswith("|*")}
                keluar["sistem"][m]["U1:bahasa"] = bahasa
    if split == "ujian3":
        for m, r in ram.items():
            keluar["sistem"][m]["kategori"] = _kategori(dokumen, r)
    return keluar


def _f(x) -> str:
    return "–" if x is None else f"{x:.3f}"


def laporan(ringkasan: list[dict]) -> str:
    b = ["# MyPII-Bench: model PII luar (deskriptif)", "",
         "> Dijana `python -m mypii.nilai.luar` daripada `hasil/luar/`; jangan sunting dengan tangan. Pindaan PRA-DAFTAR **2026-11-14**:",
         "> semua split ujian sudah dibuka, jadi ini perbandingan **deskriptif selepas kejadian**, bukan dakwaan. ‡ = eksplorasi.", "",
         "**U1** = F1 tepat mikro atas dua kelas yang semua sistem sokong: ID (MyKad ∪ SSM) dan TELEFON. **NRIC ketat** = emas MyKad",
         "sahaja, ramalan ID yang bertindih SSM diabaikan. **Bertipe** = tiga entiti MyPII (Meddies tiada label SSM, jadi tiada baris).",
         "CI = bootstrap dokumen 95% (1000, benih 2026). Δ = MyPII v2 − model.", ""]
    for r in ringkasan:
        b += [f"## `{r['split']}` ({r['dokumen']} dokumen)", "",
              "| Sistem | U1 F1 [CI] | Δ MyPII [CI] | ID | TELEFON | NRIC ketat | Bertipe `*` | SSM bertipe |",
              "|---|---|---|---|---|---|---|---|"]
        for m, s in r["sistem"].items():
            u = s["U1:semua|*"]
            d = "" if m == "mypii" else f"{_f(u.get('delta_mypii'))} [{_f(u['delta_ci']['bawah'])}, {_f(u['delta_ci']['atas'])}]"
            bt, ssm = s.get("bertipe:semua|*", {}), s.get("bertipe:semua|MY_SSM", {})
            b.append(f"| {NAMA[m]} | {_f(u['f1'])} [{_f(u['bawah'])}, {_f(u['atas'])}] | {d or '–'} | "
                     f"{_f(s['U1:semua|ID']['f1'])} | {_f(s['U1:semua|TEL']['f1'])} | {_f(s['NRIC_ketat:semua|N']['f1'])} | "
                     f"{_f(bt.get('f1'))} | {_f(ssm.get('f1'))} |")
        b.append("")
        b.append("Setiap bahasa (U1): " + "; ".join(
            f"{NAMA[m]}: " + ", ".join(f"{k.split(':')[1]} {_f(v)}" for k, v in sorted(s['U1:bahasa'].items()))
            for m, s in r["sistem"].items()) + ".")
        if r["split"] == "ujian3":
            b.append("")
            b.append("Kategori sukar `ujian3` (b–d = span emas dikesan / n; e = nombor 12 digit tanpa label ditanda / n, lebih rendah lebih baik):")
            for m, s in r["sistem"].items():
                b.append(f"- {NAMA[m]}: " + ", ".join(f"{x} {v['kena']}/{v['n']}" for x, v in s["kategori"].items()))
        b.append("")
    b += ["## Had (baca sebelum memetik)", "",
          "- Deskriptif selepas kejadian: ketiga-tiga split sudah dibuka (3–5 Nov); dakwaan bersih perlukan split ujian baharu (ujian4).",
          "- Label emas tidak lengkap: semakan IAA mendapati dokumen dengan MyKad/SSM/telefon tidak berlabel 0.067 (`dev`) dan 0.167",
          "  (`ujian2`). Sistem dengan dapatan semula tinggi (Meddies) kehilangan ketepatan atas nombor sebenar yang tidak dilabel, jadi",
          "  ketepatan mereka di sini ialah had bawah. Arah sebaliknya juga mungkin: negatif keras sengaja tidak dilabel.",
          "- Kelebihan rumah: MyPII v2 dilatih atas latih3 (penjana yang sama dengan bentuk v3); data sintetik, bukan dokumen sebenar.",
          "- MyPII v2 atas `ujian` (templat v1) = 0.870, lebih rendah daripada v1 (0.993) di split itu: v2 kurang dapatan semula pada gaya v1.",
          "- Meddies CC BY-NC 4.0: penilaian penyelidikan sahaja.", ""]
    b += ["## Tidak dinilai", ""] + [f"- {k}: {v} (14 Nov 2026, PELAN-HF-E §B)." for k, v in TIDAK_DIJALANKAN.items()] + [""]
    return "\n".join(b)


def main() -> int:
    model_ada = [m for m in PETA if all((AKAR / f"hasil/luar/{s}-{m}.jsonl").is_file() for s in SPLIT)]
    ringkasan = [nilai_split(s, model_ada) for s in SPLIT]
    (AKAR / "hasil/luar/ringkasan.json").write_text(json.dumps(ringkasan, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (AKAR / "docs/BANDINGAN-LUAR.md").write_text(laporan(ringkasan), encoding="utf-8")
    print(f"model: {model_ada}; hasil/luar/ringkasan.json + docs/BANDINGAN-LUAR.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
