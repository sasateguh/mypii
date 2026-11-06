"""Jana templat + nama dengan LLM (9router) untuk MyPII-Bench — PELAN-B B1 (`ujian2`), B2 (`latih`).

    set -a; . ~/ops/mypii/9router.env; set +a
    uv run python -m mypii.jana.templat_llm --sasaran ujian2

Hanya STATISTIK pengesah dicetak (kiraan, genre, nisbah, sebab tolak) — kandungan templat/nama tidak pernah dicetak, supaya
pembina boleh menjana split ujian tanpa melihatnya. Fail ditulis HANYA bila semua ambang lulus, dan TIDAK menindih fail sedia ada
(ujian2 dimeterai selepas komit pertama). Semua model, prompt, genre dan ambang = `config/mypii.yaml` `llm:` + `templat_llm:`.
"""

import argparse
import datetime
import json
import os
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from string import Template

import yaml

from mypii import klien_anthropic, konfig
from mypii.jana import jana
from mypii.klien_llm import GagalLLM, Hantar, hantar_9router, json_dari, tanya

ENTITI_SLOT = {"MY_NRIC", "MY_SSM", "MY_SSM_LAMA", "MY_PHONE"}
ANGKA_SLOT = ENTITI_SLOT | {"NEG", "TARIKH"} | set(jana.NEGATIF_P1)
DIGIT_LITERAL = re.compile(r"\d(?:[ \-./]?\d){3,}")


def slot_sah() -> set[str]:
    return {"NAMA", "SYARIKAT", "BANDAR", "NEG", "TARIKH", *jana.ENTITI, *jana.NEGATIF_P1, *jana.ALIAS}


def _norm(teks: str) -> str:
    return re.sub(r"\s+", " ", teks).strip().casefold()


def _ada_jenama(teks: str, jenama: list[str]) -> bool:
    t = teks.casefold()
    return any(re.search(rf"(?<!\w){re.escape(j)}(?!\w)", t) for j in jenama)


