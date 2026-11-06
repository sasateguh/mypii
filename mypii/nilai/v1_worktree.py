"""Sistem `mypii-v1` (PRA-DAFTAR §7-v2, PELAN-V2 P14): ramalan pengecam + config dari tag `nilai.v1.tag`, dimuat dari `git worktree`
sementara pada tag itu. Enggan bila sha worktree ≠ sha tag. Worktree dibuang selepas larian (berjaya atau gagal).

Subproses memakai interpreter yang sama, cwd + PYTHONPATH = worktree → `import mypii` = kod tag, `konfig.AKAR` = worktree (config tag).
Pembolehubah `GIT_*` dibuang (perangkap cangkuk git — ~/CLAUDE.md). Hanya `{id, teks}` dihantar; tiada rangkaian.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mypii import konfig

_KOD = """import json, sys
from mypii.nilai.harness import ramal
d = json.load(open(sys.argv[1], encoding="utf-8"))
json.dump(ramal("mypii", d), open(sys.argv[2], "w", encoding="utf-8"))
"""


def _env(**tambah: str) -> dict:
    e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return {**e, **tambah}


def _git(*arg: str, cwd: Path) -> str:
    return subprocess.run(["git", *arg], cwd=cwd, env=_env(), check=True, capture_output=True, text=True).stdout.strip()


def ramal(dokumen: list[dict], akar: Path = konfig.AKAR) -> list[list[dict]]:
    tag = konfig.utama()["nilai"]["v1"]["tag"]
    sha_tag = _git("rev-parse", f"{tag}^{{commit}}", cwd=akar)
    with tempfile.TemporaryDirectory(prefix="mypii-v1-") as t:
        wt = Path(t) / "wt"
        _git("worktree", "add", "--detach", str(wt), sha_tag, cwd=akar)
        try:
            if _git("rev-parse", "HEAD", cwd=wt) != sha_tag:
                raise SystemExit(f"mypii-v1: sha worktree ≠ tag {tag} ({sha_tag[:12]}) — enggan")
            masuk, keluar = Path(t) / "dok.json", Path(t) / "ramalan.json"
            masuk.write_text(json.dumps([{"id": d["id"], "teks": d["teks"]} for d in dokumen]), encoding="utf-8")
            subprocess.run([sys.executable, "-c", _KOD, str(masuk), str(keluar)], cwd=wt, check=True,
                           env=_env(PYTHONPATH=str(wt), MYPII_KONFIG=str(wt / "config")))
            return json.loads(keluar.read_text(encoding="utf-8"))
        finally:
            _git("worktree", "remove", "--force", str(wt), cwd=akar)
