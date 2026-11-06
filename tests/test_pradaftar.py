"""PELAN-C C4b (ADR-014): split dikunci ditolak tanpa pra-daftar bersih dalam git HEAD — repo git tmp, tiada fail ujian sebenar."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from mypii.nilai import harness, pradaftar

FAIL = "docs/PRA-DAFTAR.md"


def _git(akar: Path, *h: str) -> str:
    return subprocess.run(["git", "-C", str(akar), *h], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "README").write_text("x\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "asas")
    return tmp_path


def _komit_pd(repo: Path, teks: str = "# pra-daftar\n") -> str:
    (repo / "docs").mkdir(exist_ok=True)
    (repo / FAIL).write_text(teks)
    _git(repo, "add", FAIL)
    _git(repo, "commit", "-qm", "pd")
    return _git(repo, "rev-parse", "HEAD")


def test_config_menunjuk_pradaftar_repo():
    assert pradaftar.fail_pradaftar() == FAIL and (harness.AKAR / FAIL).is_file()


def test_bukan_repo_ditolak(tmp_path):
    with pytest.raises(pradaftar.Ditolak, match="bukan repo git"):
        pradaftar.semak(tmp_path, FAIL)


def test_tiada_dalam_head_ditolak_walau_ada_di_cakera(repo):
    (repo / "docs").mkdir()
    (repo / FAIL).write_text("belum dikomit\n")
    with pytest.raises(pradaftar.Ditolak, match="tiada dalam git HEAD"):
        pradaftar.semak(repo, FAIL)
    _git(repo, "add", FAIL)  # di-stage sahaja juga belum dalam HEAD
    with pytest.raises(pradaftar.Ditolak, match="tiada dalam git HEAD"):
        pradaftar.semak(repo, FAIL)


@pytest.mark.parametrize("ubah", ["sunting", "stage", "padam"])
def test_berbeza_dari_head_ditolak(repo, ubah):
    _komit_pd(repo)
    if ubah == "padam":
        (repo / FAIL).unlink()
    else:
        (repo / FAIL).write_text("# pra-daftar\nhipotesis ditukar selepas melihat\n")
        if ubah == "stage":
            _git(repo, "add", FAIL)
    with pytest.raises(pradaftar.Ditolak, match="berbeza dari git HEAD"):
        pradaftar.semak(repo, FAIL)


def test_bersih_diterima_dengan_sha_komit_dan_blob(repo):
    sha = _komit_pd(repo)
    (repo / "README").write_text("fail lain kotor tidak mengapa\n")
    _git(repo, "commit", "-qam", "lain")  # komit selepasnya tidak menukar sha pra-daftar
    h = pradaftar.semak(repo, FAIL)
    assert h == {"fail": FAIL, "komit": sha, "blob": _git(repo, "rev-parse", f"HEAD:{FAIL}")}


@pytest.fixture
def harness_tmp(repo, monkeypatch, tmp_path):
    monkeypatch.setattr(harness, "AKAR", repo)
    monkeypatch.setattr(harness, "_dokumen", lambda s: pytest.fail(f"split {s} dibaca sebelum pra-daftar disahkan"))
    monkeypatch.setattr(harness, "ramal", lambda *a: pytest.fail("tidak boleh meramal"))
    return repo


@pytest.mark.parametrize("split", ["ujian", "ujian2"])
@pytest.mark.parametrize("statistik", [False, True])
def test_harness_tolak_sebelum_split_dibaca(harness_tmp, monkeypatch, capsys, tmp_path, split, statistik):
    argv = ["h", "--split", split, "--benarkan-ujian", "--keluar", str(tmp_path / "out")] + (["--statistik"] * statistik)
    monkeypatch.setattr(sys, "argv", argv)
    assert harness.main() == 2
    assert "tiada dalam git HEAD" in capsys.readouterr().err
    (harness_tmp / "docs").mkdir()
    (harness_tmp / FAIL).write_text("kotor\n")
    _git(harness_tmp, "add", FAIL)
    _git(harness_tmp, "commit", "-qm", "pd")
    (harness_tmp / FAIL).write_text("kotor lagi\n")
    assert harness.main() == 2
    assert "berbeza dari git HEAD" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_harness_tanpa_bendera_tetap_exit_2(harness_tmp, monkeypatch, capsys):
    _komit_pd(harness_tmp)
    monkeypatch.setattr(sys, "argv", ["h", "--split", "ujian2"])
    assert harness.main() == 2
    assert "dikunci" in capsys.readouterr().err


def test_harness_diterima_tulis_sha_dalam_hasil(harness_tmp, monkeypatch, capsys, tmp_path):
    sha = _komit_pd(harness_tmp)
    dok = [{"id": "d0", "bahasa": "bm", "spans": [{"mula": 0, "tamat": 3, "entiti": "MY_NRIC"}]}]
    monkeypatch.setattr(harness, "_dokumen", lambda s: dok)  # palsu: split sebenar TIDAK dibaca
    monkeypatch.setattr(harness, "ramal", lambda s, d: [list(x["spans"]) for x in d])
    keluar = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["h", "--split", "ujian2", "--benarkan-ujian", "--sistem", "mypii", "--keluar", str(keluar)])
    assert harness.main() == 0
    assert sha in capsys.readouterr().err
    h = json.loads((keluar / "ujian2-mypii.json").read_text())
    assert h["_pradaftar"]["komit"] == sha and h["semua|*"]["tepat"]["f1"] == 1.0


def test_dev_tidak_perlu_pradaftar(harness_tmp, monkeypatch, tmp_path):
    monkeypatch.setattr(harness, "_dokumen", lambda s: [])
    monkeypatch.setattr(harness, "ramal", lambda s, d: [])
    monkeypatch.setattr(sys, "argv", ["h", "--split", "dev", "--sistem", "mypii", "--keluar", str(tmp_path / "o")])
    assert harness.main() == 0
    assert "_pradaftar" not in json.loads((tmp_path / "o/dev-mypii.json").read_text())


# --- PELAN-V2 P4: split v3 (latih3/dev3/ujian3) ---

PINDAAN_V2 = "\n### 2026-11-04 — MyPII v2: dev3 + ujian3 (selepas ujian v1 dibuka)\nx\n"
PINDAAN_KUASA = "\n### 2026-11-20 — MyPII v2: kuasa + pengecam dibekukan (sebelum ujian3 dibuka)\ny\n"


def test_laluan_split_v3_dari_config_v1_tidak_berubah():
    from mypii import konfig
    from mypii.nilai import iterasi
    assert konfig.fail_split("dev") == "data/bench/dev.jsonl" and konfig.fail_cincangan("ujian2") == "data/bench/CINCANGAN.json"
    assert konfig.fail_split("dev3") == "data/bench_v3/dev3.jsonl" and konfig.fail_split("ujian3") == "data/bench_v3/ujian3.jsonl"
    c3 = json.loads((harness.AKAR / "data/bench_v3/CINCANGAN3.json").read_text())
    assert iterasi.dev_sha8(harness.AKAR, "dev3") == c3["dev3"]["sha256"][:8]
    assert len(harness._dokumen("dev3")) == c3["dev3"]["dokumen"] and "ujian3" in harness.konfig.utama()["nilai"]["split_dikunci"]


@pytest.mark.parametrize("bendera", [False, True])
def test_ujian3_ditolak_sebelum_dibaca_tanpa_bendera_atau_tanpa_pindaan_v2(harness_tmp, monkeypatch, capsys, tmp_path, bendera):
    _komit_pd(harness_tmp, "# pra-daftar\n" + PINDAAN_V2)   # pindaan P2 sahaja — pindaan kuasa P13 belum
    argv = ["h", "--split", "ujian3", "--keluar", str(tmp_path / "out")] + (["--benarkan-ujian"] * bendera)
    monkeypatch.setattr(sys, "argv", argv)
    assert harness.main() == 2
    assert ("menuntut ≥ 2 pindaan" if bendera else "dikunci") in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_ujian3_diterima_dengan_dua_pindaan_v2(harness_tmp, monkeypatch, tmp_path):
    sha = _komit_pd(harness_tmp, "# pra-daftar\n" + PINDAAN_V2 + PINDAAN_KUASA)
    dibaca = []
    monkeypatch.setattr(harness, "_dokumen", lambda s: dibaca.append(s) or [])
    monkeypatch.setattr(harness, "ramal", lambda s, d: [])
    monkeypatch.setattr(sys, "argv", ["h", "--split", "ujian3", "--benarkan-ujian", "--sistem", "mypii", "--keluar", str(tmp_path / "o")])
    assert harness.main() == 0 and dibaca == ["ujian3"]
    assert json.loads((tmp_path / "o/ujian3-mypii.json").read_text())["_pradaftar"]["komit"] == sha
    assert pradaftar.semak_pindaan(harness_tmp, "ujian2") == 0   # split v1: tiada syarat pindaan v2 (tingkah laku lama)


@pytest.mark.parametrize("split", ["latih3", "dev3"])
def test_latih3_dev3_tidak_dikunci(harness_tmp, monkeypatch, tmp_path, split):
    monkeypatch.setattr(harness, "_dokumen", lambda s: [])
    monkeypatch.setattr(harness, "ramal", lambda s, d: [])
    monkeypatch.setattr(sys, "argv", ["h", "--split", split, "--sistem", "mypii", "--keluar", str(tmp_path / "o")])
    assert harness.main() == 0
    assert "_pradaftar" not in json.loads((tmp_path / f"o/{split}-mypii.json").read_text())
