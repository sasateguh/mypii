"""PELAN-C C2a (ADR-006 §Iterasi): `hasil/iterasi.tsv` — fail tmp + repo git tmp, tiada spaCy/Presidio/rangkaian."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from mypii.nilai import harness, iterasi

LAJUR = ["tarikh", "komit", "dev_sha8", "f1", "status", "baris_kod", "keterangan"]


def _git(akar: Path, *h: str) -> str:
    return subprocess.run(["git", "-C", str(akar), *h], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "mypii/pengecam").mkdir(parents=True)
    (tmp_path / "mypii/pengecam/a.py").write_text("x = 1\ny = 2\n")
    (tmp_path / "data/bench").mkdir(parents=True)
    (tmp_path / "data/bench/CINCANGAN.json").write_text(json.dumps({"dev": {"sha256": "abcdef0123456789" * 4}}))
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "asas")
    return tmp_path


def _baca(f: Path) -> list[list[str]]:
    return [b.split("\t") for b in f.read_text(encoding="utf-8").splitlines()]


def test_pengepala_sekali_dan_medan_lengkap(repo, tmp_path):
    f = tmp_path / "out/iterasi.tsv"
    iterasi.catat("simpan", "satu", 0.9, akar=repo, laluan=f)
    iterasi.catat("ukur", "dua", akar=repo, laluan=f)
    b = _baca(f)
    assert b[0] == LAJUR and len(b) == 3 and all(len(x) == len(LAJUR) for x in b)
    r = dict(zip(LAJUR, b[1]))
    assert r["komit"] == _git(repo, "rev-parse", "--short", "HEAD")
    assert (r["dev_sha8"], r["f1"], r["status"], r["baris_kod"]) == ("abcdef01", "0.9", "simpan", "+0/-0")
    assert r["tarikh"].endswith("Z") and r["tarikh"][:2] == "20"
    assert dict(zip(LAJUR, b[2]))["f1"] == ""


def test_tree_kotor_tanda_tambah_dan_baris_kod(repo, tmp_path):
    (repo / "mypii/pengecam/a.py").write_text("x = 1\nz = 3\nw = 4\n")
    (repo / "lain.txt").write_text("di luar laluan_kod\n")
    r = iterasi.catat("buang", "cuba", 0.5, akar=repo, laluan=tmp_path / "i.tsv")
    assert r["komit"].endswith("+") and r["baris_kod"] == "+2/-1"


def test_fail_hasil_sendiri_bukan_tree_kotor(repo):
    # regresi: baris pertama mengubah TSV → setiap baris berikutnya tertanda `+` walaupun kod bersih
    f = repo / "hasil/iterasi.tsv"
    iterasi.catat("ukur", "satu", akar=repo, laluan=f)
    assert not iterasi.catat("ukur", "dua", akar=repo, laluan=f)["komit"].endswith("+")
    (repo / "kod.py").write_text("x = 1\n")
    assert iterasi.catat("ukur", "tiga", akar=repo, laluan=f)["komit"].endswith("+")


def test_medan_bertab_dibersihkan(repo, tmp_path):
    f = tmp_path / "i.tsv"
    iterasi.catat("ukur", "a\tb\nc  \r\n d", akar=repo, laluan=f)
    assert _baca(f)[1][-1] == "a b c d" and len(_baca(f)[1]) == len(LAJUR)


def test_keterangan_dipotong_ikut_had(repo, tmp_path):
    had = iterasi._k()["had_keterangan"]
    r = iterasi.catat("ukur", "x" * (had + 50), akar=repo, laluan=tmp_path / "i.tsv")
    assert len(r["keterangan"]) == had and r["keterangan"].endswith("…")


def test_status_tidak_sah_dan_bukan_git(tmp_path):
    with pytest.raises(ValueError):
        iterasi.catat("entah", "x", akar=tmp_path, laluan=tmp_path / "i.tsv")
    r = iterasi.catat("ukur", "x", akar=tmp_path, laluan=tmp_path / "i.tsv")
    assert (r["komit"], r["dev_sha8"]) == ("-", "?")


@pytest.fixture
def harness_tmp(repo, tmp_path, monkeypatch):
    f = tmp_path / "h.tsv"
    asal = iterasi.catat
    monkeypatch.setattr(harness.iterasi, "catat", lambda *a, **k: asal(*a, **k, akar=repo, laluan=f))
    return f


def test_harness_crash_direkod_dan_gagal(harness_tmp, monkeypatch):
    def rosak(a):
        raise RuntimeError("model hilang")
    monkeypatch.setattr(harness, "nilai", rosak)
    monkeypatch.setattr(sys, "argv", ["harness", "--iterasi", "simpan", "--keterangan", "cubaan X"])
    with pytest.raises(RuntimeError):
        harness.main()
    r = dict(zip(LAJUR, _baca(harness_tmp)[1]))
    assert (r["status"], r["f1"]) == ("crash", "")
    assert r["keterangan"] == "RuntimeError: model hilang (cubaan X)"


def test_harness_lulus_catat_f1_sistem_config(harness_tmp, monkeypatch):
    skor = {"mypii": {"semua|*": {"tepat": {"f1": 0.8877}}}, "presidio-asal": {"semua|*": {"tepat": {"f1": 0.43}}}}
    monkeypatch.setattr(harness, "nilai", lambda a: skor)
    monkeypatch.setattr(sys, "argv", ["harness", "--iterasi", "ukur", "--keterangan", "C2a"])
    assert harness.main() == 0
    r = dict(zip(LAJUR, _baca(harness_tmp)[1]))
    assert (r["status"], r["f1"], r["keterangan"]) == ("ukur", "0.8877", "C2a")


def test_harness_tolak_status_crash_tangan(harness_tmp, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["harness", "--iterasi", "crash"])
    assert harness.main() == 2 and not harness_tmp.exists()


def _skrip():
    laluan = Path(__file__).resolve().parent.parent / "scripts/iterasi_dari_log.py"
    spec = importlib.util.spec_from_file_location("iterasi_dari_log", laluan)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


LOG = """| Tarikh | # | Perubahan | F1 * | NRIC | SSM | PHONE | Presidio | Keputusan |
|---|---|---|---|---|---|---|---|---|
| 2026-10-28 | P1 | asas | 0.79 | a | b | c | 0.5 | **garis dasar baharu** |
| 2026-10-28 | P2 | OCR (0→o, 1/l/\\|→i) dan `(?:^|\\W)` | 0.83 | a | b | c | 0.5 | **simpan** — naik |
| 2026-10-28 | P3 | cuba | 0.82 | a | b | c | 0.5 | buang walaupun simpan… |
| 2026-10-29 | P2 UNDUR | balik | 0.81 | a | b | c | 0.5 | **undur** |
| 2026-10-30 | B2 | dev-v2 `531532cf…` baharu | 0.88 | a | b | c | 0.4 | **garis dasar dev-v2** |
| 2026-10-30 | B3 | pesaing | 0.88 | a | b | c | 0.4 | ukur (tiada keputusan simpan/buang) |
| 2026-10-30 | C1b | proses sahaja | pembaikan — tiada F1 |
| 2026-10-30 | X | prosa sahaja dengan 0.99 |
"""


def test_pemeta_log():
    r = _skrip().tukar(LOG)
    assert [x["status"] for x in r] == ["ukur", "simpan", "buang", "buang", "ukur", "ukur", "ukur", "ukur"]
    assert [x["f1"] for x in r] == ["0.79", "0.83", "0.82", "0.81", "0.88", "0.88", "", ""]
    assert [x["dev_sha8"] for x in r] == ["?"] * 4 + ["531532cf"] * 4
    assert all(x["komit"] == "-" for x in r)
    assert r[1]["keterangan"].startswith("LOG P2: OCR (0→o, 1/l/|→i)")


def test_isi_semula_enggan_fail_berisi(tmp_path, monkeypatch):
    m = _skrip()
    log, f = tmp_path / "LOG.md", tmp_path / "i.tsv"
    log.write_text(LOG)
    monkeypatch.setattr(sys, "argv", ["x", "--log", str(log), "--keluar", str(f)])
    assert m.main() == 0 and len(_baca(f)) == 9
    assert m.main() == 2 and len(_baca(f)) == 9
