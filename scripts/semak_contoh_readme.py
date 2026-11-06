"""Jalankan blok ```python pertama README dengan interpreter yang diberi, banding dengan blok ```text selepasnya.

    python scripts/semak_contoh_readme.py <python-venv-bersih>    # rc 0 = output sama bait demi bait

Dipakai CI (selepas `pip install` wheel dalam venv bersih) dan .awam/terbit-awam.sh: contoh README mesti benar untuk pakej yang dibina.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent


def blok() -> tuple[str, str]:
    teks = (AKAR / "README.md").read_text(encoding="utf-8")
    m = re.search(r"```python\n(.*?)```.*?```text\n(.*?)```", teks, re.DOTALL)
    if not m:
        raise SystemExit("README: tiada blok ```python diikuti blok ```text")
    return m.group(1), m.group(2)


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    kod, jangka = blok()
    with tempfile.TemporaryDirectory() as d:  # cwd luar repo: `import mypii` mesti datang dari pakej yang dipasang
        f = Path(d) / "contoh.py"
        f.write_text(kod, encoding="utf-8")
        r = subprocess.run([sys.argv[1], str(f)], check=False, cwd=d, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        return 1
    if r.stdout != jangka:
        print(f"contoh README BERBEZA:\n--- jangka\n{jangka}--- dapat\n{r.stdout}")
        return 1
    print("contoh README sama dengan output pakej")
    return 0


if __name__ == "__main__":
    sys.exit(main())
