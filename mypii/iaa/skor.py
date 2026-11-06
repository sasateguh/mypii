"""Skor IAA (PELAN-IAA P9, ADR-015 §Skor): persetujuan penyemak + kadar ralat label → `iaa.skor.keluar` + blok BANDINGAN.

    python -m mypii.iaa.skor   # `make iaa-skor`; membaca data/iaa/sampel.json + data/iaa/jawapan/<penyemak>.jsonl SAHAJA

Tiada teks dokumen dibaca: split/bahasa datang dari sampel (id tidak ditulis ke output), jawapan dari eksport/llm (format sama).
Hanya dokumen berstatus `siap` dikira; `separa`/`rosak`/`gagal` dilapor sebagai kiraan.
- (a) κ Cohen per span + % persetujuan mentah; (c) κ per dokumen + %; (b) F1 persetujuan = 2|A∩B| / (|A|+|B|) mikro atas dokumen,
  nilai dinormalkan (`normal`); dokumen yang kedua-duanya `tiada` dilapor berasingan.
- Kadar ralat setiap penyemak setiap split: span salah/jenis lain, dokumen dengan PII tidak bertanda, dokumen janggal; beza dev − ujian2.
- CI = bootstrap persentil atas DOKUMEN (`statistik.indeks_bootstrap/persentil`, ulangan/benih/aras = `nilai.statistik`).
Pasangan yang penyemaknya belum ada = "menunggu <id> (x/n)" — bukan ralat.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

from mypii import konfig
from mypii.nilai import statistik
from mypii.nilai.bandingan import tulis_blok

AKAR = konfig.AKAR
METRIK_RALAT = ("span_salah", "tak_bertanda", "janggal")


def kappa(pasangan: list[tuple[str, str]]) -> float | None:
    """κ Cohen atas pasangan label (A, B); None bila tiada data atau persetujuan jangkaan = 1 (κ tidak tertakrif)."""
    n = len(pasangan)
    if not n:
        return None
    po = sum(a == b for a, b in pasangan) / n
    kat = {x for p in pasangan for x in p}
    pe = sum((sum(a == k for a, _ in pasangan) / n) * (sum(b == k for _, b in pasangan) / n) for k in kat)
    return None if pe >= 1 else (po - pe) / (1 - pe)


def setuju(pasangan: list[tuple[str, str]]) -> float | None:
    return sum(a == b for a, b in pasangan) / len(pasangan) if pasangan else None


def normal(v: str) -> str:
    """MyKad/telefon → digit sahaja; SSM (ada huruf) → alnum huruf besar. Sama untuk digit, jadi satu peraturan."""
    return re.sub(r"[^0-9A-Z]", "", v.upper())


def nilai_b(j: dict) -> set[str]:
    """Nilai (b) dinormalkan; jawapan `tiada` tidak membawa `nilai` (stor + llm), jadi set kosong."""
    return {normal(v) for v in j["b"].get("nilai", [])} - {""}


def n_span(j: dict) -> int:
    return sum(1 for k in j if re.fullmatch(r"a\d+", k))


def muat_jawapan(laluan: Path) -> dict[int, dict] | None:
    """`<penyemak>.jsonl` → {urutan: baris}; None bila fail tiada (penyemak belum dieksport)."""
    if not laluan.exists():
        return None
    return {b["urutan"]: b for b in map(json.loads, laluan.read_text(encoding="utf-8").splitlines()) if b}


def _siap(baris: dict[int, dict]) -> dict[int, dict]:
    return {u: b["jawapan"] for u, b in baris.items() if b["status"] == "siap"}


# ---- statistik per dokumen: setiap metrik = fungsi atas senarai sumbangan dokumen (dikongsi oleh titik + bootstrap) ----

def _nisbah(sumb: list[tuple[float, float]]) -> float | None:
    a, b = sum(x for x, _ in sumb), sum(y for _, y in sumb)
    return a / b if b else None


def _f1(sumb: list[tuple[int, int]]) -> float | None:
    return _nisbah([(2 * i, s) for i, s in sumb])


def _rata(f):
    return lambda sumb: f([p for d in sumb for p in d])


def _ci(sumb: list, f, indeks: list[list[int]], aras: float, dp: int) -> dict:
    titik = f(sumb)
    sah = [v for v in (f([sumb[i] for i in ix]) for ix in indeks) if v is not None]
    a = (1 - aras) / 2
    return {"nilai": None if titik is None else round(titik, dp),
            "bawah": round(statistik.persentil(sah, a), dp) if sah else None,
            "atas": round(statistik.persentil(sah, 1 - a), dp) if sah else None}


def pasangan(ja: dict[int, dict], jb: dict[int, dict], st: dict) -> dict:
    """Persetujuan dua penyemak atas dokumen yang SIAP oleh kedua-duanya."""
    u = sorted(set(ja) & set(jb))
    sa = [[(ja[x][f"a{n}"], jb[x][f"a{n}"]) for n in range(1, n_span(ja[x]) + 1)] for x in u]
    sc = [[(ja[x]["c"], jb[x]["c"])] for x in u]
    sb = [(len(nilai_b(ja[x]) & nilai_b(jb[x])), len(nilai_b(ja[x])) + len(nilai_b(jb[x]))) for x in u]
    ix = statistik.indeks_bootstrap(len(u), st["ulangan"], st["benih"]) if u else []
    ci = lambda s, f: _ci(s, f, ix, st["aras"], st["perpuluhan"])
    return {"dokumen": len(u), "span": sum(map(len, sa)),
            "a": {"kappa": ci(sa, _rata(kappa)), "setuju": ci(sa, _rata(setuju))},
            "c": {"kappa": ci(sc, _rata(kappa)), "setuju": ci(sc, _rata(setuju))},
            "b": {"f1": ci(sb, _f1), "nilai_a": sum(len(nilai_b(ja[x])) for x in u),
                  "nilai_b": sum(len(nilai_b(jb[x])) for x in u),
                  "kedua_tiada": sum(not nilai_b(ja[x]) and not nilai_b(jb[x]) for x in u)}}


def _sumb_ralat(j: dict, pil: dict) -> dict:
    """pil = `iaa.pilihan`: a[0] = betul, b[1] = ada, c[1] = janggal."""
    n = n_span(j)
    return {"span_salah": (sum(j[f"a{i}"] != pil["a"][0] for i in range(1, n + 1)), n),
            "tak_bertanda": (int(j["b"].get("pilih") == pil["b"][1]), 1),
            "janggal": (int(j["c"] == pil["c"][1]), 1)}


def ralat(j: dict[int, dict], split_of: dict[int, str], st: dict, split: list[str], pil: dict) -> dict:
    """Kadar ralat label setiap split + beza split[0] − split[1] (bootstrap berasingan dalam setiap split)."""
    out, sampel = {}, {}
    for i, s in enumerate(split):
        sumb = [_sumb_ralat(j[u], pil) for u in sorted(j) if split_of.get(u) == s]
        ix = statistik.indeks_bootstrap(len(sumb), st["ulangan"], st["benih"] + i) if sumb else []
        out[s] = {"dokumen": len(sumb), "span": sum(x["span_salah"][1] for x in sumb)}
        sampel[s] = {}
        for m in METRIK_RALAT:
            d = [x[m] for x in sumb]
            out[s][m] = _ci(d, _nisbah, ix, st["aras"], st["perpuluhan"])
            sampel[s][m] = (_nisbah(d), [_nisbah([d[k] for k in x]) for x in ix])
    if len(split) == 2 and all(out[s]["dokumen"] for s in split):
        a, b, beza = split[0], split[1], {}
        for m in METRIK_RALAT:
            (ta, ra), (tb, rb) = sampel[a][m], sampel[b][m]
            d = [x - y for x, y in zip(ra, rb) if x is not None and y is not None]
            q = (1 - st["aras"]) / 2
            beza[m] = {"nilai": None if ta is None or tb is None else round(ta - tb, st["perpuluhan"]),
                       "bawah": round(statistik.persentil(d, q), st["perpuluhan"]) if d else None,
                       "atas": round(statistik.persentil(d, 1 - q), st["perpuluhan"]) if d else None}
        out[f"{a}-{b}"] = beza
    return out


def kira(sampel: dict, jawapan: dict[str, dict[int, dict] | None], k: dict, st: dict) -> dict:
    n = sampel["n"]
    split_of = {d["urutan"]: d["split"] for d in sampel["dokumen"]}
    split = list(k["sampel"]["split"])
    status = {}
    for p, b in jawapan.items():
        status[p] = {"siap": 0} if b is None else {s: sum(x["status"] == s for x in b.values())
                                                     for s in ("siap", "separa", "rosak", "gagal")}
        status[p]["n"] = n
    ada = {p: _siap(b) for p, b in jawapan.items() if b is not None and _siap(b)}
    psg = {}
    utama = tuple(k["skor"]["utama"])
    ada_utama = all(p in ada for p in utama)
    for a, b in map(tuple, k["skor"]["pasangan"]):
        nama = f"{a}×{b}"
        tiada = [p for p in (a, b) if p not in ada]
        r = ({"keadaan": "menunggu " + ", ".join(f"{p} ({status.get(p, {}).get('siap', 0)}/{n})" for p in tiada)}
             if tiada else {"keadaan": "lengkap" if min(status[a]["siap"], status[b]["siap"]) == n else "separa"}
             | pasangan(ada[a], ada[b], st))
        psg[nama] = r | {"utama": (a, b) == utama if ada_utama else (a, b) == tuple(k["skor"]["pasangan"][0])}
    return {"n": n, "sampel_sha256": sampel.get("sha256"), "statistik": {x: st[x] for x in ("ulangan", "benih", "aras")},
            "penyemak": status, "pasangan": psg,
            "ralat": {p: ralat(j, split_of, st, split, k["pilihan"]) for p, j in sorted(ada.items())}}


def _f(x: dict) -> str:
    if x["nilai"] is None:
        return "—"
    ci = "" if x["bawah"] is None else f" [{x['bawah']:.3f}, {x['atas']:.3f}]"
    return f"{x['nilai']:.3f}{ci}"


def blok(h: dict, sumber: str) -> str:
    """Markdown blok jana; setiap angka dari `h`."""
    L = [f"<!-- dijana `make iaa-skor` (mypii/iaa/skor.py) dari `{sumber}` — JANGAN sunting dengan tangan -->", "",
         (f"Sampel n = {h['n']} dokumen; CI {int(h['statistik']['aras'] * 100)}% bootstrap persentil atas dokumen "
          f"(ulangan {h['statistik']['ulangan']}, benih {h['statistik']['benih']})."), "",
         "| Penyemak | siap | separa | rosak | gagal |", "|---|---|---|---|---|"]
    for p, s in sorted(h["penyemak"].items()):
        L.append(f"| {p} | {s['siap']}/{s['n']} | {s.get('separa', 0)} | {s.get('rosak', 0)} | {s.get('gagal', 0)} |")
    L += ["", "**Persetujuan** (dokumen siap oleh kedua-dua penyemak sahaja)", "",
          "| Pasangan | keadaan | dokumen | span | κ (a) | % setuju (a) | κ (c) | % setuju (c) | F1 (b) | kedua-dua tiada (b) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for nama, r in h["pasangan"].items():
        tanda = f"**{nama}** (utama)" if r["utama"] else nama
        if "dokumen" not in r:
            L.append(f"| {tanda} | {r['keadaan']} | — | — | — | — | — | — | — | — |")
            continue
        L.append(f"| {tanda} | {r['keadaan']} | {r['dokumen']} | {r['span']} | {_f(r['a']['kappa'])} | {_f(r['a']['setuju'])} | "
                 f"{_f(r['c']['kappa'])} | {_f(r['c']['setuju'])} | {_f(r['b']['f1'])} | {r['b']['kedua_tiada']} |")
    L += ["", "**Kadar ralat label** (pecahan; menurut setiap penyemak — deskriptif, tiada ujian hipotesis)", "",
          "| Penyemak | split | dokumen | span | span salah/jenis lain | dokumen PII tidak bertanda | dokumen janggal |",
          "|---|---|---|---|---|---|---|"]
    for p, r in h["ralat"].items():
        for s, x in r.items():
            if "dokumen" in x:
                L.append(f"| {p} | {s} | {x['dokumen']} | {x['span']} | {_f(x['span_salah'])} | {_f(x['tak_bertanda'])} | {_f(x['janggal'])} |")
            else:
                L.append(f"| {p} | beza {s} | — | — | {_f(x['span_salah'])} | {_f(x['tak_bertanda'])} | {_f(x['janggal'])} |")
    menunggu = [f"{n}: {r['keadaan']}" for n, r in h["pasangan"].items() if "dokumen" not in r]
    if menunggu:
        L += ["", "Belum dikira — " + "; ".join(menunggu) + ". Baris LLM sahaja ialah pandangan SATU penyemak mesin, bukan persetujuan."]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    k = konfig.utama()["iaa"]
    st = konfig.utama()["nilai"]["statistik"]
    fs = AKAR / k["sampel"]["fail"]
    sampel = json.loads(fs.read_text(encoding="utf-8")) | {"sha256": hashlib.sha256(fs.read_bytes()).hexdigest()}
    ids = list(dict.fromkeys(p for psg in k["skor"]["pasangan"] for p in psg))
    jawapan = {p: muat_jawapan(AKAR / k["skor"]["jawapan"] / f"{p}.jsonl") for p in ids}
    h = kira(sampel, jawapan, k, st)
    keluar = AKAR / k["skor"]["keluar"]
    keluar.parent.mkdir(parents=True, exist_ok=True)
    keluar.write_text(json.dumps(h, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tulis_blok(AKAR / k["skor"]["laporan"], blok(h, k["skor"]["keluar"]), k["skor"]["penanda"])
    for nama, r in h["pasangan"].items():
        print(f"{nama}: {r['keadaan']}" + (f" dokumen={r['dokumen']} span={r['span']}" if "dokumen" in r else ""))
    for p, s in sorted(h["penyemak"].items()):
        print(f"{p}: siap={s['siap']}/{s['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
