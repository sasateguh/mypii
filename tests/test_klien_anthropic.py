"""PELAN-CLAUDE P2 (ADR-016): klien Anthropic + lejar had keras + penghala `anthropic/` dalam garis.ramal_llm — luar talian.

`hantar` palsu (tiada rangkaian); modul `anthropic` palsu disuntik ke sys.modules untuk `klien_anthropic.hantar` (SDK tidak perlu dipasang).
"""

import hashlib
import json
import sys
import threading
from types import SimpleNamespace

import pytest

from mypii import klien_anthropic as ka
from mypii import konfig
from mypii.nilai import bandingan, garis, harness

K = konfig.utama()["garis_dasar"]["llm"]
PENGESAHAN = [m for m in K["model"] if m not in K.get("eksplorasi", [])]  # eksplorasi di HUJUNG `model` (PELAN-MODEL-LAIN P6)
ANTH = [m for m in PENGESAHAN if m.startswith("anthropic/")]  # garis dasar pengesahan; calon eksplorasi = tests/test_probe_llm.py
LAMA = [m for m in PENGESAHAN if not m.startswith("anthropic/")]
DOK = [{"id": str(i), "bahasa": "ms", "teks": f"IC 900101-14-56{i:02d} tel 012-34567{i:02d}", "spans": []} for i in range(6)]


class Palsu:
    """hantar(model_id, prompt, permintaan) → (teks, usage); merekod setiap panggilan (selamat benang)."""

    def __init__(self, jawapan="[]", usage=None, ralat=None):
        self.jawapan, self.usage, self.ralat = jawapan, usage or {"masuk": 100, "keluar": 10}, ralat
        self.panggilan, self._k = [], threading.Lock()

    def __call__(self, model_id, prompt, permintaan):
        with self._k:
            self.panggilan.append((model_id, prompt, permintaan))
        if self.ralat:
            raise self.ralat
        return self.jawapan, dict(self.usage)


@pytest.fixture
def anth(monkeypatch):
    """Config anthropic boleh diubah setiap ujian tanpa menyentuh fail."""
    k = K["anthropic"]
    monkeypatch.setitem(konfig.utama()["llm"], "serentak", 1)  # susunan panggilan tentu → had dicapai pada dokumen yang diketahui
    return k


def test_config_model_anthropic_di_hujung_dan_ada_tetapan():
    assert ANTH and PENGESAHAN[-len(ANTH):] == ANTH and K["model"][:len(LAMA)] == LAMA
    for m in ANTH:
        t = ka.tetapan(m)
        assert t["id"] == m.removeprefix("anthropic/") and "temperature" not in t["permintaan"]
        assert t["permintaan"]["max_tokens"] == K["anthropic"]["max_tokens"] and set(t["harga"]) == {"masuk", "keluar"}
    assert 0 < K["anthropic"]["had_usd"] <= 20


def test_lejar_terkumpul_tepat_dan_cache_disambung(tmp_path, anth):
    m = ANTH[0]
    h = Palsu(usage={"masuk": 1234, "keluar": 56})
    _, st = garis.ramal_llm(m, DOK, hantar=h, akar=tmp_path)
    assert len(h.panggilan) == len(DOK) and st["panggilan"] == len(DOK) and st["gagal"] == 0 and st["had_dicapai"] is False
    harga = ka.tetapan(m)["harga"]
    satu = (1234 * harga["masuk"] + 56 * harga["keluar"]) / 1e6
    lejar = json.loads((tmp_path / anth["lejar"]).read_text())
    assert lejar["model"][m] == {"masuk": 1234 * len(DOK), "keluar": 56 * len(DOK), "panggilan": len(DOK),
                                 "usd": pytest.approx(satu * len(DOK), abs=1e-5)}
    assert lejar["jumlah_usd"] == pytest.approx(satu * len(DOK), abs=1e-5) and st["usd"] == pytest.approx(satu * len(DOK), abs=1e-5)
    assert "teks" not in json.dumps(lejar) and DOK[0]["teks"] not in json.dumps(lejar)
    # larian kedua: semua dari cache, tiada panggilan, lejar tidak berubah
    h2 = Palsu()
    _, st2 = garis.ramal_llm(m, DOK, hantar=h2, akar=tmp_path)
    assert h2.panggilan == [] and st2["dari_cache"] == len(DOK) and json.loads((tmp_path / anth["lejar"]).read_text()) == lejar


