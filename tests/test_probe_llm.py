"""PELAN-MODEL-LAIN P3 (pindaan PRA-DAFTAR 2026-11-03, ADR-017): probe format eksplorasi + parameter Opus/Fable + `kos_claude --rancang`.

Semua luar talian: `hantar` palsu (9router + Anthropic), `kira` palsu (count_tokens), lejar dalam tmp_path.
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from mypii import klien_anthropic as ka
from mypii import konfig
from mypii.nilai import garis, kos_claude, probe_llm

K = konfig.utama()["garis_dasar"]["llm"]
EKS = K["eksplorasi"]
EKS_ANTH = [m for m in EKS if m.startswith("anthropic/")]
EKS_9R = [m for m in EKS if not m.startswith("anthropic/")]
PENGESAHAN_ANTH = [m for m in K["model"] if m.startswith("anthropic/")]
# id menurun: susunan FAIL ≠ susunan diisih → probe mesti mengambil N pertama ikut fail
DOK = [{"id": str(9 - i), "bahasa": "ms", "teks": f"IC 900101-14-56{i:02d} tel 012-34567{i:02d}", "spans": []} for i in range(8)]


@pytest.fixture(autouse=True)
def pantas(monkeypatch):
    monkeypatch.setitem(konfig.utama()["llm"], "jeda_saat", 0)
    monkeypatch.setitem(konfig.utama()["llm"], "serentak", 1)
    monkeypatch.setattr(garis.os, "nice", lambda n: 0)


@pytest.fixture
def lejar_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(ka.Lejar, "dari_config", classmethod(lambda cls, akar=None: cls(tmp_path / "lejar.json", 20)))
    return tmp_path


class H9:
    """hantar 9router palsu: jawapan ikut model; `ralat` = OSError setiap panggilan."""

    def __init__(self, jawapan):
        self.jawapan, self.panggilan = jawapan, []

    def __call__(self, model, prompt, suhu):
        self.panggilan.append((model, suhu))
        j = self.jawapan[model]
        if isinstance(j, Exception):
            raise j
        return j


class HA:
    def __init__(self, jawapan, usage=None):
        self.jawapan, self.usage, self.panggilan = jawapan, usage or {"masuk": 100, "keluar": 40}, []

    def __call__(self, mid, prompt, permintaan):
        self.panggilan.append((mid, permintaan))
        j = self.jawapan[f"anthropic/{mid}"]
        if isinstance(j, BaseException):
            raise j
        return j, dict(self.usage)


def _jawapan_lulus():
    return {m: '[{"teks": "012-3456700", "entiti": "MY_PHONE"}]' for m in EKS}


def _cari_kunci(x, kata):
    if isinstance(x, dict):
        return any(kata in str(k).lower() or _cari_kunci(v, kata) for k, v in x.items())
    if isinstance(x, list):
        return any(_cari_kunci(v, kata) for v in x)
    return kata in str(x).lower()


# --- parameter Opus/Fable (klien_anthropic) ----------------------------------------------------------------------------------

def test_calon_claude_ada_tetapan_tanpa_suhu_pemikiran_fallback():
    assert EKS_ANTH, "config eksplorasi tiada calon anthropic/"
    for m in EKS_ANTH:
        t, c = ka.tetapan(m), K["anthropic"]["model"][m.removeprefix("anthropic/")]
        assert t["permintaan"]["max_tokens"] == c["max_tokens"] != K["anthropic"]["max_tokens"]
        assert not {"temperature", "thinking", "fallbacks", "betas"} & set(t["permintaan"])
        assert t["permintaan"]["output_config"] == c["parameter"]["output_config"]


def test_pengesahan_max_tokens_lalai_global_dan_permintaan_tidak_berubah():
    for m in PENGESAHAN_ANTH:
        c = K["anthropic"]["model"][m.removeprefix("anthropic/")]
        assert "max_tokens" not in c
        assert ka.tetapan(m)["permintaan"] == {"max_tokens": K["anthropic"]["max_tokens"], **c["parameter"]}


def test_cache_dikomit_sonnet_haiku_kunci_tidak_berubah_atas_dev():
    """Kunci cache (model + prompt + permintaan + teks) Sonnet/Haiku = kunci jawapan dikomit P4 lama: tiada panggilan semula."""
    dev = [json.loads(x) for x in (konfig.AKAR / "data/bench/dev.jsonl").read_text(encoding="utf-8").splitlines()]
    for m in PENGESAHAN_ANTH:
        cache = garis._muat_cache(garis.fail_cache(m))
        assert all(garis.kunci_dok(m, d["teks"]) in cache for d in dev)   # P8 (5 Nov): entri dev3 Haiku juga sah dalam fail sama


def test_kos_terburuk_guna_max_tokens_model():
    m = EKS_ANTH[0]
    t = ka.tetapan(m)
    assert ka.kos_terburuk("", t) == ka.kos({"masuk": 0, "keluar": t["permintaan"]["max_tokens"]}, t["harga"])


def test_refusal_jawapan_kosong_dikira_rosak(tmp_path, lejar_tmp):
    rekod = {}

    class Messages:
        def create(self, **kw):
            rekod["kw"] = kw
            return SimpleNamespace(content=[SimpleNamespace(type="text", text='[{"teks": "x", "entiti": "MY_PHONE"}]')],
                                   usage=SimpleNamespace(input_tokens=5, output_tokens=3), stop_reason="refusal")

    class Anthropic:
        def __init__(self, **kw):
            self.messages = Messages()

    class _E(Exception):
        status_code = 0

    mod = SimpleNamespace(Anthropic=Anthropic, APIStatusError=_E, RateLimitError=_E, APIConnectionError=_E)
    mp = pytest.MonkeyPatch()
    mp.setitem(sys.modules, "anthropic", mod)
    mp.setenv(K["anthropic"]["env_kunci"], "kunci-palsu")
    ka._klien.cache_clear()
    try:
        teks, usage = ka.hantar("claude-x", "p", {})
        assert teks == "" and usage == {"masuk": 5, "keluar": 3}
        _, st = garis.ramal_llm(EKS_ANTH[0], DOK[:2], akar=tmp_path)  # jalan SDK (palsu) sebenar
        assert st["rosak"] == 2 and st["gagal"] == 0 and st["usd"] > 0
        assert "temperature" not in rekod["kw"] and "thinking" not in rekod["kw"]
    finally:
        mp.undo()
        ka._klien.cache_clear()


# --- ramal_llm menerima eksplorasi ---------------------------------------------------------------------------------------------

def test_ramal_llm_terima_eksplorasi_tolak_model_lain(tmp_path):
    _, st = garis.ramal_llm(EKS_9R[0], DOK[:1], hantar=H9(_jawapan_lulus()), akar=tmp_path)
    assert st["panggilan"] == 1 and "ralat" not in st
    with pytest.raises(SystemExit, match="bukan garis dasar"):
        garis.ramal_llm("cbcn/kimi-k3", DOK[:1], hantar=H9({"cbcn/kimi-k3": "[]"}), akar=tmp_path)


# --- probe ---------------------------------------------------------------------------------------------------------------------

def _probe(tmp_path, j9, ja, n=5, monkeypatch=None):
    monkeypatch.setitem(K["probe"], "dokumen", n)
    return probe_llm.jalankan(DOK, "dev", akar=tmp_path, hantar_9router=H9(j9), hantar_anthropic=HA(ja))


def test_probe_semua_lulus_n_pertama_ikut_susunan_fail(tmp_path, lejar_tmp, monkeypatch):
    j = _jawapan_lulus()
    h = _probe(tmp_path, j, j, n=3, monkeypatch=monkeypatch)
    assert h["id"] == [d["id"] for d in DOK[:3]] and h["dokumen"] == 3
    assert h["lulus"] == EKS and h["gugur"] == []
    for m in EKS:
        assert h["model"][m] | {"jenis_ralat": []} == h["model"][m]
        assert (h["model"][m]["diterima"], h["model"][m]["diurai"], h["model"][m]["panggilan"]) == (3, 3, 3)
    assert all("usd" in h["model"][m] for m in EKS_ANTH) and not any("usd" in h["model"][m] for m in EKS_9R)


def test_probe_gagal_rosak_tolak_jadi_gugur_dengan_jenis_ralat(tmp_path, lejar_tmp, monkeypatch):
    j = _jawapan_lulus()
    j[EKS_9R[0]] = OSError("HTTP 400 suhu ditolak")        # gagal selepas ulang
    j[EKS_9R[1]] = "maaf, saya tidak boleh"                 # tidak diurai
    j[EKS_ANTH[0]] = ka.TolakAPI("claude: HTTP 400 BadRequestError: parameter")
    j[EKS_ANTH[1]] = ""                                      # refusal → kosong
    h = _probe(tmp_path, j, j, monkeypatch=monkeypatch)
    assert set(h["gugur"]) == {EKS_9R[0], EKS_9R[1], *EKS_ANTH} and h["lulus"] == EKS_9R[2:]
    a, b = h["model"][EKS_9R[0]], h["model"][EKS_9R[1]]
    assert (a["diterima"], a["lulus"]) == (0, False) and any("OSError" in x for x in a["jenis_ralat"])
    assert (b["diterima"], b["diurai"]) == (5, 0) and any("tidak diurai" in x for x in b["jenis_ralat"])
    assert h["model"][EKS_ANTH[0]]["jenis_ralat"][0].startswith("TolakAPI")
    assert h["model"][EKS_ANTH[1]]["diurai"] == 0


def test_probe_separa_gagal_tetap_gugur(tmp_path, lejar_tmp, monkeypatch):
    j = _jawapan_lulus()

    class Separa(H9):
        def __call__(self, model, prompt, suhu):
            if model == EKS_9R[0] and DOK[1]["teks"] in prompt:
                raise OSError("tamat masa")
            return super().__call__(model, prompt, suhu)

    monkeypatch.setitem(K["probe"], "dokumen", 5)
    h = probe_llm.jalankan(DOK, "dev", akar=tmp_path, hantar_9router=Separa(j), hantar_anthropic=HA(j))
    assert EKS_9R[0] in h["gugur"] and h["model"][EKS_9R[0]]["diterima"] == 4


def test_probe_tiada_f1_tiada_teks_dalam_output(tmp_path, lejar_tmp, monkeypatch):
    j = _jawapan_lulus()
    j[EKS_9R[1]] = "teks jawapan rahsia 012-3456700"
    h = _probe(tmp_path, j, j, monkeypatch=monkeypatch)
    for kata in ("f1", "tepat", "separa", "spans", "jawapan rahsia", "012-34567", "ic 9001"):
        assert not _cari_kunci(h, kata), kata


def test_probe_cache_disambung_larian_penuh(tmp_path, lejar_tmp, monkeypatch):
    """Probe = kunci cache sama: larian penuh selepasnya memanggil hanya dokumen BAKI (bukan larian kedua)."""
    j = _jawapan_lulus()
    _probe(tmp_path, j, j, n=3, monkeypatch=monkeypatch)
    h9 = H9(j)
    _, st = garis.ramal_llm(EKS_9R[0], DOK, hantar=h9, akar=tmp_path)
    assert (st["dari_cache"], st["panggilan"], len(h9.panggilan)) == (3, len(DOK) - 3, len(DOK) - 3)


def test_probe_split_dikunci_ditolak_sebelum_fail_dibaca(monkeypatch):
    def jangan(*_):
        raise AssertionError("split dikunci dibaca")

    monkeypatch.setattr("mypii.nilai.harness._dokumen", jangan)
    monkeypatch.setitem(K["probe"], "split", ["dev", *konfig.utama()["nilai"]["split_dikunci"]])
    for s in konfig.utama()["nilai"]["split_dikunci"] + ["latih"]:
        with pytest.raises(SystemExit, match="split"):
            probe_llm.main(["--split", s])


def test_probe_main_tulis_fail(tmp_path, lejar_tmp, monkeypatch):
    monkeypatch.setattr(konfig, "AKAR", tmp_path)
    monkeypatch.setattr("mypii.nilai.harness._dokumen", lambda s: DOK)
    j, asal = _jawapan_lulus(), probe_llm.jalankan
    monkeypatch.setattr(probe_llm, "jalankan", lambda d, s: asal(d, s, akar=tmp_path, hantar_9router=H9(j), hantar_anthropic=HA(j)))
    assert probe_llm.main(["--split", "dev"]) == 0
    h = json.loads(probe_llm.fail_hasil("dev", tmp_path).read_text())
    assert h["lulus"] == EKS


# --- kos_claude --rancang ------------------------------------------------------------------------------------------------------

def _lejar(tmp_path, pengesahan_usd=1.0, probe_usd=0.01, keluar=10, panggilan=5, had=20):
    lj = ka.Lejar(tmp_path / "lejar-rancang.json", had)
    for m in PENGESAHAN_ANTH:
        lj.data["model"][m] = {"masuk": 0, "keluar": 0, "usd": pengesahan_usd, "panggilan": 1000}
    for m in EKS_ANTH:
        lj.data["model"][m] = {"masuk": 0, "keluar": keluar * panggilan, "usd": probe_usd, "panggilan": panggilan}
    lj.data["jumlah_usd"] = round(sum(x["usd"] for x in lj.data["model"].values()), 6)
    return lj


def _probe_lulus(gugur=()):
    return {"model": {m: {"lulus": m not in gugur, "jenis_ralat": ["OSError"] if m in gugur else []} for m in EKS}}


def _kira(token=1000):
    return lambda mid, prompt, parameter: token


def _anggar_satu(m, n_dok, token=1000, keluar=10):
    t = ka.tetapan(m)
    return (n_dok * token * t["harga"]["masuk"] + keluar * n_dok * K["anthropic"]["kos"]["margin"] * t["harga"]["keluar"]) / 1e6


def test_rancang_formula_dan_semua_muat(tmp_path):
    lj = _lejar(tmp_path)
    r = kos_claude.rancang(DOK, _probe_lulus(), kira=_kira(), lejar=lj, tidur=lambda s: None)
    assert r["dipilih"] == EKS_ANTH and r["digugurkan"] == {} and r["muat"]
    for m in EKS_ANTH:
        satu = _anggar_satu(m, len(DOK))
        assert r["model"][m]["usd_satu_split"] == round(satu, 6) and r["model"][m]["usd_perlu"] == round(3 * satu - 0.01, 6)
    lama = 2 * 1.0 * len(PENGESAHAN_ANTH)
    assert r["perlu_ujian_usd"] == round(lama + sum(2 * r["model"][m]["usd_satu_split"] for m in EKS_ANTH), 6)
    assert r["baki_usd"] == round(20 - lj.data["jumlah_usd"], 6) and r["margin"] == K["anthropic"]["kos"]["margin"]


def _token_supaya(tmp_path, muat_bilangan):
    """Cari token masuk supaya pengesahan + `muat_bilangan` calon termurah-dahulu muat (ikut susunan gugur)."""
    for token in range(1000, 10_000_000, 1000):
        lj = _lejar(tmp_path)
        r = kos_claude.rancang(DOK * 50, _probe_lulus(), kira=_kira(token), lejar=lj, tidur=lambda s: None)
        if len(r["dipilih"]) == muat_bilangan:
            return r
    raise AssertionError("tiada token yang memberi bilangan dipilih itu")


def test_rancang_gugur_ikut_susunan_config_fable_dahulu_kemudian_opus(tmp_path):
    gugur = K["anthropic"]["kos"]["gugur"]
    assert gugur[0].endswith("fable-5-1") and gugur[1].endswith("opus-5-5")  # pindaan: Fable dahulu, kemudian Opus
    r1 = _token_supaya(tmp_path, 1)
    assert list(r1["digugurkan"]) == gugur[:1] and r1["dipilih"] == [m for m in EKS_ANTH if m != gugur[0]]
    assert r1["digugurkan"][gugur[0]].startswith("kos:") and r1["muat"]
    r0 = _token_supaya(tmp_path, 0)
    assert list(r0["digugurkan"]) == gugur and r0["dipilih"] == [] and r0["muat"]
    assert r0["perlu_ujian_usd"] == round(2 * 1.0 * len(PENGESAHAN_ANTH), 6)


def test_rancang_susunan_dari_config_bukan_kod(tmp_path, monkeypatch):
    monkeypatch.setitem(K["anthropic"]["kos"], "gugur", list(reversed(K["anthropic"]["kos"]["gugur"])))
    r = _token_supaya(tmp_path, 1)
    assert list(r["digugurkan"]) == K["anthropic"]["kos"]["gugur"][:1]


def test_rancang_pengesahan_sahaja_tidak_muat_exit_3(tmp_path):
    lj = _lejar(tmp_path, pengesahan_usd=4.0)  # 2 × 2 × 4 = 16 > baki 20 − 8.02
    r = kos_claude.rancang(DOK, _probe_lulus(), kira=_kira(), lejar=lj, tidur=lambda s: None)
    assert not r["muat"] and r["dipilih"] == [] and lj.had == 20


def test_rancang_probe_gagal_gugur_tanpa_count_tokens(tmp_path):
    dipanggil = []
    lj = _lejar(tmp_path)
    r = kos_claude.rancang(DOK, _probe_lulus(gugur=EKS_ANTH[:1]), lejar=lj, tidur=lambda s: None,
                           kira=lambda mid, p, q: dipanggil.append(mid) or 1000)
    assert r["digugurkan"][EKS_ANTH[0]].startswith("probe:") and EKS_ANTH[0] not in r["dipilih"]
    assert EKS_ANTH[0].removeprefix("anthropic/") not in dipanggil and dipanggil


def test_rancang_tanpa_probe_berbayar_ditolak(tmp_path):
    lj = _lejar(tmp_path)
    del lj.data["model"][EKS_ANTH[0]]
    with pytest.raises(SystemExit, match="probe"):
        kos_claude.rancang(DOK, _probe_lulus(), kira=_kira(), lejar=lj, tidur=lambda s: None)


def test_rancang_split_dikunci_ditolak_sebelum_dibaca(monkeypatch):
    def jangan(*_):
        raise AssertionError("split dikunci dibaca")

    monkeypatch.setattr("mypii.nilai.harness._dokumen", jangan)
    for s in konfig.utama()["nilai"]["split_dikunci"]:
        with pytest.raises(SystemExit, match="split"):
            kos_claude.main(["--split", s, "--rancang"])


def test_main_rancang_tulis_blok_dan_anggaran_semula_mengekalkannya(tmp_path, monkeypatch):
    monkeypatch.setattr(konfig, "AKAR", tmp_path)
    monkeypatch.setattr("mypii.nilai.harness._dokumen", lambda s: DOK)
    lj = _lejar(tmp_path)
    monkeypatch.setattr(ka.Lejar, "dari_config", classmethod(lambda cls, akar=None: lj))
    monkeypatch.setattr(kos_claude, "kira_token_api", _kira())
    monkeypatch.setattr(kos_claude.rancang, "__defaults__", (_kira(), None, tmp_path, lambda s: None))
    fp = probe_llm.fail_hasil("dev", tmp_path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(_probe_lulus()))
    fail = tmp_path / K["anthropic"]["kos"]["fail"].format(split="dev")
    fail.write_text(json.dumps({"split": "dev", "lain": 1}))
    assert kos_claude.main(["--split", "dev", "--rancang"]) == 0
    h = json.loads(fail.read_text())
    blok = K["anthropic"]["kos"]["blok_rancang"]
    assert h["lain"] == 1 and h[blok]["dipilih"] == EKS_ANTH


def test_probe_tidak_import_klien_anthropic_terus():
    """Gerbang §17: klien Anthropic hanya diimport dari garis.py / kos_claude.py — probe melalui `garis` sahaja."""
    import re

    src = Path(probe_llm.__file__).read_text(encoding="utf-8")
    assert not re.search(r"klien_anthropic|import anthropic|from anthropic", src)
