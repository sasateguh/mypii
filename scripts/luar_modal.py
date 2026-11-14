"""Inferens model PII LUAR atas MyPII-Bench di Modal (langkah B, KAJIAN-HF-MODAL-V3 §3B/§8; pindaan PRA-DAFTAR 2026-11-14).

    uvx -p 3.12 --from modal==1.6.3 modal run scripts/luar_modal.py --model meddies --split dev3 --had 20
    (masuk = fail split tempatan; keluar = hasil/luar/<split>-<model>.jsonl, satu baris {id, spans:[{mula,tamat,label,teks}]})

Kod model pihak ketiga (Meddies `modeling_meddies_pii.py` + kod jauh LiquidAI; pelayan Rust PII Engineer) berjalan DALAM kontena
Modal sahaja (red team §8#2: kotak pasir), bukan di hos. Revisi dipin di bawah; ramalan mentah dipulangkan, pemetaan label +
skor dibuat di hos (`mypii/nilai/luar.py`). Tiada endpoint hidup; setiap fungsi ada had masa. Had belanja = Budget workspace pemilik.
"""

from __future__ import annotations

import json
from pathlib import Path

import modal

MEDDIES = ("Meddies/meddies-pii-v2", "0e5361e4d47ba4a92e56f7635a65daac54fec791")
PE = ("pii-engineer/PII-Engineer-Multi-NER-v2.1", "efacd9242671d0300da535207d7952dc3f82f57e")
PE_ZH = ("pii-engineer/PII-Engineer-Chinese-NER-v1.0", "d16aa1c54f34f993b2d4c30c218ee9d712959b2d")
PE_GIT = ("https://github.com/gantz-ai/pii.engineer", "4ff53986a53351b3a516872a557832b44b166628")
SEDIA = "Please call Ahmad bin Ali at 012-345 6789 about invoice 2041 before Friday, thank you."
ORT = "https://github.com/microsoft/onnxruntime/releases/download/v1.20.1/onnxruntime-linux-x64-1.20.1.tgz"

GLINER = ("urchade/gliner_multi_pii-v1", "1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d")
GLINER_LABEL = {"identity card number": "MY_NRIC", "registration number": "MY_SSM", "phone number": "MY_PHONE"}   # pra-daftar
GLINER_AMBANG = 0.5

app = modal.App("mypii-luar")

img_meddies = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.14.1", "transformers==5.22.1", "peft==0.21.2", "safetensors==0.8.0",
                    "accelerate==1.15.0", "huggingface_hub==2.3.0")
    .run_commands(f"python -c \"from huggingface_hub import snapshot_download; snapshot_download('{MEDDIES[0]}', "
                  f"revision='{MEDDIES[1]}', local_dir='/model')\"")
)

img_gliner = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("gliner==0.2.29", "torch==2.14.1", "transformers==5.16.1", "huggingface_hub==1.33.0",
                    "sentencepiece==0.2.2", "protobuf==7.36.2", "tiktoken==0.14.0")   # uv pip compile, --exclude-newer 2026-10-31
    .run_commands(f"python -c \"from huggingface_hub import snapshot_download; snapshot_download('{GLINER[0]}', "
                  f"revision='{GLINER[1]}', local_dir='/gliner')\"")
)

img_pe = (
    modal.Image.from_registry("rust:1.78-bookworm", add_python="3.12")
    .apt_install("git", "curl", "ca-certificates", "libssl-dev", "pkg-config")
    .run_commands(
        f"git clone {PE_GIT[0]} /src && cd /src && git checkout {PE_GIT[1]}",
        "cd /src && cargo build --release --package pii-engineer-server && rustc --version > /src/RUSTC",
        f"mkdir -p /ort && curl -sL {ORT} | tar -xz -C /ort --strip-components=1",
        "pip install huggingface_hub==2.3.0 requests==2.32.5",
        f"python -c \"from huggingface_hub import snapshot_download as s; "
        f"s('{PE[0]}', revision='{PE[1]}', local_dir='/src/models/PII-Engineer-Multi-NER-v2.1'); "
        f"s('{PE_ZH[0]}', revision='{PE_ZH[1]}', local_dir='/src/models/PII-Engineer-Chinese-NER-v1.0')\"",
    )
    .env({"ORT_DYLIB_PATH": "/ort/lib/libonnxruntime.so", "PII_ENGINEER_RATE_LIMIT_RPM": "1000000",
          "GLINER_MODELS": "models/PII-Engineer-Multi-NER-v2.1", "CHINESE_NER_MODEL": "models/PII-Engineer-Chinese-NER-v1.0"})
)


