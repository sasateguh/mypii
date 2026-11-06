"""Ramalan pengelas konteks (PELAN-V2 P11): artifak `model/konteks-v2.json` (pekali + perbendaharaan) → kebarangkalian numpy.

Tiada sklearn, tiada rangkaian. Artifak disemak sha256 = config `konteks.sha256` sebelum dipakai (artifak lain = ralat, bukan senyap).
"""

import hashlib
import json
from functools import lru_cache

import numpy as np

from mypii import konfig
from mypii.pengecam.ciri import ciri


def _k() -> dict:
    return konfig.utama()["konteks"]


@lru_cache(maxsize=1)
def _model() -> dict | None:
    k = _k()
    if not k.get("aktif"):
        return None
    laluan = konfig.akar_data() / k["artifak"]
    data = laluan.read_bytes()
    if hashlib.sha256(data).hexdigest() != k["sha256"]:
        raise RuntimeError(f"{k['artifak']}: sha256 tidak sama dengan config konteks.sha256 — latih semula atau kemas config")
    m = json.loads(data)
    return {e: {"vocab": x["vocab"], "w": np.asarray(x["w"], dtype=np.float64), "b": float(x["b"])}
            for e, x in m["entiti"].items()}


def kebarangkalian(teks: str, mula: int, tamat: int, entiti: str) -> float | None:
    """P(calon = PII sebenar) atau None bila pengelas tidak aktif / tiada model entiti itu."""
    m = _model()
    if not m or entiti not in m:
        return None
    e = m[entiti]
    idx = [e["vocab"][f] for f in ciri(teks, mula, tamat, _k()["ciri"]) if f in e["vocab"]]
    z = e["b"] + float(e["w"][idx].sum()) if idx else e["b"]
    return float(1.0 / (1.0 + np.exp(-z)))
