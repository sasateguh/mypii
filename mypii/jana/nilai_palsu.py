"""Penjana nilai sintetik. Setiap fungsi menerima random.Random supaya hasil boleh diulang (benih tetap)."""

import random
from datetime import date, timedelta

import phonenumbers

from mypii import konfig


def _tarikh_lahir(rng: random.Random) -> date:
    awal, akhir = konfig.utama()["jana"]["tahun_lahir"]
    mula = date(awal, 1, 1)
    return mula + timedelta(days=rng.randrange((date(akhir, 12, 31) - mula).days))


def _gaya_nombor(rng: random.Random, kumpulan: list[str]) -> str:
    gaya = rng.choice(["-", " ", ""])
    return gaya.join(kumpulan)


def nric(rng: random.Random) -> str:
    t = _tarikh_lahir(rng)
    pb = rng.choice(sorted(konfig.kod_pb_sah()))
    return _gaya_nombor(rng, [t.strftime("%y%m%d"), pb, f"{rng.randrange(10000):04d}"])


def ssm(rng: random.Random) -> str:
    if rng.random() < 0.8:
        return f"{rng.randint(1960, 2026)}{rng.choice(konfig.utama()['pengecam']['MY_SSM']['kod_jenis'])}{rng.randrange(10**6):06d}"
    return f"{rng.randint(1000, 1599999)}-{rng.choice('ABCDEFGHKMPTUVWX')}"


def telefon(rng: random.Random) -> str:
    """Nombor dalam julat yang diperuntukkan (libphonenumber MY) — label emas mesti realistik. Lihat ADR-002."""
    while True:
        calon = _telefon_calon(rng)
        if phonenumbers.is_valid_number(phonenumbers.parse(calon, "MY")):
            return calon


def _telefon_calon(rng: random.Random) -> str:
    if rng.random() < 0.75:  # bimbit
        awalan = rng.choice(["010", "011", "012", "013", "014", "016", "017", "018", "019"])
        tengah = f"{rng.randrange(10000):04d}" if awalan == "011" else f"{rng.randrange(200, 1000)}"
        ekor = f"{rng.randrange(10000):04d}"
        if rng.random() < 0.3:
            return f"+60{rng.choice(['', ' ', '-'])}{awalan[1:]}{rng.choice(['', ' ', '-'])}{tengah}{rng.choice(['', ' '])}{ekor}"
        return f"{awalan}{rng.choice(['-', ' ', ''])}{tengah}{rng.choice(['', ' '])}{ekor}"
    if rng.random() < 0.5:  # Lembah Klang: 03 + 8 digit
        return f"03-{rng.randrange(2000, 9999)} {rng.randrange(10000):04d}"
    kawasan = rng.choice(["04", "05", "06", "07", "09"])
    return f"{kawasan}-{rng.randrange(200, 999)} {rng.randrange(10000):04d}"


def negatif(rng: random.Random) -> str:
    """Nombor yang MENYERUPAI PII tetapi bukan: IC tidak sah, no. invois 12 digit, no. siri, tarikh-nombor."""
    jenis = rng.randrange(5)
    if jenis == 0:  # bulan mustahil
        return f"{rng.randrange(100):02d}{rng.randint(13, 99)}{rng.randint(1, 28):02d}-{rng.randint(1, 16):02d}-{rng.randrange(10000):04d}"
    if jenis == 1:  # kod PB tidak sah
        pb = rng.choice(konfig.muat("kod_pb")["tidak_sah"])
        return f"{rng.randint(50, 99)}0{rng.randint(1, 9)}1{rng.randint(0, 9)}-{pb}-{rng.randrange(10000):04d}"
    if jenis == 2:  # invois 12 digit yang bermula dengan tahun tetapi kod jenis bukan 01–06
        return f"INV{rng.randint(2015, 2026)}{rng.randint(10, 99)}{rng.randrange(10**6):06d}"
    if jenis == 3:  # nombor siri 10 digit
        return f"{rng.randrange(10**9, 10**10)}"
    return f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/{rng.randint(2020, 2026)} {rng.randrange(10**6):06d}"


def tarikh(rng: random.Random) -> str:
    d = date(2025, 1, 1) + timedelta(days=rng.randrange(600))
    return rng.choice([d.strftime("%d/%m/%Y"), d.strftime("%d-%m-%Y"), d.strftime("%-d %b %Y")])


# --- Negatif keras P1 (fungsi BAHARU sahaja; fungsi di atas tidak diubah supaya split ujian kekal sama) ---

