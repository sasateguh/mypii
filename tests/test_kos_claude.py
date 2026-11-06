"""PELAN-CLAUDE P3 (ADR-016): `make kos-claude` — anggaran kos luar talian (`kira` palsu, tiada rangkaian, tiada SDK)."""

import json
import math
import threading

import pytest

from mypii import klien_anthropic as ka
from mypii import konfig
from mypii.nilai import garis, kos_claude

K = konfig.utama()["garis_dasar"]["llm"]
ANTH = [m for m in K["model"] if m.startswith("anthropic/")]
LAMA = [m for m in K["model"] if not m.startswith("anthropic/") and m not in K.get("eksplorasi", [])]  # pengesahan sahaja
DOK = [{"id": str(i), "bahasa": "ms", "teks": f"IC 900101-14-56{i:02d} tel 012-34567{i:02d}", "spans": []} for i in range(5)]


class Kira:
    """kira(model_id, prompt, parameter) → token = len(prompt) (tentu); merekod panggilan."""

    def __init__(self, ralat_dahulu=0, ralat=None):
        self.panggilan, self._k, self.baki_ralat = [], threading.Lock(), ralat_dahulu
        self.ralat = ralat or OSError("RateLimitError 429")

    def __call__(self, model_id, prompt, parameter):
        with self._k:
            self.panggilan.append((model_id, prompt, parameter))
            if self.baki_ralat:
                self.baki_ralat -= 1
                raise self.ralat
        return len(prompt)


@pytest.fixture
def cache_lama(tmp_path):
    """Jawapan cache 9router palsu untuk DOK: panjang 10, 20, 30, 40, 100 aksara (median 30 ≠ min 40, maks 100) bagi setiap model lama."""
    for m in LAMA:
        f = garis.fail_cache(m, tmp_path)
        f.parent.mkdir(parents=True, exist_ok=True)
        garis._tulis_cache(f, {garis.kunci_dok(m, d["teks"]): "x" * n for d, n in zip(DOK, (10, 20, 30, 40, 100), strict=True)})
    return tmp_path


def _lejar(tmp_path, jumlah=0.0, had=20):
    lj = ka.Lejar(tmp_path / "lejar.json", had)
    lj.data["jumlah_usd"] = jumlah
    return lj


def test_split_dikunci_ditolak_sebelum_dibaca(monkeypatch):
    def jangan(*_):
        raise AssertionError("split dikunci dibaca")

    monkeypatch.setattr("mypii.nilai.harness._dokumen", jangan)
    # walaupun config `kos.split` tersilap menyenaraikan split dikunci, ia tetap ditolak
    monkeypatch.setitem(K["anthropic"]["kos"], "split", ["dev", *konfig.utama()["nilai"]["split_dikunci"]])
    for s in konfig.utama()["nilai"]["split_dikunci"] + ["latih"]:
        with pytest.raises(SystemExit, match="split"):
            kos_claude.main(["--split", s])


def test_config_kos_dev_sahaja():
    assert K["anthropic"]["kos"]["split"] == ["dev"]


def test_anggaran_tepat_dan_parameter_sama_seperti_larian(cache_lama):
    h = Kira()
    r = kos_claude.anggar(DOK, "dev", kira=h, lejar=_lejar(cache_lama), akar=cache_lama, tidur=lambda s: None)
    assert len(h.panggilan) == len(DOK) * len(ANTH)
    n = K["anthropic"]["aksara_setiap_token"]
    kel = r["keluar_setiap_dokumen"]
    assert (kel["jangka"], kel["atas"], kel["terburuk"]) == (math.ceil(30 / n), math.ceil(100 / n), K["anthropic"]["max_tokens"])
    assert kel["asas_jawapan"] == len(DOK) * len(LAMA)
    for m in ANTH:
        t = ka.tetapan(m)
        dihantar = [c for c in h.panggilan if c[0] == t["id"]]
        prompts = [K["prompt"].replace("{teks}", d["teks"]) for d in DOK]
        assert sorted(c[1] for c in dihantar) == sorted(prompts)
        assert all(c[2] == {x: v for x, v in t["permintaan"].items() if x != "max_tokens"} for c in dihantar)
        assert all("temperature" not in c[2] and "max_tokens" not in c[2] for c in dihantar)
        v = r["model"][m]
        assert v["token_masuk"] == sum(map(len, prompts))
        for x in ("jangka", "atas", "terburuk"):
            assert v[f"usd_{x}"] == round(ka.kos({"masuk": v["token_masuk"], "keluar": kel[x] * len(DOK)}, t["harga"]), 6)
    assert r["jumlah_usd"]["terburuk"] == round(sum(r["model"][m]["usd_terburuk"] for m in ANTH), 6)
    assert r["muat_terburuk"] is True and r["baki_usd"] == 20


def test_baki_had_dikira_dari_lejar(cache_lama):
    r = kos_claude.anggar(DOK, "dev", kira=Kira(), lejar=_lejar(cache_lama, jumlah=19.999999), akar=cache_lama)
    assert r["baki_usd"] == round(20 - 19.999999, 6) and r["muat_terburuk"] is False


