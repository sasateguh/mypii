"""PELAN-V2 P14: `scripts/ujian3-muktamad.sh` atas repo git SEMENTARA dengan split ujian3 PALSU + `uv` palsu.

Tiada `data/bench_v3/ujian3.jsonl` sebenar dibaca; tiada `~/ops/mypii` sebenar disentuh (HOME, arkib, env dalam `tmp_path`).
Yang disalin dari repo: PRA-DAFTAR (blok §7-v2 + pindaan beku sebenar), config, .gitignore dan skrip itu sendiri.
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
SKRIP = "scripts/ujian3-muktamad.sh"
KUNCI_PALSU = "kunci-anthropic-PALSU-u3-jangan-dicetak"

UV = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, os, pathlib, sys
    a = sys.argv[1:]
    with open(os.environ["UV_LOG"], "a") as f:
        f.write(json.dumps({"argv": a, "kunci": os.environ.get("ANTHROPIC_API_KEY", "") != ""}) + "\\n")
    if a[:1] == ["--version"] or "--version" in a:
        print("palsu 0"); sys.exit(0)
    if "pytest" in a:
        sys.exit(int(os.environ.get("UV_PYTEST_RC", "0")))
    if "mypii.nilai.harness" not in a:
        sys.exit(9)
    stat = "--statistik" in a
    if os.environ.get("UV_CRASH") == ("statistik" if stat else "ramal"):
        sys.exit(1)
    h = pathlib.Path("hasil")
    if stat:
        hip = {"H4a": {"sistem": "llm:anthropic/claude-haiku-5-5", "delta": 0.05, "disokong": True},
               "H4b": {"sistem": "mypii-v1", "delta": 0.3, "disokong": True}}
        sis = ["mypii", "mypii-v1", "presidio-asal", "llm:anthropic/claude-haiku-5-5"]
        (h / "ujian3-statistik.json").write_text(json.dumps({
            "kunci_utama": "semua|*", "dokumen": 1, "eksplorasi": ["presidio-asal"],
            "sistem": {s: {"semua|*": {"f1": 0.9, "bawah": 0.8, "atas": 0.95}} for s in sis},
            "banding": {"presidio-asal": {"semua|*": {"delta": 0.5, "bawah": 0.4, "atas": 0.6, "p_bootstrap": 0.0, "p_rawak": 0.001}}},
            "v2": {"k": 2, "alfa": 0.05, "hipotesis": hip}}))
        sys.exit(0)
    (h / "ramalan").mkdir(exist_ok=True)
    (h / "ujian3-mypii.json").write_text("{}")
    (h / "ramalan" / "ujian3-mypii.jsonl").write_text("{}")
    c = h / "cache" / "llm"
    with open(c / "anthropic_claude-haiku-5-5.jsonl", "a") as f:
        f.write("ujian3\\n")
    lj = c / "anthropic-lejar.json"
    d = json.loads(lj.read_text()); d["jumlah_usd"] += 0.1; lj.write_text(json.dumps(d))
    if os.environ.get("UV_GAGAL"):
        print("1 panggilan gagal (palsu)", file=sys.stderr)
    print('llm:anthropic/claude-haiku-5-5: {"dokumen": 1, "panggilan": 1, "gagal": 0, "rosak": 0}', file=sys.stderr)
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
    m = re.search(r"^#### §7-v2 Perintah tepat ujian3\n```\n(.*?)\n```", teks, re.DOTALL | re.MULTILINE)
    assert m
    return [b for b in m.group(1).splitlines() if b.strip()]


@pytest.fixture
def k(tmp_path: Path) -> dict:
    r = tmp_path / "repo"
    for f in ("docs/PRA-DAFTAR.md", "config/mypii.yaml", ".gitignore", SKRIP, "scripts/muktamad-lib.sh"):
        _tulis(r, f, (AKAR / f).read_bytes())
    isi = b'{"palsu": "ujian3"}\n'
    s = hashlib.sha256(isi).hexdigest()
    _tulis(r, "data/bench_v3/ujian3.jsonl", isi)
    _tulis(r, "data/bench_v3/dev3.jsonl", b'{"palsu": "dev3"}\n')
    _tulis(r, "data/bench_v3/KUNCI3.json", json.dumps({"ujian3": {"sha256": s, "dokumen": 1}}))
    _tulis(r, "data/bench_v3/UJIAN3-MUKTAMAD", f"{s} palsu\n")
    _tulis(r, "hasil/cache/llm/anthropic-lejar.json", json.dumps(
        {"jumlah_usd": 3.0, "model": {"anthropic/claude-haiku-5-5": {"usd": 0.2, "panggilan": 2000}}}))
    _tulis(r, "hasil/cache/llm/anthropic_claude-haiku-5-5.jsonl", "asal\n")
    _git(r, "init", "-q")
    _komit(r)
    env_dir = tmp_path / "env"
    _tulis(env_dir, "anthropic.env", f"ANTHROPIC_API_KEY={KUNCI_PALSU}\n")
    _tulis(tmp_path, "bin/uv", UV)
    (tmp_path / "bin/uv").chmod(0o755)
    (tmp_path / "home").mkdir()
    env = _env_bersih() | {"PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}", "HOME": str(tmp_path / "home"),
                           "MYPII_ARKIB": str(tmp_path / "arkib"), "MYPII_ENV_DIR": str(env_dir), "UV_LOG": str(tmp_path / "uv.jsonl")}
    for x in ("ANTHROPIC_API_KEY", "UV_CRASH", "UV_GAGAL", "UV_PYTEST_RC"):
        env.pop(x, None)
    return {"r": r, "env": env, "arkib": tmp_path / "arkib", "uvlog": tmp_path / "uv.jsonl"}


def _jalan(k, *h, **env):
    return subprocess.run(["bash", str(k["r"] / SKRIP), *h], capture_output=True, text=True, check=False, env=k["env"] | env, timeout=120)


def _harness(k):
    if not k["uvlog"].exists():
        return []
    return [x["argv"] for x in map(json.loads, k["uvlog"].read_text().splitlines()) if "mypii.nilai.harness" in x["argv"]]


def test_skrip_dua_perintah_7v2_bait_sama():
    sk = (AKAR / SKRIP).read_text()
    blok = re.search(r"^PERINTAH=\(\n(.*?)\n\)", sk, re.DOTALL | re.MULTILINE).group(1)
    assert [b.strip("'") for b in blok.splitlines()] == _perintah((AKAR / "docs/PRA-DAFTAR.md").read_text())
    assert not re.search(r"^\s*set\s+-[a-z]*x", sk, re.MULTILINE)


def test_larian_lengkap_arkib_dan_cache_dipulih(k):
    p = _jalan(k)
    assert p.returncode == 0, p.stderr
    assert _harness(k) == [b.split()[1:] for b in _perintah((k["r"] / "docs/PRA-DAFTAR.md").read_text())]
    r = k["r"]
    assert _git(r, "status", "--porcelain") == ""
    assert (r / "hasil/cache/llm/anthropic_claude-haiku-5-5.jsonl").read_text() == "asal\n"   # cache ujian3 TIDAK dalam repo
    assert json.loads((r / "hasil/cache/llm/anthropic-lejar.json").read_text())["jumlah_usd"] == 3.0
    (d,) = [m.parent for m in k["arkib"].glob("*/MULA")]
    assert (d / "SELESAI").exists() and not (d / "CRASH").exists()
    assert (d / "cache/hasil/cache/llm/anthropic_claude-haiku-5-5.jsonl").read_text() == "asal\nujian3\n"
    rg = json.loads((d / "RINGKASAN.json").read_text())
    assert set(rg["hipotesis"]) == {"H4a", "H4b"} and rg["holm_k"] == 2 and set(rg["deskriptif"]) == {"presidio-asal"}
    assert rg["lejar_usd_selepas"] == pytest.approx(3.1)
    semua = p.stdout + p.stderr + "".join(f.read_text(errors="replace") for f in d.rglob("*") if f.is_file())
    assert KUNCI_PALSU not in semua


@pytest.mark.parametrize("sabotaj,mesej", [
    (lambda k: _tulis(k["r"], "nota.txt", "x"), "tidak bersih"),
    (lambda k: _tulis(k["arkib"], "20260101T000000Z/MULA", "sha: x\n"), "MULA"),
    (lambda k: (_tulis(k["r"], "data/bench_v3/UJIAN3-MUKTAMAD", "0" * 64 + "\n"), _komit(k["r"])), "sha256"),
    (lambda k: (_tulis(k["r"], "docs/PRA-DAFTAR.md", (k["r"] / "docs/PRA-DAFTAR.md").read_text().replace(
        "kuasa + pengecam dibekukan", "kuasa")), _komit(k["r"])), "dibekukan"),
    (lambda k: (_tulis(k["r"], "docs/PRA-DAFTAR.md", (k["r"] / "docs/PRA-DAFTAR.md").read_text().replace(
        "--split ujian3 --sistem mypii mypii-v1", "--split ujian3 --sistem mypii")), _komit(k["r"])), "§7-v2"),
    (lambda k: (_tulis(k["r"], "hasil/cache/llm/anthropic-lejar.json", json.dumps(
        {"jumlah_usd": 17.0, "model": {"anthropic/claude-haiku-5-5": {"usd": 0.2, "panggilan": 2000}}})), _komit(k["r"])), "baki"),
])
def test_enggan_sebelum_harness(k, sabotaj, mesej):
    sabotaj(k)
    p = _jalan(k)
    assert p.returncode == 4 and mesej in p.stderr, p.stderr
    assert _harness(k) == []


def test_kering_tiada_harness(k):
    p = _jalan(k, "--kering")
    assert p.returncode == 0 and p.stdout.startswith("SEDIA"), p.stdout + p.stderr
    assert _harness(k) == []


def test_crash_kemudian_ulang_sekali_sahaja(k):
    p = _jalan(k, UV_CRASH="statistik")
    assert p.returncode == 5
    p = _jalan(k, "--ulang-crash", "ujian palsu")
    assert p.returncode == 0, p.stderr
    p = _jalan(k, "--ulang-crash", "lagi")
    assert p.returncode == 4


def test_panggilan_gagal_diulang_sekali(k):
    p = _jalan(k, UV_GAGAL="1")
    assert p.returncode == 0, p.stderr
    assert len([a for a in _harness(k) if "--statistik" not in a]) == 2