def _perkataan(teks: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", jana.SLOT.sub(" ", teks).casefold())


def nisbah_bahasa(teks: str, bahasa: str, k: dict) -> float | None:
    """Bahagian kata fungsi `bahasa` daripada semua kata fungsi yang dikenali (config `bahasa_semak`). None = terlalu sedikit untuk
    menilai (atau bahasa tidak disemak, cth manglish)."""
    kb = k["bahasa_semak"]
    if bahasa not in kb["kata_fungsi"]:
        return None
    kira = Counter()
    for w in _perkataan(teks):
        for b, senarai in kb["kata_fungsi"].items():
            kira[b] += w in senarai
    jumlah = sum(kira.values())
    return None if jumlah < kb["min_kata_fungsi"] else kira[bahasa] / jumlah


def sebab_tolak(teks: str, k: dict, bahasa: str | None = None) -> str | None:
    """None = templat sah; selain itu nama pendek sebab (untuk statistik)."""
    if not isinstance(teks, str):
        return "bukan_teks"
    slot = jana.SLOT.findall(teks)
    if any(s not in slot_sah() for s in slot):
        return "slot_tidak_sah"
    tanpa = jana.SLOT.sub(" ", teks)
    if "{" in tanpa or "}" in tanpa:
        return "kurungan_liar"
    if DIGIT_LITERAL.search(tanpa):
        return "nombor_literal"
    if not set(slot) & ANGKA_SLOT:
        return "tiada_slot_nombor"
    lo, hi = k["panjang"]
    if not lo <= len(teks) <= hi:
        return "panjang"
    if _ada_jenama(tanpa, k["jenama_larangan"]):
        return "jenama"
    if bahasa in k["bahasa_semak"]["kata_fungsi"]:
        n = nisbah_bahasa(teks, bahasa, k)
        if n is None:   # terlalu sedikit isyarat = tidak boleh dibuktikan bahasanya → tolak (penyemak 30 Okt: lulus senyap)
            return "bahasa_tidak_dinilai"
        if n < k["bahasa_semak"]["min_nisbah"]:
            return "bahasa"
    return None


def negatif_sahaja(teks: str) -> bool:
    return not set(jana.SLOT.findall(teks)) & ENTITI_SLOT


def tapis_templat(jawapan: dict, k: dict, sedia: set[str], larangan: frozenset[str] = frozenset()) -> tuple[dict, Counter]:
    """jawapan {(bahasa, genre): [teks]} → {bahasa: {genre: [teks]}} sah + kiraan tolak. `sedia` = teks dinormal yang sudah ada
    (templat latih) — pendua dengannya juga ditolak. `larangan` = templat sasaran lain (B2: ujian2) → `sama_sasaran_elak`."""
    dilihat, tolak, hasil = set(sedia), Counter(), {}
    for (bahasa, genre), senarai in jawapan.items():
        for t in senarai:
            sebab = sebab_tolak(t, k, bahasa) or ("sama_sasaran_elak" if isinstance(t, str) and _norm(t) in larangan else None) \
                or ("pendua" if _norm(t) in dilihat else None)
            if sebab:
                tolak[sebab] += 1
                continue
            dilihat.add(_norm(t))
            hasil.setdefault(bahasa, {}).setdefault(genre, []).append(t)
    return hasil, tolak


def statistik(hasil: dict) -> dict:
    semua = [t for g in hasil.values() for s in g.values() for t in s]
    neg = sum(negatif_sahaja(t) for t in semua)
    return {"templat": len(semua), "negatif_sahaja": neg, "nisbah_negatif": round(neg / len(semua), 4) if semua else 0.0,
            "bahasa": {b: {"templat": sum(map(len, g.values())), "genre": len(g),
                           "nisbah_negatif": round(sum(negatif_sahaja(t) for s in g.values() for t in s)
                                                   / max(1, sum(map(len, g.values()))), 4)} for b, g in sorted(hasil.items())}}


def semak_ambang(st: dict, k: dict, s: dict | None = None) -> list[str]:
    gagal, minimum = [], (s or {}).get("min_templat", k["min_templat"])   # `s` = sasaran (B2 latih: ≥ 240)
    if st["templat"] < minimum:
        gagal.append(f"templat {st['templat']} < {minimum}")
    for b in k["bahasa"]:
        sb = st["bahasa"].get(b, {"genre": 0, "nisbah_negatif": 0.0})
        if sb["genre"] < k["min_genre_setiap_bahasa"]:
            gagal.append(f"{b}: genre {sb['genre']} < {k['min_genre_setiap_bahasa']}")
        if sb["nisbah_negatif"] < k["min_nisbah_negatif"]:
            gagal.append(f"{b}: nisbah negatif {sb['nisbah_negatif']} < {k['min_nisbah_negatif']}")
    return gagal


ORANG_RATA = ("nama_pertama", "nama_akhir")   # nama.yaml v1 (tangan): senarai rata, NAMA = pertama + akhir rawak


def _kat_orang(kat: str) -> bool:
    return kat in ORANG_RATA or kat.startswith(("pertama_", "keluarga_"))


def _token_orang(nama: dict, sambung: set[str]) -> set[str]:
    return {w for kat, v in nama.items() if _kat_orang(kat) for n in v for w in n.casefold().split()} - sambung


def _ada_akhiran_syarikat(x: str, k: dict) -> bool:
    t = _norm(x).replace(".", " ")
    return any(re.search(rf"(?<!\w){re.escape(a)}(?!\w)", t) for a in k["nama"]["akhiran_syarikat"])


def huruf_besar(x: str, k: dict) -> str:
    """Token nama selain penyambung (bin/binti/a/l…) bermula huruf besar — 'bin zahidi' → 'bin Zahidi', 'yeoh' → 'Yeoh'."""
    sambung = {s.casefold() for s in k["nama"]["sambung"]}
    return " ".join(w if w.casefold() in sambung else w[:1].upper() + w[1:] for w in x.split())


def bentuk_orang(kat: str, x: str, k: dict, keluarga: set[str]) -> str | None:
    """Nama orang mesti BAHAGIAN nama, bukan nama penuh. `pertama_*`/nama_pertama: ≤ N token, tiada penyambung, token terakhir
    bukan nama keluarga calon. `keluarga_*`: tepat satu token. nama_akhir (rata v1): 'penyambung X' atau satu token. Semua: tiada
    akhiran syarikat; token selain penyambung berhuruf besar (`nama.huruf_besar`)."""
    kn = k["nama"]
    w = x.casefold().split()
    sambung = {s.casefold() for s in kn["sambung"]}
    if _ada_akhiran_syarikat(x, k):
        return "syarikat_sebagai_orang"
    if kn.get("huruf_besar") and any(t.casefold() not in sambung and not t[:1].isupper() for t in x.split()):
        return "huruf_kecil"
    if kat == "nama_pertama" or kat.startswith("pertama_"):
        if len(w) > kn["maks_token_pertama"] or set(w) & sambung:
            return "nama_penuh"
        if len(w) > 1 and w[-1] in keluarga:
            return "ada_nama_keluarga"
    elif kat.startswith("keluarga_"):
        if len(w) != 1:
            return "nama_penuh"
    elif kat == "nama_akhir":
        penyambung = w[0] in {s.casefold() for s in kn["penyambung_akhir"]}
        if not (len(w) == 1 or (penyambung and 2 <= len(w) <= 1 + kn["maks_token_selepas_penyambung"])):
            return "nama_penuh"
    return None


BUKAN_ORANG = ("bandar", "syarikat")   # ADR-009: senarai yang mesti SATU nama tempat / SATU nama syarikat


def bentuk_bukan_orang(kat: str, x: str, k: dict, token_orang: set[str]) -> str | None:
    """`bandar`: satu nama tempat — tiada pemisah ('|', ','…), tiada akhiran syarikat, ≤ N token berhuruf besar, tiada token nama
    orang. `syarikat`: satu nama — tiada pemisah, ≤ N token, berakhiran syarikat bila `syarikat_wajib_akhiran`. (Penyemak 30 Okt:
    60/60 bandar ujian2 ialah 'Nama | Syarikat | Bandar, Negeri'.)"""
    kb = k["nama"]["bentuk_bukan_orang"]
    if any(c in x for c in kb["pemisah_larangan"]):
        return "bukan_satu_nama"
    w = x.split()
    if kat == "bandar":
        if _ada_akhiran_syarikat(x, k):
            return "syarikat_sebagai_bandar"
        if len(w) > kb["maks_token_bandar"]:
            return "terlalu_panjang"
        if any(not t[:1].isupper() for t in w):
            return "huruf_kecil"
        if {t.casefold() for t in w} & token_orang:
            return "token_nama_orang"
    elif kat == "syarikat":
        if len(w) > kb["maks_token_syarikat"]:
            return "terlalu_panjang"
        if kb["syarikat_wajib_akhiran"] and not _ada_akhiran_syarikat(x, k):
            return "tiada_akhiran_syarikat"
    return None


def _keluarga(nama: dict, k: dict) -> set[str]:
    """Token nama keluarga calon — senarai `keluarga_*`, ATAU (rata v1) entri nama_akhir satu token + token terakhir selepas a/l, a/p,
    anak… (BUKAN bin/binti — nama bapa Melayu juga nama pertama biasa) — untuk mengesan nama pertama yang sebenarnya nama penuh."""
    melayu = {s.casefold() for s in k["nama"]["penyambung_bapa_melayu"]}
    kel = {x.casefold() for kat, v in nama.items() if kat.startswith("keluarga_") for x in v if isinstance(x, str)}
    return kel | {w[-1] for x in nama.get("nama_akhir", []) if isinstance(x, str) and (w := x.casefold().split()) and w[0] not in melayu}


def tapis_nama(calon: dict, lama: dict, k: dict) -> tuple[dict, Counter]:
    """Nama baharu bersilang KOSONG dengan `lama` (nama.yaml): nama orang ikut TOKEN (selain bin/binti/a/l…), syarikat + bandar
    ikut entri penuh. Nama orang dibetulkan ke huruf besar dahulu, kemudian `bentuk_orang`; tiada jenama larangan, pendua, digit."""
    sambung = {s.casefold() for s in k["nama"]["sambung"]}
    token_lama = _token_orang(lama, sambung)
    if k["nama"].get("huruf_besar"):
        calon = {kat: [huruf_besar(x, k) if _kat_orang(kat) and isinstance(x, str) else x for x in v] for kat, v in calon.items()}
    keluarga = _keluarga(calon, k)
    token_orang = token_lama | _token_orang({kat: [x for x in v if isinstance(x, str)] for kat, v in calon.items()}, sambung)
    entri_lama = {_norm(x) for v in lama.values() for x in v}
    hasil, tolak = {}, Counter()
    for kat, senarai in calon.items():
        dilihat = set()
        for x in senarai:
            if not isinstance(x, str) or not x.strip() or re.search(r"[\d{}]", x):
                sebab = "bentuk"
            elif _norm(x) in entri_lama or _norm(x) in dilihat:
                sebab = "pendua"
            elif _kat_orang(kat) and (b := bentuk_orang(kat, x, k, keluarga)):
                sebab = b
            elif _kat_orang(kat) and set(x.casefold().split()) & token_lama:
                sebab = "token_bersilang"
            elif kat in BUKAN_ORANG and (b := bentuk_bukan_orang(kat, x.strip(), k, token_orang)):
                sebab = b
            elif _ada_jenama(x, k["jenama_larangan"]):
                sebab = "jenama"
            else:
                dilihat.add(_norm(x))
                hasil.setdefault(kat, []).append(x.strip())
                continue
            tolak[f"{kat}:{sebab}"] += 1
    return hasil, tolak


def _templat_sedia() -> set[str]:
    return {_norm(t) for senarai in jana._templat().values() for _, t in senarai}


def _elak(s: dict, akar: Path) -> tuple[frozenset[str], dict]:
    """Templat (dinormal) + nama sasaran `elak_sasaran` (B2: ujian2) untuk penapis SAHAJA — tidak pernah dicetak/ditulis."""
    templat, nama = set(), {}
    for lain in s.get("elak_sasaran", []):
        sl = konfig.utama()["templat_llm"]["sasaran"][lain]
        for f in sorted((akar / sl["folder"]).glob("*.yaml")):
            templat |= {_norm(t) for senarai in yaml.safe_load(f.read_text(encoding="utf-8"))["genre"].values() for t in senarai}
        if (fn := akar / sl["fail_nama"]).exists():
            for kat, v in yaml.safe_load(fn.read_text(encoding="utf-8")).items():
                nama.setdefault(kat, []).extend(v)
    return frozenset(templat), nama


def _gabung(a: dict, b: dict) -> dict:
    return {kat: [*a.get(kat, []), *b.get(kat, [])] for kat in {*a, *b}}


def _tulis_yaml(fail: Path, data: dict, kepala: str) -> None:
    fail.write_text(kepala + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=10_000), encoding="utf-8")


