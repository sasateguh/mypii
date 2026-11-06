"""PELAN-B B1: penjana templat/nama LLM + split ujian2 — luar talian (klien palsu), tiada kandungan ujian2 dibaca."""

import hashlib
import itertools
import json
import re
import shutil
import sys

import pytest
import yaml

from mypii import klien_llm, konfig
from mypii.jana import jana, templat_llm
from mypii.nilai import harness

K = konfig.utama()["templat_llm"]
SUKU = ["za", "ri", "mo", "ke", "lu", "ta", "vi", "no", "qe", "xu"]


def _rekaan(n: int, awalan: str) -> list[str]:
    return [awalan + "".join(p).capitalize() for p in itertools.islice(itertools.product(SUKU, repeat=3), n)]


def hantar_palsu(model, prompt, suhu):
    if "Genre:" in prompt:
        g = re.search(r"Genre: (\w+)", prompt).group(1)
        baris = re.search(r"Language: (.+)", prompt).group(1)
        b = baris.split()[0]
        if baris.startswith("Malaysian English"):
            pos = [f"[{g} {i}] Please contact {{NAMA}} at {{MY_PHONE}} with your IC {{MY_NRIC}} for the form." for i in range(5)]
            neg = [f"[{g} n{i}] The payment to account {{NEG_AKAUN}} for invoice {{NEG_INVOIS}} was received." for i in range(3)]
        else:
            pos = [f"[{b} {g} {i}] Sila hubungi {{NAMA}} di {{MY_PHONE}} dengan IC {{MY_NRIC}} untuk borang." for i in range(5)]
            neg = [f"[{b} {g} n{i}] Bayaran ke akaun {{NEG_AKAUN}} untuk invois {{NEG_INVOIS}} telah diterima." for i in range(3)]
        return "```json\n" + json.dumps(pos + neg) + "\n```"
    kat = next(k for k, h in K["nama"]["huraian"].items() if h in prompt)
    akhir = " Sdn Bhd" if kat == "syarikat" else ""
    awalan = kat.split("_")[-1][:2] + kat[0]
    return json.dumps([(x + akhir).lower() if kat.startswith("keluarga_") else x + akhir for x in _rekaan(60, awalan.capitalize())])


@pytest.fixture
def akar(tmp_path):
    (tmp_path / "data").mkdir()
    shutil.copy(konfig.AKAR / "data/nama.yaml", tmp_path / "data/nama.yaml")
    return tmp_path


def test_sebab_tolak():
    k = K
    assert templat_llm.sebab_tolak("Sila hubungi {NAMA} di {MY_PHONE} untuk urusan sewa rumah ini.", k) is None
    assert templat_llm.sebab_tolak("Sila hubungi {NAMA} di {NOMBOR_PELIK} untuk urusan sewa rumah ini.", k) == "slot_tidak_sah"
    assert templat_llm.sebab_tolak("Sila hubungi {nama} di {MY_PHONE} untuk urusan sewa rumah ini.", k) == "kurungan_liar"
    assert templat_llm.sebab_tolak("Sila hubungi {NAMA} di 012-345 6789 untuk urusan sewa rumah ini.", k) == "nombor_literal"
    assert templat_llm.sebab_tolak("Sila hubungi {NAMA} di {MY_PHONE}, unit 12 tingkat 3, sewa rumah.", k) is None
    assert templat_llm.sebab_tolak("Sila hubungi {NAMA} untuk urusan sewa rumah yang dibincangkan.", k) == "tiada_slot_nombor"
    assert templat_llm.sebab_tolak("Tel {MY_PHONE}", k) == "panjang"
    assert templat_llm.sebab_tolak("Pindahan ke akaun Maybank {NEG_AKAUN} telah diterima semalam.", k) == "jenama"
    assert templat_llm.sebab_tolak(["x"], k) == "bukan_teks"


