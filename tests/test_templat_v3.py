"""PELAN-V2 P4: sasaran templat v3 (latih3 / ujian3) + probe penjana — LLM palsu, folder sementara, tiada rangkaian."""

import json
import random
import re
import shutil

import pytest
import yaml
from test_templat_llm import hantar_palsu as hantar_nama  # nama: penjana palsu B1 yang sama

from mypii import konfig
from mypii.jana import jana, templat_llm

K = konfig.utama()["templat_llm"]
P = konfig.utama()["llm"]["penjana"]


def hantar_v3(model, prompt, suhu):
    """5 positif (slot v3 setiap kategori b–d) + 3 negatif ({NEG12_TANPA}) setiap panggilan; teks unik ikut bahasa + genre."""
    if "Genre:" not in prompt:
        return hantar_nama(model, prompt, suhu)
    g = re.search(r"Genre: (\w+)", prompt).group(1)
    b = re.search(r"Language: (\S+)", prompt).group(1)
    n = int(re.search(r"Write exactly (\d+)", prompt).group(1))
    if b == "Malaysian":
        pos = ["Please contact {NAMA} at {MY_PHONE_BS} about the firm {MY_SSM_LLP} for the form",
               "The form for {NAMA} with IC {OCR_MY_NRIC} was received at the office",
               "Please call {NAMA} at {PATAH_MY_PHONE} for the delivery of this order",
               "The company {OCR_MY_SSM} has a new address for all the payment details",
               "Please send the form to {NAMA} with IC {PATAH_MY_NRIC} at the branch office"]
        neg = ["The reference {NEG12_TANPA} for this payment was received on {TARIKH} at the office",
               "The invoice {NEG_INVOIS} for the payment was received and is with the office",
               "The number {NEG12_TANPA} is on the form that we have received from the branch"]
    else:
        pos = ["Sila hubungi {NAMA} di {MY_PHONE_BS} untuk firma {MY_SSM_LLP} dan borang ini",
               "Borang untuk {NAMA} dengan IC {OCR_MY_NRIC} telah diterima oleh pihak pejabat",
               "Sila hubungi {NAMA} di {PATAH_MY_PHONE} untuk penghantaran dan bayaran ini",
               "Syarikat {OCR_MY_SSM} telah menukar alamat untuk semua urusan dan bayaran",
               "Sila hantar borang kepada {NAMA} dengan IC {PATAH_MY_NRIC} di pejabat cawangan"]
        neg = ["Rujukan {NEG12_TANPA} untuk bayaran ini telah diterima pada {TARIKH} oleh pejabat",
               "Invois {NEG_INVOIS} untuk bayaran ini telah diterima dan disimpan oleh pihak kami",
               "Nombor {NEG12_TANPA} ada pada borang yang telah kami terima dari cawangan"]
    return json.dumps([f"[{b} {g} {i}] {t}." for i, t in enumerate((pos + neg) * 2)][:n])


@pytest.fixture
def akar(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    shutil.copy(konfig.AKAR / "data/nama.yaml", tmp_path / "data/nama.yaml")
    monkeypatch.setitem(konfig.utama()["llm"], "jeda_saat", 0)
    return tmp_path


def _probe_lulus(akar, sasaran, model):
    f = templat_llm.fail_probe(sasaran, akar)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"dipilih": model}))


# --- config ---

def test_config_sasaran_v3_selaras_jana_v3_dan_genre_berbeza():
    s, jv = K["sasaran"], konfig.utama()["jana_v3"]
    assert (s["ujian3"]["folder"], s["ujian3"]["fail_nama"]) == (jv["templat_ujian3"], jv["nama_ujian3"])
    assert s["latih3"]["v3"] and s["ujian3"]["v3"] and not s["latih"].get("v3") and not s["ujian2"].get("v3")
    lama = set(s["latih"]["genre"]) | set(s["ujian2"]["genre"])
    lama |= {g for f in (konfig.AKAR / "data/templat").glob("*.yaml") for g in yaml.safe_load(f.read_text(encoding="utf-8"))["genre"]}
    assert not set(s["ujian3"]["genre"]) & (lama | set(s["latih3"]["genre"]))
    assert not set(s["latih3"]["genre"]) & set(s["ujian2"]["genre"])
    assert len(s["ujian3"]["genre"]) >= K["min_genre_setiap_bahasa"] <= len(s["latih3"]["genre"])
    assert s["ujian3"]["folder"] in s["latih3"]["elak_folder"] and s["latih3"]["folder"] in s["ujian3"]["elak_folder"]
    assert {"data/templat_ujian", "data/templat_ujian2"} <= set(s["latih3"]["elak_folder"]) & set(s["ujian3"]["elak_folder"])
    assert {"data/templat_ujian", "data/templat_ujian2", s["latih3"]["folder"]} <= set(s["ujian3"]["genre_unik_dari"])
    assert s["ujian3"]["folder"] in s["latih3"]["genre_unik_dari"] and "data/templat" in s["ujian3"]["genre_unik_dari"]


