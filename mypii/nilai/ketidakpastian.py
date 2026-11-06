"""Blok jana "Ketidakpastian" `docs/BANDINGAN.md` dari `hasil/<split>-statistik.json` (PELAN-C C3b, ADR-013).

    python -m mypii.nilai.ketidakpastian           # dijalankan oleh `make statistik` selepas harness --statistik

Tiada pengiraan statistik di sini: setiap angka dibaca dari fail statistik (output `statistik.jalankan`). Yang diterbitkan di sini
hanyalah perbandingan logik atas angka itu (selang bertindih?, selang Δ melepasi 0?) supaya ayat tafsiran tidak ditulis tangan.
Hanya split dev: split dikunci ditolak. Sistem eksplorasi (ADR-017) berlabel "(eksplorasi)", tiada p Holm, dan TIDAK masuk ayat
ringkasan keluarga Holm — satu baris deskriptif berasingan sahaja.
"""

import argparse
import json
import sys

from mypii import konfig
from mypii.nilai import bandingan
from mypii.nilai.bandingan_md import _jadual
from mypii.nilai.statistik import pengesahan

AKAR = konfig.AKAR


def _k() -> dict:
    return konfig.utama()["nilai"]["statistik"]


def _p(v, lantai: float) -> str:
    """p bootstrap 0 = tiada sampel melepasi 2δ → dilapor '< 1/B' (ADR-006)."""
    return "–" if v is None else (f"< {lantai:.3g}" if v == 0 else f"{v}")


def _ci(v: dict) -> str:
    return f"{v['f1']} [{v['bawah']}, {v['atas']}]"


def _label(s: str, eks: set[str]) -> str:
    return f"{s} (eksplorasi)" if s in eks else s


def bertindih(a: dict, b: dict) -> bool:
    return a["bawah"] <= b["atas"] and b["bawah"] <= a["atas"]


def blok(h: dict) -> str:
    c, rj, ku = h["config"], h["rujukan"], h["kunci_utama"]
    pct, B = round(c["aras"] * 100), c["ulangan"]
    kunci, eks = list(h["sistem"][rj]), set(h.get("eksplorasi", []))
    out = [(f"<!-- dijana `make statistik` (mypii/nilai/ketidakpastian.py) dari `hasil/{h['split']}-statistik.json` — "
            "JANGAN sunting dengan tangan -->"), "",
           (f"Split `{h['split']}`, {h['dokumen']} dokumen; unit sampel semula = {h['unit']}; ulangan {B}, benih {c['benih']}, "
            f"aras {c['aras']}, pembetulan {c['kaedah']} atas {len(pengesahan(h))} garis dasar (setiap kunci berasingan)."
            + (f" {len(eks)} garis dasar eksplorasi di luar keluarga Holm: p mentah sahaja, tanpa pembetulan." if eks else "")), "",
           f"### F1 tepat + selang bootstrap {pct}% (persentil)", ""]
    out.append(_jadual(["sistem"] + [f"`{x.split('|', 1)[1]}`" for x in kunci],
                       [[_label(s, eks)] + [_ci(ks[x]) for x in kunci] for s, ks in h["sistem"].items()]))
    out += [f"### `{rj}` lawan setiap garis dasar (berpasangan)", ""]
    baris = []
    for s, ks in h["banding"].items():
        for x in kunci:
            v, kosong = ks[x], h["sistem"][s][x]["atas"] == 0
            baris.append([_label(s, eks), f"`{x.split('|', 1)[1]}`" + (" †" if kosong else ""), v["delta"], f"[{v['bawah']}, {v['atas']}]",
                          _p(v["p_bootstrap"], 1 / B), _p(v["p_rawak"], 1 / B), _p(v["p_holm_bootstrap"], 1 / B),
                          _p(v["p_holm_rawak"], 1 / B), "ya" if bertindih(h["sistem"][rj][x], h["sistem"][s][x]) else "tidak",
                          "ya" if v["bawah"] > 0 else "tidak"])
    out.append(_jadual([f"{rj} lawan", "kunci", "ΔF1", f"CI {pct}% Δ", "p bootstrap", "p rawak", "p Holm (bootstrap)",
                        "p Holm (rawak)", "CI F1 bertindih", "CI Δ > 0"], baris))
    out += [f"† Selang F1 garis dasar = [0, 0] untuk entiti ini (tiada ramalan betul langsung): Δ = F1 `{rj}` sendiri.", ""]
    out += ["### Ringkasan mekanikal (dikira dari jadual di atas)", "", *_ringkasan(h, ku), ""]
    return "\n".join(out)


