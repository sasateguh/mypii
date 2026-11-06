"""Stor jawapan IAA (PELAN-IAA P3, ADR-015): SQLite, satu baris setiap ketikan (log tambah).

Jawapan semasa = baris TERAKHIR setiap (penyemak, urutan, soalan). Undur = padam baris terakhir penyemak itu, jadi jawapan
sebelumnya (atau kosong) kembali. `journal_mode=DELETE` supaya backup harian ~/ops menyalin satu fail yang konsisten.
Soalan: `a<n>` (span ke-n, bermula 1) · `b` · `c` — nilai disahkan di sini sebelum disimpan.
"""

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

SKEMA = """CREATE TABLE IF NOT EXISTS jawapan (
  id INTEGER PRIMARY KEY AUTOINCREMENT, penyemak TEXT NOT NULL, urutan INTEGER NOT NULL,
  soalan TEXT NOT NULL, nilai TEXT NOT NULL, ts TEXT NOT NULL)"""


class NilaiTakSah(ValueError):
    pass


def sahkan(dok: dict, soalan: str, nilai, pilihan: dict, had_b: int, had_aksara: int) -> object:
    """Pulangkan nilai ternormal atau NilaiTakSah. `dok` = dokumen bundel (untuk bilangan span)."""
    if soalan.startswith("a") and soalan[1:].isdigit():
        if not 1 <= int(soalan[1:]) <= len(dok["spans"]) or soalan != f"a{int(soalan[1:])}":
            raise NilaiTakSah("span tiada")
        if nilai not in pilihan["a"]:
            raise NilaiTakSah("pilihan (a) tidak sah")
        return nilai
    if soalan == "c":
        if nilai not in pilihan["c"]:
            raise NilaiTakSah("pilihan (c) tidak sah")
        return nilai
    if soalan == "b":
        if not isinstance(nilai, dict) or nilai.get("pilih") not in pilihan["b"]:
            raise NilaiTakSah("pilihan (b) tidak sah")
        if nilai["pilih"] == pilihan["b"][0]:
            return {"pilih": nilai["pilih"]}
        senarai = nilai.get("nilai")
        if not isinstance(senarai, list) or not all(isinstance(s, str) for s in senarai):
            raise NilaiTakSah("nilai (b) mesti senarai teks")
        bersih = [s.strip() for s in senarai if s.strip()]
        if not 1 <= len(bersih) <= had_b or any(len(s) > had_aksara for s in bersih):
            raise NilaiTakSah(f"nilai (b): 1–{had_b} baris, setiap baris ≤ {had_aksara} aksara")
        return {"pilih": nilai["pilih"], "nilai": bersih}
    raise NilaiTakSah("soalan tidak dikenali")


def siap(dok: dict, jawapan: dict) -> bool:
    """Dokumen siap = setiap span (a) + (b) + (c) dijawab."""
    return all(f"a{n}" in jawapan for n in range(1, len(dok["spans"]) + 1)) and "b" in jawapan and "c" in jawapan


class Stor:
    def __init__(self, laluan: Path):
        self._kunci = threading.Lock()
        self._db = sqlite3.connect(laluan, check_same_thread=False, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=DELETE")
        self._db.execute(SKEMA)

    def simpan(self, penyemak: str, urutan: int, soalan: str, nilai) -> None:
        ts = datetime.now(UTC).isoformat(timespec="seconds")
        with self._kunci:
            self._db.execute("INSERT INTO jawapan (penyemak, urutan, soalan, nilai, ts) VALUES (?,?,?,?,?)",
                             (penyemak, urutan, soalan, json.dumps(nilai, ensure_ascii=False), ts))

    def undur(self, penyemak: str) -> int | None:
        """Padam ketikan terakhir penyemak; pulangkan urutan dokumennya (None = tiada apa untuk diundur)."""
        with self._kunci:
            r = self._db.execute("SELECT id, urutan FROM jawapan WHERE penyemak=? ORDER BY id DESC LIMIT 1",
                                 (penyemak,)).fetchone()
            if r is None:
                return None
            self._db.execute("DELETE FROM jawapan WHERE id=?", (r[0],))
            return r[1]

    def jawapan(self, penyemak: str) -> dict[int, dict]:
        """urutan → {soalan: nilai} (nilai terkini)."""
        out: dict[int, dict] = {}
        with self._kunci:
            baris = self._db.execute("SELECT urutan, soalan, nilai FROM jawapan WHERE penyemak=? ORDER BY id",
                                     (penyemak,)).fetchall()
        for urutan, soalan, nilai in baris:
            out.setdefault(urutan, {})[soalan] = json.loads(nilai)
        return out

    def ada_ketikan(self, penyemak: str) -> bool:
        with self._kunci:
            return self._db.execute("SELECT 1 FROM jawapan WHERE penyemak=? LIMIT 1", (penyemak,)).fetchone() is not None

    def penyemak(self) -> list[str]:
        """Id penyemak yang ada sekurang-kurangnya satu ketikan (tersusun)."""
        with self._kunci:
            return [r[0] for r in self._db.execute("SELECT DISTINCT penyemak FROM jawapan ORDER BY penyemak")]

    def tutup(self) -> None:
        self._db.close()
