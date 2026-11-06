"""PELAN-MODEL-LAIN P8: `scripts/ujian-muktamad.sh` atas repo git SEMENTARA dengan split PALSU + `uv` palsu.

Tiada fail `data/bench/ujian*` sebenar dibaca, tiada `~/ops/mypii` sebenar disentuh (HOME, arkib dan env dalam `tmp_path`).
Yang disalin dari repo: PRA-DAFTAR (blok §7 sebenar), config, .gitignore dan skrip itu sendiri.
"""

import hashlib
import json
import os
import re
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[1]
SKRIP = "scripts/ujian-muktamad.sh"
KUNCI_PALSU = "kunci-anthropic-PALSU-jangan-dicetak-91"
KUNCI_9R = "kunci-9router-PALSU-jangan-dicetak-37"

UV = textwrap.dedent('''\
    #!/usr/bin/env python3
    """uv palsu: rekod argv; harness → hasil/ramalan/cache palsu. Kawalan env: UV_CRASH, UV_GAGAL, UV_PYTEST_RC."""
    import json, os, pathlib, sys
    import yaml
    a = sys.argv[1:]
    with open(os.environ["UV_LOG"], "a") as f:
        f.write(json.dumps({"argv": a, "kunci": os.environ.get("ANTHROPIC_API_KEY", "") != ""}) + "\\n")
    if a[:1] == ["--version"]:
        print("uv 0.0.0 (palsu)"); sys.exit(0)
    if "pytest" in a:
        sys.exit(int(os.environ.get("UV_PYTEST_RC", "0")))
    if "--version" in a:
        print("Python 3.0.0 (palsu)"); sys.exit(0)
    if "mypii.nilai.harness" not in a:
        sys.exit(9)
    split, stat = a[a.index("--split") + 1], "--statistik" in a
    if os.environ.get("UV_BUNUH") == split:  # proses skrip dibunuh (SIGKILL: tiada trap, tiada CRASH)
        import signal; os.kill(os.getppid(), signal.SIGKILL); sys.exit(1)
    if os.environ.get("UV_CRASH") == split + ("-statistik" if stat else "-ramal"):
        print("Traceback (palsu)", file=sys.stderr); sys.exit(1)
    h = pathlib.Path("hasil")
    llm = yaml.safe_load(pathlib.Path("config/mypii.yaml").read_text())["garis_dasar"]["llm"]
    eks = ["llm:" + m for m in llm["model"] if m in llm["eksplorasi"]]
    sistem = ["presidio-asal", "pii-guard"] + ["llm:" + m for m in llm["model"]]
    if stat:
        b = lambda s: {"semua|*": {"delta": 0.05, "bawah": 0.01, "atas": 0.09, "p_bootstrap": 0.001, "p_rawak": 0.002,
                                   "p_holm_bootstrap": None if s in eks else 0.003, "p_holm_rawak": None if s in eks else 0.2}}
        (h / f"{split}-statistik.json").write_text(json.dumps({
            "kunci_utama": "semua|*", "dokumen": 1, "eksplorasi": eks, "split": split,
            "sistem": {s: {"semua|*": {"f1": 0.9, "bawah": 0.85, "atas": 0.95}} for s in ["mypii"] + sistem},
            "banding": {s: b(s) for s in sistem}}))
        sys.exit(0)
    (h / "ramalan").mkdir(exist_ok=True)
    (h / f"{split}-mypii.json").write_text("{}")
    (h / "ramalan" / f"{split}-mypii.jsonl").write_text("{}")
    c = h / "cache" / "llm"
    with open(c / "palsu.jsonl", "a") as f:
        f.write(split + "\\n")
    (c / f"baru-{split}.jsonl").write_text(split)
    lj = c / "anthropic-lejar.json"
    d = json.loads(lj.read_text()); d["jumlah_usd"] += 1.0; lj.write_text(json.dumps(d))
    if split in os.environ.get("UV_GAGAL", "").split(","):
        print("rv/deepseek-ai/DeepSeek-V4.1-Flash: 1 panggilan gagal (tiada dalam cache; jalankan semula) — Timeout", file=sys.stderr)
    print('llm:rv/deepseek-ai/DeepSeek-V4.1-Flash: {"dokumen": 1, "dari_cache": 0, "panggilan": 1, "gagal": 0, "rosak": 0}',
          file=sys.stderr)
''')


def _env_bersih() -> dict:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(r: Path, *h: str) -> str:
    return subprocess.run(["git", "-C", str(r), *h], capture_output=True, text=True, check=True, env=_env_bersih()).stdout


def _tulis(r: Path, laluan: str, isi: str | bytes) -> None:
    f = r / laluan
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(isi if isinstance(isi, bytes) else isi.encode())


