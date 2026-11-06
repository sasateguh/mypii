"""PELAN-C C4b (ADR-014): split dikunci dibaca HANYA bila pra-daftar sudah dikomit dan bersih dalam `git HEAD`.

`semak(akar)` dipanggil oleh harness SEBELUM fail split dibaca. Ditolak bila fail pra-daftar (config
`nilai.statistik.pradaftar.fail`) tiada dalam HEAD, atau salinan kerja/indeks berbeza dari HEAD (diubah, di-stage, dipadam).
Diterima → sha komit terakhir yang menyentuh fail itu + sha blob, dicetak dan ditulis dalam setiap fail hasil ujian.
"""

import re
from pathlib import Path

from mypii import konfig
from mypii.nilai.iterasi import _git


class Ditolak(Exception):
    """Pra-daftar tidak boleh dipercayai — split dikunci TIDAK dibaca."""


def fail_pradaftar() -> str:
    return konfig.utama()["nilai"]["statistik"]["pradaftar"]["fail"]


def semak(akar: Path, fail: str | None = None) -> dict:
    fail = fail or fail_pradaftar()
    if not _git(akar, "rev-parse", "--verify", "HEAD"):
        raise Ditolak(f"{akar} bukan repo git dengan komit — pra-daftar {fail} tidak boleh disahkan")
    blob = _git(akar, "rev-parse", f"HEAD:{fail}")
    if not blob:
        raise Ditolak(f"{fail} tiada dalam git HEAD — komit pra-daftar DAHULU, kemudian jalankan ujian")
    kotor = _git(akar, "status", "--porcelain", "--", fail)
    if kotor:
        raise Ditolak(f"{fail} berbeza dari git HEAD ({kotor}) — pindaan pra-daftar mesti dikomit dahulu (§Pindaan)")
    return {"fail": fail, "komit": _git(akar, "log", "-1", "--format=%H", "--", fail), "blob": blob}


def semak_pindaan(akar: Path, split: str, fail: str | None = None) -> int:
    """PELAN-V2 P4: split dalam `pradaftar.pindaan_split` (ujian3) menuntut ≥ `min` tajuk yang padan `corak` dalam fail pra-daftar di
    HEAD (pindaan v2 P2 + pindaan kuasa P13). Dipanggil SELEPAS `semak` (HEAD = salinan kerja) dan SEBELUM fail split dibaca."""
    p = konfig.utama()["nilai"]["statistik"]["pradaftar"].get("pindaan_split", {}).get(split)
    if not p:
        return 0
    fail = fail or fail_pradaftar()
    n = len(re.findall(p["corak"], _git(akar, "show", f"HEAD:{fail}"), re.MULTILINE))
    if n < p["min"]:
        raise Ditolak(f"split {split} menuntut ≥ {p['min']} pindaan '{p['corak']}' dalam {fail} di HEAD, ada {n} — "
                      "pindaan v2 + pindaan kuasa mesti dikomit dahulu")
    return n