def test_had_dicapai_panggilan_berhenti_dan_gagal_dikira(tmp_path, anth, monkeypatch):
    m = ANTH[0]
    t = ka.tetapan(m)
    terburuk = ka.kos_terburuk(K["prompt"].replace("{teks}", DOK[0]["teks"]), t)
    sebenar = (100 * t["harga"]["masuk"] + 10 * t["harga"]["keluar"]) / 1e6
    # had cukup untuk dua panggilan (kos sebenar) + satu tempahan terburuk, tidak cukup untuk tempahan seterusnya
    monkeypatch.setitem(anth, "had_usd", 2 * sebenar + terburuk * 1.0001)
    h = Palsu()
    r, st = garis.ramal_llm(m, DOK, hantar=h, akar=tmp_path)
    assert len(h.panggilan) == 3 and st["gagal"] == len(DOK) - 3 and st["had_dicapai"] is True
    lejar = json.loads((tmp_path / anth["lejar"]).read_text())
    assert lejar["model"][m]["panggilan"] == 3 and lejar["jumlah_usd"] <= anth["had_usd"]
    assert len(garis._muat_cache(garis.fail_cache(m, tmp_path))) == 3 and r[3:] == [[]] * (len(DOK) - 3)


def test_had_sudah_habis_dari_lejar_lama_tiada_panggilan(tmp_path, anth):
    (tmp_path / anth["lejar"]).parent.mkdir(parents=True)
    (tmp_path / anth["lejar"]).write_text(json.dumps({"jumlah_usd": anth["had_usd"], "model": {}}))
    h = Palsu()
    _, st = garis.ramal_llm(ANTH[-1], DOK, hantar=h, akar=tmp_path)
    assert h.panggilan == [] and st["gagal"] == len(DOK) and st["had_dicapai"] is True


def test_panggilan_gagal_melepaskan_tempahan_tanpa_rekod(tmp_path, anth):
    h = Palsu(ralat=OSError("putus"))
    _, st = garis.ramal_llm(ANTH[0], DOK, hantar=h, akar=tmp_path)
    assert st["gagal"] == len(DOK) and st["had_dicapai"] is False and len(h.panggilan) == len(DOK)
    assert not (tmp_path / anth["lejar"]).exists() and not garis.fail_cache(ANTH[0], tmp_path).exists()


def test_tempahan_gagal_dilepas_baki_kekal_untuk_panggilan_lain(tmp_path, anth, monkeypatch):
    m = ANTH[0]
    terburuk = ka.kos_terburuk(K["prompt"].replace("{teks}", DOK[0]["teks"]), ka.tetapan(m))
    monkeypatch.setitem(anth, "had_usd", terburuk * 1.5)  # hanya SATU tempahan muat pada satu masa

    class GagalDuaDahulu(Palsu):
        def __call__(self, *a):
            if len(self.panggilan) < 2:
                self.panggilan.append(a)
                raise OSError("putus")
            return super().__call__(*a)

    h = GagalDuaDahulu()
    _, st = garis.ramal_llm(m, DOK, hantar=h, akar=tmp_path)
    assert len(h.panggilan) == len(DOK) and st["gagal"] == 2 and st["had_dicapai"] is False


def test_tolak_api_menghentikan_larian(tmp_path, anth):
    h = Palsu(ralat=ka.TolakAPI("HTTP 400"))
    with pytest.raises(ka.TolakAPI):
        garis.ramal_llm(ANTH[0], DOK, hantar=h, akar=tmp_path)
    assert len(h.panggilan) == 1


def test_permintaan_dihantar_tanpa_suhu_dan_teks_dalam_prompt(tmp_path, anth):
    h = Palsu()
    garis.ramal_llm(ANTH[0], DOK[:1], hantar=h, akar=tmp_path)
    (mid, prompt, permintaan), = h.panggilan
    assert mid == ANTH[0].removeprefix("anthropic/") and DOK[0]["teks"] in prompt and "{teks}" not in prompt
    assert permintaan == ka.tetapan(ANTH[0])["permintaan"] and "temperature" not in permintaan


