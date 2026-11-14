"""Perisai SM-01 (ADR-015): imej semakan IAA sentiasa mengambil tampalan OS Debian; cache pembina dipecah setiap hari."""

import re
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent.parent / "deploy" / "iaa"


def _arahan(dockerfile: str) -> list[str]:
    """Arahan Dockerfile (baris sambungan `\\` digabung, komen dibuang)."""
    gabung = re.sub(r"\\\n", " ", dockerfile)
    return [b.strip() for b in gabung.splitlines() if b.strip() and not b.lstrip().startswith("#")]


def test_dockerfile_apt_upgrade_selepas_arg_tampalan_sebelum_user():
    arahan = _arahan((DEPLOY / "Dockerfile").read_text(encoding="utf-8"))
    i_from = next(i for i, a in enumerate(arahan) if a.startswith("FROM "))
    i_arg = next(i for i, a in enumerate(arahan) if re.fullmatch(r"ARG TAMPALAN_OS(=\S+)?", a))
    i_upg = next(i for i, a in enumerate(arahan) if a.startswith("RUN ") and "apt-get upgrade -y" in a)
    i_user = next(i for i, a in enumerate(arahan) if a.startswith("USER "))
    i_pip = next(i for i, a in enumerate(arahan) if a.startswith("RUN ") and "pip install" in a)
    assert i_from < i_arg < i_upg < i_user
    assert i_upg < i_pip
    upg = arahan[i_upg]
    # ARG mesti DIRUJUK dalam RUN — ARG yang tidak dipakai tidak memecah cache lapisan itu.
    assert "TAMPALAN_OS" in upg
    assert upg.index("apt-get update") < upg.index("apt-get upgrade")
    assert "rm -rf /var/lib/apt/lists/*" in upg


def test_deploy_sh_bina_dengan_pull_dan_tarikh_tampalan():
    sh = (DEPLOY / "deploy.sh").read_text(encoding="utf-8")
    bina = [b for b in sh.splitlines() if "bina-imej.sh" in b and not b.lstrip().startswith("#")]
    assert len(bina) == 1
    assert "--pull" in bina[0]
    # Nilai dikira semasa deploy (tarikh UTC), bukan terkod.
    assert '--build-arg TAMPALAN_OS="$(date -u +%F)"' in bina[0]