def test_tapis_templat_buang_pendua_termasuk_templat_latih():
    t = "Sila hubungi {NAMA} di {MY_PHONE} untuk urusan sewa rumah ini."
    hasil, tolak = templat_llm.tapis_templat({("ms", "a"): [t, "  " + t.upper()], ("ms", "b"): [t]}, K, set())
    assert hasil == {"ms": {"a": [t]}} and tolak["pendua"] == 2
    _, tolak = templat_llm.tapis_templat({("ms", "a"): [t]}, K, {templat_llm._norm(t)})
    assert tolak["pendua"] == 1


def test_tapis_nama_bersilang_kosong_ikut_token():
    lama = yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    pertama = lama["nama_pertama"][0]
    calon = {"nama_pertama": [f"Nur {pertama}", "Zorvana", "Zorvana"], "nama_akhir": ["bin Qelutar", lama["nama_akhir"][0]],
             "syarikat": [lama["syarikat"][0], "Maxis Kedai Sdn Bhd", "Qelu Jaya Trading"], "bandar": [lama["bandar"][0], "Qeluvar"]}
    hasil, tolak = templat_llm.tapis_nama(calon, lama, K)
    assert hasil == {"nama_pertama": ["Zorvana"], "nama_akhir": ["bin Qelutar"], "syarikat": ["Qelu Jaya Trading"],
                     "bandar": ["Qeluvar"]}
    assert tolak["nama_pertama:token_bersilang"] == 1 and tolak["syarikat:jenama"] == 1


def test_bentuk_nama_orang_tolak_nama_penuh_dan_syarikat():
    """Regresi penolakan B1 (30 Okt): nama_akhir berisi nama penuh + syarikat, nama_pertama berisi nama penuh."""
    calon = {"nama_pertama": ["Zorvana", "Qeli Mavu", "Qeli Mavu Taro", "Zuri Qelfang", "Ravi bin Qel"],
             "nama_akhir": ["bin Qelutar", "a/p Zorvadi", "Qelfang", "Mavu Taro Qelibi", "Qelu Biru Media Sdn Bhd",
                            "Senja Qel Trade", "anak Qel Mavu Taro"],
             "syarikat": ["Qelu Biru Media Sdn Bhd"], "bandar": ["Qeluvar"]}
    hasil, tolak = templat_llm.tapis_nama(calon, {"nama_pertama": [], "nama_akhir": [], "syarikat": [], "bandar": []}, K)
    assert hasil["nama_pertama"] == ["Zorvana", "Qeli Mavu"]
    assert hasil["nama_akhir"] == ["bin Qelutar", "a/p Zorvadi", "Qelfang"]
    assert hasil["syarikat"] == ["Qelu Biru Media Sdn Bhd"]  # syarikat sah dalam senarai syarikat
    assert tolak["nama_pertama:nama_penuh"] == 2 and tolak["nama_pertama:ada_nama_keluarga"] == 1
    assert tolak["nama_akhir:nama_penuh"] == 2 and tolak["nama_akhir:syarikat_sebagai_orang"] == 2


def test_nama_latih_lulus_bentuk():
    """Pengesah tidak menolak bentuk nama.yaml yang ditulis tangan (kawalan positif)."""
    lama = yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    kel = templat_llm._keluarga(lama, K)
    assert sum(bool(templat_llm.bentuk_orang(kat, x, K, kel)) for kat in ("nama_pertama", "nama_akhir") for x in lama[kat]) == 0


def test_bahasa_templat_en_mesti_inggeris():
    bm = "Sila hubungi {NAMA} di {MY_PHONE} untuk urusan sewa rumah ini dan bayaran akan dibuat kepada kami."
    en = "Please contact {NAMA} at {MY_PHONE} for the house rental and the payment will be made to us."
    assert templat_llm.sebab_tolak(bm, K, "en") == "bahasa"
    assert templat_llm.sebab_tolak(en, K, "en") is None
    assert templat_llm.sebab_tolak(en, K, "ms") == "bahasa"
    assert templat_llm.sebab_tolak(bm, K, "ms") is None
    assert templat_llm.sebab_tolak(bm, K, "manglish") is None  # campuran — tidak disemak
    assert templat_llm.nisbah_bahasa("Tel {MY_PHONE} ok", "en", K) is None  # terlalu sedikit kata fungsi
    _, tolak = templat_llm.tapis_templat({("en", "a"): [bm, en]}, K, set())
    assert tolak == {"bahasa": 1}


