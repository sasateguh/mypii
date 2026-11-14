"""PELAN-V21 P6: pelayan penjana Modal (`scripts/penjana_modal.py`) selaras dengan config; laluan `modal/` dalam penjana templat.

Skrip mengimport `modal` (tiada dalam persekitaran ujian), jadi `MODEL` dibaca dengan `ast` tanpa menjalankannya.
"""

import ast
import re

import pytest

from mypii import klien_llm, konfig
from mypii.jana import templat_llm

K = konfig.utama()


def _model_skrip() -> dict:
    pokok = ast.parse((konfig.AKAR / "scripts/penjana_modal.py").read_text(encoding="utf-8"))
    for n in pokok.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "MODEL" for t in n.targets):
            return ast.literal_eval(n.value)
    raise AssertionError("MODEL tiada dalam scripts/penjana_modal.py")


def test_model_dipin_selaras_config():
    m = _model_skrip()
    dilayan = {f"modal/{repo}" for repo, _, _, _ in m.values()}
    p = K["llm"]["penjana"]["ujian4"]
    assert dilayan == set(K["llm"]["modal"]["url_env"]) == {p["model"], *p["sandaran"]}
    assert all(re.fullmatch(r"[0-9a-f]{40}", rev) for _, rev, _, _ in m.values())   # revisi penuh, bukan cawangan


def test_hantar_penjana_modal_ke_pelayan_sendiri(monkeypatch):
    dipanggil = []
    monkeypatch.setattr(templat_llm, "hantar_modal", lambda m, p, s: dipanggil.append((m, s)) or "[]")
    monkeypatch.setattr(templat_llm, "hantar_9router", lambda *a: pytest.fail("9router dipanggil untuk modal/"))
    model = K["llm"]["penjana"]["ujian4"]["model"]
    assert templat_llm.hantar_penjana(model, "x", 0.8) == "[]" and dipanggil == [(model, 0.8)]


def test_hantar_modal_enggan_tanpa_env(monkeypatch):
    k = K["llm"]["modal"]
    for e in [*k["url_env"].values(), k["env_kunci"]]:
        monkeypatch.delenv(e, raising=False)
    with pytest.raises(SystemExit, match="modal serve"):
        klien_llm.hantar_modal(K["llm"]["penjana"]["ujian4"]["model"], "x", 0.8)