def _komit(r: Path, mesej: str = "ubah") -> None:
    _git(r, "add", "-A")
    _git(r, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", mesej)


def _perintah_7(teks: str) -> list[str]:
    m = re.search(r"^## 7\..*?\n```\n(.*?)\n```", teks, re.DOTALL | re.MULTILINE)
    assert m, "blok kod §7 tiada"
    return [b for b in m.group(1).splitlines() if b.strip()]


@pytest.fixture
def k(tmp_path: Path) -> dict:
    r = tmp_path / "repo"
    for f in ("docs/PRA-DAFTAR.md", "config/mypii.yaml", ".gitignore", SKRIP):
        _tulis(r, f, (AKAR / f).read_bytes())
    for split, kunci in (("ujian", "KUNCI.json"), ("ujian2", "KUNCI2.json")):
        isi = f'{{"palsu": "{split}"}}\n'.encode()
        _tulis(r, f"data/bench/{split}.jsonl", isi)
        _tulis(r, f"data/bench/{kunci}", json.dumps({split: {"sha256": hashlib.sha256(isi).hexdigest(), "dokumen": 1}}))
    _tulis(r, "hasil/dev-kos-claude.json", json.dumps({"rancang_eksplorasi": {"perlu_ujian_usd": 4.0}}))
    _tulis(r, "hasil/cache/llm/anthropic-lejar.json", json.dumps({"jumlah_usd": 2.0, "model": {}}))
    _tulis(r, "hasil/cache/llm/palsu.jsonl", "asal\n")
    _git(r, "init", "-q")
    _komit(r, "asas")
    env_dir = tmp_path / "env"
    _tulis(env_dir, "anthropic.env", f"ANTHROPIC_API_KEY={KUNCI_PALSU}\n")
    _tulis(env_dir, "9router.env", f"NINEROUTER_API_KEY={KUNCI_9R}\n")
    _tulis(tmp_path, "bin/uv", UV)
    (tmp_path / "bin/uv").chmod(0o755)
    (tmp_path / "home").mkdir()
    env = _env_bersih() | {"PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}", "HOME": str(tmp_path / "home"),
                           "MYPII_ARKIB": str(tmp_path / "arkib"), "MYPII_ENV_DIR": str(env_dir),
                           "UV_LOG": str(tmp_path / "uv.jsonl")}
    for x in ("ANTHROPIC_API_KEY", "UV_CRASH", "UV_GAGAL", "UV_PYTEST_RC"):
        env.pop(x, None)
    return {"r": r, "env": env, "arkib": tmp_path / "arkib", "uvlog": tmp_path / "uv.jsonl", "tmp": tmp_path}


def _jalan(k: dict, *hujah: str, **env) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(k["r"] / SKRIP), *hujah], capture_output=True, text=True, check=False, env=k["env"] | env,
                          timeout=120)


def _uv(k: dict) -> list[dict]:
    return [json.loads(b) for b in k["uvlog"].read_text().splitlines()] if k["uvlog"].exists() else []


def _harness(k: dict) -> list[list[str]]:
    return [x["argv"] for x in _uv(k) if "mypii.nilai.harness" in x["argv"]]


def _mula(k: dict) -> list[Path]:
    return sorted(k["arkib"].glob("*/MULA")) if k["arkib"].exists() else []


def test_skrip_mengandungi_empat_perintah_7_bait_sama():
    sk = (AKAR / SKRIP).read_text()
    blok = re.search(r"^PERINTAH=\(\n(.*?)\n\)", sk, re.DOTALL | re.MULTILINE).group(1)
    assert [b.strip("'") for b in blok.splitlines()] == _perintah_7((AKAR / "docs/PRA-DAFTAR.md").read_text())
    assert not re.search(r"^\s*set\s+-[a-z]*x", sk, re.MULTILINE)
    assert not re.search(r"\b(printenv|env)\s*($|[|>;])|declare -p|export -p", sk, re.MULTILINE)


