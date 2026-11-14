"""PELAN-V21 P8: `scripts/ujian4-muktamad.sh` atas repo git SEMENTARA dengan split ujian4 PALSU + `uv` palsu (harness, Modal, H5).

Tiada `data/bench_v3/ujian4.jsonl` sebenar dibaca; tiada `~/ops/mypii` atau Modal sebenar disentuh (HOME, arkib, env dalam `tmp_path`).
Yang disalin dari repo: PRA-DAFTAR (blok §7-v21 + pindaan v2.1 sebenar), config, pengecam (untuk tag beku), .gitignore, skrip + pustaka.
"""

import hashlib
import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[1]
SKRIP = "scripts/ujian4-muktamad.sh"
KUNCI_PALSU = "kunci-anthropic-PALSU-u4-jangan-dicetak"

UV = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, os, pathlib, sys
    a = sys.argv[1:]
    with open(os.environ["UV_LOG"], "a") as f:
        f.write(json.dumps({"argv": a, "kunci": os.environ.get("ANTHROPIC_API_KEY", "") != ""}) + "\\n")
    if "--version" in a:
        print("palsu 0"); sys.exit(0)
    if "pytest" in a:
        sys.exit(int(os.environ.get("UV_PYTEST_RC", "0")))
    v, luar = pathlib.Path("hasil/v21"), pathlib.Path("hasil/luar")
    jenis = "ramal" if "mypii.nilai.harness" in a else "luar" if "modal" in a else "h5" if "mypii.nilai.statistik_v21" in a else None
    if jenis is None:
        sys.exit(9)
    if os.environ.get("UV_CRASH") == jenis:
        sys.exit(1)
    if jenis == "ramal":
        (v / "ramalan").mkdir(parents=True, exist_ok=True)
        for s in ("mypii", "mypii-v2", "llm_anthropic_claude-haiku-5-5"):
            (v / f"ujian4-{s}.json").write_text(json.dumps({"semua|*": {"tepat": {"p": 0.9, "r": 0.9, "f1": 0.9}}}))
            (v / "ramalan" / f"ujian4-{s}.jsonl").write_text("{}")
        c = pathlib.Path("hasil/cache/llm")
        with open(c / "anthropic_claude-haiku-5-5.jsonl", "a") as f:
            f.write("ujian4\\n")
        lj = c / "anthropic-lejar.json"
        d = json.loads(lj.read_text()); d["jumlah_usd"] += 0.1; lj.write_text(json.dumps(d))
        if os.environ.get("UV_GAGAL"):
            print("1 panggilan gagal (palsu)", file=sys.stderr)
        print('llm:anthropic/claude-haiku-5-5: {"dokumen": 1, "panggilan": 1, "gagal": 0, "rosak": 0}', file=sys.stderr)
    elif jenis == "luar":
        m = a[a.index("--model") + 1]
        luar.mkdir(parents=True, exist_ok=True)
        (luar / f"ujian4-{m}.jsonl").write_text("{}")
        (luar / f"ujian4-{m}.versi.json").write_text(json.dumps({"model": [m, "0" * 40]}))
    else:
        hip = {h: {"sistem": s, "delta": 0.1, "disokong": True} for h, s in
               (("H5a", "mypii-v2"), ("H5b", "llm:anthropic/claude-haiku-5-5"), ("H5c", "luar:meddies"), ("H5d", "luar:gliner"))}
        (v / "ujian4-h5.json").write_text(json.dumps({"dokumen": 1, "k": 4, "alfa": 0.05, "hipotesis": hip,
                                                      "susulan": {"H5a+": {"diuji": True, "disokong": False}}}))
