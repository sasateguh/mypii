"""Hipotesis H5 (PELAN-V21; pindaan PRA-DAFTAR "MyPII v2.1") — dev3 = kuasa (MDE) SAHAJA, ujian4 = keputusan, dibuka sekali.

    python -m mypii.nilai.statistik_v21 --split dev3            # <keluar>/dev3-h5.json + jadual (tiada split dikunci dibaca)

Metrik `jenis` = F1 tepat mikro `semua|*` atas entiti MyPII (`harness.skor`); `u1` = F1 tepat mikro atas kelas ID (MyKad ∪ SSM) dan
TELEFON (`luar.KELAS`, sama dengan langkah B) — untuk model luar yang tiada label SSM. Ramalan: harness `<keluar>/ramalan/` dan
`hasil/luar/<split>-<model>.jsonl` (sistem `luar:<model>`). Indeks bootstrap = `statistik.indeks_bootstrap` (benih, ulangan config).
- Margin δ > 0 (bukan-inferioriti): p bootstrap atas Δ dianjak (Berg-Kirkpatrick; corak H4a `statistik_v2`), p rawak deskriptif.
- δ = 0 (keunggulan): p bootstrap sedia ada; `rawak: true` → DISOKONG juga perlukan p rawak × k (Bonferroni) < α (corak H4b).
- Holm k = bilangan `hipotesis`. `susulan` (urutan tetap): diuji pada α penuh HANYA bila induk disokong; di luar Holm.
- Kuasa: SE Δ dari lebar CI bootstrap; MDE ketat (α/k) dan longgar (α), kuasa config; kuasa anggaran pada Δ dev3 (+ δ).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import NormalDist

from mypii import konfig
from mypii.nilai import harness, luar
from mypii.nilai import statistik as st

_Z = NormalDist()


def _k() -> dict:
    return konfig.utama()["nilai"]["statistik"]["v21"]


def _sistem_luar(s: str) -> str | None:
    return s.split(":", 1)[1] if s.startswith("luar:") else None


def ramalan(split: str, dokumen: list[dict], sistem: list[str], keluar: Path) -> dict[str, list[list[dict]]]:
    return {s: luar.ramalan_luar(_sistem_luar(s), split, dokumen) if _sistem_luar(s)
            else harness.baca_ramalan(keluar, split, s, dokumen) for s in sistem}


def _pandangan(metrik: str, dokumen: list[dict], ram: dict) -> tuple[list[dict], dict]:
    if metrik == "jenis":
        return dokumen, ram
    if metrik == "u1":
        return [{**d, "spans": luar._kelas(d["spans"])} for d in dokumen], {s: [luar._kelas(r) for r in rr] for s, rr in ram.items()}
    raise ValueError(f"metrik {metrik!r} tidak dikenali (jenis | u1)")


def _uji(h: dict, dokumen: list[dict], ram: dict, ix: list[list[int]], kk: dict) -> dict:
    dd, rr = _pandangan(h["metrik"], dokumen, {"mypii": ram["mypii"], h["sistem"]: ram[h["sistem"]]})
    kunci, margin = "semua|*", float(h["margin"])
    sa = st.f1_sampel(dd, rr["mypii"], ix, [kunci])[kunci]
    sb = st.f1_sampel(dd, rr[h["sistem"]], ix, [kunci])[kunci]
    b = st.berpasangan(dd, rr["mypii"], rr[h["sistem"]], kunci, kk["ulangan"], kk["benih"], kk["aras"],
                       {kunci: sa}, {kunci: sb})
    if margin:
        d = [x - y for x, y in zip(sa, sb, strict=True) if x is not None and y is not None]
        anjak = b["delta"] + margin
        p = 1.0 if anjak <= 0 or not d else sum(1 for x in d if x + margin > 2 * anjak) / len(d)
    else:
        p = b["p_bootstrap"]
    f = {s: (harness.skor(dd, r).get(kunci) or {}).get("tepat", {}).get("f1") for s, r in rr.items()}
    return {"sistem": h["sistem"], "metrik": h["metrik"], "margin": margin, "f1_mypii": f["mypii"], "f1_lawan": f[h["sistem"]],
            "delta": b["delta"], "bawah": b["bawah"], "atas": b["atas"], "p_bootstrap": round(p, kk["perpuluhan"]),
            "p_rawak": b["p_rawak"], "rawak_syarat": bool(h.get("rawak"))}


def kuasa(x: dict, k: int, alfa: float, kuasa_: float, aras: float, dp: int) -> dict:
    """SE Δ dari CI persentil (anggapan normal), MDE (z_{1−α'} + z_kuasa)·SE, kuasa anggaran bila Δ sebenar = Δ diukur."""
    se = (x["atas"] - x["bawah"]) / (2 * _Z.inv_cdf((1 + aras) / 2))
    zb = _Z.inv_cdf(kuasa_)
    z_ketat, z_longgar = _Z.inv_cdf(1 - alfa / k), _Z.inv_cdf(1 - alfa)
    anggar = None if se <= 0 else round(_Z.cdf((x["delta"] + x["margin"]) / se - z_ketat), dp)
    return {"se": round(se, dp), "mde_ketat": round((z_ketat + zb) * se, dp), "mde_longgar": round((z_longgar + zb) * se, dp),
            "kuasa_anggaran_ketat": anggar}


def h5(split: str, dokumen: list[dict], ram: dict) -> dict:
    k, kk = _k(), konfig.utama()["nilai"]["statistik"]
    ix = st.indeks_bootstrap(len(dokumen), kk["ulangan"], kk["benih"])
    hip = {n: _uji(h, dokumen, ram, ix, kk) for n, h in k["hipotesis"].items()}
    n, alfa = len(hip), k["alfa"]
    terlaras = st.holm({x: v["p_bootstrap"] for x, v in hip.items()})
    for nama, x in hip.items():
        x["p_holm_bootstrap"] = round(terlaras[nama], kk["perpuluhan"])
        x["p_rawak_bonferroni"] = round(min(1.0, x["p_rawak"] * n), kk["perpuluhan"])
        x["disokong"] = x["p_holm_bootstrap"] < alfa and (not x["rawak_syarat"] or x["p_rawak_bonferroni"] < alfa)
        x["beza_kecil"] = not x["margin"] and x["delta"] is not None and x["delta"] < k["beza_kecil"]
        x["kuasa"] = kuasa(x, n, alfa, k["kuasa"], kk["aras"], kk["perpuluhan"])
    sus = {}
    for nama, h in (k.get("susulan") or {}).items():
        x = _uji(h, dokumen, ram, ix, kk)
        x["induk"] = h["induk"]
        x["diuji"] = bool(hip[h["induk"]]["disokong"])
        x["disokong"] = x["diuji"] and x["p_bootstrap"] < alfa and (not x["rawak_syarat"] or x["p_rawak"] < alfa)
        x["beza_kecil"] = x["delta"] is not None and x["delta"] < k["beza_kecil"]
        sus[nama] = x
    return {"split": split, "dokumen": len(dokumen), "k": n, "alfa": alfa, "ulangan": kk["ulangan"], "benih": kk["benih"],
            "hipotesis": hip, "susulan": sus}


def jadual_md(v: dict) -> str:
    o = ["| hipotesis | lawan | metrik | δ | F1 v2.1 | F1 lawan | ΔF1 [CI 95%] | p boot | p Holm | p rawak (×k) | disokong | MDE α/k |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nama, x in [*v["hipotesis"].items(), *v["susulan"].items()]:
        sok = "YA" if x["disokong"] else ("tidak diuji" if x.get("diuji") is False else "TIDAK")
        o.append(f"| {nama} | {x['sistem']} | {x['metrik']} | {x['margin']:g} | {x['f1_mypii']} | {x['f1_lawan']} | "
                 f"{x['delta']} [{x['bawah']}, {x['atas']}] | {st._p(x['p_bootstrap'], v['ulangan'])} | "
                 f"{st._p(x['p_holm_bootstrap'], v['ulangan']) if 'p_holm_bootstrap' in x else '–'} | {x['p_rawak']}"
                 f"{' (' + str(x['p_rawak_bonferroni']) + ')' if 'p_rawak_bonferroni' in x else ''} | {sok}"
                 f"{' (beza kecil)' if x['beza_kecil'] and x['disokong'] else ''} | {x.get('kuasa', {}).get('mde_ketat', '–')} |")
    return "\n".join(o) + (f"\n\nHolm k = {v['k']}, α = {v['alfa']} sehala; susulan = urutan tetap selepas induk disokong "
                           "(α penuh, di luar Holm).")


def main() -> int:
    k = _k()
    p = argparse.ArgumentParser()
    p.add_argument("--split", required=True, choices=k["split"])
    p.add_argument("--keluar", type=Path, default=konfig.AKAR / k["keluar"])
    p.add_argument("--benarkan-ujian", action="store_true")
    a = p.parse_args()
    if a.split in konfig.utama()["nilai"]["split_dikunci"]:
        from mypii.nilai import pradaftar
        if not a.benarkan_ujian:
            print(f"split {a.split} dikunci — skrip satu-tembak sahaja (--benarkan-ujian)", file=sys.stderr)
            return 2
        try:
            pd = pradaftar.semak(konfig.AKAR)
            pradaftar.semak_pindaan(konfig.AKAR, a.split)
        except pradaftar.Ditolak as e:
            print(f"split {a.split} ditolak: {e}", file=sys.stderr)
            return 2
    else:
        pd = None
    dokumen = harness._dokumen(a.split)
    sistem = ["mypii", *{h["sistem"] for h in [*k["hipotesis"].values(), *(k.get("susulan") or {}).values()]}]
    v = h5(a.split, dokumen, ramalan(a.split, dokumen, sorted(set(sistem)), a.keluar)) | ({"_pradaftar": pd} if pd else {})
    (a.keluar / f"{a.split}-h5.json").write_text(json.dumps(v, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(jadual_md(v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