def jana_sasaran(sasaran: str, hantar: Hantar = hantar_9router, akar: Path = konfig.AKAR) -> dict:
    """Panggil LLM, tapis, semak ambang, tulis. Pulang statistik SAHAJA."""
    k = konfig.utama()["templat_llm"]
    s = k["sasaran"][sasaran]
    peranan = konfig.utama()["llm"]["penjana"][sasaran]
    models = [peranan["model"], *peranan["sandaran"]]
    folder, fail_nama, awalan = akar / s["folder"], akar / s["fail_nama"], s.get("awalan_fail", "")
    sasaran_fail = [folder / f"{awalan}{b}.yaml" for b in k["bahasa"]]
    wujud = any(f.exists() for f in sasaran_fail) if awalan else folder.exists() and any(folder.iterdir())
    if wujud or fail_nama.exists():
        raise SystemExit(f"{s['folder']} / {s['fail_nama']} sudah wujud — DIMETERAI, tidak ditindih (undur: PELAN-B §Undur)")

    slot_teks = "\n".join(f"{{{n}}} = {h}" for n, h in k["slot"].items() if n in slot_sah())
    kerja = {(b, g): Template(k["prompt_templat"]).substitute(
        bahasa=hb, genre=g, huraian=hg, n=k["templat_setiap_panggilan"], neg=k["negatif_setiap_panggilan"], slot=slot_teks)
        + s.get("prompt_tambahan", "") for b, hb in k["bahasa"].items() for g, hg in s["genre"].items()}
    larangan, nama_elak = _elak(s, akar)
    lama = yaml.safe_load((akar / "data/nama.yaml").read_text(encoding="utf-8"))
    sambung = {x.casefold() for x in k["nama"]["sambung"]}
    token = sorted(_token_orang(lama, sambung))
    elak = {kat: token if _kat_orang(kat) else lama.get(kat, []) for kat in k["nama"]["huraian"]}
    kerja_nama = {kat: Template(k["prompt_nama"]).substitute(n=k["nama"]["minta"], huraian=h, elak=", ".join(elak[kat]))
                  for kat, h in k["nama"]["huraian"].items()}

    def senarai(teks: str) -> list:
        x = json_dari(teks)
        if not isinstance(x, list):
            raise TypeError("bukan senarai")
        return x

    def satu(prompt: str):
        try:
            return tanya(models, prompt, peranan["suhu"], urai=senarai, hantar=hantar)
        except GagalLLM as e:
            return None, str(e)

    with ThreadPoolExecutor(max_workers=konfig.utama()["llm"]["serentak"]) as ex:
        r_templat = dict(zip(kerja, ex.map(satu, kerja.values())))
        r_nama = dict(zip(kerja_nama, ex.map(satu, kerja_nama.values())))

    model_kira = Counter(m for m, _ in [*r_templat.values(), *r_nama.values()] if m)
    gagal_panggil = [f"{kunci}: {x}" for kunci, (m, x) in [*r_templat.items(), *r_nama.items()] if m is None]
    hasil, tolak = tapis_templat({kunci: x for kunci, (m, x) in r_templat.items() if m}, k, _templat_sedia(), larangan)
    nama, tolak_nama = tapis_nama({kat: x for kat, (m, x) in r_nama.items() if m}, _gabung(lama, nama_elak), k)
    st = statistik(hasil)
    st |= {"dipohon": len(kerja) * k["templat_setiap_panggilan"], "tolak": dict(tolak), "panggilan_gagal": gagal_panggil,
           "model": dict(model_kira), "nama": {kat: len(v) for kat, v in nama.items()}, "tolak_nama": dict(tolak_nama)}
    masalah = semak_ambang(st, k, s) + [f"nama {kat} {len(nama.get(kat, []))} < {n}" for kat, n in k["nama"]["min"].items()
                                     if len(nama.get(kat, [])) < n]
    if masalah:
        st["gagal_ambang"] = masalah
        return st
    kepala = (f"# Dijana {datetime.date.today()} oleh `python -m mypii.jana.templat_llm --sasaran {sasaran}` "
              f"(model: {', '.join(sorted(model_kira))}). JANGAN sunting tangan.\n")
    if sasaran.startswith("ujian"):
        kepala += "# DIMETERAI (PELAN-B B1): jangan buka, jangan sunting — gerbang menolak sebarang perubahan.\n"
    folder.mkdir(parents=True, exist_ok=True)
    for b, genre in hasil.items():
        _tulis_yaml(folder / f"{awalan}{b}.yaml", {"genre": genre}, kepala)
    _tulis_yaml(fail_nama, nama, kepala)
    return st