@app.function(image=img_meddies, gpu="T4", timeout=3600)
def meddies(dokumen: list[dict]) -> dict:
    import sys

    import torch

    sys.path.insert(0, "/model")
    import traceback

    from modeling_meddies_pii import MeddiesPiiExtractor

    peranti = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        m = MeddiesPiiExtractor.from_pretrained("/model", device=peranti)   # bentuk adapter = laluan yang dinilai pengeluar
        keluar = []
        for d in dokumen:
            keluar.append({"id": d["id"], "spans": [{"mula": int(s.start), "tamat": int(s.end), "label": str(s.label),
                                                     "teks": str(s.text)} for s in m.extract(d["teks"])]})
    except Exception:   # noqa: BLE001 — objek torch dalam ralat tidak boleh dinyahsiri di hos
        raise RuntimeError(traceback.format_exc()[-3000:]) from None
    return {"ramalan": keluar, "versi": {"model": list(MEDDIES), "peranti": peranti, "torch": str(torch.__version__)}}


@app.function(image=img_gliner, gpu="T4", timeout=3600)
def gliner(dokumen: list[dict]) -> dict:
    import traceback

    import torch
    from gliner import GLiNER

    try:
        m = GLiNER.from_pretrained("/gliner")   # tokenizer model asas dimuat turun dari HF
        if torch.cuda.is_available():
            m = m.to("cuda")
        keluar = []
        for d in dokumen:
            e = m.predict_entities(d["teks"], list(GLINER_LABEL), threshold=GLINER_AMBANG)
            keluar.append({"id": d["id"], "spans": [{"mula": int(x["start"]), "tamat": int(x["end"]), "label": str(x["label"]),
                                                     "teks": str(x["text"]), "skor": float(x["score"])} for x in e]})
    except Exception:   # noqa: BLE001
        raise RuntimeError(traceback.format_exc()[-3000:]) from None
    import gliner as g
    return {"ramalan": keluar, "versi": {"model": list(GLINER), "label": GLINER_LABEL, "ambang": GLINER_AMBANG,
                                         "gliner": g.__version__, "cuda": torch.cuda.is_available()}}


@app.function(image=img_pe, cpu=4, memory=8192, timeout=3600)
def pii_engineer(dokumen: list[dict]) -> dict:
    import subprocess
    import time

    import requests

    log = open("/tmp/pelayan.log", "w")   # noqa: SIM115 — kekal terbuka sepanjang hayat subproses pelayan
    pelayan = subprocess.Popen(["/src/target/release/pii-engineer-server"], cwd="/src", stdout=log, stderr=subprocess.STDOUT,
                               env={**__import__("os").environ, "PII_ENGINEER_HOST": "127.0.0.1", "PII_ENGINEER_PORT": "8000"})
    url = "http://127.0.0.1:8000/api/detect"
    for _ in range(180):
        if pelayan.poll() is not None:
            break
        try:
            requests.post(url, json={"text": SEDIA}, timeout=10)   # apa-apa jawapan HTTP = pelayan hidup
            break
        except requests.RequestException:
            time.sleep(2)
    else:
        raise RuntimeError(f"pelayan PII Engineer tidak bermula (rc {pelayan.poll()}):\n{Path('/tmp/pelayan.log').read_text()[-3000:]}")
    keluar, bait, ralat = [], 0, []
    for d in dokumen:
        r = requests.post(url, json={"text": d["teks"]}, timeout=60)   # label lalai pelayan (tiada `labels`) = seperti dihantar
        if not r.ok:   # pra-daftar: dokumen yang pelayan gagal = tiada ramalan, dikira + dilapor
            ralat.append(d["id"])
            keluar.append({"id": d["id"], "spans": [], "ralat": r.status_code})
            continue
        spans, b = _aksara(d["teks"], r.json().get("entities", []))
        bait += b
        keluar.append({"id": d["id"], "spans": spans})
    pelayan.terminate()
    return {"ramalan": keluar, "versi": {"model": PE, "zh": PE_ZH, "git": PE_GIT, "ort": ORT,
                                         "rustc": Path("/src/RUSTC").read_text().strip(), "ofset_bait_ditukar": bait,
                                         "dokumen_ralat": len(ralat), "contoh_ralat": ralat[:10]}}


