"""Latih pengelas konteks (PELAN-V2 P10, PRA-DAFTAR Keputusan 4) → `model/konteks-v2.json`.

    python -m mypii.konteks_latih            # split = config konteks.split_latih SAHAJA

- Split selain `konteks.split_latih`, atau dalam `konteks.split_tolak` / `nilai.split_dikunci`, DITOLAK SEBELUM fail dibaca.
- Calon = padanan corak pengecam (normalisasi + validasi, TANPA konteks frasa) setiap entiti; label = span emas tepat (mula, tamat, entiti).
- Ciri = `mypii.pengecam.ciri.ciri` (sama dengan ramalan); perbendaharaan = ciri dengan kekerapan dokumen ≥ `min_kekerapan`.
- scikit-learn LogisticRegression (extra `latih`) = alat LATIH sahaja; benih/C/iterasi dari config. Artifak = JSON terisih, pekali
  dibundar `perpuluhan` → latih semula = bait sama. Cetak sha256 artifak (salin ke config `konteks.sha256`).
"""

import argparse
import hashlib
import json
import sys
from collections import Counter

from mypii import konfig
from mypii.pengecam import semua_pengecam
from mypii.pengecam.ciri import ciri


def _k() -> dict:
    return konfig.utama()["konteks"]


def semak_split(split: str) -> None:
    k = _k()
    if split != k["split_latih"] or split in k["split_tolak"] or split in konfig.utama()["nilai"]["split_dikunci"]:
        raise SystemExit(f"split {split}: pengelas konteks hanya dilatih atas konteks.split_latih ({k['split_latih']})")


def calon(dokumen: list[dict]) -> dict[str, tuple[list[list[str]], list[int]]]:
    """entiti → (senarai ciri setiap calon, label 0/1)."""
    kc = _k()["ciri"]
    keluar: dict[str, tuple[list, list]] = {}
    pengecam = semua_pengecam("en")
    for d in dokumen:
        emas = {(s["mula"], s["tamat"], s["entiti"]) for s in d["spans"]}
        for p in pengecam:
            e = p.supported_entities[0]
            dilihat = set()
            for r in p.analyze(d["teks"], [e]):
                if (r.start, r.end) in dilihat:
                    continue
                dilihat.add((r.start, r.end))
                x, y = keluar.setdefault(e, ([], []))
                x.append(ciri(d["teks"], r.start, r.end, kc))
                y.append(int((r.start, r.end, e) in emas))
    return keluar


def latih(data: dict[str, tuple[list[list[str]], list[int]]]) -> dict:
    import numpy as np
    from scipy.sparse import csr_matrix
    from sklearn.linear_model import LogisticRegression

    k = _k()
    model = {}
    for e in sorted(data):
        x, y = data[e]
        kira = Counter(f for fs in x for f in set(fs))
        vocab = {f: i for i, f in enumerate(sorted(f for f, n in kira.items() if n >= k["min_kekerapan"]))}
        baris, lajur = [], []
        for i, fs in enumerate(x):
            for f in fs:
                if f in vocab:
                    baris.append(i)
                    lajur.append(vocab[f])
        X = csr_matrix((np.ones(len(baris)), (baris, lajur)), shape=(len(x), len(vocab)))
        lr = LogisticRegression(C=k["C"], max_iter=k["iterasi_maks"], solver="liblinear", random_state=k["benih"])
        lr.fit(X, np.asarray(y))
        p = k["perpuluhan"]
        model[e] = {"vocab": vocab, "w": [round(float(v), p) for v in lr.coef_[0]], "b": round(float(lr.intercept_[0]), p),
                    "calon": len(y), "positif": int(sum(y))}
    return {"versi": 1, "split": k["split_latih"], "ciri": k["ciri"], "entiti": model}


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--split", default=_k()["split_latih"])
    split = a.parse_args().split
    semak_split(split)   # SEBELUM fail dibaca
    fail = konfig.AKAR / konfig.fail_split(split)
    dokumen = [json.loads(x) for x in fail.read_text(encoding="utf-8").splitlines()]
    m = latih(calon(dokumen))
    keluar = konfig.AKAR / _k()["artifak"]
    keluar.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(m, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    keluar.write_bytes(data)
    print(json.dumps({e: {"calon": x["calon"], "positif": x["positif"], "ciri": len(x["vocab"])} for e, x in m["entiti"].items()}))
    print(f"sha256 {hashlib.sha256(data).hexdigest()}  bait {len(data)}  → config konteks.sha256")
    return 0


if __name__ == "__main__":
    sys.exit(main())