def _sebab_tolak_sasaran(t, k: dict, b: str, s: dict) -> str | None:
    """Sasaran v3: pengesah SAMA dengan `tapis_templat_v3` (slot di luar `slot_sah_v3` = `slot_tidak_sah`, kemudian `sebab_tolak` atas
    teks dipetakan `ke_v1`). Sebelum 5 Nov `semak_fail` memakai pengesah v1 atas teks v3 → slot v3 sah dikira tolak (positif palsu)."""
    if not s.get("v3") or not isinstance(t, str):
        return sebab_tolak(t, k, b)
    if any(x not in slot_sah_v3(k) for x in jana.SLOT_V3.findall(t)):
        return "slot_tidak_sah"
    return sebab_tolak(ke_v1(t, k), k, b)


def semak_fail(sasaran: str, akar: Path = konfig.AKAR) -> dict:
    """Jalankan pengesah SEMASA atas fail yang sudah ditulis — KIRAAN sebab tolak sahaja, tiada kandungan (selamat untuk ujian2)."""
    k = konfig.utama()["templat_llm"]
    s = k["sasaran"][sasaran]
    tolak, jumlah = Counter(), 0
    awalan = s.get("awalan_fail", "")
    for f in sorted((akar / s["folder"]).glob(f"{awalan}*.yaml")):
        b = f.stem.removeprefix(awalan)
        for senarai in yaml.safe_load(f.read_text(encoding="utf-8"))["genre"].values():
            for t in senarai:
                jumlah += 1
                tolak[f"{b}:{_sebab_tolak_sasaran(t, k, b, s) or 'sah'}"] += 1
    if not s.get("fail_nama"):  # latih3: nama = nama.yaml + nama_tambahan sedia ada, tiada fail nama sasaran sendiri
        return {"templat": jumlah, "templat_ikut_sebab": dict(sorted(tolak.items())), "nama_ikut_sebab": {}}
    nama = yaml.safe_load((akar / s["fail_nama"]).read_text(encoding="utf-8"))
    keluarga = _keluarga(nama, k)
    t_nama = Counter(f"{kat}:{bentuk_orang(kat, x, k, keluarga) or 'sah'}" for kat, v in nama.items() if _kat_orang(kat)
                     for x in v)
    sambung = {x.casefold() for x in k["nama"]["sambung"]}
    lama = yaml.safe_load((akar / "data/nama.yaml").read_text(encoding="utf-8"))
    token_orang = _token_orang(lama, sambung) | _token_orang(nama, sambung)
    t_nama.update(f"{kat}:{bentuk_bukan_orang(kat, x, k, token_orang) or 'sah'}" for kat in BUKAN_ORANG for x in nama.get(kat) or [])
    # ADR-008: sasaran berkumpulan mesti ada setiap senarai yang dirujuk `jana.nama_kumpulan` (≥ min); senarai rata = tiada
    # padanan penyambung ikut jantina/komuniti ("Irfan binti …") → tolak
    for kat, n in k["nama"]["min"].items():
        if _kat_orang(kat) and len(nama.get(kat) or []) < n:
            t_nama[f"{kat}:kurang_daripada_min"] += 1
    for kat in ORANG_RATA:
        if kat in nama and kat not in k["nama"]["huraian"]:
            t_nama[f"{kat}:format_rata"] += 1
    return {"templat": jumlah, "templat_ikut_sebab": dict(sorted(tolak.items())), "nama_ikut_sebab": dict(sorted(t_nama.items()))}


