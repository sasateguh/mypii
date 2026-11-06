"""Mesej penyemak butang-sahaja (PELAN-IAA-HALAMAN P4): teks tanpa URL/domain; pautan dalam butang; deploy.sh enggan ulang.

Tiada Telegram sebenar: `NOTIFY_BIN` = skrip palsu yang merekod argumen + NOTIFY_BUTANG ke fail sementara.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mypii import konfig
from mypii.iaa import mesej

AKAR = Path(__file__).resolve().parent.parent
SKRIP = AKAR / "deploy" / "iaa" / "deploy.sh"
HOS = konfig.utama()["iaa"]["pelayan"]["nama_hos"]
PAUTAN = f"https://{HOS}/s/" + "T" * 43   # fixture: token palsu berbentuk token_urlsafe(32)


@pytest.fixture(scope="module")
def t():
    return mesej.muat_teks()


def test_teks_dwibahasa_tanpa_url_atau_domain(t):
    teks = mesej.bina_teks(t, HOS)
    assert not mesej.DOMAIN.search(teks) and HOS not in teks
    for b in mesej.BAHASA:
        assert t[b]["judul"] in teks and t[b]["mesej_butang"] in teks   # `{butang}` diganti label bahasa itu
    assert "{butang}" not in teks


def test_kunci_mesej_sama_ms_en(t):
    assert {k for k in t["ms"] if k.startswith("mesej_")} == {k for k in t["en"] if k.startswith("mesej_")}
    assert set(mesej.KUNCI) <= set(t["ms"])


@pytest.mark.parametrize("cemar", [f"Buka {HOS} sekarang", "Lawati semak.example.my", "pergi https://x", "www.contoh",
                                   "Buka EXAMPLE.COM"])
def test_teks_berdomain_ditolak(t, cemar):
    t2 = {b: {**t[b], "mesej_teks": cemar} for b in t}
    with pytest.raises(ValueError):
        mesej.bina_teks(t2, HOS)


def test_label_berdomain_ditolak(t):
    t2 = {b: {**t[b], "mesej_butang": "buka.my"} for b in t}
    with pytest.raises(ValueError):
        mesej.bina_butang(t2, PAUTAN, HOS)


def test_butang_membawa_pautan(t):
    papan = json.loads(mesej.bina_butang(t, PAUTAN, HOS))
    assert papan == [[{"text": mesej.label(t), "url": PAUTAN}]]


@pytest.mark.parametrize("salah", ["", "http://" + PAUTAN[8:], f"https://lain.my/s/{'T' * 43}", f"https://{HOS}/s/pendek",
                                   f"https://{HOS}/keadaan/{'T' * 43}", PAUTAN + "\nx"])
def test_pautan_salah_ditolak_tanpa_dipetik(t, salah):
    with pytest.raises(ValueError) as e:
        mesej.bina_butang(t, salah, HOS)
    assert "T" * 16 not in str(e.value)


# ---------- deploy.sh --penyemak mesej (notify palsu) ----------

def _lari(tmp_path, notify_rc=0, pautan=PAUTAN, id_="p2"):
    cari = tmp_path / "pautan.sh"   # ganti `docker exec … penyemak pautan <id>`
    cari.write_text(f'#!/bin/sh\nprintf "%s\\n" "{pautan}"\n')
    cari.chmod(0o755)
    rekod = tmp_path / "notify.rekod"
    palsu = tmp_path / "notify.sh"
    palsu.write_text(f'#!/bin/sh\nprintf "%s\\n--\\n%s\\n--\\n%s %s %s\\n" "$1" "$NOTIFY_BUTANG" "$2" "$NOTIFY_TERUS" '
                     f'"$NOTIFY_KOD_KELUAR" >> "{rekod}"\nexit {notify_rc}\n')
    palsu.chmod(0o755)
    env = {**os.environ, "MYPII_IAA_FOLDER": str(tmp_path), "IAA_DEPLOY_LOG": str(tmp_path / "deploy.log"),
           "IAA_PAUTAN": str(cari), "IAA_MESEJ": f"{sys.executable} -m mypii.iaa.mesej",
           "NOTIFY_BIN": str(palsu)}
    r = subprocess.run(["bash", str(SKRIP), "--penyemak", "mesej", id_], env=env, cwd=AKAR, capture_output=True, text=True,
                       timeout=60, check=False)
    return r, (rekod.read_text() if rekod.exists() else "")


def test_skrip_hantar_sekali_dengan_butang(tmp_path):
    r, rekod = _lari(tmp_path)
    assert r.returncode == 0, r.stderr
    teks, butang, lain = rekod.split("\n--\n")
    assert HOS not in teks and "http" not in teks
    assert json.loads(butang)[0][0]["url"] == PAUTAN
    assert lain.split() == ["info", "1", "1"]                      # NOTIFY_TERUS + NOTIFY_KOD_KELUAR
    penanda = tmp_path / "mesej-p2.dihantar"
    assert penanda.exists() and (penanda.stat().st_mode & 0o777) == 0o600
    assert "T" * 16 not in r.stdout + r.stderr + (tmp_path / "deploy.log").read_text()   # token tidak dicetak/dilog


def test_skrip_enggan_bila_penanda_wujud(tmp_path):
    (tmp_path / "mesej-p2.dihantar").touch()
    r, rekod = _lari(tmp_path)
    assert r.returncode != 0 and rekod == ""


def test_notify_gagal_tiada_penanda(tmp_path):
    r, rekod = _lari(tmp_path, notify_rc=3)
    assert r.returncode != 0 and rekod != ""
    assert not (tmp_path / "mesej-p2.dihantar").exists()
    r2, _ = _lari(tmp_path)                                         # cuba lagi dibenarkan
    assert r2.returncode == 0


def test_pautan_rosak_tiada_hantaran(tmp_path):
    r, rekod = _lari(tmp_path, pautan="https://lain.my/s/" + "T" * 43)
    assert r.returncode != 0 and rekod == ""
    assert "T" * 16 not in r.stdout + r.stderr
    assert not (tmp_path / "mesej-p2.dihantar").exists()


@pytest.mark.parametrize("id_", ["", "../x", "P1", "a b"])
def test_id_tidak_sah(tmp_path, id_):
    r, rekod = _lari(tmp_path, id_=id_)
    assert r.returncode == 2 and rekod == ""
