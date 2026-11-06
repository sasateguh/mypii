"""Pelayan halaman semakan IAA (PELAN-IAA P3, ADR-015): `ThreadingHTTPServer` stdlib, tiada pihak ketiga.

    python -m mypii.iaa.pelayan [--folder <dir>]   # `make iaa-pelayan`; folder = iaa.pakej.folder (env MYPII_IAA_FOLDER)

Laluan: `GET /s/<token>` halaman · `GET /s/<token>/keadaan[?u=<urutan>]` · `POST /s/<token>/jawab` · `POST /s/<token>/undur`
· `/statik/<fail>` · `/teks/<bahasa>.json` · `/robots.txt` · `/sihat` · `GET /` halaman pintu. Token salah = 404 sama seperti laluan
tiada; badan setiap 404 GET/HEAD = halaman pintu yang sama dengan `/` (PELAN-IAA-HALAMAN, ADR-015 §Halaman pintu) — tiada oracle token.
GET tidak pernah menulis (pratonton pautan Telegram). Halaman hanya menerima teks + span EMAS — tiada id, split atau ramalan.
"""

import argparse
import hmac
import html
import json
import os
import re
import sys
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from mypii import konfig
from mypii.iaa.stor import NilaiTakSah, Stor, sahkan, siap

STATIK = Path(__file__).resolve().parent / "statik"
TEKS = Path(__file__).resolve().parent / "teks"
JENIS_STATIK = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}
TEMPLAT = {"pintu.html"}   # dijana pelayan, bukan dihidang mentah di /statik/
KEPALA = {
    "Content-Security-Policy": "default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    "X-Robots-Tag": "noindex, nofollow",
    "Cache-Control": "no-store, no-transform",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def bina_pintu(templat: Path = STATIK / "pintu.html", teks: Path = TEKS) -> bytes:
    """Halaman pintu BM + EN: `{{<bahasa>.<kunci>}}` → teks fail bahasa di-escape; `{butang}` → label butang mesej (tebal).

    Kunci hilang = KeyError semasa mula (gagal awal, bukan halaman separuh)."""
    t = {b: json.loads((teks / f"{b}.json").read_text(encoding="utf-8")) for b in ("ms", "en")}

    def isi(m: re.Match) -> str:
        d = t[m[1]]
        nilai = html.escape(d[m[2]])
        return nilai.replace("{butang}", f"<strong>{html.escape(d['mesej_butang'])}</strong>")

    return re.sub(r"\{\{(ms|en)\.(\w+)\}\}", isi, templat.read_text(encoding="utf-8")).encode()


class Aplikasi:
    """Keadaan dikongsi semua permintaan: bundel (baca-sahaja), token, stor, config."""

    def __init__(self, bundel: dict, token: dict[str, str], stor: Stor, k: dict):
        self.stor, self.k = stor, k
        self.token = [(p, t.encode()) for p, t in token.items() if t]
        self.dok = {"uji": bundel["uji"]}
        self._utama = bundel["dokumen"]
        self.pintu = bina_pintu()   # dibaca SEKALI semasa mula (kontena baca-sahaja; teks berubah = deploy)

    def senarai(self, penyemak: str) -> list[dict]:
        return self.dok.get(penyemak, self._utama)

    def penyemak(self, token: str) -> str | None:
        """Banding masa-tetap dengan SETIAP token (tiada pintasan awal)."""
        jumpa = None
        for p, t in self.token:
            if hmac.compare_digest(t, token.encode()):
                jumpa = p
        return jumpa

    def keadaan(self, penyemak: str, u: int | None = None) -> dict:
        senarai = self.senarai(penyemak)
        jaw = self.stor.jawapan(penyemak)
        bilangan_siap = sum(1 for d in senarai if siap(d, jaw.get(d["urutan"], {})))
        semasa = next((d["urutan"] for d in senarai if not siap(d, jaw.get(d["urutan"], {}))), None)
        lihat = u if u is not None and 1 <= u <= len(senarai) else semasa
        out = {"n": len(senarai), "siap": bilangan_siap, "semasa": semasa,
               "boleh_undur": self.stor.ada_ketikan(penyemak), "pilihan": self.k["pilihan"],
               "had_nilai_b": self.k["pelayan"]["had_nilai_b"], "dokumen": None}
        if lihat is not None:
            d = senarai[lihat - 1]
            j = jaw.get(lihat, {})
            out["dokumen"] = {"urutan": lihat, "teks": d["teks"], "spans": d["spans"], "jawapan": j, "siap": siap(d, j)}
        return out


class Pengendali(BaseHTTPRequestHandler):
    server_version = "mypii-iaa"
    sys_version = ""

    def __init__(self, app: Aplikasi, *a, **kw):
        self.app = app
        super().__init__(*a, **kw)

    def log_message(self, fmt, *args):   # token dalam laluan — jangan sekali-kali dilog
        pass

    def _hantar(self, kod: int, badan: bytes, jenis: str = "text/plain; charset=utf-8") -> None:
        self.send_response(kod)
        for k, v in KEPALA.items():
            self.send_header(k, v)
        self.send_header("Content-Type", jenis)
        self.send_header("Content-Length", str(len(badan)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(badan)

    def _json(self, kod: int, obj) -> None:
        self._hantar(kod, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _404(self) -> None:
        """GET/HEAD: badan pintu mesra (status kekal 404). POST: ringkas seperti asal (app.js tidak membaca badan 404)."""
        if self.command in ("GET", "HEAD"):
            return self._hantar(404, self.app.pintu, JENIS_STATIK[".html"])
        self._hantar(404, b"tiada / not found\n")

    def _token(self, bahagian: list[str]) -> str | None:
        return self.app.penyemak(bahagian[1]) if len(bahagian) >= 2 and bahagian[0] == "s" else None

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url = urlsplit(self.path)
        bahagian = url.path.strip("/").split("/")
        if url.path == "/":
            return self._hantar(200, self.app.pintu, JENIS_STATIK[".html"])
        if url.path == "/sihat":
            return self._hantar(200, b"ok\n")
        if url.path == "/robots.txt":
            return self._hantar(200, b"User-agent: *\nDisallow: /\n")
        if len(bahagian) == 2 and bahagian[0] == "statik" and (STATIK / bahagian[1]).suffix in JENIS_STATIK \
                and bahagian[1] in {f.name for f in STATIK.iterdir()} - TEMPLAT:
            f = STATIK / bahagian[1]
            return self._hantar(200, f.read_bytes(), JENIS_STATIK[f.suffix])
        if len(bahagian) == 2 and bahagian[0] == "teks" and bahagian[1] in {f.name for f in TEKS.glob("*.json")}:
            return self._hantar(200, (TEKS / bahagian[1]).read_bytes(), "application/json; charset=utf-8")
        p = self._token(bahagian)
        if p is None:
            return self._404()
        if len(bahagian) == 2:
            return self._hantar(200, (STATIK / "index.html").read_bytes(), JENIS_STATIK[".html"])
        if len(bahagian) == 3 and bahagian[2] == "keadaan":
            u = parse_qs(url.query).get("u", [""])[0]
            return self._json(200, self.app.keadaan(p, int(u) if u.isdigit() else None))
        return self._404()

    def do_POST(self):
        bahagian = urlsplit(self.path).path.strip("/").split("/")
        p = self._token(bahagian)
        if p is None or len(bahagian) != 3 or bahagian[2] not in ("jawab", "undur"):
            return self._404()
        try:
            panjang = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._json(400, {"ralat": "panjang"})
        if panjang > self.app.k["pelayan"]["had_badan"]:
            return self._json(413, {"ralat": "besar"})
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._json(415, {"ralat": "jenis"})   # borang rentas-tapak tidak boleh menghantar JSON tanpa preflight
        try:
            badan = json.loads(self.rfile.read(panjang) or b"{}")
        except ValueError:
            return self._json(400, {"ralat": "json"})
        if bahagian[2] == "undur":
            u = self.app.stor.undur(p)
            return self._json(200, self.app.keadaan(p, u))
        senarai = self.app.senarai(p)
        u = badan.get("urutan") if isinstance(badan, dict) else None
        if not isinstance(u, int) or not 1 <= u <= len(senarai) or not isinstance(badan.get("soalan"), str):
            return self._json(400, {"ralat": "urutan"})
        pl = self.app.k["pelayan"]
        try:
            nilai = sahkan(senarai[u - 1], badan["soalan"], badan.get("nilai"), self.app.k["pilihan"],
                           pl["had_nilai_b"], pl["had_aksara_b"])
        except NilaiTakSah as e:
            return self._json(400, {"ralat": str(e)})
        self.app.stor.simpan(p, u, badan["soalan"], nilai)
        return self._json(200, self.app.keadaan(p, u))


def bina_pelayan(app: Aplikasi, hos: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((hos, port), partial(Pengendali, app))


def muat(folder: Path, k: dict) -> Aplikasi:
    pk = k["pakej"]
    bundel = json.loads((folder / pk["bundel"]).read_text(encoding="utf-8"))
    token = json.loads((folder / pk["penyemak"]).read_text(encoding="utf-8"))
    return Aplikasi(bundel, token, Stor(folder / pk["stor"]), k)


def main(argv: list[str] | None = None) -> int:
    k = konfig.utama()["iaa"]
    ap = argparse.ArgumentParser(description="Pelayan halaman semakan IAA")
    ap.add_argument("--folder", type=Path,
                    default=Path(os.environ.get("MYPII_IAA_FOLDER", k["pakej"]["folder"])).expanduser())
    ap.add_argument("--port", type=int, default=k["pelayan"]["port"])
    a = ap.parse_args(argv)
    app = muat(a.folder, k)
    print(f"mypii-iaa: {k['pelayan']['hos']}:{a.port} penyemak={len(app.token)}", flush=True)
    bina_pelayan(app, k["pelayan"]["hos"], a.port).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