# --- PELAN-V2 P4 (PRA-DAFTAR pindaan 2026-11-04): sasaran v3 latih3/ujian3. Fungsi BAHARU sahaja; fungsi B1/B2 di atas tidak diubah. ---

def slot_sah_v3(k: dict) -> set[str]:
    return slot_sah() | set(k["slot_v3"])


def ke_v1(teks: str, k: dict) -> str:
    """Slot v3 → slot v1 setara (`slot_v3.<s>.setara`) supaya pengesah + statistik v1 dipakai tanpa diubah. Panjang diukur atas teks
    dipetakan (beza ≤ 6 aksara setiap slot v3)."""
    return jana.SLOT_V3.sub(lambda m: "{" + k["slot_v3"].get(m.group(1), {}).get("setara", m.group(1)) + "}", teks)


def tapis_templat_v3(jawapan: dict, k: dict, sedia: set[str], larangan: frozenset[str] = frozenset()) -> tuple[dict, Counter]:
    """Seperti `tapis_templat` atas teks dipetakan `ke_v1` (pendua/larangan dibanding dalam bentuk dipetakan), tetapi hasil = teks ASAL
    dengan slot v3. Slot di luar `slot_sah_v3` = `slot_tidak_sah` sebelum pemetaan."""
    asal, dipeta, tolak = {}, {}, Counter()
    for kunci, senarai in jawapan.items():
        for t in senarai:
            if isinstance(t, str) and any(x not in slot_sah_v3(k) for x in jana.SLOT_V3.findall(t)):
                tolak["slot_tidak_sah"] += 1
                continue
            m = ke_v1(t, k) if isinstance(t, str) else t
            dipeta.setdefault(kunci, []).append(m)
            if isinstance(t, str):
                asal.setdefault((kunci, m), []).append(t)
    hasil, t2 = tapis_templat(dipeta, k, sedia, larangan)
    tolak.update(t2)
    return {b: {g: [asal[((b, g), m)].pop(0) for m in v] for g, v in gs.items()} for b, gs in hasil.items()}, tolak


def kiraan_kategori(hasil: dict, k: dict) -> dict[str, int]:
    """Bilangan templat yang memakai sekurang-kurangnya satu slot setiap kategori `kategori_v3` (b–e)."""
    semua = [set(jana.SLOT_V3.findall(t)) for g in hasil.values() for v in g.values() for t in v]
    return {kat: sum(bool(x & set(slot)) for x in semua) for kat, slot in k["kategori_v3"].items()}


def statistik_v3(hasil: dict, k: dict) -> dict:
    dipeta = {b: {g: [ke_v1(t, k) for t in v] for g, v in gs.items()} for b, gs in hasil.items()}
    return statistik(dipeta) | {"kategori": kiraan_kategori(hasil, k)}


