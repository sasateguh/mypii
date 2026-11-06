"""Ciri pengelas konteks (PELAN-V2 P10/P11, PRA-DAFTAR Keputusan 4) — Python tulen, dipakai SAMA oleh latihan dan ramalan.

Calon = padanan corak pengecam (mula, tamat). Ciri = kehadiran (binari):
- n-gram perkataan (1, 2) dalam tetingkap ±`tetingkap_token` token kiri/kanan, token terdekat kiri/kanan;
- n-gram aksara (`ngram_aksara`) daripada `aksara_kiri` aksara terakhir sebelum calon;
- bentuk calon (digit → 0, huruf → a) dan sama ada calon dipecah baris.
Nombor DITOPENG: setiap digit → "0", larian 0 yang panjang diringkas (`bentuk_maks`), jadi bentuk nombor ialah ciri, bukan digit.
Semua nilai dari config `konteks:`; tiada rangkaian.
"""

from itertools import pairwise

import regex as re

_TOKEN = re.compile(r"\w+|[^\w\s]")


def topeng(s: str, maks: int) -> str:
    s = re.sub(r"\d", "0", s.lower())
    return re.sub(rf"0{{{maks + 1},}}", "0" * maks + "+", s)


def bentuk(s: str) -> str:
    return re.sub(r"[^\W\d_]", "a", re.sub(r"\d", "0", s))


def ciri(teks: str, mula: int, tamat: int, k: dict) -> list[str]:
    n, maks, aks = k["tetingkap_token"], k["bentuk_maks"], k["aksara_kiri"]
    kiri = [topeng(t, maks) for t in _TOKEN.findall(teks[max(0, mula - k["aksara_maks"]):mula])][-n:]
    kanan = [topeng(t, maks) for t in _TOKEN.findall(teks[tamat:tamat + k["aksara_maks"]])][:n]
    f = {f"k:{t}" for t in kiri} | {f"n:{t}" for t in kanan}
    f |= {f"k2:{a}_{b}" for a, b in pairwise(kiri)} | {f"n2:{a}_{b}" for a, b in pairwise(kanan)}
    if kiri:
        f.add(f"k0:{kiri[-1]}")
    if kanan:
        f.add(f"n0:{kanan[0]}")
    lajur = topeng(teks[max(0, mula - aks):mula], maks)
    g = k["ngram_aksara"]
    f |= {f"c:{lajur[i:i + g]}" for i in range(max(0, len(lajur) - g + 1))}
    calon = teks[mula:tamat]
    f.add(f"b:{bentuk(calon)}")
    if "\n" in calon:
        f.add("b:patah")
    return sorted(f)