def test_muat_diukur_dengan_terburuk_bukan_jangkaan(cache_lama):
    r = kos_claude.anggar(DOK, "dev", kira=Kira(), lejar=_lejar(cache_lama), akar=cache_lama)
    j = r["jumlah_usd"]
    assert j["jangka"] < j["atas"] < j["terburuk"]
    baki = (j["atas"] + j["terburuk"]) / 2
    r = kos_claude.anggar(DOK, "dev", kira=Kira(), lejar=_lejar(cache_lama, jumlah=20 - baki), akar=cache_lama)
    assert r["muat_terburuk"] is False


def test_ralat_sementara_diulang_tolak_api_tidak(cache_lama):
    tidur = []
    h = Kira(ralat_dahulu=2)
    kos_claude.anggar(DOK[:1], "dev", kira=h, lejar=_lejar(cache_lama), akar=cache_lama, tidur=tidur.append)
    assert len(tidur) == 2 and len(h.panggilan) == len(ANTH) + 2
    h = Kira(ralat_dahulu=1, ralat=ka.TolakAPI("HTTP 400"))
    with pytest.raises(ka.TolakAPI):
        kos_claude.anggar(DOK[:1], "dev", kira=h, lejar=_lejar(cache_lama), akar=cache_lama, tidur=lambda s: None)


def test_ralat_sementara_berterusan_akhirnya_gagal(cache_lama):
    h = Kira(ralat_dahulu=10**6)
    with pytest.raises(OSError):
        kos_claude.anggar(DOK[:1], "dev", kira=h, lejar=_lejar(cache_lama), akar=cache_lama, tidur=lambda s: None)
    assert len(h.panggilan) == K["anthropic"]["kos"]["ulang"] + 1


def test_tiada_cache_lama_ditolak(tmp_path):
    with pytest.raises(SystemExit, match="tiada jawapan cache"):
        kos_claude.anggar(DOK, "dev", kira=Kira(), lejar=_lejar(tmp_path), akar=tmp_path)


def test_tiada_kunci_env_mesej_jelas(monkeypatch):
    monkeypatch.delenv(K["anthropic"]["env_kunci"], raising=False)
    with pytest.raises(SystemExit, match="anthropic.env"):
        kos_claude.kira_token_api("claude-haiku-5-5", "x", {})


@pytest.mark.parametrize("panggil", [lambda: kos_claude.kira_token_api("claude-haiku-5-5", "x", {}),
                                     lambda: ka.hantar("claude-haiku-5-5", "x", {})])
def test_tiada_kunci_tanpa_sdk_mesej_jelas(monkeypatch, panggil):
    """Regresi gerbang Depot: CI memasang tanpa extra `garis` — semakan kunci mesti mendahului `import anthropic`."""
    monkeypatch.delenv(K["anthropic"]["env_kunci"], raising=False)
    monkeypatch.setitem(__import__("sys").modules, "anthropic", None)
    with pytest.raises(SystemExit, match="anthropic.env"):
        panggil()


def test_main_menulis_kiraan_sahaja_tanpa_teks(tmp_path, monkeypatch, cache_lama):
    monkeypatch.setattr(konfig, "AKAR", cache_lama)
    monkeypatch.setattr("mypii.nilai.harness._dokumen", lambda s: DOK)
    monkeypatch.setattr(kos_claude, "kira_token_api", Kira())
    assert kos_claude.main(["--split", "dev"]) == 0
    teks = (cache_lama / K["anthropic"]["kos"]["fail"].format(split="dev")).read_text(encoding="utf-8")
    assert all(d["teks"] not in teks for d in DOK) and "900101" not in teks
    assert json.loads(teks)["dokumen"] == len(DOK)


def test_asas_keluar_tidak_kira_model_eksplorasi(cache_lama, monkeypatch):
    """PELAN-MODEL-LAIN P6: model eksplorasi bukan-Anthropic masuk `model` bersama cachenya — asas token keluar TIDAK berubah."""
    asas = kos_claude.panjang_jawapan_sedia(DOK, cache_lama)
    eks = "cf/@cf/palsu/eksplorasi"
    f = garis.fail_cache(eks, cache_lama)
    garis._tulis_cache(f, {garis.kunci_dok(eks, d["teks"]): "y" * 999 for d in DOK})
    k = {**K, "model": [*K["model"], eks], "eksplorasi": [*K.get("eksplorasi", []), eks]}
    monkeypatch.setattr(kos_claude, "_k", lambda: k)
    assert kos_claude.panjang_jawapan_sedia(DOK, cache_lama) == asas
    monkeypatch.setattr(kos_claude, "_k", lambda: {**k, "eksplorasi": K.get("eksplorasi", [])})  # kawalan: tanpa label = dikira
    assert len(kos_claude.panjang_jawapan_sedia(DOK, cache_lama)) == len(asas) + len(DOK)