def ssm_lama(rng: random.Random) -> str:
    """SSM format lama `123456-X` (positif; slot {MY_SSM_LAMA} dilabel MY_SSM)."""
    return f"{rng.randint(1000, 1599999)}-{rng.choice('ABCDEFGHKMPTUVWX')}"


def akaun_bank(rng: random.Random) -> str:
    """No. akaun bank rekaan 10–16 digit. Separuh ialah 12 digit yang SAH sebagai MyKad dari segi bentuk
    (YYMMDD + kod PB sah) — negatif paling sukar: hanya konteks membezakannya."""
    if rng.random() < 0.5:
        return _gaya_nombor(rng, [_tarikh_lahir(rng).strftime("%y%m%d"), rng.choice(sorted(konfig.kod_pb_sah())),
                                  f"{rng.randrange(10000):04d}"]).replace("-", " ")
    n = rng.choice([10, 13, 14, 16])
    digit = f"{rng.randrange(1, 10)}{rng.randrange(10 ** (n - 1)):0{n - 1}d}"
    return " ".join(digit[i:i + 4] for i in range(0, n, 4)) if rng.random() < 0.5 else digit


def invois12(rng: random.Random) -> str:
    """No. invois/pesanan 12 digit tanpa awalan; kadang bermula dengan tahun + kod 01–06 (bentuk SSM baharu)."""
    if rng.random() < 0.5:
        return f"{rng.randint(2015, 2026)}{rng.choice(['01', '02', '03', '04', '05', '06'])}{rng.randrange(10**6):06d}"
    return f"{rng.randrange(10**11, 10**12)}"


def telefon_tidak_sah(rng: random.Random) -> str:
    """Nombor berbentuk telefon yang libphonenumber anggap TIDAK sah (terlalu pendek/panjang, awalan tiada)."""
    while True:
        calon = rng.choice([
            f"01{rng.randint(0, 9)}-{rng.randrange(10**4, 10**5)}",
            f"01{rng.randint(0, 9)}-{rng.randrange(100, 1000)} {rng.randrange(10**5, 10**6)}",
            f"03-{rng.randrange(100, 1000)} {rng.randrange(10, 100)}",
            f"015-{rng.randrange(100, 1000)} {rng.randrange(1000, 10000)}",
            f"0{rng.randint(2, 9)}{rng.randrange(10**5, 10**6)}",
        ])
        if not phonenumbers.is_valid_number(phonenumbers.parse(calon, "MY")):
            return calon


def tarikh_angka(rng: random.Random) -> str:
    """Tarikh/masa rapat dengan angka: cap masa, no. rujukan bertarikh, YYMMDD diikuti masa."""
    d = date(2025, 1, 1) + timedelta(days=rng.randrange(600))
    return rng.choice([
        f"{d:%Y%m%d}{rng.randrange(10000):04d}",
        f"{d:%y%m%d} {rng.randrange(24):02d}{rng.randrange(60):02d}",
        f"{d:%d%m%Y}-{rng.randrange(1000):03d}",
        f"{d:%y%m%d}-{rng.randrange(100, 1000)}-{rng.randrange(10000):04d}",
    ])


def kod_produk(rng: random.Random) -> str:
    """Kod produk/siri berbentuk SSM lama `123456-X` tetapi tiada kaitan syarikat."""
    return f"{rng.randint(1000, 999999)}-{rng.choice('ABCDEFGHKMPTUVWX')}"


# --- Negatif keras B2 (fungsi BAHARU sahaja) ---

def no_ahli12(rng: random.Random) -> str:
    """No. ahli/polisi 12 digit rapat. Separuh SAH sebagai MyKad dari segi bentuk (YYMMDD + kod PB sah + 4 digit), suku berbentuk
    SSM baharu (tahun + 01–06), selebihnya rawak — hanya konteks ('no. ahli', 'polisi') membezakannya (ANALISIS-RALAT: no. ahli)."""
    x = rng.random()
    if x < 0.5:
        return f"{_tarikh_lahir(rng):%y%m%d}{rng.choice(sorted(konfig.kod_pb_sah()))}{rng.randrange(10000):04d}"
    if x < 0.75:
        return f"{rng.randint(2015, 2026)}{rng.choice(['01', '02', '03', '04', '05', '06'])}{rng.randrange(10**6):06d}"
    return f"{rng.randrange(10**11, 10**12)}"