''')


def _env_bersih() -> dict:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(r: Path, *h: str) -> str:
    return subprocess.run(["git", "-C", str(r), *h], capture_output=True, text=True, check=True, env=_env_bersih()).stdout


def _tulis(r: Path, laluan: str, isi) -> None:
    f = r / laluan
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(isi if isinstance(isi, bytes) else isi.encode())


def _komit(r: Path) -> None:
    _git(r, "add", "-A")
    _git(r, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x")


def _perintah(teks: str) -> list[str]:
    m = re.search(r"^#### §7-v21 Perintah tepat ujian4\n```\n(.*?)\n```", teks, re.DOTALL | re.MULTILINE)
    assert m
    return [b for b in m.group(1).splitlines() if b.strip()]


@pytest.fixture
def k(tmp_path: Path) -> dict:
    r = tmp_path / "repo"
    for f in ("docs/PRA-DAFTAR.md", "config/mypii.yaml", "config/kod_pb.yaml", "config/ssm_rob.yaml", ".gitignore", SKRIP,
              "scripts/muktamad-lib.sh", *[str(p.relative_to(AKAR)) for p in (AKAR / "mypii/pengecam").glob("*.py")],
              "model/konteks-v2.json"):
        _tulis(r, f, (AKAR / f).read_bytes())
    _tulis(r, "hasil/cache/llm/anthropic-lejar.json", json.dumps(
        {"jumlah_usd": 3.0, "model": {"anthropic/claude-haiku-5-5": {"usd": 0.2, "panggilan": 2000}}}))
    _tulis(r, "hasil/cache/llm/anthropic_claude-haiku-5-5.jsonl", "asal\n")
    _tulis(r, "data/bench_v3/dev3.jsonl", b'{"palsu": "dev3"}\n')
    _git(r, "init", "-q")
    _komit(r)
    _git(r, "tag", "mypii-v21-beku")   # pengecam beku = keadaan sebelum ujian4 dijana
    isi = b'{"palsu": "ujian4"}\n'
    s = hashlib.sha256(isi).hexdigest()
    _tulis(r, "data/bench_v3/ujian4.jsonl", isi)
    _tulis(r, "data/bench_v3/KUNCI4.json", json.dumps({"ujian4": {"sha256": s, "dokumen": 1}}))
    _tulis(r, "data/bench_v3/UJIAN4-MUKTAMAD", f"{s} palsu\n")
    _komit(r)
    env_dir = tmp_path / "env"
    _tulis(env_dir, "anthropic.env", f"ANTHROPIC_API_KEY={KUNCI_PALSU}\n")
    _tulis(tmp_path, "bin/uv", UV)
    (tmp_path / "bin/uv").chmod(0o755)
    _tulis(tmp_path, "home/.modal.toml", "[palsu]\n")
    env = _env_bersih() | {"PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}", "HOME": str(tmp_path / "home"),
                           "MYPII_ARKIB": str(tmp_path / "arkib"), "MYPII_ENV_DIR": str(env_dir), "UV_LOG": str(tmp_path / "uv.jsonl")}
    for x in ("ANTHROPIC_API_KEY", "UV_CRASH", "UV_GAGAL", "UV_PYTEST_RC"):
        env.pop(x, None)
    return {"r": r, "env": env, "arkib": tmp_path / "arkib", "uvlog": tmp_path / "uv.jsonl"}


def _jalan(k, *h, **env):
    return subprocess.run(["bash", str(k["r"] / SKRIP), *h], capture_output=True, text=True, check=False, env=k["env"] | env, timeout=120)


def _panggil(k):
    if not k["uvlog"].exists():
        return []
    return [x["argv"] for x in map(json.loads, k["uvlog"].read_text().splitlines()) if "pytest" not in x["argv"]
            and "--version" not in x["argv"] and x["argv"][:1] != ["--version"]]


def test_skrip_perintah_7v21_bait_sama_tiada_set_x():
    sk = (AKAR / SKRIP).read_text()
    blok = re.search(r"^PERINTAH=\(\n(.*?)\n\)", sk, re.DOTALL | re.MULTILINE).group(1)
    assert [b.strip("'") for b in blok.splitlines()] == _perintah((AKAR / "docs/PRA-DAFTAR.md").read_text())
    assert not re.search(r"^\s*set\s+-[a-z]*x", sk, re.MULTILINE)


def test_larian_lengkap_arkib_cache_dipulih_tree_bersih(k):
    p = _jalan(k)
    assert p.returncode == 0, p.stderr
    assert _panggil(k) == [b.split()[1:] for b in _perintah((k["r"] / "docs/PRA-DAFTAR.md").read_text())]
    r = k["r"]
    assert _git(r, "status", "--porcelain") == ""
    assert (r / "hasil/cache/llm/anthropic_claude-haiku-5-5.jsonl").read_text() == "asal\n"   # cache ujian4 TIDAK dalam repo
    (d,) = [m.parent for m in k["arkib"].glob("*/MULA")]
    assert (d / "SELESAI").exists() and not (d / "CRASH").exists()
    assert (d / "hasil/luar/ujian4-meddies.jsonl").exists() and (d / "hasil/v21/ramalan/ujian4-mypii.jsonl").exists()
    rg = json.loads((d / "RINGKASAN.json").read_text())
    assert set(rg["hipotesis"]) == {"H5a", "H5b", "H5c", "H5d"} and rg["holm_k"] == 4 and set(rg["susulan"]) == {"H5a+"}
    assert set(rg["f1_jenis"]) == {"mypii", "mypii-v2", "llm_anthropic_claude-haiku-5-5"}
    assert set(rg["luar"]) == {"ujian4-meddies.versi.json", "ujian4-gliner.versi.json"}
    assert rg["lejar_usd_selepas"] == pytest.approx(3.1)
    semua = p.stdout + p.stderr + "".join(f.read_text(errors="replace") for f in d.rglob("*") if f.is_file())
    assert KUNCI_PALSU not in semua


@pytest.mark.parametrize("sabotaj,mesej", [
    (lambda k: _tulis(k["r"], "nota.txt", "x"), "tidak bersih"),
    (lambda k: _tulis(k["arkib"], "20260101T000000Z/MULA", "sha: x\n"), "MULA"),
    (lambda k: (_tulis(k["r"], "data/bench_v3/UJIAN4-MUKTAMAD", "0" * 64 + "\n"), _komit(k["r"])), "sha256"),
    (lambda k: (_tulis(k["r"], "docs/PRA-DAFTAR.md", (k["r"] / "docs/PRA-DAFTAR.md").read_text().replace(
        "MyPII v2.1", "MyPII vX")), _komit(k["r"])), "MyPII v2.1"),   # SEMUA tajuk pindaan v2.1 ((b) dan (c))
    (lambda k: (_tulis(k["r"], "docs/PRA-DAFTAR.md", (k["r"] / "docs/PRA-DAFTAR.md").read_text().replace(
        "--model gliner --split ujian4", "--model gliner --split ujian3")), _komit(k["r"])), "§7-v21"),
    (lambda k: (_tulis(k["r"], "mypii/pengecam/konteks.py", (k["r"] / "mypii/pengecam/konteks.py").read_text() + "\n# ubah\n"),
                _komit(k["r"])), "pengecam/model berubah"),
    (lambda k: (_tulis(k["r"], "config/mypii.yaml", (k["r"] / "config/mypii.yaml").read_text().replace(
        "ambang_positif: 0.05", "ambang_positif: 0.06")), _komit(k["r"])), "config pengecam berubah"),
    (lambda k: (_tulis(k["r"], "hasil/cache/llm/anthropic-lejar.json", json.dumps(
        {"jumlah_usd": 16.9, "model": {"anthropic/claude-haiku-5-5": {"usd": 0.2, "panggilan": 2000}}})), _komit(k["r"])), "baki"),
    (lambda k: (k["r"].parent / "home/.modal.toml").unlink(), "Modal"),
])
def test_enggan_sebelum_uv(k, sabotaj, mesej):
    sabotaj(k)
    p = _jalan(k)
    assert p.returncode == 4 and mesej in p.stderr, p.stderr
    assert _panggil(k) == []


def test_kering_sedia_tiada_uv(k):
    p = _jalan(k, "--kering")
    assert p.returncode == 0 and p.stdout.startswith("SEDIA"), p.stdout + p.stderr
    assert _panggil(k) == []


def test_crash_luar_kemudian_ulang_sekali_sahaja(k):
    p = _jalan(k, UV_CRASH="luar")
    assert p.returncode == 5
    p = _jalan(k, "--ulang-crash", "ujian palsu")
    assert p.returncode == 0, p.stderr
    p = _jalan(k, "--ulang-crash", "lagi")
    assert p.returncode == 4


def test_panggilan_gagal_harness_diulang_sekali(k):
    p = _jalan(k, UV_GAGAL="1")
    assert p.returncode == 0, p.stderr
    assert len([a for a in _panggil(k) if "mypii.nilai.harness" in a]) == 2