def test_slot_v3_setara_sah_dan_kategori_merangkumi_b_hingga_e():
    assert {v["setara"] for v in K["slot_v3"].values()} <= templat_llm.slot_sah()
    assert {x for v in K["kategori_v3"].values() for x in v} <= set(K["slot_v3"])
    assert set(K["kategori_v3"]) == {"b", "c", "d", "e"}   # (a) ROB GUGUR (P1: 0 awalan disahkan)
    assert "MY_ROB" not in templat_llm.slot_sah_v3(K)


def test_setiap_slot_v3_sah_diisi_oleh_jana_isi_v3():
    nama = jana.gabung_nama(yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8")),
                            konfig.AKAR / konfig.utama()["jana"]["nama_tambahan"])
    t = " ".join(f"{{{x}}}" for x in sorted(templat_llm.slot_sah_v3(K)))
    teks, spans, _ = jana.isi_v3(t, random.Random(1), nama)
    assert "{" not in teks and "}" not in teks and spans


def test_keluarga_calon_sebenar_lulus_dan_sabotaj_ditolak():
    templat_llm.semak_keluarga(K, P)
    salin = {x: dict(v) for x, v in P.items()}
    salin["ujian3"] = {**P["ujian3"], "sandaran": [P["latih3"]["model"]]}
    with pytest.raises(SystemExit, match="bertindih"):
        templat_llm.semak_keluarga(K, salin)
    k2 = {**K, "keluarga": {**K["keluarga"], "ag/gemini-9": "google"}}
    with pytest.raises(SystemExit, match="larangan"):
        templat_llm.semak_keluarga(k2, {**P, "latih3": {**P["latih3"], "model": "ag/gemini-9"}})
    with pytest.raises(SystemExit, match="tiada dalam"):
        templat_llm.semak_keluarga(K, {**P, "ujian3": {**P["ujian3"], "model": "x/tidak-dikenali"}})


# --- pengesah ---

def test_tapis_templat_v3_simpan_slot_asal_tolak_slot_liar_dan_pendua():
    t = "Sila hubungi {NAMA} di {MY_PHONE_BS} untuk urusan sewa rumah ini dan bayaran."
    liar = "Sila hubungi {NAMA} di {OCR_MY_ROB} untuk urusan sewa rumah ini dan bayaran."
    sama_v1 = "Sila hubungi {NAMA} di {MY_PHONE} untuk urusan sewa rumah ini dan bayaran."
    hasil, tolak = templat_llm.tapis_templat_v3({("ms", "a"): [t, liar, t]}, K, set())
    assert hasil == {"ms": {"a": [t]}} and tolak == {"slot_tidak_sah": 1, "pendua": 1}
    _, tolak = templat_llm.tapis_templat_v3({("ms", "a"): [t]}, K, {templat_llm._norm(sama_v1)})
    assert tolak == {"pendua": 1}   # dibanding dalam bentuk dipetakan v1
    _, tolak = templat_llm.tapis_templat_v3({("ms", "a"): [t]}, K, set(), frozenset({templat_llm._norm(sama_v1)}))
    assert tolak == {"sama_sasaran_elak": 1}
    neg = "Rujukan {NEG12_TANPA} untuk bayaran ini telah diterima oleh pihak kami semalam."
    st = templat_llm.statistik_v3({"ms": {"a": [t, neg]}}, K)
    assert st["negatif_sahaja"] == 1 and st["kategori"] == {"b": 0, "c": 1, "d": 0, "e": 1}


def test_prompt_v3_lengkap():
    p = templat_llm.prompt_v3("ujian3", "ms", next(iter(K["sasaran"]["ujian3"]["genre"])), 8, 3)
    assert "$" not in p and all(f"{{{x}}}" in p for x in K["slot_v3"])
    assert "{NEG12_TANPA}" not in p.split("contain NONE of")[1].split(";")[0]   # (e) bukan positif



