"""Jana MyPII-Bench: templat bertanda slot → slot diisi nilai sintetik → label span tepat (tiada anotasi manual).

    python -m mypii.jana.jana [--keluar data/bench]
"""

import argparse
import hashlib
import json
import random
import re
from pathlib import Path

import yaml

from mypii import konfig
from mypii.jana import nilai_palsu, nilai_v3

AKAR = konfig.AKAR
SLOT = re.compile(r"\{([A-Z_]+)\}")
ENTITI = {"MY_NRIC": nilai_palsu.nric, "MY_SSM": nilai_palsu.ssm, "MY_PHONE": nilai_palsu.telefon}
ALIAS = {"MY_SSM_LAMA": ("MY_SSM", nilai_palsu.ssm_lama)}  # slot → (label emas, penjana)
NEGATIF_P1 = {
    "NEG_AKAUN": nilai_palsu.akaun_bank, "NEG_INVOIS": nilai_palsu.invois12, "NEG_TEL": nilai_palsu.telefon_tidak_sah,
    "NEG_TARIKH": nilai_palsu.tarikh_angka, "NEG_KOD": nilai_palsu.kod_produk,
    "NEG_AHLI": nilai_palsu.no_ahli12,  # PELAN-B B2 (tiada templat lama memakainya — split lama tidak berubah)
}
TAMBAHAN = "_tambahan"  # kunci dalam kamus nama latih/dev: fail nama berkumpulan `jana.nama_tambahan` (B2)


def _templat(folder: str | Path = "data/templat") -> dict[str, list[tuple[str, str]]]:
    """{bahasa: [(genre, teks)]}. Fail `<awalan_templat_llm><bahasa>.yaml` (B2: `llm_ms.yaml`) digabung ke bahasa yang sama."""
    awalan = konfig.utama()["jana"]["awalan_templat_llm"]
    hasil = {}
    for fail in sorted((AKAR / folder).glob("*.yaml")):  # laluan mutlak = dipakai terus
        genre = yaml.safe_load(fail.read_text(encoding="utf-8"))["genre"]
        hasil.setdefault(fail.stem.removeprefix(awalan), []).extend((g, t) for g, senarai in genre.items() for t in senarai)
    return hasil


def jantina_gelaran(sebelum: str) -> str | None:
    """Jantina yang dituntut gelaran tepat sebelum slot NAMA ('En. {NAMA}' → l, 'Puan {NAMA}' → p) — `jana.gelaran_jantina`."""
    t = sebelum.casefold().rstrip()
    for jantina, gelaran in konfig.utama()["jana"]["gelaran_jantina"].items():
        if any(re.search(rf"(?<!\w){re.escape(g.casefold())}$", t) for g in gelaran):
            return jantina
    return None


def nama_orang(r: random.Random, nama: dict, sebelum: str = "") -> str:
    """Senarai rata (nama.yaml v1) = pertama + akhir rawak — TIDAK diubah, supaya cincangan v1 kekal. Fail berkumpulan (ADR-008) =
    kumpulan dipilih ikut berat `jana.nama_kumpulan`, penyambung sepadan jantina, nama bapa dari nama diri lelaki komuniti sama.
    ADR-009: gelaran sebelum slot (`sebelum`) mengehadkan kumpulan kepada jantina itu; nama bapa ≠ nama diri.
    B2 (ADR-010): kamus latih/dev membawa fail berkumpulan di `TAMBAHAN` — dipilih dengan kebarangkalian `jana.nisbah_nama_tambahan`
    (tiada kunci itu = tiada rng dipakai, jadi split ujian/ujian2 tidak berubah)."""
    if (tambahan := nama.get(TAMBAHAN)) and r.random() < konfig.utama()["jana"]["nisbah_nama_tambahan"]:
        nama = tambahan
    if "nama_pertama" in nama:
        return f"{r.choice(nama['nama_pertama'])} {r.choice(nama['nama_akhir'])}"
    k = konfig.utama()["jana"]
    kumpulan = k["nama_kumpulan"]
    jantina = jantina_gelaran(sebelum)
    kunci = sorted(k["kumpulan_jantina"][jantina] if jantina else kumpulan)
    g = kumpulan[r.choices(kunci, [kumpulan[x]["berat"] for x in kunci])[0]]
    pertama = r.choice(nama[g["pertama"]])
    if "penyambung" in g:
        bapa = [x for x in nama[g["bapa"]] if x != pertama] or nama[g["bapa"]]
        return f"{pertama} {g['penyambung']} {r.choice(bapa)}"
    keluarga = r.choice(nama[g["keluarga"]])
    return f"{keluarga} {pertama}" if g.get("keluarga_dahulu") else f"{pertama} {keluarga}"


