"""Klien 9router (stdlib sahaja): satu prompt `user` → teks jawapan. Ulang + sandaran ikut `config/mypii.yaml` `llm:`.

Kunci dari env (nama dalam config `llm.env_kunci`), tidak pernah dari repo dan tidak pernah dicetak.
Ujian unit memberi fungsi `hantar` palsu — tiada rangkaian.
"""

import json
import os
import re
import time
import urllib.request
from collections.abc import Callable

from mypii import konfig

Hantar = Callable[[str, str, float], str]  # (model, prompt, suhu) → teks jawapan


class GagalLLM(RuntimeError):
    pass


def hantar_9router(model: str, prompt: str, suhu: float) -> str:
    k = konfig.utama()["llm"]
    kunci = os.environ.get(k["env_kunci"])
    if not kunci:
        raise SystemExit(f"env {k['env_kunci']} tiada — `set -a; . ~/ops/mypii/9router.env; set +a` dahulu")
    badan = {"model": model, "stream": False, "temperature": suhu,
             "messages": [{"role": "user", "content": prompt}]}
    if k.get("max_tokens"):  # tanpa ini Cloudflare memotong pada 256 token (probe Mistral 5 Nov gagal 0/16 kerana itu)
        badan["max_tokens"] = k["max_tokens"]
    req = urllib.request.Request(k["url"], data=json.dumps(badan).encode(), method="POST", headers={
        "Authorization": f"Bearer {kunci}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=k["had_masa_saat"]) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def json_dari(teks: str):
    """JSON pertama dalam jawapan (model kadang membalut dengan ```json atau ayat)."""
    teks = re.sub(r"```(?:json)?", "", teks)
    for buka, tutup in (("[", "]"), ("{", "}")):
        a, b = teks.find(buka), teks.rfind(tutup)
        if 0 <= a < b:
            try:
                return json.loads(teks[a:b + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("tiada JSON sah dalam jawapan")


def tanya(models: list[str], prompt: str, suhu: float, urai: Callable = json_dari,
          hantar: Hantar = hantar_9router, tidur: Callable[[float], None] = time.sleep) -> tuple[str, object]:
    """Cuba setiap model (utama dahulu, kemudian sandaran) `ulang` kali; jawapan yang gagal diurai = cubaan gagal.
    Pulang (model yang menjawab, hasil urai). Mesej ralat TIDAK memuatkan kandungan jawapan."""
    k = konfig.utama()["llm"]
    ralat = []
    for model in models:
        for cubaan in range(k["ulang"]):
            try:
                return model, urai(hantar(model, prompt, suhu))
            except (OSError, ValueError, KeyError, IndexError, TypeError) as e:  # rangkaian/HTTP, JSON rosak, bentuk
                ralat.append(f"{model}#{cubaan + 1}: {type(e).__name__}")
                if cubaan + 1 < k["ulang"]:
                    tidur(k["jeda_saat"])
    raise GagalLLM("; ".join(ralat))
