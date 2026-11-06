"""Mesej Telegram penyemak IAA (PELAN-IAA-HALAMAN P4, ADR-015 §Halaman pintu) — BUTANG SAHAJA.

    python -m mypii.iaa.mesej teks            # teks mesej BM + EN (tiada URL/domain) → stdout
    python -m mypii.iaa.mesej butang < pautan # JSON papan kekunci inline `[[{"text","url"}]]` → stdout (untuk NOTIFY_BUTANG)

Teks = `teks/{ms,en}.json` kunci `mesej_*` (+ `judul`); `{butang}` → label butang bahasa itu. Teks yang mengandungi URL, domain atau
nama hos config `iaa.pelayan.nama_hos` DITOLAK (ValueError) — pautan hanya hidup dalam butang, supaya penerima tidak menaip nama laman
sendiri dan mendarat di halaman pintu. Pautan dibaca dari stdin (bukan argv: tidak kelihatan dalam `ps`) dan TIDAK PERNAH dicetak dalam ralat.
"""

import json
import re
import sys
from pathlib import Path

from mypii import konfig

TEKS = Path(__file__).resolve().parent / "teks"
BAHASA = ("ms", "en")
KUNCI = ("mesej_teks", "mesej_simpan")
DOMAIN = re.compile(r"https?|://|www\.|\b[a-z0-9-]+\.(com|my|net|org|dev|io)\b", re.IGNORECASE)


def muat_teks(folder: Path = TEKS) -> dict[str, dict]:
    return {b: json.loads((folder / f"{b}.json").read_text(encoding="utf-8")) for b in BAHASA}


def tapis(teks: str, nama_hos: str) -> str:
    """Pulangkan `teks` jika tiada URL/domain/nama hos; jika ada → ValueError (rentetan yang ditemui TIDAK dipetik)."""
    if DOMAIN.search(teks) or nama_hos.lower() in teks.lower():
        raise ValueError("teks mesej mengandungi URL/domain — pautan hanya dalam butang")
    return teks


def label(t: dict[str, dict]) -> str:
    return " · ".join(t[b]["mesej_butang"] for b in BAHASA)


def bina_teks(t: dict[str, dict], nama_hos: str) -> str:
    """Baris pertama = judul BM · EN (notify menebalkannya); kemudian perenggan BM, kemudian EN."""
    bahagian = [" · ".join(t[b]["judul"] for b in BAHASA)]
    for b in BAHASA:
        bahagian.append("\n".join(t[b][k].replace("{butang}", t[b]["mesej_butang"]) for k in KUNCI))
    teks = "\n\n".join(bahagian)
    tapis(label(t), nama_hos)
    return tapis(teks, nama_hos)


def bina_butang(t: dict[str, dict], pautan: str, nama_hos: str) -> str:
    """JSON papan kekunci inline satu butang; pautan mesti `https://<nama_hos>/s/<token>` (lain = ValueError, pautan tidak dipetik)."""
    if not re.fullmatch(rf"https://{re.escape(nama_hos)}/s/[A-Za-z0-9_-]{{16,}}", pautan):
        raise ValueError("pautan bukan pautan penyemak yang sah")
    return json.dumps([[{"text": tapis(label(t), nama_hos), "url": pautan}]], ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv not in (["teks"], ["butang"]):
        print("guna: python -m mypii.iaa.mesej teks|butang (pautan dari stdin)", file=sys.stderr)
        return 2
    nama_hos = konfig.utama()["iaa"]["pelayan"]["nama_hos"]
    t = muat_teks()
    try:
        keluar = bina_teks(t, nama_hos) if argv == ["teks"] else bina_butang(t, sys.stdin.read().strip(), nama_hos)
    except (ValueError, KeyError) as e:
        print(f"GAGAL: {e}", file=sys.stderr)
        return 1
    sys.stdout.write(keluar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
