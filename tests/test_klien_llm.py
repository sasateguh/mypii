"""v2.x: `hantar_9router` menghantar `llm.max_tokens` (Cloudflare lalai 256 token memotong jawapan templat — probe Mistral 5 Nov)."""

import json

import pytest

from mypii import klien_llm, konfig


class _Jawapan:
    def __init__(self):
        self.badan = json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.badan


@pytest.fixture
def tangkap(monkeypatch):
    dihantar = []

    def urlopen(req, timeout):
        dihantar.append(json.loads(req.data))
        return _Jawapan()

    monkeypatch.setattr(klien_llm.urllib.request, "urlopen", urlopen)
    monkeypatch.setenv(konfig.utama()["llm"]["env_kunci"], "kunci-palsu")
    return dihantar


def test_max_tokens_dari_config_dihantar(tangkap):
    assert klien_llm.hantar_9router("cf/x", "p", 0.5) == "ok"
    assert tangkap[0]["max_tokens"] == konfig.utama()["llm"]["max_tokens"] and tangkap[0]["stream"] is False


def test_tanpa_max_tokens_config_tidak_dihantar(tangkap, monkeypatch):
    monkeypatch.delitem(konfig.utama()["llm"], "max_tokens")
    klien_llm.hantar_9router("cf/x", "p", 0.5)
    assert "max_tokens" not in tangkap[0]