def test_kunci_cache_model_lama_tidak_berubah():
    for m in LAMA:
        asal = hashlib.sha256(json.dumps([m, K["prompt"], "abc"], ensure_ascii=False).encode()).hexdigest()
        assert garis.kunci_dok(m, "abc") == asal == garis.kunci_cache(m, K["prompt"], "abc")


def test_cache_dikomit_model_lama_masih_lengkap_atas_dev():
    dev = [json.loads(x) for x in (konfig.AKAR / "data/bench/dev.jsonl").read_text(encoding="utf-8").splitlines()]
    for m in LAMA:
        cache = garis._muat_cache(garis.fail_cache(m))
        assert all(garis.kunci_dok(m, d["teks"]) in cache for d in dev)


def test_parameter_berubah_kunci_berubah(monkeypatch):
    m = ANTH[0]
    asal = garis.kunci_dok(m, "abc")
    mid = m.removeprefix("anthropic/")
    monkeypatch.setitem(K["anthropic"]["model"][mid], "parameter", {"thinking": {"type": "adaptive"}})
    ubah_param = garis.kunci_dok(m, "abc")
    monkeypatch.setitem(K["anthropic"], "max_tokens", K["anthropic"]["max_tokens"] + 1)
    assert len({asal, ubah_param, garis.kunci_dok(m, "abc")}) == 3
    assert asal != garis.kunci_cache(m, K["prompt"], "abc")


def test_model_anthropic_tanpa_tetapan_ditolak(tmp_path, monkeypatch):
    monkeypatch.setitem(K, "model", K["model"] + ["anthropic/claude-tiada"])
    with pytest.raises(SystemExit, match="tiada tetapan"):
        garis.ramal_llm("anthropic/claude-tiada", DOK, hantar=Palsu(), akar=tmp_path)


def test_bandingan_tanpa_cache_tiada_rangkaian_tiada_lejar(tmp_path, monkeypatch):
    monkeypatch.setattr(garis, "fail_cache", lambda m, akar=None: tmp_path / "tiada.jsonl")
    monkeypatch.setattr(konfig, "AKAR", tmp_path)
    monkeypatch.setattr(ka.Lejar, "dari_config", classmethod(lambda cls, akar=None: cls(tmp_path / "lejar.json", 20)))
    with pytest.raises(SystemExit, match="tiada dalam cache"):
        bandingan.ramal_semua(DOK, [f"llm:{ANTH[0]}"])
    assert not (tmp_path / "lejar.json").exists()


def test_semua_melangkau_claude_tanpa_cache_dengan_amaran(tmp_path, monkeypatch, capsys):
    """Penolakan penyemak P2: sebelum P4 (tiada fail cache) `semua` tidak memuatkan `anthropic/` — tiada API, tiada rc 2."""
    asal = garis.fail_cache
    monkeypatch.setattr(garis, "fail_cache", lambda m, akar=None: tmp_path / "tiada.jsonl" if m in ANTH else asal(m))
    s = harness.senarai_sistem(["semua"])
    tanpa_anth = [f"llm:{m}" for m in K["model"] if m not in ANTH]  # LAMA + eksplorasi di hujung (PELAN-MODEL-LAIN P6)
    assert not any("anthropic/" in x for x in s) and s[-len(tanpa_anth):] == tanpa_anth
    assert all(f"llm:{m}: belum dijalankan" in capsys.readouterr().err for m in ANTH[:1])
    assert harness.senarai_sistem([f"llm:{m}" for m in ANTH]) == [f"llm:{m}" for m in ANTH]  # P4: diminta terang = dibenarkan


def test_semua_memuatkan_claude_di_hujung_bila_cache_wujud(tmp_path, monkeypatch):
    (tmp_path / "ada.jsonl").write_text("")
    monkeypatch.setattr(garis, "fail_cache", lambda m, akar=None: tmp_path / "ada.jsonl")
    s = harness.senarai_sistem(["semua"])
    assert s[3:] == [f"llm:{m}" for m in K["model"]]
    assert [x for x in s[3:] if x[4:] in PENGESAHAN][-len(ANTH):] == [f"llm:{m}" for m in ANTH]  # Claude di hujung pengesahan