def test_keluarga_b_kecuali_hanya_ujian3_dan_haiku_dilarang():
    """Pindaan 2026-11-05 (c): mistral/anthropic dibenarkan untuk ujian3 SAHAJA; Haiku (pembanding H4a) dilarang di mana-mana."""
    assert K["keluarga_larangan_kecuali"] == {"ujian3": ["mistral", "anthropic"]}
    mistral = P["ujian3"]["model"]
    with pytest.raises(SystemExit, match="larangan"):   # sama model, sasaran latih3 → tiada pengecualian
        templat_llm.semak_keluarga(K, {**P, "latih3": {**P["latih3"], "model": mistral}, "ujian3": {**P["ujian3"], "model": P["latih3"]["model"]}})
    haiku = "anthropic/claude-haiku-5-5"
    k2 = {**K, "keluarga": {**K["keluarga"], haiku: "anthropic"}}
    with pytest.raises(SystemExit, match="penjana_larangan_tepat"):
        templat_llm.semak_keluarga(k2, {**P, "ujian3": {**P["ujian3"], "sandaran": [haiku]}})


def test_hantar_penjana_anthropic_lejar_dan_had(tmp_path, monkeypatch):
    from mypii import klien_anthropic as ka
    panggil = []
    monkeypatch.setattr(ka, "hantar", lambda mid, p, perm: panggil.append((mid, perm)) or ("[]", {"masuk": 1000, "keluar": 500}))
    monkeypatch.setattr(templat_llm, "_LEJAR", [ka.Lejar(tmp_path / "l.json", 20)])
    monkeypatch.setattr(templat_llm, "hantar_9router", lambda *a: pytest.fail("9router dipanggil untuk anthropic/"))
    assert templat_llm.hantar_penjana("anthropic/claude-sonnet-5-5", "x" * 30, 0.8) == "[]"
    mid, perm = panggil[0]
    assert mid == "claude-sonnet-5-5" and perm["max_tokens"] == K["anthropic_max_tokens"] and "temperature" not in perm
    assert templat_llm._LEJAR[0].data["model"]["anthropic/claude-sonnet-5-5"]["panggilan"] == 1
    monkeypatch.setattr(templat_llm, "_LEJAR", [ka.Lejar(tmp_path / "l2.json", 0.0001)])
    with pytest.raises(ka.HadDicapai):
        templat_llm.hantar_penjana("anthropic/claude-sonnet-5-5", "x", 0.8)
    assert len(panggil) == 1   # had dicapai → tiada panggilan
    monkeypatch.setattr(templat_llm, "hantar_9router", lambda m, p, t: "ok9")
    assert templat_llm.hantar_penjana(P["ujian3"]["model"], "x", 0.8) == "ok9"

# --- probe ---

def test_probe_calon_pertama_gagal_sandaran_dipilih_tiada_kandungan(akar):
    panggil = []

    def hantar(model, prompt, suhu):
        panggil.append(model)
        if model == P["ujian3"]["model"]:
            raise OSError("mati")
        return hantar_v3(model, prompt, suhu)

    h = templat_llm.probe_v3("ujian3", hantar=hantar, akar=akar)
    assert h["dipilih"] == P["ujian3"]["sandaran"][0]
    assert [c["lulus"] for c in h["calon"]] == [False, True]
    assert h["genre"] == list(K["sasaran"]["ujian3"]["genre"])[:K["probe"]["genre"]]
    assert set(h["calon"][1]["per_genre"]) == set(h["genre"])
    teks = templat_llm.fail_probe("ujian3", akar).read_text()
    assert "{NAMA}" not in teks and "Sila" not in teks   # statistik sahaja
    with pytest.raises(SystemExit, match="tidak diulang"):
        templat_llm.probe_v3("ujian3", hantar=hantar, akar=akar)


def test_probe_ambang_jumlah_merentas_genre_bukan_satu_lambungan(akar):
    """Pindaan 2026-11-05: satu genre lemah tidak menggagalkan calon; jumlah sah < ambang menggagalkan."""
    g = list(K["sasaran"]["latih3"]["genre"])[:K["probe"]["genre"]]
    n, ambang = K["probe"]["templat"], K["probe"]["min_nisbah_sah"]

    def sebahagian(bil_sah):
        def hantar(m, p, t):
            genre = re.search(r"Genre: (\w+)", p).group(1)
            sah = json.loads(hantar_v3(m, p, t))[:bil_sah.get(genre, 0)]
            return json.dumps(sah + ["{SLOT_PELIK} rosak"] * (n - len(sah)))
        return hantar

    lemah_satu = {x: n for x in g} | {g[0]: 0}
    h = templat_llm.probe_v3("latih3", hantar=sebahagian(lemah_satu), akar=akar)
    assert h["dipilih"] == P["latih3"]["model"] and h["calon"][0]["per_genre"][g[0]] == 0
    templat_llm.fail_probe("latih3", akar).unlink()
    kurang = {x: int(n * ambang) - 1 for x in g}
    h = templat_llm.probe_v3("latih3", hantar=sebahagian(kurang), akar=akar)
    assert h["dipilih"] is None