BM_DALAM_EN = [  # regresi penolakan B1b (30 Okt): templat 'en' BM penuh dengan < 3 kata fungsi lama lulus SENYAP (rekaan, bukan ujian2)
    "Pembiayaan peribadi untuk {NAMA} di {BANDAR}. Sila hubungi {MY_PHONE} segera.",
    "Bil sewa bulanan diterima daripada {NAMA}, akaun {NEG_AKAUN}.",
    "TUNTUTAN KEMALANGAN — pemohon {NAMA}, IC {MY_NRIC}, tarikh {TARIKH}.",
    "BORANG PERMOHONAN PINJAMAN: nama {NAMA}, no. IC {MY_NRIC}, tel {MY_PHONE}.",
    "Permohonan pembiayaan perniagaan {SYARIKAT} ({MY_SSM}) di {BANDAR}.",
    "Agensi {SYARIKAT} menguruskan sewaan rumah {NAMA}, tel {MY_PHONE}.",
]


@pytest.mark.parametrize("teks", BM_DALAM_EN)
def test_templat_bm_pendek_dalam_en_ditolak(teks):
    assert templat_llm.sebab_tolak(teks, K, "en") in {"bahasa", "bahasa_tidak_dinilai"}


def test_templat_tanpa_isyarat_bahasa_ditolak_untuk_en_ms_sahaja():
    t = "Ref {NEG_KOD} / {MY_PHONE} / {TARIKH} / {BANDAR} — ok."
    assert templat_llm.sebab_tolak(t, K, "en") == "bahasa_tidak_dinilai"
    assert templat_llm.sebab_tolak(t, K, "ms") == "bahasa_tidak_dinilai"
    assert templat_llm.sebab_tolak(t, K, "manglish") is None
    assert templat_llm.sebab_tolak(t, K) is None


def test_nama_huruf_kecil_dibetulkan_penjana_ditolak_pengesah():
    """Regresi penolakan B1b: nama_akhir 'bin zahidi'/'cheah' → dokumen 'Fiona yeoh'."""
    assert templat_llm.huruf_besar("bin qelutar", K) == "bin Qelutar"
    assert templat_llm.huruf_besar("a/p zorvadi", K) == "a/p Zorvadi"
    assert templat_llm.bentuk_orang("nama_akhir", "bin qelutar", K, set()) == "huruf_kecil"
    assert templat_llm.bentuk_orang("keluarga_cina", "qelfang", K, set()) == "huruf_kecil"
    assert templat_llm.bentuk_orang("keluarga_cina", "Qel Fang", K, set()) == "nama_penuh"
    assert templat_llm.bentuk_orang("pertama_cina", "Qel Fang", K, set()) is None
    hasil, tolak = templat_llm.tapis_nama({"keluarga_cina": ["qelfang"], "pertama_melayu_l": ["zorvan hakim"]},
                                          {"nama_pertama": [], "nama_akhir": []}, K)
    assert hasil == {"keluarga_cina": ["Qelfang"], "pertama_melayu_l": ["Zorvan Hakim"]} and not tolak