def test_bandingan_llm_semua_luar_talian_atas_cache_dikomit_tanpa_fail_baharu():
    """Penolakan penyemak P2: setiap `llm:` dalam `semua` (yang `make bandingan` muatkan) lulus atas cache DIKOMIT dev tanpa
    rangkaian, dan tiada fail baharu dicipta dalam folder cache. (pii-guard/presidio perlu extra — di luar gerbang pytest.)"""
    cache = konfig.AKAR / K["cache"]
    sebelum = sorted(p.name for p in cache.iterdir())
    dev = [json.loads(x) for x in (konfig.AKAR / "data/bench/dev.jsonl").read_text(encoding="utf-8").splitlines()]
    llm = [s for s in harness.senarai_sistem(["semua"]) if s.startswith("llm:")]
    assert llm and set(bandingan.ramal_semua(dev, llm)) == set(llm)
    assert sorted(p.name for p in cache.iterdir()) == sebelum


# ---- klien_anthropic.hantar dengan modul `anthropic` palsu ----

class _APIError(Exception):
    pass


class _APIStatusError(_APIError):
    def __init__(self, status_code, message="x"):
        super().__init__(message)
        self.status_code, self.message = status_code, message


class _RateLimitError(_APIStatusError):
    pass


class _APIConnectionError(_APIError):
    pass


@pytest.fixture
def sdk(monkeypatch):
    rekod = {}

    class Messages:
        def create(self, **kw):
            rekod["kw"] = kw
            if "ralat" in rekod:
                raise rekod["ralat"]
            return SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text="[{"),
                                            SimpleNamespace(type="text", text="}]")],
                                   usage=SimpleNamespace(input_tokens=7, output_tokens=2),
                                   stop_reason=rekod.get("stop_reason", "end_turn"))

    class Anthropic:
        def __init__(self, **kw):
            rekod["klien"] = kw
            self.messages = Messages()

    mod = SimpleNamespace(Anthropic=Anthropic, APIError=_APIError, APIStatusError=_APIStatusError,
                          RateLimitError=_RateLimitError, APIConnectionError=_APIConnectionError)
    monkeypatch.setitem(sys.modules, "anthropic", mod)
    monkeypatch.setenv(K["anthropic"]["env_kunci"], "kunci-palsu-ujian")
    ka._klien.cache_clear()
    yield rekod
    ka._klien.cache_clear()


def test_hantar_gabung_text_tanpa_suhu(sdk):
    t = ka.tetapan(ANTH[0])
    teks, usage = ka.hantar(t["id"], "p", t["permintaan"])
    assert teks == "[{}]" and usage == {"masuk": 7, "keluar": 2}
    assert sdk["kw"] == {"model": t["id"], "messages": [{"role": "user", "content": "p"}], **t["permintaan"]}
    assert "temperature" not in sdk["kw"] and sdk["klien"]["api_key"] == "kunci-palsu-ujian"
    assert sdk["klien"]["max_retries"] == K["anthropic"]["ulang_sdk"]


def test_hantar_tiada_kunci_mesej_jelas(sdk, monkeypatch):
    monkeypatch.delenv(K["anthropic"]["env_kunci"])
    with pytest.raises(SystemExit, match=K["anthropic"]["env_kunci"]):
        ka.hantar("m", "p", {})
    assert "kw" not in sdk


@pytest.mark.parametrize("ralat,jenis", [(_RateLimitError(429), OSError), (_APIStatusError(529), OSError),
                                         (_APIConnectionError(), OSError), (_APIStatusError(400, "thinking ditolak"), ka.TolakAPI),
                                         (_APIStatusError(401), ka.TolakAPI)])
def test_hantar_peta_ralat(sdk, ralat, jenis):
    sdk["ralat"] = ralat
    with pytest.raises(jenis) as e:
        ka.hantar("m", "p", {})
    assert "kunci-palsu-ujian" not in str(e.value)