def test_probe_lulus_pertama_tidak_memanggil_sandaran_dan_semua_gagal_tiada_pilihan(akar):
    panggil = []
    h = templat_llm.probe_v3("ujian3", hantar=lambda m, p, t: panggil.append(m) or hantar_v3(m, p, t), akar=akar)
    assert h["dipilih"] == P["ujian3"]["model"] and set(panggil) == {P["ujian3"]["model"]}
    h = templat_llm.probe_v3("latih3", hantar=lambda m, p, t: '["{SLOT_PELIK} " ]', akar=akar)
    assert h["dipilih"] is None and not any(c["lulus"] for c in h["calon"])


# --- jana ---

def test_jana_v3_tanpa_probe_ditolak(akar):
    with pytest.raises(SystemExit, match="probe"):
        templat_llm.jana_sasaran_v3("latih3", hantar=hantar_v3, akar=akar)
    assert not (akar / K["sasaran"]["latih3"]["folder"]).exists()


def test_jana_latih3_model_dipilih_sahaja_kategori_dan_meterai(akar):
    _probe_lulus(akar, "latih3", P["latih3"]["model"])
    panggil = set()
    st = templat_llm.jana_sasaran_v3("latih3", hantar=lambda m, p, t: panggil.add(m) or hantar_v3(m, p, t), akar=akar)
    assert "gagal_ambang" not in st, st.get("gagal_ambang")
    assert panggil == {P["latih3"]["model"]} and st["model"] == P["latih3"]["model"]
    assert all(n >= K["sasaran"]["latih3"]["min_kategori"] for n in st["kategori"].values())
    s = K["sasaran"]["latih3"]
    assert sorted(f.name for f in (akar / s["folder"]).glob("*.yaml")) == sorted(f"llm_{b}.yaml" for b in K["bahasa"])
    t = jana._templat(akar / s["folder"])   # dibaca oleh jana_v3 (P5) dengan slot v3 utuh
    assert any("{MY_SSM_LLP}" in x for _, x in t["ms"]) and "{NAMA}" not in json.dumps(st)
    with pytest.raises(SystemExit, match="DIMETERAI"):
        templat_llm.jana_sasaran_v3("latih3", hantar=hantar_v3, akar=akar)


def test_jana_latih3_panggilan_berganda_digabung_sebelum_pengesah(akar):
    """Pindaan 2026-11-05 (b): `panggilan` N = N panggilan setiap bahasa × genre; pendua antara panggilan ditolak; ujian3 kekal 1."""
    s = K["sasaran"]["latih3"]
    assert s["panggilan"] == 2 and K["sasaran"]["ujian3"].get("panggilan", 1) == 1
    _probe_lulus(akar, "latih3", P["latih3"]["model"])
    kiraan = []
    st = templat_llm.jana_sasaran_v3("latih3", hantar=lambda m, p, t: kiraan.append(1) or hantar_v3(m, p, t), akar=akar)
    assert len(kiraan) == s["panggilan"] * len(K["bahasa"]) * len(s["genre"])
    assert st["dipohon"] == len(kiraan) * K["templat_setiap_panggilan"]
    assert st["tolak"].get("pendua", 0) > 0   # jawapan palsu sama setiap panggilan → panggilan kedua = pendua