def test_nama_kumpulan_penyambung_ikut_jantina_dan_komuniti():
    """Regresi penolakan B1b: 'Irfan binti …', 'Saging a/l …' — gabungan rawak pertama × akhir tanpa jantina/komuniti."""
    kump = konfig.utama()["jana"]["nama_kumpulan"]
    nama = {kat: [f"{kat.title().replace('_', '')}{i}" for i in range(3)] for kat in K["nama"]["huraian"]}
    r = __import__("random").Random(7)
    for _ in range(400):
        n = jana.nama_orang(r, nama).split()
        if "binti" in n or "bin" in n:
            i = n.index("binti" if "binti" in n else "bin")
            asal = "PertamaMelayuP" if n[i] == "binti" else "PertamaMelayuL"
            assert n[0].startswith(asal) and n[i + 1].startswith("PertamaMelayuL")
        elif "a/l" in n or "a/p" in n:
            assert n[-1].startswith("PertamaIndiaL") and n[0].startswith("PertamaIndia" + ("P" if "a/p" in n else "L"))
        elif "anak" in n:
            assert n[0].startswith("PertamaIban") and n[-1].startswith("PertamaIbanL")
        elif n[0].startswith("KeluargaCina"):
            assert n[1].startswith("PertamaCina")  # susunan Cina: keluarga dahulu
        else:
            assert (n[0].startswith("PertamaInggeris") and n[1].startswith("KeluargaCina")) or \
                   (n[0].startswith("PertamaKadazan") and n[1].startswith("KeluargaKadazan"))
    rujuk = {v for g in kump.values() for kunci in ("pertama", "bapa", "keluarga") if (v := g.get(kunci))}
    assert rujuk <= set(K["nama"]["min"]) <= set(K["nama"]["huraian"])


def test_nama_rata_v1_tidak_berubah():
    """nama.yaml v1 = cara lama tepat (cincangan v1 bergantung pada jujukan rng yang sama)."""
    lama = yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    a, b = __import__("random").Random(3), __import__("random").Random(3)
    assert [jana.nama_orang(a, lama) for _ in range(50)] == \
           [f"{b.choice(lama['nama_pertama'])} {b.choice(lama['nama_akhir'])}" for _ in range(50)]


def test_semak_fail_tolak_format_rata_untuk_sasaran_berkumpulan(akar):
    s = K["sasaran"]["ujian2"]
    (akar / s["folder"]).mkdir(parents=True)
    (akar / s["folder"] / "en.yaml").write_text(yaml.safe_dump({"genre": {"x": [BM_DALAM_EN[0]]}}))
    shutil.copy(konfig.AKAR / "data/nama.yaml", akar / s["fail_nama"])
    st = templat_llm.semak_fail("ujian2", akar=akar)
    assert st["templat_ikut_sebab"] == {"en:bahasa_tidak_dinilai": 1} or st["templat_ikut_sebab"] == {"en:bahasa": 1}
    assert st["nama_ikut_sebab"]["nama_pertama:format_rata"] == 1
    assert st["nama_ikut_sebab"]["pertama_melayu_l:kurang_daripada_min"] == 1


def test_semak_fail_kiraan_sahaja(akar):
    templat_llm.jana_sasaran("ujian2", hantar=hantar_palsu, akar=akar)
    st = templat_llm.semak_fail("ujian2", akar=akar)
    assert st["templat"] == sum(v for kunci, v in st["templat_ikut_sebab"].items())
    tolak = [k for b in ("templat_ikut_sebab", "nama_ikut_sebab") for k in st[b] if not k.endswith(":sah")]
    assert tolak == []  # output penjana (huruf kecil dibetulkan) lulus pengesah yang sama — corak gerbang §2
    assert "NAMA}" not in json.dumps(st) and "MY_" not in json.dumps(st)  # tiada teks templat


def test_tanya_ulang_kemudian_sandaran(monkeypatch):
    panggilan = []

    def hantar(model, prompt, suhu):
        panggilan.append(model)
        if model == "utama":
            raise OSError("rangkaian")
        return "jawapan: [1, 2]"

    model, hasil = klien_llm.tanya(["utama", "sandaran"], "p", 0.0, hantar=hantar, tidur=lambda s: None)
    ulang = konfig.utama()["llm"]["ulang"]
    assert (model, hasil) == ("sandaran", [1, 2]) and panggilan == ["utama"] * ulang + ["sandaran"]
    with pytest.raises(klien_llm.GagalLLM) as e:
        klien_llm.tanya(["utama"], "p", 0.0, hantar=hantar, tidur=lambda s: None)
    assert "rangkaian" not in str(e.value)  # ralat = jenis sahaja, bukan kandungan