def semak_keluarga(k: dict, penjana: dict) -> None:
    """Calon v3 mesti berkeluarga (`templat_llm.keluarga`), bukan keluarga larangan (kecuali `keluarga_larangan_kecuali.<sasaran>`,
    pindaan 2026-11-05 c), bukan `penjana_larangan_tepat` (Haiku = pembanding H4a), dan keluarga latih3 ∩ ujian3 = ∅ (PRA-DAFTAR v2)."""
    kel, kecuali, tepat = {}, k.get("keluarga_larangan_kecuali") or {}, set(k.get("penjana_larangan_tepat") or [])
    for sasaran in (x for x, s in k["sasaran"].items() if s.get("v3")):
        for m in [penjana[sasaran]["model"], *penjana[sasaran]["sandaran"]]:
            if m in tepat:
                raise SystemExit(f"{sasaran}: model {m} dilarang sebagai penjana (penjana_larangan_tepat)")
            if m not in k["keluarga"]:
                raise SystemExit(f"{sasaran}: model {m} tiada dalam templat_llm.keluarga")
            if k["keluarga"][m] not in kecuali.get(sasaran, []) and \
                    any(x in f"{m} {k['keluarga'][m]}".casefold() for x in k["keluarga_larangan"]):
                raise SystemExit(f"{sasaran}: model {m} dari keluarga larangan (penjana/garis dasar lepas)")
            kel.setdefault(sasaran, set()).add(k["keluarga"][m])
    sama = kel.get("latih3", set()) & kel.get("ujian3", set())
    if sama:
        raise SystemExit(f"keluarga latih3 dan ujian3 bertindih: {sorted(sama)}")


def _folder_yaml(akar: Path, folder: str) -> list[Path]:
    return sorted((akar / folder).glob("*.yaml")) if (akar / folder).is_dir() else []


def elak_v3(s: dict, k: dict, akar: Path) -> tuple[frozenset[str], set[str], dict]:
    """(templat dinormal + dipetakan dari `elak_folder`, kunci genre dari `genre_unik_dari`, nama dari `elak_nama`) — untuk penapis
    SAHAJA, tidak dicetak."""
    templat, genre, nama = set(), set(), {}
    for folder in dict.fromkeys([*s["elak_folder"], *s["genre_unik_dari"]]):
        for f in _folder_yaml(akar, folder):
            g = yaml.safe_load(f.read_text(encoding="utf-8"))["genre"]
            genre |= set(g) if folder in s["genre_unik_dari"] else set()
            templat |= {_norm(ke_v1(t, k)) for v in g.values() for t in v if isinstance(t, str)} if folder in s["elak_folder"] else set()
    for fn in (akar / x for x in s["elak_nama"]):
        if fn.exists():
            nama = _gabung(nama, yaml.safe_load(fn.read_text(encoding="utf-8")) or {})
    return frozenset(templat), genre, nama


def _fail_sasaran_v3(s: dict, k: dict, akar: Path) -> list[Path]:
    return [akar / s["folder"] / f"{s.get('awalan_fail', '')}{b}.yaml" for b in k["bahasa"]] + \
        ([akar / s["fail_nama"]] if s.get("fail_nama") else [])


def prompt_v3(sasaran: str, bahasa: str, genre: str, n: int, neg: int) -> str:
    """`prompt_templat_v3` dengan slot v1 + `slot_v3`; `$positif` = slot entiti v1 + slot v3 positif (selain kategori e)."""
    k = konfig.utama()["templat_llm"]
    slot = {**{x: h for x, h in k["slot"].items() if x in slot_sah()}, **{x: v["huraian"] for x, v in k["slot_v3"].items()}}
    negatif = set(k["kategori_v3"]["e"])  # (e) = negatif keras PRA-DAFTAR v2
    positif = ", ".join(f"{{{x}}}" for x in [*sorted(ENTITI_SLOT), *k["slot_v3"]] if x not in negatif)
    return Template(k["prompt_templat_v3"]).substitute(
        bahasa=k["bahasa"][bahasa], genre=genre, huraian=k["sasaran"][sasaran]["genre"][genre], n=n, neg=neg,
        slot="\n".join(f"{{{x}}} = {h}" for x, h in slot.items()), positif=positif)


def fail_probe(sasaran: str, akar: Path = konfig.AKAR) -> Path:
    return akar / konfig.utama()["templat_llm"]["probe"]["fail"].format(sasaran=sasaran)


_LEJAR = []


def hantar_penjana(model: str, prompt: str, suhu: float) -> str:
    """Penjana v3: `anthropic/<id>` → API terus melalui `klien_anthropic` (lejar + had keras; kos terburuk ditempah dahulu; suhu TIDAK
    dihantar; `max_tokens` = `templat_llm.anthropic_max_tokens`); selain itu → 9router. Had dicapai = HadDicapai (BERHENTI)."""
    if not klien_anthropic.ialah(model):
        return hantar_9router(model, prompt, suhu)
    t = klien_anthropic.tetapan(model)
    t["permintaan"]["max_tokens"] = konfig.utama()["templat_llm"]["anthropic_max_tokens"]
    if not _LEJAR:
        _LEJAR.append(klien_anthropic.Lejar.dari_config())
    lejar, terburuk = _LEJAR[0], klien_anthropic.kos_terburuk(prompt, t)
    if not lejar.tempah(terburuk):
        raise klien_anthropic.HadDicapai(f"{model}: had lejar USD {lejar.had} akan dilepasi — BERHENTI")
    try:
        teks, usage = klien_anthropic.hantar(t["id"], prompt, t["permintaan"])
    except BaseException:
        lejar.lepas(terburuk)
        raise
    lejar.rekod(model, usage, t["harga"], terburuk)
    return teks