def test_jana_ujian3_nama_bersilang_kosong_dengan_semua_fail_nama(akar):
    _probe_lulus(akar, "ujian3", P["ujian3"]["model"])
    kat = "pertama_melayu_l"
    nama_u2 = json.loads(hantar_nama("m", K["nama"]["huraian"][kat], 0))[0]
    (akar / "data/nama_ujian2.yaml").write_text(yaml.safe_dump({kat: [nama_u2]}))
    kiraan = []
    st = templat_llm.jana_sasaran_v3("ujian3", hantar=lambda m, p, t: kiraan.append("Genre:" in p) or hantar_v3(m, p, t), akar=akar)
    assert "gagal_ambang" not in st, st.get("gagal_ambang")
    s3 = K["sasaran"]["ujian3"]
    assert kiraan.count(False) == s3["panggilan_nama"] * len(K["nama"]["huraian"])   # pindaan d: N panggilan nama
    assert kiraan.count(True) == len(K["bahasa"]) * len(s3["genre"])               # templat kekal 1 panggilan
    assert st["tolak_nama"].get(f"{kat}:pendua", 0) >= 1
    nama3 = yaml.safe_load((akar / K["sasaran"]["ujian3"]["fail_nama"]).read_text(encoding="utf-8"))
    assert nama_u2 not in nama3[kat] and set(nama3) == set(K["nama"]["min"])



def test_semak_fail_v3_memakai_pengesah_penjanaan(akar):
    """5 Nov: semak_fail (gerbang §6) dulu memakai pengesah v1 atas teks v3 → slot v3 sah = tolak palsu. Kini sama dengan penjanaan."""
    _probe_lulus(akar, "ujian3", P["ujian3"]["model"])
    st = templat_llm.jana_sasaran_v3("ujian3", hantar=hantar_v3, akar=akar)
    assert "gagal_ambang" not in st
    r = templat_llm.semak_fail("ujian3", akar)
    assert r["templat"] > 0 and not [x for x in r["templat_ikut_sebab"] if not x.endswith(":sah")]
    f = akar / K["sasaran"]["ujian3"]["folder"] / "ms.yaml"
    d = yaml.safe_load(f.read_text(encoding="utf-8"))
    g = next(iter(d["genre"]))
    d["genre"][g].append("Sila hubungi {NAMA} di {SLOT_REKAAN} untuk borang ini dan bayaran yang telah diterima")
    f.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    assert templat_llm.semak_fail("ujian3", akar)["templat_ikut_sebab"].get("ms:slot_tidak_sah") == 1

def test_semak_fail_latih3_tanpa_fail_nama(akar):
    """v2.x: latih3 tiada `fail_nama` (nama = nama.yaml + nama_tambahan) — semak_fail dulu KeyError; kini kiraan templat sahaja."""
    _probe_lulus(akar, "latih3", P["latih3"]["model"])
    st = templat_llm.jana_sasaran_v3("latih3", hantar=hantar_v3, akar=akar)
    assert "gagal_ambang" not in st and "fail_nama" not in K["sasaran"]["latih3"]
    r = templat_llm.semak_fail("latih3", akar)
    assert r["templat"] > 0 and r["nama_ikut_sebab"] == {}
    assert not [x for x in r["templat_ikut_sebab"] if not x.endswith(":sah")]


def test_jana_genre_bertindih_dengan_folder_elak_berhenti_sebelum_llm(akar):
    _probe_lulus(akar, "ujian3", P["ujian3"]["model"])
    g = next(iter(K["sasaran"]["ujian3"]["genre"]))
    (akar / "data/templat_ujian").mkdir(parents=True)
    (akar / "data/templat_ujian/ms.yaml").write_text(yaml.safe_dump({"genre": {g: ["x {MY_NRIC}"]}}))
    with pytest.raises(SystemExit, match="genre sama"):
        templat_llm.jana_sasaran_v3("ujian3", hantar=lambda *a: pytest.fail("LLM dipanggil"), akar=akar)


def test_jana_v3_ambang_kategori_gagal_tidak_menulis(akar):
    _probe_lulus(akar, "latih3", P["latih3"]["model"])

    def tanpa_llp(m, p, t):
        return hantar_v3(m, p, t).replace("{MY_SSM_LLP}", "{MY_SSM}")

    st = templat_llm.jana_sasaran_v3("latih3", hantar=tanpa_llp, akar=akar)
    assert any(x.startswith("kategori b 0") for x in st["gagal_ambang"])
    assert not (akar / K["sasaran"]["latih3"]["folder"]).exists()


def test_main_v3_probe_rc3_bila_semua_gagal(akar, monkeypatch, capsys):
    monkeypatch.setattr(templat_llm, "probe_v3", lambda s: {"dipilih": None, "calon": []})
    monkeypatch.setattr(templat_llm.os, "nice", lambda n: 0)
    monkeypatch.setattr("sys.argv", ["t", "--sasaran", "latih3", "--probe"])
    assert templat_llm.main() == 3
    monkeypatch.setattr("sys.argv", ["t", "--sasaran", "latih", "--probe"])
    assert templat_llm.main() == 2