def test_jana_sasaran_menulis_dan_cetak_statistik_sahaja(akar):
    st = templat_llm.jana_sasaran("ujian2", hantar=hantar_palsu, akar=akar)
    assert "gagal_ambang" not in st
    n_bahasa, n_genre = len(K["bahasa"]), len(K["sasaran"]["ujian2"]["genre"])
    assert st["templat"] == n_bahasa * n_genre * 8 and st["nisbah_negatif"] == 0.375
    s = K["sasaran"]["ujian2"]
    assert sorted(p.stem for p in (akar / s["folder"]).glob("*.yaml")) == sorted(K["bahasa"])
    nama = yaml.safe_load((akar / s["fail_nama"]).read_text(encoding="utf-8"))
    assert set(nama) == set(K["nama"]["min"])
    assert "{NAMA}" not in json.dumps(st)  # tiada teks templat dalam statistik
    with pytest.raises(SystemExit, match="DIMETERAI"):
        templat_llm.jana_sasaran("ujian2", hantar=hantar_palsu, akar=akar)


def test_jana_sasaran_tidak_menulis_bila_ambang_gagal(akar, monkeypatch):
    def separuh(model, prompt, suhu):
        if "Genre:" in prompt and "Manglish" in prompt:
            raise OSError("model mati")
        return hantar_palsu(model, prompt, suhu)

    monkeypatch.setitem(konfig.utama()["llm"], "jeda_saat", 0)
    st = templat_llm.jana_sasaran("ujian2", hantar=separuh, akar=akar)
    assert any("manglish" in m for m in st["gagal_ambang"])
    assert not (akar / K["sasaran"]["ujian2"]["folder"]).exists()
    assert not (akar / K["sasaran"]["ujian2"]["fail_nama"]).exists()


def test_jana_ujian2_kunci2_dicipta_sekali_dan_berhenti_bila_berbeza(akar, tmp_path):
    folder = akar / "t2"
    folder.mkdir()
    (folder / "ms.yaml").write_text(yaml.safe_dump({"genre": {"x": ["IC {MY_NRIC} tel {MY_PHONE}", "akaun {NEG_AKAUN}"]}}))
    nama = akar / "nama2.yaml"
    nama.write_text(yaml.safe_dump({"nama_pertama": ["Zora"], "nama_akhir": ["bin Qel"], "syarikat": ["Q Sdn Bhd"],
                                    "bandar": ["Qeluvar"]}))
    keluar = tmp_path / "bench"
    keluar.mkdir()
    r = jana.jana_ujian2(keluar, folder, nama)
    assert r["dokumen"] == konfig.utama()["jana"]["bilangan_ujian2"]
    assert json.loads((keluar / "KUNCI2.json").read_text()) == {"ujian2": r}
    assert jana.jana_ujian2(keluar, folder, nama) == r  # deterministik, kunci sama
    asal = json.dumps({"ujian2": {"dokumen": 1, "sha256": "0" * 64}})
    (keluar / "KUNCI2.json").write_text(asal)
    with pytest.raises(SystemExit, match="BERUBAH"):
        jana.jana_ujian2(keluar, folder, nama)
    assert (keluar / "KUNCI2.json").read_text() == asal


def test_harness_ujian2_dikunci(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["harness", "--split", "ujian2"])
    assert harness.main() == 2


def test_kunci2_sepadan_ujian2():
    """ujian2.jsonl yang dikomit = KUNCI2.json (cincangan sahaja; kandungan tidak dibaca)."""
    bench = konfig.AKAR / "data/bench"
    kunci = json.loads((bench / "KUNCI2.json").read_text())["ujian2"]
    assert hashlib.sha256((bench / "ujian2.jsonl").read_bytes()).hexdigest() == kunci["sha256"]


def test_nama_ujian2_bersilang_kosong_dengan_nama_latih():
    """Kiraan sahaja — jika gagal, pytest memaparkan nombor, bukan nama."""
    lama = yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    baru = yaml.safe_load((konfig.AKAR / konfig.utama()["jana"]["nama_ujian2"]).read_text(encoding="utf-8"))
    entri_lama = {templat_llm._norm(x) for v in lama.values() for x in v}
    bersilang = sum(templat_llm._norm(x) in entri_lama for v in baru.values() for x in v)
    assert bersilang == 0


