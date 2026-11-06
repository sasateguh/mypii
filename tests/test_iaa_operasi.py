"""Operasi kontena IAA (PELAN-IAA P5, ADR-015): token penyemak, kemajuan x/n, susun atur imej tanpa presidio."""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from mypii import konfig
from mypii.iaa import operasi
from mypii.iaa.stor import Stor

AKAR = Path(__file__).resolve().parent.parent
K = konfig.utama()["iaa"]


def test_tambah_token_0600_dan_tidak_menindih(tmp_path):
    f = tmp_path / "penyemak.json"
    t1 = operasi.tambah(f, "p1", 32)
    assert len(t1) >= 40 and stat.S_IMODE(f.stat().st_mode) == 0o600
    t2 = operasi.tambah(f, "p2", 32)
    assert t1 != t2 and json.loads(f.read_text()) == {"p1": t1, "p2": t2}
    with pytest.raises(ValueError, match="sudah wujud"):
        operasi.tambah(f, "p1", 32)
    assert json.loads(f.read_text())["p1"] == t1
    assert not (tmp_path / "penyemak.json.baru").exists()


@pytest.mark.parametrize("salah", ["", "P1", "../x", "p 1", "a" * 17, "1p"])
def test_tambah_id_tidak_sah(tmp_path, salah):
    with pytest.raises(ValueError, match="tidak sah"):
        operasi.tambah(tmp_path / "penyemak.json", salah, 32)


def _folder(tmp_path):
    pk = K["pakej"]
    dok = [{"urutan": n, "teks": "x", "spans": [{"mula": 0, "tamat": 1, "entiti": "MY_SSM"}]} for n in (1, 2, 3)]
    (tmp_path / pk["bundel"]).write_text(json.dumps({"n": 3, "dokumen": dok, "uji": dok[:1]}))
    (tmp_path / pk["penyemak"]).write_text(json.dumps({"p1": "a" * 20, "uji": "b" * 20}))
    s = Stor(tmp_path / pk["stor"])
    for soalan, nilai in (("a1", "betul"), ("b", {"pilih": "tiada"}), ("c", "ya")):
        s.simpan("p1", 2, soalan, nilai)
    s.simpan("p1", 3, "a1", "betul")          # separuh → belum siap
    s.tutup()


def test_kemajuan_kira_dokumen_siap_sahaja(tmp_path):
    _folder(tmp_path)
    assert operasi.kemajuan(tmp_path, K) == {"p1": (1, 3), "uji": (0, 1)}


def test_main_pautan_dan_kemajuan_tanpa_teks(tmp_path, monkeypatch, capsys):
    _folder(tmp_path)
    monkeypatch.setenv("MYPII_IAA_FOLDER", str(tmp_path))
    assert operasi.main(["kemajuan"]) == 0
    assert capsys.readouterr().out.split("\n")[:2] == ["p1 1/3", "uji 0/1"]
    assert operasi.main(["penyemak", "senarai"]) == 0
    assert capsys.readouterr().out.strip() == "p1 uji"
    assert operasi.main(["penyemak", "pautan", "p1"]) == 0
    assert capsys.readouterr().out.strip() == f"https://{K['pelayan']['nama_hos']}/s/{'a' * 20}"
    assert operasi.main(["penyemak", "pautan", "p9"]) == 1
    assert operasi.main(["penyemak", "tambah", "p1"]) == 1


def test_sihat_port_tertutup_palsu():
    assert operasi.sihat(1, masa=0.5) is False


def _copy_dockerfile():
    teks = (AKAR / "deploy/iaa/Dockerfile").read_text()
    return [ln.split()[1] for ln in teks.splitlines() if ln.startswith("COPY ")]


def test_imej_tanpa_init_mypii_tidak_menarik_presidio(tmp_path):
    """Susun atur imej (COPY Dockerfile sahaja) boleh mengimport pelayan + operasi tanpa mypii/__init__.py."""
    for src in _copy_dockerfile():
        s, d = AKAR / src, tmp_path / src
        if s.is_dir():
            shutil.copytree(s, d, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(s, d)
    assert not (tmp_path / "mypii/__init__.py").exists()
    # -I -S: tanpa .pth pemasangan editable (repo dengan mypii/__init__.py); hanya folder imej + PyYAML.
    import yaml
    laluan = [str(tmp_path), str(Path(yaml.__file__).resolve().parent.parent)]
    kod = (f"import sys; sys.path[:0] = {laluan!r}; import mypii.iaa.pelayan, mypii.iaa.operasi; "
           "assert not any(m.split('.')[0] in ('presidio_analyzer', 'spacy') or m == 'mypii.pengecam' "
           "for m in sys.modules), sorted(sys.modules)")
    env = {k: v for k, v in os.environ.items() if k != "MYPII_KONFIG"}
    r = subprocess.run([sys.executable, "-I", "-S", "-c", kod], cwd=tmp_path, env=env, capture_output=True,
                       text=True, check=False)
    assert r.returncode == 0, r.stderr[-800:]


def test_dockerignore_senarai_benar():
    baris = [ln for ln in (AKAR / ".dockerignore").read_text().splitlines() if ln and not ln.startswith("#")]
    assert baris[0] == "*"
    benar = {ln[1:].rstrip("/") for ln in baris if ln.startswith("!")}
    for src in _copy_dockerfile():
        assert src.rstrip("/") in benar, src
    assert not any(re.match(r"(data|hasil|\.env|\.venv)", b) for b in benar)
