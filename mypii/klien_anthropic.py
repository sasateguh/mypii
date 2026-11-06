"""Klien API Anthropic TERUS (PELAN-CLAUDE, ADR-016) + lejar belanja dengan had keras. Hanya `garis.ramal_llm` memanggilnya.

Model garis dasar `anthropic/<id>` dihantar melalui SDK rasmi `anthropic` (extra `garis`, diimport MALAS) — bukan 9router.
Semua nilai (harga, had USD, max_tokens, parameter setiap model, nama env kunci, laluan lejar) = `config/mypii.yaml`
`garis_dasar.llm.anthropic`. Kunci dari env sahaja; tidak pernah dicetak, dicache atau ditulis ke lejar.
`temperature` TIDAK dihantar (API menolak nilai bukan lalai untuk Sonnet 5.5 / Haiku 5.5; Opus 5.5 / Fable 5.1 menolaknya terus).
`max_tokens` = `max_tokens` model bila ada, lain lalai global (PRA-DAFTAR pindaan 2026-11-03: model berfikir perlu ruang lebih).
`stop_reason: refusal` = jawapan KOSONG (rosak bila diurai, dikira) — bukan ralat yang diulang; tiada `fallbacks` (model lain mencemar).
"""

import functools
import json
import math
import os
import threading
from pathlib import Path

from mypii import konfig

AWALAN = "anthropic/"


class HadDicapai(RuntimeError):
    """Panggilan TIDAK dibuat kerana ia boleh melepasi had belanja."""


class TolakAPI(RuntimeError):
    """API menolak permintaan (4xx selain 429) — bukan sementara; larian dihentikan (jangan teka parameter lain)."""


def _k() -> dict:
    return konfig.utama()["garis_dasar"]["llm"]["anthropic"]


def ialah(model: str) -> bool:
    return model.startswith(AWALAN)


def tetapan(model: str) -> dict:
    """`anthropic/<id>` → {id, harga, permintaan}. `permintaan` = medan yang dihantar selain model/mesej (dan masuk kunci cache)."""
    k, mid = _k(), model.removeprefix(AWALAN)
    if mid not in k["model"]:
        raise SystemExit(f"model {model}: tiada tetapan dalam config garis_dasar.llm.anthropic.model")
    m = k["model"][mid]
    return {"id": mid, "harga": m["harga"], "permintaan": {"max_tokens": m.get("max_tokens", k["max_tokens"]), **m["parameter"]}}


def kos(usage: dict, harga: dict) -> float:
    return (usage["masuk"] * harga["masuk"] + usage["keluar"] * harga["keluar"]) / 1e6


def kos_terburuk(prompt: str, t: dict) -> float:
    """Token masuk dianggar dari aksara (dibundar ke atas) + `max_tokens` penuh sebagai keluar."""
    masuk = math.ceil(len(prompt) / _k()["aksara_setiap_token"])
    return kos({"masuk": masuk, "keluar": t["permintaan"]["max_tokens"]}, t["harga"])


@functools.lru_cache(maxsize=1)
def _klien(kunci: str, masa: float, ulang: int):
    import anthropic

    return anthropic.Anthropic(api_key=kunci, timeout=masa, max_retries=ulang)


def hantar(model_id: str, prompt: str, permintaan: dict) -> tuple[str, dict]:
    """Satu mesej `user` → (gabungan blok `text`, usage {masuk, keluar}); refusal → ("", usage) (kos tetap direkod).
    Mesej ralat tidak memuatkan kunci atau prompt."""
    k = _k()
    kunci = os.environ.get(k["env_kunci"])
    if not kunci:
        raise SystemExit(f"env {k['env_kunci']} tiada — `set -a; . ~/ops/mypii/anthropic.env; set +a` dahulu")
    import anthropic  # selepas semakan kunci: mesej jelas walaupun extra `garis` tiada (CI)

    try:
        r = _klien(kunci, k["had_masa_saat"], k["ulang_sdk"]).messages.create(
            model=model_id, messages=[{"role": "user", "content": prompt}], **permintaan)
    except anthropic.RateLimitError as e:
        raise OSError(f"RateLimitError {e.status_code}") from None
    except anthropic.APIStatusError as e:
        if e.status_code < 500 and e.status_code not in (408, 409):
            raise TolakAPI(f"{model_id}: HTTP {e.status_code} {type(e).__name__}: {e.message}") from None
        raise OSError(f"{type(e).__name__} {e.status_code}") from None
    except anthropic.APIConnectionError as e:
        raise OSError(type(e).__name__) from None
    # blok `thinking` (Opus/Fable) diabaikan; refusal = jawapan kosong walaupun ada teks separa
    teks = "" if r.stop_reason == "refusal" else "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
    return teks, {"masuk": r.usage.input_tokens, "keluar": r.usage.output_tokens}


class Lejar:
    """Belanja terkumpul (dikomit). `tempah` di bawah kunci benang: terkumpul + tempahan dalam penerbangan + kos terburuk > had
    → False dan tiada panggilan lagi selepas itu. `rekod` melepaskan tempahan, menambah kos SEBENAR dari usage, menulis atomik."""

    def __init__(self, laluan: Path, had_usd: float):
        self.laluan, self.had = laluan, float(had_usd)
        self._kunci = threading.Lock()
        self._tempahan = 0.0
        self.dicapai = False
        self.henti = False  # TolakAPI dalam satu benang → benang lain tidak memanggil lagi
        self.usd_larian = 0.0
        self.data = json.loads(laluan.read_text(encoding="utf-8")) if laluan.exists() else {"jumlah_usd": 0.0, "model": {}}

    @classmethod
    def dari_config(cls, akar: Path = konfig.AKAR) -> "Lejar":
        k = _k()
        return cls(akar / k["lejar"], k["had_usd"])

    def tempah(self, usd: float) -> bool:
        with self._kunci:
            if self.dicapai or self.data["jumlah_usd"] + self._tempahan + usd > self.had:
                self.dicapai = True
                return False
            self._tempahan += usd
            return True

    def lepas(self, usd: float) -> None:
        with self._kunci:
            self._tempahan -= usd

    def rekod(self, model: str, usage: dict, harga: dict, tempahan: float) -> None:
        with self._kunci:
            self._tempahan -= tempahan
            usd = kos(usage, harga)
            m = self.data["model"].setdefault(model, {"masuk": 0, "keluar": 0, "usd": 0.0, "panggilan": 0})
            m["masuk"] += usage["masuk"]
            m["keluar"] += usage["keluar"]
            m["panggilan"] += 1
            m["usd"] = round(m["usd"] + usd, 6)
            self.data["jumlah_usd"] = round(sum(x["usd"] for x in self.data["model"].values()), 6)
            self.usd_larian += usd
            self._tulis()

    def _tulis(self) -> None:
        self.laluan.parent.mkdir(parents=True, exist_ok=True)
        sementara = self.laluan.with_name(self.laluan.name + ".tmp")
        sementara.write_text(json.dumps(self.data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(sementara, self.laluan)