def test_span_ujian2_dalam_teks():
    """Kiraan span rosak sahaja (kandungan tidak dipaparkan bila gagal)."""
    buruk = 0
    for baris in (konfig.AKAR / "data/bench/ujian2.jsonl").read_text(encoding="utf-8").splitlines():
        d = json.loads(baris)
        for s in d["spans"]:
            nilai = d["teks"][s["mula"]:s["tamat"]]
            buruk += not (0 <= s["mula"] < s["tamat"] <= len(d["teks"]) and nilai.strip() == nilai)
    assert buruk == 0


TRIPLET = "Zorvana Qelutar | Qelu Lume Trading | Arau, Perlis"


def test_bandar_triplet_ditolak():
    """Regresi penolakan B1b ke-3 (30 Okt): 60/60 `bandar` ujian2 = 'Nama | Syarikat | Bandar, Negeri' lulus `tapis_nama` + `--semak`."""
    calon = {"pertama_melayu_l": ["Qelzan"], "syarikat": ["Qelu Lume Trading", "Qelu Lume", TRIPLET, "Qelu Lume, Trading Sdn Bhd"],
             "bandar": ["Qeluvar", "Bandar Baru Qeluvar", TRIPLET, "Arau, Perlis", "Qelu Lume Trading", "Kampung Qel Baru Hilir",
                        "qelumar", "Bukit Qelzan"]}
    hasil, tolak = templat_llm.tapis_nama(calon, {"syarikat": [], "bandar": []}, K)
    assert hasil["bandar"] == ["Qeluvar", "Bandar Baru Qeluvar"] and hasil["syarikat"] == ["Qelu Lume Trading"]
    assert tolak["bandar:bukan_satu_nama"] == 2 and tolak["bandar:syarikat_sebagai_bandar"] == 1
    assert tolak["bandar:terlalu_panjang"] == 1 and tolak["bandar:huruf_kecil"] == 1 and tolak["bandar:token_nama_orang"] == 1
    assert tolak["syarikat:bukan_satu_nama"] == 2 and tolak["syarikat:tiada_akhiran_syarikat"] == 1


def test_bandar_token_nama_latih_ditolak():
    """Token nama orang nama.yaml dalam `bandar` (penyemak: Siti, Rajesh… dalam triplet) = tolak walaupun satu nama."""
    lama = yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    orang = lama["nama_pertama"][0].split()[0]
    _, tolak = templat_llm.tapis_nama({"bandar": [f"Bukit {orang}"]}, lama, K)
    assert tolak == {"bandar:token_nama_orang": 1}


def test_semak_fail_lapor_bentuk_bandar_syarikat(akar):
    templat_llm.jana_sasaran("ujian2", hantar=hantar_palsu, akar=akar)
    s = K["sasaran"]["ujian2"]
    nama = yaml.safe_load((akar / s["fail_nama"]).read_text(encoding="utf-8"))
    nama["bandar"].append(TRIPLET)
    nama["syarikat"].append(TRIPLET)
    (akar / s["fail_nama"]).write_text(yaml.safe_dump(nama, allow_unicode=True))
    st = templat_llm.semak_fail("ujian2", akar=akar)["nama_ikut_sebab"]
    assert st["bandar:bukan_satu_nama"] == 1 and st["syarikat:bukan_satu_nama"] == 1
    assert st["bandar:sah"] == len(nama["bandar"]) - 1


def test_nama_latih_bandar_syarikat_lulus_bentuk():
    """Kawalan positif: bandar/syarikat nama.yaml (tangan) tidak ditolak oleh bentuk satu-nama (token nama orang dikecualikan:
    nama.yaml dibina sebelum ADR-009 dan tidak dijana semula)."""
    lama = yaml.safe_load((konfig.AKAR / "data/nama.yaml").read_text(encoding="utf-8"))
    sebab = {templat_llm.bentuk_bukan_orang(kat, x, K, set()) for kat in templat_llm.BUKAN_ORANG for x in lama[kat]}
    assert sebab == {None}


