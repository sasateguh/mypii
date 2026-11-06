"""Penjana nilai sintetik MyPII v2 (data v3 — PELAN-V2 Keputusan 3, PRA-DAFTAR pindaan 2026-11-04).

Modul BAHARU: `nilai_palsu.py` v1 tidak diubah (susunan rng split v1 kekal). Setiap fungsi menerima `random.Random` split v3 sendiri.
Nilai/kebarangkalian dari `config/mypii.yaml` `jana_v3:`; fakta format dari `config/ssm_rob.yaml` (sumber rasmi P1).
Kategori: (b) SSM LLP 04–06 tahun ≥ `ssm_rob.yaml llp.tahun_min` · (c) talian tetap Sabah/Sarawak · (d) OCR / patah baris · (e) negatif 12 digit
berbentuk MyKad tanpa kata negatif. (a) ROB lama GUGUR (`rob_lama.awalan_disahkan` kosong) — `rob_lama()` enggan menjana tanpa awalan.
"""

import random
import re

import phonenumbers

from mypii import konfig
from mypii.jana import nilai_palsu


def k3() -> dict:
    return konfig.utama()["jana_v3"]


def _kod_entiti() -> dict[str, dict]:
    return konfig.muat("ssm_rob")["kod_entiti"]


def llp_tahun_min() -> int:
    """Tahun terawal nombor LLP — SATU sumber: `ssm_rob.yaml llp.tahun_min` (Akta 743, fakta rasmi P1)."""
    return int(konfig.muat("ssm_rob")["llp"]["tahun_min"])


def _tahun_ssm(rng: random.Random, kod: str) -> int:
    awal, akhir = k3()["ssm_tahun"]
    if _kod_entiti()[kod]["llp"]:
        awal = max(awal, llp_tahun_min())
    return rng.randint(awal, akhir)


def ssm(rng: random.Random) -> str:
    """SSM 12 digit (format 11 Okt 2019): tahun + kod entiti dari `ssm_rob.yaml` + siri 6 digit. Kod LLP (04–06) SENTIASA tahun ≥
    `ssm_rob.yaml llp.tahun_min` (Akta 743 berkuat kuasa 26 Dis 2012) — v1 boleh menjana LLP 1960-an; v3 tidak."""
    kod = rng.choice(sorted(_kod_entiti()))
    return f"{_tahun_ssm(rng, kod)}{kod}{rng.randrange(10**6):06d}"


def llp(rng: random.Random) -> str:
    """Kategori (b): SSM 12 digit LLP (kod `llp: true` sahaja)."""
    kod = rng.choice(sorted(k for k, v in _kod_entiti().items() if v["llp"]))
    return f"{_tahun_ssm(rng, kod)}{kod}{rng.randrange(10**6):06d}"


def rob_lama(rng: random.Random) -> str:
    """Kategori (a) — hanya awalan yang DISAHKAN sumber rasmi. Kosong (P1) = enggan (slot tidak boleh dipakai)."""
    if not konfig.muat("ssm_rob")["rob_lama"]["awalan_disahkan"]:
        raise ValueError("rob_lama: tiada awalan ROB disahkan (config/ssm_rob.yaml) — kategori (a) GUGUR, slot {MY_ROB} dilarang")
    raise NotImplementedError("rob_lama: bentuk belum ditakrif — tambah bersama sumber rasmi (pindaan PRA-DAFTAR baharu)")


def talian_bs(rng: random.Random) -> str:
    """Kategori (c): talian tetap Sabah/Sarawak 08X + 6 digit (digit pertama dari `ssm_rob.yaml` talian_tetap_bs), sah libphonenumber
    (ADR-002); gaya penulisan dari `jana_v3.gaya_talian_bs`."""
    t = konfig.muat("ssm_rob")["talian_tetap_bs"]
    while True:
        kod = rng.choice(sorted(t["digit_pertama"]))
        pel = rng.choice(t["digit_pertama"][kod]) + f"{rng.randrange(10 ** (t['panjang_pelanggan'] - 1)):0{t['panjang_pelanggan'] - 1}d}"
        calon = rng.choice(k3()["gaya_talian_bs"]).format(kod=kod, k=kod[1:], a=pel[:3], b=pel[3:])
        if phonenumbers.is_valid_number(phonenumbers.parse(calon, "MY")):
            return calon


def neg12(rng: random.Random) -> str:
    """Kategori (e): no. ahli/polisi 12 digit yang SAH sebagai MyKad dari segi bentuk (YYMMDD + kod PB sah + 4 digit); gaya dari
    `jana_v3.gaya_neg12`. Tiada label — hanya ketiadaan konteks IC (dan ketiadaan kata negatif) yang tinggal."""
    lahir = nilai_palsu._tarikh_lahir(rng)
    a, b, c = f"{lahir:%y%m%d}", rng.choice(sorted(konfig.kod_pb_sah())), f"{rng.randrange(10000):04d}"
    return rng.choice(k3()["gaya_neg12"]).format(a=a, b=b, c=c)


def ocr(rng: random.Random, nilai: str) -> str | None:
    """Kategori (d) OCR: SATU digit di DALAM nombor (diapit digit kiri + kanan) diganti aksara serupa (`jana_v3.ocr_ganti`).
    Tiada kedudukan layak = None (nilai tidak diubah, tiada kategori)."""
    peta = k3()["ocr_ganti"]
    layak = [i for i in range(1, len(nilai) - 1)
             if nilai[i] in peta and nilai[i - 1].isdigit() and nilai[i + 1].isdigit()]
    if not layak:
        return None
    i = rng.choice(layak)
    return nilai[:i] + peta[nilai[i]] + nilai[i + 1:]


def patah(rng: random.Random, nilai: str, entiti: str) -> str | None:
    """Kategori (d) patah baris: satu sempadan kumpulan diganti `jana_v3.patah_baris`. Sempadan = pemisah sedia ada (`-`/ruang di antara
    digit) atau, bagi nombor rapat, kedudukan `jana_v3.patah_sempadan.<entiti>`. Tiada sempadan = None."""
    pemisah = [m.start() for m in re.finditer(r"(?<=\d)[- ](?=\d)", nilai)]
    ganti = rng.choice(k3()["patah_baris"])
    if pemisah:
        i = rng.choice(pemisah)
        return nilai[:i] + ganti + nilai[i + 1:]
    sempadan = [i for i in k3()["patah_sempadan"].get(entiti, []) if 0 < i < len(nilai)]
    if not sempadan or not nilai.isdigit():
        return None
    i = rng.choice(sempadan)
    return nilai[:i] + ganti + nilai[i:]


def ada_kata_negatif(teks: str) -> bool:
    """Teks mengandungi frasa `pengecam.konteks_umum.negatif` (sempadan perkataan, casefold)."""
    t = teks.casefold()
    return any(re.search(rf"(?<!\w){re.escape(f.casefold())}(?!\w)", t)
               for f in konfig.utama()["pengecam"]["konteks_umum"]["negatif"])
