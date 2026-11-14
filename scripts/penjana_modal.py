"""Pelayan penjana templat SEMENTARA di Modal (PELAN-V21 P6): vLLM serasi-OpenAI untuk model berlesen terbuka, dihos sendiri.

    export MYPII_MODAL_KUNCI="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"   # kunci sesi, tidak disimpan
    uvx -p 3.12 --from modal==1.6.3 modal serve scripts/penjana_modal.py
    → cetak URL setiap fungsi web (…-pelayan-qwen-dev.modal.run) → `MYPII_MODAL_URL_QWEN` / `MYPII_MODAL_URL_SEALION` (nama env:
    config `llm.modal.url_env`) + `MYPII_MODAL_KUNCI` untuk `templat_llm` (laluan `modal/`, `klien_llm.hantar_modal`).

Berhenti bila proses `modal serve` tamat (tiada endpoint kekal; tiada `modal deploy`). Model + revisi dipin di bawah = sama dengan
`config/mypii.yaml` `llm.modal.url_env` + `llm.penjana.ujian4` (ujian `tests/test_penjana_modal.py`). Berat disimpan dalam Volume `mypii-hf-cache` supaya
mula semula tidak memuat turun lagi. Had belanja = Budget workspace pemilik + `timeout`/`scaledown_window` di bawah.
"""

from __future__ import annotations

import os
import subprocess
import threading

import modal

VLLM = "0.33.0"
HF_HUB = "1.33.0"
# nama dilayan = laluan `modal/<repo>` dalam config; (repo, revisi, gpu, hujah vllm tambahan)
MODEL = {
    "qwen": ("Qwen/Qwen3.8-27B-FP8", "c3a462cc3d38cf351f3b26cbd763469eeb74ef81", "H100",
             ["--language-model-only", "--reasoning-parser", "qwen3", "--max-model-len", "32768"]),
    "sealion": ("aisingapore/Apertus-SEA-LION-v4-8B-IT", "3cb02025474d0e3f57be2e95278f0e3f31c8dba0", "L40S",
                ["--max-model-len", "16384"]),
}
ENV_KUNCI = "MYPII_MODAL_KUNCI"   # dalam kontena = nilai rahsia yang sama (Secret.from_dict menyuntik nama ini)

# Imej CUDA devel (nvcc): DeepGEMM (FP8 blok, Hopper) dan FlashInfer (lapisan hibrid Qwen3.8) mengkompil kernel JIT semasa engine
# bermula — imej slim tiada toolkit → engine gagal (asap 14 Nov, dua kali). 13.0.3 = cuda-toolkit yang dipin torch 2.14.0 (vLLM 0.33.0).
CUDA = "nvidia/cuda:13.0.3-devel-ubuntu24.04"
img = (
    modal.Image.from_registry(CUDA, add_python="3.12")
    .uv_pip_install(f"vllm=={VLLM}", f"huggingface_hub=={HF_HUB}")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "VLLM_NO_USAGE_STATS": "1", "DO_NOT_TRACK": "1"})
)
cache = modal.Volume.from_name("mypii-hf-cache", create_if_missing=True)
rahsia = modal.Secret.from_dict({ENV_KUNCI: os.environ.get(ENV_KUNCI, "")})
app = modal.App("mypii-penjana")


def _vllm(nama: str) -> None:
    repo, revisi, _, tambahan = MODEL[nama]
    kunci = os.environ.get(ENV_KUNCI, "")
    if len(kunci) < 24:
        raise SystemExit(f"{ENV_KUNCI} tiada/pendek — pelayan tidak dimulakan tanpa kunci")
    proses = subprocess.Popen(["vllm", "serve", repo, "--revision", revisi, "--served-model-name", f"modal/{repo}",
                               "--api-key", kunci, "--host", "0.0.0.0", "--port", "8000", "--seed", "2026",
                               "--max-num-seqs", "32", *tambahan])

    def _jaga() -> None:   # vLLM mati → kontena tamat serta-merta (web_server sebaliknya menunggu port sehingga startup_timeout)
        rc = proses.wait()
        print(f"vllm keluar rc={rc} — kontena ditamatkan", flush=True)
        os._exit(1)

    threading.Thread(target=_jaga, daemon=True).start()


_ATUR = {"image": img, "timeout": 3600, "scaledown_window": 300, "secrets": [rahsia],
         "volumes": {"/root/.cache/huggingface": cache,
                     "/root/.cache/vllm": modal.Volume.from_name("mypii-vllm-cache", create_if_missing=True)}}


@app.function(gpu=MODEL["qwen"][2], **_ATUR)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=1200)
def pelayan_qwen() -> None:
    _vllm("qwen")


@app.function(gpu=MODEL["sealion"][2], **_ATUR)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=1200)
def pelayan_sealion() -> None:
    _vllm("sealion")