def test_larian_lengkap(k):
    p = _jalan(k)
    assert p.returncode == 0, p.stderr
    assert "SELESAI" in p.stdout
    perintah = _perintah_7((k["r"] / "docs/PRA-DAFTAR.md").read_text())
    assert _harness(k) == [b.split()[1:] for b in perintah]  # tepat empat, susunan ujian2 → ujian
    assert all(x["kunci"] for x in _uv(k) if "mypii.nilai.harness" in x["argv"])
    r = k["r"]
    assert _git(r, "status", "--porcelain") == ""
    assert (r / "hasil/cache/llm/palsu.jsonl").read_text() == "asal\n"
    assert not list((r / "hasil/cache/llm").glob("baru-*"))
    assert json.loads((r / "hasil/cache/llm/anthropic-lejar.json").read_text())["jumlah_usd"] == 2.0
    (d,) = [m.parent for m in _mula(k)]
    mula = (d / "MULA").read_text()
    assert f"sha: {_git(r, 'rev-parse', 'HEAD').strip()}" in mula
    assert "pelaksana: ejen autopilot mypii-ujian atas kebenaran pemilik 3 Nov 2026" in mula
    assert (d / "SELESAI").exists() and not (d / "CRASH").exists()
    assert (d / "cache/hasil/cache/llm/palsu.jsonl").read_text() == "asal\nujian2\nujian\n"
    assert (d / "cache/hasil/cache/llm/baru-ujian2.jsonl").exists() and (d / "cache/hasil/cache/llm/baru-ujian.jsonl").exists()
    assert (d / "hasil/ujian2-statistik.json").exists() and (d / "hasil/ramalan/ujian-mypii.jsonl").exists()
    assert stat.S_IMODE(d.stat().st_mode) == 0o700 and stat.S_IMODE(k["arkib"].stat().st_mode) == 0o700
    manifest = (d / "MANIFEST.sha256").read_text().splitlines()
    fail = {b.split("  ", 1)[1]: b.split("  ", 1)[0] for b in manifest}
    assert "./RINGKASAN.json" in fail and "./SELESAI" in fail and "./MULA" in fail
    for nama, h in fail.items():
        assert hashlib.sha256((d / nama).read_bytes()).hexdigest() == h
    rg = json.loads((d / "RINGKASAN.json").read_text())
    h1 = rg["split"]["ujian2"]["hipotesis"]
    assert {x: v["sistem"] for x, v in h1.items()} == {
        "H1a": "presidio-asal", "H1b": "pii-guard", "H1c": "llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "H1d": "llm:rv/deepseek-ai/DeepSeek-V4.1-Flash", "H1e": "llm:anthropic/claude-sonnet-5-5", "H1f": "llm:anthropic/claude-haiku-5-5"}
    assert set(rg["split"]["ujian"]["hipotesis"]) == {f"H2{c}" for c in "abcdef"}
    assert h1["H1a"]["disokong"] is False  # p Holm rawak palsu 0.2 ≥ α → kedua-dua p mesti < α (§8)
    assert set(rg["split"]["ujian2"]["eksplorasi"]) == {"llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct",
                                                        "llm:rv/zai-org/GLM-5.3-Flash"}
    assert rg["split"]["ujian"]["llm"]["llm:rv/deepseek-ai/DeepSeek-V4.1-Flash"]["gagal"] == 0
    assert rg["lejar_usd_selepas"] == 4.0
    semua = p.stdout + p.stderr + "".join(f.read_text(errors="replace") for f in d.rglob("*") if f.is_file())
    assert KUNCI_PALSU not in semua and KUNCI_9R not in semua


def _kotor(k):
    _tulis(k["r"], "nota.txt", "x")


def _hasil_wujud(k):
    _tulis(k["r"], "hasil/ujian2-mypii.json", "{}")


def _mula_wujud(k):
    _tulis(k["arkib"], "20260101T000000Z/MULA", "sha: x\n")


def _sha_salah(k):
    _tulis(k["r"], "data/bench/KUNCI2.json", json.dumps({"ujian2": {"sha256": "0" * 64, "dokumen": 1}}))
    _komit(k["r"])


def _baki_kurang(k):
    _tulis(k["r"], "hasil/cache/llm/anthropic-lejar.json", json.dumps({"jumlah_usd": 16.5, "model": {}}))
    _komit(k["r"])


def _env_tiada(k):
    (Path(k["env"]["MYPII_ENV_DIR"]) / "anthropic.env").unlink()


def _pradaftar_7_lain(k):
    f = k["r"] / "docs/PRA-DAFTAR.md"
    f.write_text(f.read_text().replace("--split ujian  --sistem semua --benarkan-ujian", "--split ujian --sistem semua --benarkan-ujian", 1))
    _komit(k["r"])


@pytest.mark.parametrize("rosak", [_kotor, _hasil_wujud, _mula_wujud, _sha_salah, _baki_kurang, _env_tiada, _pradaftar_7_lain])
def test_enggan_tanpa_uv(k, rosak):
    rosak(k)
    mula_sebelum = _mula(k)
    p = _jalan(k)
    assert p.returncode == 4, (p.stdout, p.stderr)
    assert "ENGGAN" in p.stderr
    assert _uv(k) == []
    assert _mula(k) == mula_sebelum


def test_enggan_bila_uji_gagal_sebelum_mula(k):
    p = _jalan(k, UV_PYTEST_RC="1")
    assert p.returncode == 4 and "make uji" in p.stderr
    assert _harness(k) == [] and _mula(k) == []


def test_panggilan_gagal_diulang_sekali_sahaja(k):
    p = _jalan(k, UV_GAGAL="ujian2")  # setiap panggilan ujian2 mencetak `panggilan gagal`
    assert p.returncode == 0, p.stderr
    perintah = [b.split()[1:] for b in _perintah_7((k["r"] / "docs/PRA-DAFTAR.md").read_text())]
    assert _harness(k) == [perintah[0], perintah[0], perintah[1], perintah[2], perintah[3]]


def test_kering_tiada_uv_tiada_arkib(k):
    p = _jalan(k, "--kering")
    assert p.returncode == 0 and p.stdout.startswith("SEDIA"), (p.stdout, p.stderr)
    assert _uv(k) == [] and not k["arkib"].exists()
    _kotor(k)
    p = _jalan(k, "--kering")
    assert p.returncode == 4 and p.stdout.startswith("TIDAK SEDIA")


def test_crash_kemudian_ulang_sekali(k):
    p = _jalan(k, UV_CRASH="ujian-ramal")
    assert p.returncode == 5 and "--ulang-crash" in p.stderr
    (d,) = [m.parent for m in _mula(k)]
    assert (d / "CRASH").exists() and not (d / "SELESAI").exists()
    assert _jalan(k).returncode == 4  # larian biasa kedua ditolak (MULA)
    assert _jalan(k, "--ulang-crash").returncode == 2  # sebab wajib
    n = len(_harness(k))
    p = _jalan(k, "--ulang-crash", "crash palsu dalam ujian")
    assert p.returncode == 0, p.stderr
    assert len(_harness(k)) - n == 4
    assert "sebab: crash palsu dalam ujian" in (d / "ULANG-CRASH").read_text()
    assert (d / "separa/ujian2-statistik.json").exists() and (d / "separa/log/3.log").exists()
    assert (d / "SELESAI").exists() and _git(k["r"], "status", "--porcelain") == ""
    assert _mula(k) == [d / "MULA"]
    p = _jalan(k, "--ulang-crash", "lagi")
    assert p.returncode == 4


def test_ulang_crash_kedua_ditolak_walau_crash_lagi(k):
    assert _jalan(k, UV_CRASH="ujian2-ramal").returncode == 5
    p = _jalan(k, "--ulang-crash", "sekali", UV_CRASH="ujian2-statistik")
    assert p.returncode == 5 and "GAGAL" in p.stderr
    (d,) = [m.parent for m in _mula(k)]
    assert (d / "GAGAL").exists() and (d / "gagal/cache/hasil/cache/llm/baru-ujian2.jsonl").exists()
    assert _git(k["r"], "status", "--porcelain") == ""
    n = len(_uv(k))
    assert _jalan(k, "--ulang-crash", "dua").returncode == 4
    assert len(_uv(k)) == n


def test_ulang_crash_dibunuh_tidak_boleh_diulang_lagi(k):
    assert _jalan(k, UV_CRASH="ujian2-ramal").returncode == 5
    p = _jalan(k, "--ulang-crash", "sekali", UV_BUNUH="ujian")  # ulangan dibunuh: tiada SELESAI/GAGAL/CRASH
    assert p.returncode != 0
    (d,) = [m.parent for m in _mula(k)]
    assert (d / "ULANG-CRASH").exists() and not (d / "SELESAI").exists() and not (d / "GAGAL").exists()
    n = len(_uv(k))
    p = _jalan(k, "--ulang-crash", "dua")
    assert p.returncode == 4 and "SEKALI" in p.stderr and len(_uv(k)) == n


def test_ulang_crash_tanpa_mula_ditolak(k):
    p = _jalan(k, "--ulang-crash", "tiada larian")
    assert p.returncode == 4 and _uv(k) == []


def test_ulang_bila_proses_mati_tanpa_crash(k):
    mati = subprocess.Popen(["true"])
    mati.wait()
    _tulis(k["arkib"], "20260101T000000Z/MULA", "sha: x\n")
    _tulis(k["arkib"], "20260101T000000Z/PID", f"{mati.pid}\n")
    p = _jalan(k, "--ulang-crash", "proses dibunuh")
    assert p.returncode == 0, p.stderr
    assert (k["arkib"] / "20260101T000000Z/SELESAI").exists()


def test_ulang_ditolak_bila_proses_masih_hidup(k):
    _tulis(k["arkib"], "20260101T000000Z/MULA", "sha: x\n")
    _tulis(k["arkib"], "20260101T000000Z/PID", f"{os.getpid()}\n")
    p = _jalan(k, "--ulang-crash", "masih hidup")
    assert p.returncode == 4 and "masih hidup" in p.stderr and _uv(k) == []


def test_hujah_tidak_dikenali(k):
    assert _jalan(k, "--benarkan-ujian").returncode == 2
    assert _uv(k) == []