def _ringkasan(h: dict, ku: str) -> list[str]:
    """Ringkasan keluarga Holm (pengesahan sahaja) + satu baris deskriptif eksplorasi bila ada."""
    rj, B, bd = h["rujukan"], h["config"]["ulangan"], pengesahan(h)
    k = len(bd)
    utama = {s: ks[ku] for s, ks in bd.items()}
    tindih = [s for s in utama if bertindih(h["sistem"][rj][ku], h["sistem"][s][ku])]
    sifar = [f"{s} `{x.split('|', 1)[1]}`" for s, ks in bd.items() for x, v in ks.items() if v["bawah"] <= 0]
    kecil = min(((v["delta"], s, x) for s, ks in bd.items() for x, v in ks.items()))
    lantai = round(1 / (B + 1), _k()["perpuluhan"])  # p disimpan dibundar → banding dengan lantai yang dibundar sama
    di_lantai = sum(1 for ks in bd.values() for v in ks.values() if v["p_rawak"] is not None and v["p_rawak"] <= lantai)
    jumlah = sum(len(ks) for ks in bd.values())
    return _ringkasan_holm(rj, ku, B, k, tindih, sifar, kecil, lantai, di_lantai, jumlah) + _ringkasan_eksplorasi(h, ku)


def _ringkasan_eksplorasi(h: dict, ku: str) -> list[str]:
    """Deskriptif sahaja (PRA-DAFTAR pindaan 2026-11-03): tiada perkataan menang/kalah/signifikan, tiada Holm."""
    eks = h.get("eksplorasi", [])
    if not eks:
        return []
    rj = h["rujukan"]
    sel = "; ".join(f"{s} Δ {h['banding'][s][ku]['delta']} [{h['banding'][s][ku]['bawah']}, {h['banding'][s][ku]['atas']}]"
                    for s in eks)
    return [(f"- Eksplorasi ({len(eks)} sistem, `{ku}`, {rj} − sistem): {sel}. Deskriptif sahaja — di luar keluarga Holm, tiada "
             "hipotesis, p mentah tidak dibetulkan untuk perbandingan berganda (PRA-DAFTAR pindaan 2026-11-03).")]


def _ringkasan_holm(rj, ku, B, k, tindih, sifar, kecil, lantai, di_lantai, jumlah) -> list[str]:
    return [
        f"- `{ku}`: selang F1 `{rj}` bertindih dengan {len(tindih)}/{k} garis dasar"
        + (f" ({', '.join(tindih)})." if tindih else "."),
        f"- Selang Δ yang menyentuh atau melepasi 0: {len(sifar)}/{jumlah}" + (f" ({', '.join(sifar)})." if sifar else "."),
        f"- Δ terkecil: {kecil[0]} ({rj} lawan {kecil[1]}, `{kecil[2].split('|', 1)[1]}`).",
        (f"- p rawak terkecil yang boleh dilapor dengan R = {B} ialah 1/(R+1) ≈ {lantai}; {di_lantai}/{jumlah} perbandingan "
         f"berada di lantai itu — di situ p rawak (dan p Holm rawak ≤ {k} × lantai) ialah had resolusi ujian, bukan ukuran saiz kesan."),
    ]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--split", default="dev")
    a = p.parse_args()
    if a.split in konfig.utama()["nilai"]["split_dikunci"]:
        print(f"split {a.split} dikunci — laporan ketidakpastian untuk dev sahaja", file=sys.stderr)
        return 2
    h = json.loads((AKAR / "hasil" / f"{a.split}-statistik.json").read_text(encoding="utf-8"))
    k = _k()
    bandingan.tulis_blok(AKAR / k["laporan"], blok(h), k["penanda"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