def isi(templat: str, rng: random.Random, nama: dict) -> tuple[str, list[dict]]:
    teks, spans, kedudukan = [], [], 0
    pengisi = {
        "NAMA": lambda r: nama_orang(r, nama, "".join(teks)),
        "SYARIKAT": lambda r: r.choice(nama["syarikat"]),
        "BANDAR": lambda r: r.choice(nama["bandar"]),
        "NEG": nilai_palsu.negatif,
        "TARIKH": nilai_palsu.tarikh,
        **ENTITI,
        **NEGATIF_P1,
        **{slot: penjana for slot, (_, penjana) in ALIAS.items()},
    }
    akhir = 0
    for m in SLOT.finditer(templat):
        teks.append(templat[akhir:m.start()])
        kedudukan += m.start() - akhir
        nilai = pengisi[m.group(1)](rng)
        label = ALIAS[m.group(1)][0] if m.group(1) in ALIAS else m.group(1)
        if label in ENTITI:
            spans.append({"mula": kedudukan, "tamat": kedudukan + len(nilai), "entiti": label})
        teks.append(nilai)
        kedudukan += len(nilai)
        akhir = m.end()
    teks.append(templat[akhir:])
    return "".join(teks), spans


def _dokumen(n: int, rng: random.Random, templat: dict, nama: dict, awalan: str) -> list[dict]:
    k = konfig.utama()["jana"]
    bahasa = [b for b in k["bahasa"] if b in templat] or list(templat)
    berat = [k["bahasa"].get(b, 1) for b in bahasa]
    hasil = []
    for i in range(n):
        b = rng.choices(bahasa, berat)[0]
        senarai = templat[b]
        negatif_sahaja = [t for t in senarai if not any(s in t[1] for s in ENTITI)]
        pilih = negatif_sahaja if rng.random() < k["nisbah_negatif_keras"] and negatif_sahaja else senarai
        genre, t = rng.choice(pilih)
        teks, spans = isi(t, rng, nama)
        hasil.append({"id": f"{awalan}-{i:05d}", "bahasa": b, "genre": genre, "teks": teks, "spans": spans})
    return hasil


def _tulis(fail: Path, dokumen: list[dict]) -> dict:
    with open(fail, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(d, ensure_ascii=False) + "\n" for d in dokumen)
    return {"dokumen": len(dokumen), "sha256": hashlib.sha256(fail.read_bytes()).hexdigest()}