def _aksara(teks: str, entiti: list[dict]) -> tuple[list[dict], int]:
    """Ofset pelayan Rust boleh jadi BAIT UTF-8: tukar ke ofset aksara bila teks[mula:tamat] ≠ value."""
    b, keluar, tukar = teks.encode("utf-8"), [], 0
    for e in entiti:
        mula, tamat = e["start"], e["end"]
        if teks[mula:tamat] != e["value"] and b[mula:tamat].decode("utf-8", "ignore") == e["value"]:
            mula, tamat = len(b[:mula].decode("utf-8", "ignore")), len(b[:tamat].decode("utf-8", "ignore"))
            tukar += 1
        keluar.append({"mula": mula, "tamat": tamat, "label": e["type"], "teks": teks[mula:tamat], "skor": e.get("score")})
    return keluar, tukar


@app.local_entrypoint()
def main(model: str, split: str, had: int = 0, benarkan_ujian: bool = False):
    akar = Path(__file__).resolve().parents[1]
    sys_path = str(akar)
    import sys

    sys.path.insert(0, sys_path)
    from mypii import konfig
    from mypii.nilai import pradaftar

    pradaftar.gerbang_belum_dibuka(split, benarkan_ujian, akar)   # SEBELUM fail split dibaca (PELAN-V21)
    dokumen = [json.loads(x) for x in (akar / konfig.fail_split(split)).read_text(encoding="utf-8").splitlines() if x.strip()]
    dokumen = dokumen[:had] if had else dokumen
    fn = {"meddies": meddies, "gliner": gliner, "pii-engineer": pii_engineer}[model]
    hasil = fn.remote([{"id": d["id"], "teks": d["teks"]} for d in dokumen])
    keluar = akar / "hasil" / "luar" / f"{split}{'-had' + str(had) if had else ''}-{model}.jsonl"
    keluar.parent.mkdir(parents=True, exist_ok=True)
    keluar.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in hasil["ramalan"]), encoding="utf-8")
    (keluar.with_suffix(".versi.json")).write_text(json.dumps(hasil["versi"], indent=1) + "\n", encoding="utf-8")
    print(f"{keluar.relative_to(akar)}: {len(hasil['ramalan'])} dokumen · {hasil['versi']}")


@app.function(image=img_pe, cpu=4, memory=8192, timeout=900)
def pii_engineer_probe() -> list:
    """Probe diagnostik (tiada data bench): adakah mana-mana input berjaya melalui pelayan rasmi?"""
    import os
    import subprocess
    import time

    import requests

    subprocess.Popen(["/src/target/release/pii-engineer-server"], cwd="/src", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     env={**os.environ, "PII_ENGINEER_HOST": "127.0.0.1", "PII_ENGINEER_PORT": "8000"})
    url = "http://127.0.0.1:8000/api/detect"
    for _ in range(120):
        try:
            requests.post(url, json={"text": SEDIA}, timeout=10)
            break
        except requests.RequestException:
            time.sleep(2)
    ayat = "John Doe, NRIC S9012345B, born 12 March 1985"   # contoh README pengeluar
    kes = [("readme", ayat, None), ("readme-1label", ayat, ["government_id"]),
           ("30kata", " ".join([SEDIA] * 2), None), ("100kata", " ".join([SEDIA] * 6), None)]
    keluar = []
    for nama, t, label in kes:
        r = requests.post(url, json={"text": t, **({"labels": label} if label else {})}, timeout=60)
        keluar.append((nama, r.status_code, r.text[:160]))
    return keluar


@app.local_entrypoint()
def probe():
    for x in pii_engineer_probe.remote():
        print(x)