def probe_v3(sasaran: str, hantar: Hantar = hantar_penjana, akar: Path = konfig.AKAR) -> dict:
    """Probe FORMAT sahaja: calon ikut susunan `llm.penjana.<sasaran>`; setiap calon = satu permintaan kecil bagi setiap `probe.genre`
    genre pertama (bahasa pertama). Lulus = JUMLAH templat sah merentas genre ≥ `min_nisbah_sah` × templat × genre (PRA-DAFTAR pindaan
    2026-11-05: satu genre = satu lambungan pada suhu 0.8). Genre yang gagal (rangkaian/urai) = 0 sah. Calon pertama lulus = `dipilih`;
    calon selepasnya TIDAK dipanggil. Fail hasil = statistik sahaja, tidak ditindih (probe tidak diulang untuk memilih model lain)."""
    k, penjana = konfig.utama()["templat_llm"], konfig.utama()["llm"]["penjana"]
    semak_keluarga(k, penjana)
    fail = fail_probe(sasaran, akar)
    if fail.exists():
        raise SystemExit(f"{fail.relative_to(akar)} sudah wujud — probe tidak diulang (calon dipilih sekali)")
    kp, peranan, s = k["probe"], penjana[sasaran], k["sasaran"][sasaran]
    bahasa, genres = next(iter(k["bahasa"])), list(s["genre"])[:kp["genre"]]
    perlu = kp["min_nisbah_sah"] * kp["templat"] * len(genres)
    calon, dipilih = [], None
    for m in [peranan["model"], *peranan["sandaran"]]:
        sah, tolak, ralat, per_genre = 0, Counter(), [], {}
        for genre in genres:
            try:
                _, x = tanya([m], prompt_v3(sasaran, bahasa, genre, kp["templat"], kp["negatif"]), peranan["suhu"],
                             urai=_senarai, hantar=hantar)
            except GagalLLM as e:
                ralat.append(f"{genre}: {e}")
                per_genre[genre] = 0
                continue
            hasil, t = tapis_templat_v3({(bahasa, genre): x}, k, set())
            per_genre[genre] = sum(len(v) for g in hasil.values() for v in g.values())
            sah += per_genre[genre]
            tolak.update(t)
        lulus = sah >= perlu
        c = {"model": m, "lulus": lulus, "sebab": f"sah {sah}/{kp['templat'] * len(genres)} (perlu {perlu:g})",
             "per_genre": per_genre, "tolak": dict(tolak)}
        if ralat:
            c["ralat"] = ralat
        calon.append(c)
        if lulus:
            dipilih = m
            break
    h = {"sasaran": sasaran, "tarikh": str(datetime.date.today()), "bahasa": bahasa, "genre": genres, "calon": calon,
         "dipilih": dipilih}
    fail.parent.mkdir(parents=True, exist_ok=True)
    fail.write_text(json.dumps(h, indent=2, ensure_ascii=False) + "\n")
    return h


def _senarai(teks: str) -> list:
    x = json_dari(teks)
    if not isinstance(x, list):
        raise TypeError("bukan senarai")
    return x