def jana(keluar: Path) -> dict:
    """latih + dev dari data/templat/; ujian dari data/templat_ujian/ (simpanan, benih berasingan).
    Menambah templat latih/dev TIDAK mengubah split ujian."""
    k = konfig.utama()["jana"]
    nama = yaml.safe_load((AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    n = k["bilangan_dokumen"]
    n_ujian = round(n * k["split"]["ujian"])
    n_dev = round(n * k["split"]["dev"])
    rng = random.Random(k["benih"])
    biasa = _dokumen(n - n_ujian, rng, _templat(), gabung_nama(nama, AKAR / k["nama_tambahan"]), "mypii")
    rng.shuffle(biasa)
    ujian = _dokumen(n_ujian, random.Random(k["benih"] + 1), _templat("data/templat_ujian"), nama, "mypii-u")
    keluar.mkdir(parents=True, exist_ok=True)
    ringkasan = {
        "latih": _tulis(keluar / "latih.jsonl", biasa[n_dev:]),
        "dev": _tulis(keluar / "dev.jsonl", biasa[:n_dev]),
        "ujian": _tulis(keluar / "ujian.jsonl", ujian),
    }
    # latih/dev berubah bila templat ditambah → CINCANGAN.json (boleh dikemas gelung). KUNCI.json = split ujian SAHAJA dan
    # tidak pernah ditulis semula senyap: wujud + cincangan lain = BERHENTI (ADR-003; gelung dilarang menyentuh KUNCI.json).
    cincangan = {s: ringkasan[s] for s in ("latih", "dev")}
    (keluar / "CINCANGAN.json").write_text(json.dumps(cincangan, indent=2) + "\n")
    _kunci(keluar / "KUNCI.json", "ujian", ringkasan["ujian"])
    u2 = jana_ujian2(keluar)
    if u2:
        ringkasan["ujian2"] = u2
    return ringkasan


def gabung_nama(nama: dict, fail_tambahan: Path) -> dict:
    """nama.yaml ∪ nama_tambahan untuk latih/dev SAHAJA (B2): syarikat + bandar disatukan (tanpa pendua, susunan tetap), nama orang
    berkumpulan dibawa di `TAMBAHAN`. Fail tiada = `nama` tidak berubah (dev lama)."""
    if not fail_tambahan.exists():
        return nama
    tambahan = yaml.safe_load(fail_tambahan.read_text(encoding="utf-8"))
    gabung = {**nama, TAMBAHAN: tambahan}
    for kat in ("syarikat", "bandar"):
        gabung[kat] = list(dict.fromkeys([*nama[kat], *tambahan.get(kat, [])]))
    return gabung


def _kunci(fail: Path, split: str, ringkasan: dict) -> None:
    """Cipta fail kunci HANYA bila tiada; wujud + cincangan lain = BERHENTI tanpa menyentuhnya (ADR-003, ADR-004)."""
    if not fail.exists():
        fail.write_text(json.dumps({split: ringkasan}, indent=2) + "\n")
    elif json.loads(fail.read_text())[split] != ringkasan:
        raise SystemExit(f"split {split} BERUBAH berbanding {fail.name} — BERHENTI dan laporkan (program.md); {fail.name} tidak disentuh")


def jana_ujian2(keluar: Path, templat: str | None = None, fail_nama: Path | None = None) -> dict | None:
    """Split ujian2 (PELAN-B B1): templat LLM `data/templat_ujian2/` + nama `data/nama_ujian2.yaml` (bersilang kosong dengan
    nama.yaml), benih + 2. Tiada templat/nama = langkau (None). Tidak menyentuh latih/dev/ujian."""
    k = konfig.utama()["jana"]
    templat = templat or k["templat_ujian2"]
    fail_nama = fail_nama or AKAR / k["nama_ujian2"]
    t = _templat(templat)
    if not t or not fail_nama.exists():
        return None
    nama = yaml.safe_load(fail_nama.read_text(encoding="utf-8"))
    dok = _dokumen(k["bilangan_ujian2"], random.Random(k["benih"] + 2), t, nama, "mypii-u2")
    ringkasan = _tulis(keluar / "ujian2.jsonl", dok)
    _kunci(keluar / "KUNCI2.json", "ujian2", ringkasan)
    return ringkasan


# --- Data v3 (PELAN-V2 P3, PRA-DAFTAR pindaan 2026-11-04). Fungsi BAHARU sahaja: fungsi v1 di atas tidak diubah, rng berasingan. ---

SLOT_V3 = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")  # v3 membenarkan digit (`{NEG12_TANPA}`); SLOT v1 tidak diubah

V3_POSITIF = {  # slot → (label emas, penjana, kategori v3 atau None)
    "MY_NRIC": ("MY_NRIC", nilai_palsu.nric, None),
    "MY_SSM_LAMA": ("MY_SSM", nilai_palsu.ssm_lama, None),
    "MY_SSM_LLP": ("MY_SSM", nilai_v3.llp, "b"),
    "MY_PHONE_BS": ("MY_PHONE", nilai_v3.talian_bs, "c"),
    "MY_ROB": ("MY_SSM", nilai_v3.rob_lama, "a"),  # (a) GUGUR: penjana enggan selagi tiada awalan disahkan
}


def _positif_v3(slot: str, r: random.Random, kb: dict) -> tuple[str, str, list[str]]:
    """(nilai, label, kategori) bagi slot positif v3. `{OCR_<E>}`/`{PATAH_<E>}` memaksa (d); slot biasa MY_SSM/MY_PHONE menjadi (b)/(c)
    dengan kebarangkalian `jana_v3.kebarangkalian`, dan setiap nilai positif boleh menjadi (d) OCR atau patah baris."""
    paksa, entiti = (slot.split("_", 1) if slot.startswith(("OCR_", "PATAH_")) else (None, slot))
    kat: list[str] = []
    if entiti == "MY_SSM" and r.random() < kb["llp"]:
        entiti = "MY_SSM_LLP"
    elif entiti == "MY_PHONE" and r.random() < kb["talian_bs"]:
        entiti = "MY_PHONE_BS"
    if entiti in V3_POSITIF:
        label, penjana, k = V3_POSITIF[entiti]
        kat += [k] if k else []
    else:
        label, penjana = entiti, nilai_v3.ssm if entiti == "MY_SSM" else ENTITI[entiti]
    nilai = penjana(r)
    x = r.random() if paksa is None else -1.0
    ubah = None
    if paksa == "OCR" or (paksa is None and x < kb["ocr"]):
        ubah = nilai_v3.ocr(r, nilai)
    elif paksa == "PATAH" or x < kb["ocr"] + kb["patah"]:
        ubah = nilai_v3.patah(r, nilai, label)
    if ubah is not None:
        nilai, kat = ubah, kat + ["d"]
    return nilai, label, kat


def _slot_positif_v3() -> set[str]:
    asas = {*ENTITI, *V3_POSITIF}
    return asas | {f"{a}_{e}" for a in ("OCR", "PATAH") for e in ENTITI}


def isi_v3(templat: str, rng: random.Random, nama: dict) -> tuple[str, list[dict], list[dict]]:
    """Seperti `isi` (v1) + slot v3 → (teks, spans emas, kategori [{kategori, mula, tamat}]). Kategori (e) = `{NEG12_TANPA}` atau
    `{NEG_AHLI}` yang diganti nilai 12 digit berbentuk MyKad (kebarangkalian `neg12`), DICATAT hanya bila teks akhir tiada kata
    `konteks_umum.negatif` (tiada label emas)."""
    kb = konfig.utama()["jana_v3"]["kebarangkalian"]
    positif = _slot_positif_v3()
    bahagian: list[str] = []
    spans, kategori, calon_e = [], [], []
    pengisi = {
        "NAMA": lambda r: nama_orang(r, nama, "".join(bahagian)),
        "SYARIKAT": lambda r: r.choice(nama["syarikat"]),
        "BANDAR": lambda r: r.choice(nama["bandar"]),
        "NEG": nilai_palsu.negatif,
        "TARIKH": nilai_palsu.tarikh,
        **NEGATIF_P1,
    }
    pos, akhir = 0, 0
    for m in SLOT_V3.finditer(templat):
        bahagian.append(templat[akhir:m.start()])
        pos += m.start() - akhir
        slot = m.group(1)
        if slot in positif:
            nilai, label, kat = _positif_v3(slot, rng, kb)
            spans.append({"mula": pos, "tamat": pos + len(nilai), "entiti": label})
            kategori += [{"kategori": k, "mula": pos, "tamat": pos + len(nilai)} for k in kat]
        elif slot == "NEG12_TANPA" or (slot == "NEG_AHLI" and rng.random() < kb["neg12"]):
            nilai = nilai_v3.neg12(rng)
            calon_e.append({"kategori": "e", "mula": pos, "tamat": pos + len(nilai)})
        else:
            nilai = pengisi[slot](rng)
        bahagian.append(nilai)
        pos += len(nilai)
        akhir = m.end()
    bahagian.append(templat[akhir:])
    teks = "".join(bahagian)
    if calon_e and not nilai_v3.ada_kata_negatif(teks):
        kategori += calon_e
    return teks, spans, sorted(kategori, key=lambda x: (x["mula"], x["kategori"]))


def _dokumen_v3(n: int, rng: random.Random, templat: dict, nama: dict, awalan: str) -> list[dict]:
    """Seperti `_dokumen` v1 tetapi `isi_v3` + medan `kategori`; bahasa/nisbah negatif dari `jana_v3`."""
    k = konfig.utama()["jana_v3"]
    bahasa = [b for b in k["bahasa"] if b in templat] or list(templat)
    berat = [k["bahasa"].get(b, 1) for b in bahasa]
    positif = _slot_positif_v3()
    keluar = []
    for i in range(n):
        b = rng.choices(bahasa, berat)[0]
        tanpa_entiti = [t for t in templat[b] if not set(SLOT_V3.findall(t[1])) & positif]
        sumber = tanpa_entiti if tanpa_entiti and rng.random() < k["nisbah_negatif_keras"] else templat[b]
        genre, t = rng.choice(sumber)
        teks, spans, kategori = isi_v3(t, rng, nama)
        keluar.append({"id": f"{awalan}-{i:05d}", "bahasa": b, "genre": genre, "teks": teks, "spans": spans, "kategori": kategori})
    return keluar


def _templat_v3(folder_senarai: list[str]) -> dict[str, list[tuple[str, str]]]:
    gabung: dict[str, list[tuple[str, str]]] = {}
    for folder in folder_senarai:
        for b, senarai in _templat(folder).items():
            gabung.setdefault(b, []).extend(senarai)
    return gabung


def jana_v3(keluar: Path | None = None) -> dict:
    """latih3 + dev3 (benih + `benih_tambah.latih3`, templat `jana_v3.templat`) dan, bila templat + nama ujian3 wujud, ujian3 (benih +
    `benih_tambah.ujian3`). CINCANGAN3.json = latih3/dev3; KUNCI3.json = ujian3 (tidak ditulis semula senyap — ADR-003)."""
    k, kj = konfig.utama()["jana_v3"], konfig.utama()["jana"]
    keluar = keluar or AKAR / k["keluar"]
    nama = gabung_nama(yaml.safe_load((AKAR / "data/nama.yaml").read_text(encoding="utf-8")), AKAR / kj["nama_tambahan"])
    n_latih, n_dev = k["bilangan"]["latih3"], k["bilangan"]["dev3"]
    rng = random.Random(kj["benih"] + k["benih_tambah"]["latih3"])
    biasa = _dokumen_v3(n_latih + n_dev, rng, _templat_v3(k["templat"]), nama, "mypii3")
    rng.shuffle(biasa)
    keluar.mkdir(parents=True, exist_ok=True)
    ringkasan = {"latih3": _tulis(keluar / "latih3.jsonl", biasa[n_dev:]), "dev3": _tulis(keluar / "dev3.jsonl", biasa[:n_dev])}
    (keluar / "CINCANGAN3.json").write_text(json.dumps(ringkasan, indent=2) + "\n")
    t3, fail_nama = _templat(k["templat_ujian3"]), AKAR / k["nama_ujian3"]
    if t3 and fail_nama.exists():
        nama3 = yaml.safe_load(fail_nama.read_text(encoding="utf-8"))
        dok = _dokumen_v3(k["bilangan"]["ujian3"], random.Random(kj["benih"] + k["benih_tambah"]["ujian3"]), t3, nama3, "mypii-u3")
        ringkasan["ujian3"] = _tulis(keluar / "ujian3.jsonl", dok)
        _kunci(keluar / "KUNCI3.json", "ujian3", ringkasan["ujian3"])
    return ringkasan


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--keluar", type=Path, default=None)
    p.add_argument("--v3", action="store_true", help="jana data v3 (latih3/dev3[/ujian3]) ke jana_v3.keluar")
    a = p.parse_args()
    print(json.dumps(jana_v3(a.keluar) if a.v3 else jana(a.keluar or AKAR / "data/bench"), indent=2))
