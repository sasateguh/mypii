"""Operasi kontena semakan IAA (ADR-015) — dipanggil oleh `deploy/iaa/deploy.sh` melalui `docker exec`.

    python -m mypii.iaa.operasi sihat                 # HEALTHCHECK: GET /sihat pada port config → keluar 0/1
    python -m mypii.iaa.operasi kemajuan              # "p1 12/300" setiap penyemak (KIRAAN sahaja)
    python -m mypii.iaa.operasi penyemak tambah <id>  # token rawak → penyemak.json (0600); id wujud = ralat
    python -m mypii.iaa.operasi penyemak pautan <id>  # cetak pautan ke terminal SAHAJA (jangan log/komit)
    python -m mypii.iaa.operasi penyemak senarai      # nama penyemak sahaja (tiada token)

Folder = env MYPII_IAA_FOLDER (lalai config `iaa.pakej.folder`). Tiada teks dokumen dicetak.
"""

import argparse
import json
import os
import re
import secrets
import sys
import urllib.request
from pathlib import Path

from mypii import konfig
from mypii.iaa.stor import Stor, siap

ID_SAH = re.compile(r"^[a-z][a-z0-9_]{0,15}$")


def folder_lalai(k: dict) -> Path:
    return Path(os.environ.get("MYPII_IAA_FOLDER", k["pakej"]["folder"])).expanduser()


def baca_token(laluan: Path) -> dict[str, str]:
    return json.loads(laluan.read_text(encoding="utf-8")) if laluan.exists() else {}


def tambah(laluan: Path, penyemak: str, bait: int) -> str:
    """Token baharu untuk `penyemak`; tulis atomik 0600. Id wujud / tidak sah = ValueError."""
    if not ID_SAH.match(penyemak):
        raise ValueError(f"id penyemak tidak sah: {penyemak!r} (huruf kecil/digit/_, ≤ 16)")
    token = baca_token(laluan)
    if penyemak in token:
        raise ValueError(f"penyemak {penyemak} sudah wujud — token tidak ditukar")
    token[penyemak] = secrets.token_urlsafe(bait)
    sementara = laluan.with_name(laluan.name + ".baru")
    fd = os.open(sementara, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(token, f, indent=1)
    os.chmod(sementara, 0o600)
    os.replace(sementara, laluan)
    return token[penyemak]


def kemajuan(folder: Path, k: dict) -> dict[str, tuple[int, int]]:
    """{penyemak: (siap, n)} untuk setiap penyemak dalam penyemak.json."""
    pk = k["pakej"]
    bundel = json.loads((folder / pk["bundel"]).read_text(encoding="utf-8"))
    stor = Stor(folder / pk["stor"])
    try:
        out = {}
        for p in baca_token(folder / pk["penyemak"]):
            senarai = bundel["uji"] if p == "uji" else bundel["dokumen"]
            jaw = stor.jawapan(p)
            out[p] = (sum(1 for d in senarai if siap(d, jaw.get(d["urutan"], {}))), len(senarai))
        return out
    finally:
        stor.tutup()


def sihat(port: int, masa: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/sihat", timeout=masa) as r:
            return r.status == 200
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    k = konfig.utama()["iaa"]
    ap = argparse.ArgumentParser(description="Operasi kontena semakan IAA")
    sub = ap.add_subparsers(dest="arahan", required=True)
    sub.add_parser("sihat")
    sub.add_parser("kemajuan")
    ps = sub.add_parser("penyemak")
    ps.add_argument("tindakan", choices=["tambah", "pautan", "senarai"])
    ps.add_argument("id", nargs="?")
    a = ap.parse_args(argv)
    folder = folder_lalai(k)
    laluan_token = folder / k["pakej"]["penyemak"]
    if a.arahan == "sihat":
        return 0 if sihat(k["pelayan"]["port"]) else 1
    if a.arahan == "kemajuan":
        for p, (s, n) in kemajuan(folder, k).items():
            print(f"{p} {s}/{n}")
        return 0
    if a.tindakan == "senarai":
        print(" ".join(baca_token(laluan_token)) or "(tiada)")
        return 0
    if not a.id:
        print("GAGAL: id penyemak diperlukan", file=sys.stderr)
        return 2
    if a.tindakan == "tambah":
        try:
            tambah(laluan_token, a.id, k["pelayan"]["token_bait"])
        except ValueError as e:
            print(f"GAGAL: {e}", file=sys.stderr)
            return 1
        print(f"penyemak {a.id} ditambah (pautan: `deploy.sh --penyemak pautan {a.id}`)")
        return 0
    token = baca_token(laluan_token).get(a.id)
    if not token:
        print(f"GAGAL: tiada penyemak {a.id}", file=sys.stderr)
        return 1
    print(f"https://{k['pelayan']['nama_hos']}/s/{token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
