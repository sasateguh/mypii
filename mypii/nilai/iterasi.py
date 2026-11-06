"""Rekod setiap cubaan gelung dalam `hasil/iterasi.tsv` (PELAN-C C2a, ADR-006 §Iterasi).

Satu baris TSV setiap larian `make nilai` — termasuk yang crash — supaya sejarah cubaan boleh dibaca mesin dan dicarta.
Fail itu TAMBAH-SAHAJA (gerbang autopilot menolak penyuntingan baris yang sudah dikomit). Lajur, status sah, laluan dan
had = config `nilai.iterasi:`.
"""

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from mypii import konfig


def _k() -> dict:
    return konfig.utama()["nilai"]["iterasi"]


def bersih(teks) -> str:
    """Medan TSV: tiada tab/baris baharu (diganti satu ruang), ruang berlapis dipadatkan."""
    return re.sub(r"\s+", " ", "" if teks is None else str(teks)).strip()


def _git(akar: Path, *hujah: str) -> str:
    r = subprocess.run(["git", "-C", str(akar), *hujah], check=False, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def komit(akar: Path, abai: list[str] = ()) -> str:
    """`git rev-parse --short HEAD`, `+` di hujung bila tree kotor; `-` bila bukan repo git.

    Laluan `abai` (config `kotor_abai`: output larian, termasuk TSV ini sendiri) tidak menjadikan tree kotor.
    """
    sha = _git(akar, "rev-parse", "--short", "HEAD")
    if not sha:
        return "-"
    kotor = _git(akar, "status", "--porcelain", "--", ".", *(f":(exclude){x}" for x in abai))
    return sha + ("+" if kotor else "")


def baris_kod(akar: Path, laluan: list[str]) -> str:
    """Kos kerumitan: `+tambah/-buang` baris berbanding HEAD atas laluan pengecam (fail binari dikira 0)."""
    tambah = buang = 0
    for b in _git(akar, "diff", "--numstat", "HEAD", "--", *laluan).splitlines():
        t, d, _ = b.split("\t", 2)
        tambah += int(t) if t.isdigit() else 0
        buang += int(d) if d.isdigit() else 0
    return f"+{tambah}/-{buang}"


def dev_sha8(akar: Path, split: str) -> str:
    """8 aksara pertama sha256 split dari `CINCANGAN.json` (v3: `konfig.fail_cincangan`) — baris dari split berlainan tidak dibanding.
    `?` bila tiada."""
    try:
        c = json.loads((akar / konfig.fail_cincangan(split)).read_text(encoding="utf-8"))
        return c[split]["sha256"][:8]
    except (OSError, KeyError, ValueError):
        return "?"


def baris(nilai: dict, lajur: list[str]) -> str:
    return "\t".join(bersih(nilai.get(x, "")) for x in lajur) + "\n"


def tambah(laluan: Path, rekod: list[dict]) -> None:
    """Tambah baris di hujung; pengepala ditulis HANYA bila fail tiada/kosong."""
    lajur = _k()["lajur"]
    laluan.parent.mkdir(parents=True, exist_ok=True)
    baharu = not laluan.exists() or laluan.stat().st_size == 0
    with open(laluan, "a", encoding="utf-8") as f:
        if baharu:
            f.write("\t".join(lajur) + "\n")
        f.writelines(baris(r, lajur) for r in rekod)


def catat(status: str, keterangan: str, f1=None, *, split: str = "dev", akar: Path | None = None,
          laluan: Path | None = None) -> dict:
    """Tambah SATU baris larian semasa. `f1` = `semua|*` tepat sistem config (kosong bila crash)."""
    k = _k()
    if status not in k["status"]:
        raise ValueError(f"status {status!r} tidak sah — pilih {k['status']}")
    akar = akar or konfig.AKAR
    had = k["had_keterangan"]
    ket = bersih(keterangan)
    rekod = {
        "tarikh": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "komit": komit(akar, k["kotor_abai"]),
        "dev_sha8": dev_sha8(akar, split),
        "f1": "" if f1 is None else f1,
        "status": status,
        "baris_kod": baris_kod(akar, k["laluan_kod"]),
        "keterangan": ket if len(ket) <= had else ket[: had - 1] + "…",
    }
    tambah(laluan or akar / k["fail"], [rekod])
    return rekod