@pytest.mark.parametrize("sebelum,jantina", [("Sila hubungi En. ", "l"), ("Dear Mr ", "l"), ("Kepada Puan ", "p"),
                                             ("borang Pn. ", "p"), ("hi Madam ", "p"), ("Sila hubungi ", None),
                                             ("Siren ", None), ("Pemohon: ", None)])
def test_jantina_gelaran(sebelum, jantina):
    assert jana.jantina_gelaran(sebelum) == jantina


def test_nama_ikut_gelaran_dan_bapa_bukan_diri():
    """Regresi sampel penyemak: 'En. Asyikin binti …' (gelaran ≠ jantina) dan 'X bin X' (bapa = nama diri)."""
    nama = {kat: [f"{kat.title().replace('_', '')}{i}" for i in range(2)] for kat in K["nama"]["huraian"]}
    r = __import__("random").Random(11)
    for _ in range(300):
        n = jana.nama_orang(r, nama, "Sila hubungi En. ").split()
        assert n[1] in ("bin", "a/l", "anak") and n[0].rstrip("01").endswith("L") and n[0] != n[2]
        n = jana.nama_orang(r, nama, "Kepada Puan ").split()
        assert n[1] in ("binti", "a/p", "anak") and n[0].rstrip("01").endswith("P")
        n = jana.nama_orang(r, nama).split()
        assert len(n) < 3 or n[0] != n[2]


# --- PELAN-B B2: sasaran latih (data/templat/llm_<bahasa>.yaml + nama_tambahan) ---

def test_jana_latih_menulis_berawalan_dan_menapis_ujian2(akar):
    s, s2 = K["sasaran"]["latih"], K["sasaran"]["ujian2"]
    (akar / s["folder"]).mkdir(parents=True)
    (akar / s["folder"] / "en.yaml").write_text("genre: {}\n")   # templat tangan sedia ada tidak menghalang / tidak ditindih
    sama = hantar_palsu("m", "Genre: penyata_bank\nLanguage: Malaysian English", 0)
    (akar / s2["folder"]).mkdir(parents=True)
    (akar / s2["folder"] / "en.yaml").write_text(yaml.safe_dump({"genre": {"x": [klien_llm.json_dari(sama)[0]]}}))
    kat = "pertama_melayu_l"
    nama_u2 = json.loads(hantar_palsu("m", K["nama"]["huraian"][kat], 0))[0]
    (akar / s2["fail_nama"]).write_text(yaml.safe_dump({kat: [nama_u2]}))

    prompt = []
    st = templat_llm.jana_sasaran("latih", hantar=lambda m, p, t: prompt.append(p) or hantar_palsu(m, p, t), akar=akar)
    assert "gagal_ambang" not in st and st["templat"] >= s["min_templat"]
    assert all("{NEG_AHLI}" in p for p in prompt if "Genre:" in p) and "NEG_AHLI" in templat_llm.slot_sah()
    assert st["tolak"] == {"sama_sasaran_elak": 1}
    assert st["tolak_nama"].get(f"{kat}:pendua") == 1
    assert sorted(p.name for p in (akar / s["folder"]).glob("llm_*.yaml")) == sorted(f"llm_{b}.yaml" for b in K["bahasa"])
    assert (akar / s["folder"] / "en.yaml").read_text() == "genre: {}\n"
    tambahan = yaml.safe_load((akar / s["fail_nama"]).read_text(encoding="utf-8"))
    assert nama_u2 not in tambahan[kat]
    assert templat_llm.semak_fail("latih", akar=akar)["templat"] == st["templat"]   # semak membaca llm_* SAHAJA
    with pytest.raises(SystemExit, match="DIMETERAI"):
        templat_llm.jana_sasaran("latih", hantar=hantar_palsu, akar=akar)