def jana_sasaran_v3(sasaran: str, hantar: Hantar = hantar_penjana, akar: Path = konfig.AKAR) -> dict:
    """Sasaran v3: model = `dipilih` probe SAHAJA; genre bertindih dengan folder elak = BERHENTI sebelum LLM; ambang + `min_kategori`
    setiap kategori b–e; nama (ujian3) bersilang kosong dengan nama.yaml + `elak_nama`. Pulang statistik SAHAJA."""
    k = konfig.utama()["templat_llm"]
    s, peranan = k["sasaran"][sasaran], konfig.utama()["llm"]["penjana"][sasaran]
    semak_keluarga(k, konfig.utama()["llm"]["penjana"])
    if any(f.exists() for f in _fail_sasaran_v3(s, k, akar)):
        raise SystemExit(f"{s['folder']} sudah ada fail sasaran {sasaran} — DIMETERAI, tidak ditindih")
    fp = fail_probe(sasaran, akar)
    dipilih = json.loads(fp.read_text(encoding="utf-8")).get("dipilih") if fp.exists() else None
    if not dipilih:
        raise SystemExit(f"{sasaran}: tiada calon lulus probe ({fp.relative_to(akar)}) — jalankan --probe dahulu; semua gagal = BERHENTI")
    larangan, genre_lama, nama_elak = elak_v3(s, k, akar)
    if bertindih := set(s["genre"]) & genre_lama:
        raise SystemExit(f"{sasaran}: {len(bertindih)} genre sama dengan genre `genre_unik_dari` — tukar genre (kandungan tidak dicetak)")
    # `panggilan` (pindaan 2026-11-05 b): N panggilan setiap bahasa × genre, digabung SEBELUM pengesah (pendua ditolak seperti biasa)
    kerja = {(b, g, i): prompt_v3(sasaran, b, g, k["templat_setiap_panggilan"], k["negatif_setiap_panggilan"])
             for b in k["bahasa"] for g in s["genre"] for i in range(s.get("panggilan", 1))}
    lama = yaml.safe_load((akar / "data/nama.yaml").read_text(encoding="utf-8"))
    token = sorted(_token_orang(lama, {x.casefold() for x in k["nama"]["sambung"]}))
    # `panggilan_nama` (pindaan 2026-11-05 d): N panggilan setiap kategori nama, digabung SEBELUM tapis_nama
    kerja_nama = {(kat, i): Template(k["prompt_nama"]).substitute(n=k["nama"]["minta"], huraian=h,
                                                                  elak=", ".join(token if _kat_orang(kat) else lama.get(kat, [])))
                  for kat, h in k["nama"]["huraian"].items()
                  for i in range(s.get("panggilan_nama", 1))} if s.get("fail_nama") else {}

    def satu(prompt: str):
        try:
            return tanya([dipilih], prompt, peranan["suhu"], urai=_senarai, hantar=hantar)
        except GagalLLM as e:
            return None, str(e)

    with ThreadPoolExecutor(max_workers=konfig.utama()["llm"]["serentak"]) as ex:
        r = dict(zip([*kerja, *kerja_nama], ex.map(satu, [*kerja.values(), *kerja_nama.values()])))
    sedia = {_norm(ke_v1(t, k)) for v in jana._templat().values() for _, t in v}
    jawapan = {}
    for (b, g, _), (model, x) in ((ke, r[ke]) for ke in kerja):
        if model:
            jawapan.setdefault((b, g), []).extend(x)
    hasil, tolak = tapis_templat_v3(jawapan, k, sedia, larangan)
    jawapan_nama = {}
    for (kat, _), (model, x) in ((ke, r[ke]) for ke in kerja_nama):
        if model:
            jawapan_nama.setdefault(kat, []).extend(x)
    nama, tolak_nama = tapis_nama(jawapan_nama, _gabung(lama, nama_elak), k)
    st = statistik_v3(hasil, k) | {
        "dipohon": len(kerja) * k["templat_setiap_panggilan"], "tolak": dict(tolak), "model": dipilih,
        "panggilan_gagal": [f"{x}: {r[x][1]}" for x in r if r[x][0] is None],
        "nama": {x: len(v) for x, v in nama.items()}, "tolak_nama": dict(tolak_nama)}
    masalah = semak_ambang(st, k, s) + [f"kategori {x} {n} < {s['min_kategori']}" for x, n in st["kategori"].items()
                                     if n < s["min_kategori"]]
    if s.get("fail_nama"):
        masalah += [f"nama {x} {len(nama.get(x, []))} < {n}" for x, n in k["nama"]["min"].items() if len(nama.get(x, [])) < n]
    if masalah:
        return st | {"gagal_ambang": masalah}
    kepala = f"# Dijana {datetime.date.today()} oleh `python -m mypii.jana.templat_llm --sasaran {sasaran}` (model: {dipilih}). " \
             "JANGAN sunting tangan.\n"
    if sasaran.startswith("ujian"):
        kepala += "# DIMETERAI (PELAN-V2 P6): jangan buka, jangan sunting — gerbang menolak sebarang perubahan.\n"
    (akar / s["folder"]).mkdir(parents=True, exist_ok=True)
    for b, genre in hasil.items():
        _tulis_yaml(akar / s["folder"] / f"{s.get('awalan_fail', '')}{b}.yaml", {"genre": genre}, kepala)
    if s.get("fail_nama"):
        _tulis_yaml(akar / s["fail_nama"], nama, kepala)
    return st


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sasaran", required=True, choices=sorted(konfig.utama()["templat_llm"]["sasaran"]))
    p.add_argument("--semak", action="store_true", help="kira pengesah semasa atas fail sedia ada (statistik sahaja), tiada LLM")
    p.add_argument("--probe", action="store_true", help="v3: probe format calon penjana ikut susunan (sekali); rc 3 = semua gagal")
    a = p.parse_args()
    v3 = konfig.utama()["templat_llm"]["sasaran"][a.sasaran].get("v3", False)
    if a.probe or v3:
        if not v3 or a.semak:
            print("--probe hanya untuk sasaran v3; --semak tidak untuk v3", file=sys.stderr)
            return 2
        os.nice(konfig.utama()["llm"]["nice"])
        st = probe_v3(a.sasaran) if a.probe else jana_sasaran_v3(a.sasaran)
        print(json.dumps(st, indent=2, ensure_ascii=False))
        return 3 if a.probe and not st["dipilih"] else 1 if st.get("gagal_ambang") else 0
    if a.semak:
        print(json.dumps(semak_fail(a.sasaran), indent=2, ensure_ascii=False))
        return 0
    os.nice(konfig.utama()["llm"]["nice"])
    st = jana_sasaran(a.sasaran)
    print(json.dumps(st, indent=2, ensure_ascii=False))
    return 1 if st.get("gagal_ambang") else 0


if __name__ == "__main__":
    sys.exit(main())
