"""Analisis kuasa pra-daftar dari bootstrap dev (PELAN-C C4a, ADR-007).

    python -m mypii.nilai.kuasa          # `make kuasa`; baca hasil/dev-statistik.json, cetak jadual markdown

Ralat piawai Δ dianggar dari lebar selang bootstrap persentil Δ yang sudah dikira oleh `make statistik`
(SE ≈ (atas − bawah) / (2·z_{(1+aras)/2}), anggapan taburan Δ* lebih kurang normal), diskala √(n_dev / n_sasaran).
Kesan minimum boleh dikesan (MDE, sehala) = (z_{1−α'} + z_{kuasa}) · SE, dengan α' = α/k (langkah Holm paling ketat)
dan α' = α (langkah terakhir Holm). k dan baris = garis dasar PENGESAHAN sahaja — sistem eksplorasi (ADR-017) di luar
keluarga Holm, tiada MDE. Tiada sampel semula di sini — setiap angka diterbitkan dari fail statistik + config.
"""

import argparse
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

from mypii import konfig
from mypii.nilai.statistik import pengesahan

AKAR = konfig.AKAR
_Z = NormalDist()


def _k() -> dict:
    return konfig.utama()["nilai"]["statistik"]


def kira(h: dict, alfa: float, kuasa: float, n_sasaran: int, perpuluhan: int = 4) -> list[dict]:
    """Satu baris setiap (garis dasar, kunci): Δ dev, SE anggaran, MDE Holm ketat (α/k) dan longgar (α)."""
    z_ci = _Z.inv_cdf((1 + h["config"]["aras"]) / 2)
    banding = pengesahan(h)
    k = len(banding)
    skala = math.sqrt(h["dokumen"] / n_sasaran)
    z_b = _Z.inv_cdf(kuasa)
    out = []
    for s, ks in banding.items():
        for kunci, v in ks.items():
            se = (v["atas"] - v["bawah"]) / (2 * z_ci) * skala
            out.append({
                "sistem": s, "kunci": kunci, "delta_dev": v["delta"], "se": round(se, perpuluhan),
                "mde_ketat": round((_Z.inv_cdf(1 - alfa / k) + z_b) * se, perpuluhan),
                "mde_longgar": round((_Z.inv_cdf(1 - alfa) + z_b) * se, perpuluhan),
            })
    return out


def jadual_md(baris: list[dict], k: int, alfa: float, kuasa: float) -> str:
    o = [f"| garis dasar | kunci | ΔF1 dev | SE Δ | MDE α/k={alfa / k:.4g} | MDE α={alfa:g} |",
         "|---|---|---|---|---|---|"]
    o += [f"| {b['sistem']} | `{b['kunci'].split('|', 1)[1]}` | {b['delta_dev']} | {b['se']} | {b['mde_ketat']} | "
          f"{b['mde_longgar']} |" for b in baris]
    return "\n".join(o) + f"\n\nkuasa {kuasa:g}, sehala; k = {k} garis dasar (Holm)."


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fail", type=Path, default=AKAR / "hasil" / "dev-statistik.json")
    a = p.parse_args()
    if not a.fail.exists():
        print(f"{a.fail} tiada — jalankan `make nilai-garis` + `make statistik` dahulu", file=sys.stderr)
        return 2
    h = json.loads(a.fail.read_text(encoding="utf-8"))
    if h["split"] in konfig.utama()["nilai"]["split_dikunci"]:
        print(f"split {h['split']} dikunci — analisis kuasa hanya atas dev", file=sys.stderr)
        return 2
    c = _k()
    pd = c["pradaftar"]
    baris = kira(h, pd["alfa"], pd["kuasa"], pd["dokumen_sasaran"], c["perpuluhan"])
    print(f"Sumber: {a.fail.name} (split {h['split']}, {h['dokumen']} dokumen) → sasaran {pd['dokumen_sasaran']} dokumen\n")
    print(jadual_md(baris, len(pengesahan(h)), pd["alfa"], pd["kuasa"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
