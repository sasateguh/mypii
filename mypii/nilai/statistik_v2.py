"""Hipotesis v2 H4a/H4b (PRA-DAFTAR pindaan 2026-11-04 "MyPII v2", PELAN-V2 P12/P15) atas output `statistik.jalankan`.

- H4a (bukan-inferioriti, margin δ): p bootstrap sehala atas Δ dianjak margin (Berg-Kirkpatrick, Δ+δ menggantikan Δ):
  p = #(Δ* + δ > 2(Δ̂ + δ)) / B; Δ̂ + δ ≤ 0 → 1.0. p rawak (menguji Δ = 0) dilapor deskriptif sahaja.
- H4b (keunggulan, δ = 0): p bootstrap = p sedia ada; DISOKONG perlukan juga p rawak × k (Bonferroni) < α.
- Holm k = bilangan hipotesis atas p bootstrap. Δ < `beza_kecil` bagi hipotesis keunggulan = "beza kecil" walau disokong.
Semua nilai dari config `nilai.statistik.v2`; indeks bootstrap = indeks yang sama dengan `jalankan` (benih, ulangan).
"""

from mypii import konfig
from mypii.nilai import statistik as st


def _k() -> dict:
    return konfig.utama()["nilai"]["statistik"]


def h4(h: dict, dokumen: list[dict], ramalan: dict[str, list[list[dict]]]) -> dict:
    k, v2 = _k(), _k()["v2"]
    kunci, rj, dp = k["kunci_utama"], h["rujukan"], k["perpuluhan"]
    ix = st.indeks_bootstrap(len(dokumen), k["ulangan"], k["benih"])
    sa = st.f1_sampel(dokumen, ramalan[rj], ix, [kunci])[kunci]
    keluar, p_boot = {}, {}
    for nama, hip in v2["hipotesis"].items():
        s, margin = hip["sistem"], float(hip["margin"])
        b = h["banding"][s][kunci]
        if margin:
            sb = st.f1_sampel(dokumen, ramalan[s], ix, [kunci])[kunci]
            d = [x - y for x, y in zip(sa, sb) if x is not None and y is not None]
            anjak = b["delta"] + margin
            p = 1.0 if anjak <= 0 or not d else sum(1 for x in d if x + margin > 2 * anjak) / len(d)
        else:
            p = b["p_bootstrap"]
        p_boot[nama] = round(p, dp)
        keluar[nama] = {"sistem": s, "margin": margin, "delta": b["delta"], "bawah": b["bawah"], "atas": b["atas"],
                        "p_bootstrap": p_boot[nama], "p_rawak": b["p_rawak"], "rawak_syarat": bool(hip.get("rawak"))}
    terlaras, n, alfa = st.holm(p_boot), len(p_boot), v2["alfa"]
    for nama, x in keluar.items():
        x["p_holm_bootstrap"] = round(terlaras[nama], dp)
        x["p_rawak_bonferroni"] = round(min(1.0, x["p_rawak"] * n), dp)
        x["disokong"] = x["p_holm_bootstrap"] < alfa and (not x["rawak_syarat"] or x["p_rawak_bonferroni"] < alfa)
        x["beza_kecil"] = not x["margin"] and x["delta"] is not None and x["delta"] < v2["beza_kecil"]
    return {"k": n, "alfa": alfa, "ulangan": k["ulangan"], "hipotesis": keluar}


def jadual_md(v: dict) -> str:
    o = ["| hipotesis | lawan | δ | ΔF1 | CI 95% | p boot | p Holm | p rawak (×k) | disokong |", "|---|---|---|---|---|---|---|---|---|"]
    for nama, x in v["hipotesis"].items():
        o.append(f"| {nama} | {x['sistem']} | {x['margin']:g} | {x['delta']} | [{x['bawah']}, {x['atas']}] | "
                 f"{st._p(x['p_bootstrap'], v['ulangan'])} | {st._p(x['p_holm_bootstrap'], v['ulangan'])} | "
                 f"{x['p_rawak']} ({x['p_rawak_bonferroni']}) | {'YA' if x['disokong'] else 'TIDAK'}"
                 f"{' (beza kecil)' if x['beza_kecil'] else ''} |")
    return "\n".join(o) + f"\n\nHolm k = {v['k']}, α = {v['alfa']} sehala; p rawak hanya syarat bagi hipotesis bertanda rawak."
