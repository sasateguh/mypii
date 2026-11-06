"""Pencetus cron IAA (PELAN-IAA P10): penyemak manusia n/n → `autopilot mula` SEKALI; `uji` diabaikan; gagal = tiada penanda."""

import os
import subprocess
from pathlib import Path

import pytest

SKRIP = Path(__file__).resolve().parent.parent / "deploy" / "iaa" / "pencetus.sh"


def _lari(tmp_path, kemajuan: str, mula_rc: int = 0):
    (tmp_path / "kemajuan.txt").write_text(kemajuan)
    palsu = tmp_path / "mula.sh"
    palsu.write_text(f'#!/bin/sh\necho x >> "{tmp_path}/mula.kiraan"\nexit {mula_rc}\n')
    palsu.chmod(0o755)
    env = {**os.environ, "MYPII_IAA_FOLDER": str(tmp_path), "IAA_PENCETUS_LOG": str(tmp_path / "log"),
           "IAA_KEMAJUAN": f"cat {tmp_path / 'kemajuan.txt'}", "IAA_MULA": str(palsu)}
    r = subprocess.run(["bash", str(SKRIP)], env=env, capture_output=True, text=True, timeout=30, check=False)
    kiraan = tmp_path / "mula.kiraan"
    return r.returncode, (len(kiraan.read_text().splitlines()) if kiraan.exists() else 0)


def test_belum_siap_tiada_cetusan(tmp_path):
    assert _lari(tmp_path, "p1 299/300\nuji 6/6\n") == (0, 0)
    assert not list(tmp_path.glob("pencetus-*.selesai"))


def test_uji_siap_diabaikan(tmp_path):
    assert _lari(tmp_path, "uji 6/6\n") == (0, 0)


def test_p1_siap_cetus_sekali_sahaja(tmp_path):
    assert _lari(tmp_path, "p1 300/300\nuji 0/6\n") == (0, 1)
    assert (tmp_path / "pencetus-p1.selesai").exists()
    assert _lari(tmp_path, "p1 300/300\nuji 0/6\n") == (0, 1)   # hari esok: penanda wujud → tiada cetusan kedua


def test_p2_kemudian_cetus_lagi(tmp_path):
    _lari(tmp_path, "p1 300/300\np2 10/300\n")
    assert _lari(tmp_path, "p1 300/300\np2 300/300\n") == (0, 2)
    assert (tmp_path / "pencetus-p2.selesai").exists()


def test_dua_serentak_satu_cetusan(tmp_path):
    assert _lari(tmp_path, "p1 300/300\np2 300/300\n") == (0, 1)
    assert {p.name for p in tmp_path.glob("pencetus-*.selesai")} == {"pencetus-p1.selesai", "pencetus-p2.selesai"}


def test_mula_gagal_tiada_penanda(tmp_path):
    assert _lari(tmp_path, "p1 300/300\n", mula_rc=1) == (1, 1)
    assert not (tmp_path / "pencetus-p1.selesai").exists()
    assert "GAGAL" in (tmp_path / "log").read_text()


@pytest.mark.parametrize("rosak", ["", "p1 0/0\n", "P1 300/300\n", "p1 300\n"])
def test_input_kosong_atau_rosak_tiada_cetusan(tmp_path, rosak):
    rc, n = _lari(tmp_path, rosak)
    assert n == 0 and rc == (1 if rosak == "" else 0)
