"""Pelayan semakan IAA (PELAN-IAA P3, ADR-015): token, GET tanpa kesan, simpan/sambung/undur, kepala, teks, statik."""

import ast
import html
import http.client
import json
import re
import threading
from pathlib import Path

import pytest

from mypii import konfig
from mypii.iaa import pelayan, stor

IAA = Path(pelayan.__file__).resolve().parent
TOKEN = "t" * 30     # < 40 aksara (gerbang §13)
K = konfig.utama()["iaa"]


def _bundel():
    dok = [{"urutan": n, "id": f"rahsia-id-{n}", "split": "ujian2", "bahasa": "ms",
            "teks": f"Tel 012-3456789 SSM 202001012345 dok {n}",
            "spans": [{"mula": 4, "tamat": 15, "entiti": "MY_PHONE"}, {"mula": 20, "tamat": 32, "entiti": "MY_SSM"}]}
           for n in range(1, 4)]
    uji = [{"urutan": 1, "id": "dev-x", "split": "dev", "bahasa": "en", "teks": "no pii", "spans": []}]
    return {"n": 3, "dokumen": dok, "uji": uji}


class Hidup:
    def __init__(self, folder: Path):
        self.app = pelayan.Aplikasi(_bundel(), {"p1": TOKEN, "uji": "u" * 30}, stor.Stor(folder / "j.sqlite"), K)
        self.srv = pelayan.bina_pelayan(self.app, "127.0.0.1", 0)
        self.th = threading.Thread(target=self.srv.serve_forever, args=(0.05,), daemon=True)
        self.th.start()

    def minta(self, kaedah, laluan, badan=None, kepala=None):
        c = http.client.HTTPConnection(*self.srv.server_address, timeout=5)
        data = json.dumps(badan).encode() if badan is not None else None
        h = {"Content-Type": "application/json"} if data is not None else {}
        c.request(kaedah, laluan, body=data, headers={**h, **(kepala or {})})
        r = c.getresponse()
        return r.status, dict(r.getheaders()), r.read()

    def tutup(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.app.stor.tutup()


@pytest.fixture
def h(tmp_path):
    x = Hidup(tmp_path)
    yield x
    x.tutup()


def _jawab_penuh(h, u):
    for s, v in (("a1", "betul"), ("a2", "salah"), ("b", {"pilih": "tiada"}), ("c", "ya")):
        kod, _, b = h.minta("POST", f"/s/{TOKEN}/jawab", {"urutan": u, "soalan": s, "nilai": v})
        assert kod == 200, b
    return json.loads(b)


def test_token_salah_404_sama(h):
    a = h.minta("GET", "/s/" + "x" * 30)
    b = h.minta("GET", "/tiada/langsung")
    c = h.minta("GET", "/s/" + "x" * 30 + "/keadaan")
    d = h.minta("POST", "/s/" + "x" * 30 + "/jawab", {"urutan": 1, "soalan": "c", "nilai": "ya"})
    assert a[0] == b[0] == c[0] == d[0] == 404 and a[2] == b[2] == c[2]   # GET: badan pintu sama
    assert d[2] == b"tiada / not found\n"                                  # POST 404 tidak berubah
    assert not h.app.stor.ada_ketikan("p1")


def test_kepala_tepat(h):
    for laluan in ("/", f"/s/{TOKEN}", f"/s/{TOKEN}/keadaan", "/sihat", "/robots.txt", "/statik/app.css", "/s/salah",
                   "/statik/pintu.css", "/s/"):
        _, kp, _ = h.minta("GET", laluan)
        assert kp["Content-Security-Policy"].startswith("default-src 'self'")
        assert kp["X-Robots-Tag"] == "noindex, nofollow"
        assert kp["Cache-Control"] == "no-store, no-transform"
        assert kp["Referrer-Policy"] == "no-referrer"
        assert kp["X-Content-Type-Options"] == "nosniff" and kp["X-Frame-Options"] == "DENY"
    assert h.minta("GET", "/robots.txt")[2] == b"User-agent: *\nDisallow: /\n"
    assert h.minta("GET", "/sihat")[:1] == (200,)


def test_get_tidak_menulis_dan_tiada_id_split(h):
    for laluan in (f"/s/{TOKEN}", f"/s/{TOKEN}/keadaan", f"/s/{TOKEN}/keadaan?u=2", f"/s/{TOKEN}/jawab",
                   f"/s/{TOKEN}/undur"):
        h.minta("GET", laluan)
    assert not h.app.stor.ada_ketikan("p1")
    _, _, b = h.minta("GET", f"/s/{TOKEN}/keadaan?u=2")
    assert b"rahsia-id" not in b and b"ujian2" not in b and b'"split"' not in b
    k = json.loads(b)
    assert k["n"] == 3 and k["siap"] == 0 and k["semasa"] == 1 and k["dokumen"]["urutan"] == 2


def test_simpan_sambung_selepas_mula_semula(tmp_path):
    a = Hidup(tmp_path)
    k = _jawab_penuh(a, 1)
    assert k["siap"] == 1 and k["semasa"] == 2 and k["dokumen"]["siap"] is True
    a.minta("POST", f"/s/{TOKEN}/jawab", {"urutan": 2, "soalan": "c", "nilai": "janggal"})
    a.tutup()
    b = Hidup(tmp_path)
    try:
        k = json.loads(b.minta("GET", f"/s/{TOKEN}/keadaan")[2])
        assert k["siap"] == 1 and k["semasa"] == 2 and k["dokumen"]["jawapan"] == {"c": "janggal"}
    finally:
        b.tutup()


def test_undur_jawapan_terakhir(h):
    _jawab_penuh(h, 1)
    h.minta("POST", f"/s/{TOKEN}/jawab", {"urutan": 1, "soalan": "c", "nilai": "janggal"})
    k = json.loads(h.minta("POST", f"/s/{TOKEN}/undur", {})[2])
    assert k["dokumen"]["urutan"] == 1 and k["dokumen"]["jawapan"]["c"] == "ya"   # nilai sebelumnya kembali
    k = json.loads(h.minta("POST", f"/s/{TOKEN}/undur", {})[2])
    assert "c" not in k["dokumen"]["jawapan"] and k["siap"] == 0 and k["semasa"] == 1
    for _ in range(3):
        h.minta("POST", f"/s/{TOKEN}/undur", {})
    k = json.loads(h.minta("POST", f"/s/{TOKEN}/undur", {})[2])
    assert k["boleh_undur"] is False and k["dokumen"]["urutan"] == 1


def test_kemajuan_hingga_tamat(h):
    for u in (1, 2, 3):
        k = _jawab_penuh(h, u)
    assert (k["siap"], k["n"], k["semasa"]) == (3, 3, None)
    assert json.loads(h.minta("GET", f"/s/{TOKEN}/keadaan")[2])["dokumen"] is None


def test_penyemak_uji_dokumen_sendiri(h):
    k = json.loads(h.minta("GET", "/s/" + "u" * 30 + "/keadaan")[2])
    assert k["n"] == 1 and k["dokumen"]["teks"] == "no pii"


@pytest.mark.parametrize("badan,kod", [
    ({"urutan": 9, "soalan": "c", "nilai": "ya"}, 400),
    ({"urutan": 1, "soalan": "a3", "nilai": "betul"}, 400),
    ({"urutan": 1, "soalan": "a01", "nilai": "betul"}, 400),
    ({"urutan": 1, "soalan": "a1", "nilai": "mungkin"}, 400),
    ({"urutan": 1, "soalan": "b", "nilai": {"pilih": "ada", "nilai": []}}, 400),
    ({"urutan": 1, "soalan": "b", "nilai": {"pilih": "ada", "nilai": ["9" * 41]}}, 400),
    ({"urutan": 1, "soalan": "z", "nilai": "ya"}, 400),
    ({"urutan": "1", "soalan": "c", "nilai": "ya"}, 400),
])
def test_nilai_tak_sah_ditolak(h, badan, kod):
    assert h.minta("POST", f"/s/{TOKEN}/jawab", badan)[0] == kod
    assert not h.app.stor.ada_ketikan("p1")


def test_b_ada_dinormal(h):
    k = json.loads(h.minta("POST", f"/s/{TOKEN}/jawab",
                           {"urutan": 1, "soalan": "b", "nilai": {"pilih": "ada", "nilai": [" 0123 ", "", "x"]}})[2])
    assert k["dokumen"]["jawapan"]["b"] == {"pilih": "ada", "nilai": ["0123", "x"]}


def test_had_badan_dan_jenis(h):
    besar = {"urutan": 1, "soalan": "c", "nilai": "y" * (K["pelayan"]["had_badan"] + 1)}
    assert h.minta("POST", f"/s/{TOKEN}/jawab", besar)[0] == 413
    assert h.minta("POST", f"/s/{TOKEN}/jawab", {"urutan": 1, "soalan": "c", "nilai": "ya"},
                   {"Content-Type": "text/plain"})[0] == 415
    assert not h.app.stor.ada_ketikan("p1")


def test_statik_dan_teks(h):
    assert h.minta("GET", "/statik/app.js")[0] == 200
    assert h.minta("GET", "/statik/../pelayan.py")[0] == 404
    assert h.minta("GET", "/statik/tiada.js")[0] == 404
    kod, kp, b = h.minta("GET", "/teks/en.json")
    assert kod == 200 and kp["Content-Type"].startswith("application/json") and json.loads(b)["bahasa"] == "en"
    assert h.minta("GET", "/teks/../../config.json")[0] == 404


def _kunci(o, awal=""):
    if isinstance(o, dict):
        return {x for kk, v in o.items() for x in _kunci(v, f"{awal}{kk}.")} | {awal + kk for kk in o}
    return set()


def test_pariti_teks_ms_en():
    ms, en = (json.loads((IAA / "teks" / f"{b}.json").read_text()) for b in ("ms", "en"))
    assert _kunci(ms) == _kunci(en)
    for p, v in K["pilihan"].items():
        assert set(ms[f"pilih_{p}"]) == set(v)
    html = (IAA / "statik" / "index.html").read_text()
    assert set(re.findall(r'data-t="(\w+)"', html)) <= set(ms)


def test_statik_tiada_url_luar_dan_tiada_innerhtml():
    for f in (IAA / "statik").iterdir():
        teks = f.read_text()
        assert not re.search(r"https?://", teks), f.name
        assert "innerHTML" not in teks and "insertAdjacentHTML" not in teks, f.name


def test_tiada_import_terlarang():
    for f in IAA.glob("*.py"):
        for n in ast.walk(ast.parse(f.read_text())):
            nama = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                [n.module or ""] if isinstance(n, ast.ImportFrom) else []
            for m in nama:
                assert not re.match(r"(mypii\.(pengecam|nilai\.garis)|harness|presidio)", m), (f.name, m)


# --- Halaman pintu `/` + 404 mesra (PELAN-IAA-HALAMAN P1, ADR-015 §Halaman pintu) ---

def test_pintu_akar_200_dwibahasa_tanpa_rahsia(h):
    kod, kp, b = h.minta("GET", "/")
    assert kod == 200 and kp["Content-Type"] == "text/html; charset=utf-8"
    teks = b.decode()
    assert "data-pintu" in teks and 'lang="ms"' in teks and 'lang="en"' in teks
    for bahasa in ("ms", "en"):
        t = json.loads((IAA / "teks" / f"{bahasa}.json").read_text())
        assert html.escape(t["pintu_utama"]) in teks and html.escape(t["judul"]) in teks
        assert f"<strong>{html.escape(t['mesej_butang'])}</strong>" in teks
    for larang in (TOKEN, "u" * 30, "/s/", "http", "rahsia-id", "p1", "{{", "{butang}", "<script"):
        assert larang not in teks, larang


@pytest.mark.parametrize("laluan", ["/s/", "/s", "/s/salah", "/s/" + "x" * 30, "/xyz", "/s/" + "x" * 30 + "/keadaan",
                                    f"/s/{TOKEN}/tiada", "/statik/pintu.html", "/index.html"])
def test_404_badan_pintu_sama_dengan_akar(h, laluan):
    _, _, akar = h.minta("GET", "/")
    kod, kp, b = h.minta("GET", laluan)
    assert kod == 404 and b == akar and kp["Content-Type"] == "text/html; charset=utf-8"
    kod, kp_head, b_head = h.minta("HEAD", laluan)
    assert kod == 404 and b_head == b"" and kp_head["Content-Length"] == str(len(akar))
    assert kp_head["X-Robots-Tag"] == "noindex, nofollow" and kp_head["Content-Security-Policy"].startswith("default-src 'self'")


def test_head_akar_tanpa_badan(h):
    kod, kp, b = h.minta("HEAD", "/")
    assert kod == 200 and b == b"" and int(kp["Content-Length"]) > 0


def test_token_betul_masih_halaman_semakan(h):
    kod, _, b = h.minta("GET", f"/s/{TOKEN}")
    assert kod == 200 and b == (IAA / "statik" / "index.html").read_bytes()
    assert h.minta("GET", "/statik/pintu.css")[0] == 200


def test_pintu_escape_teks(tmp_path):
    for bahasa in ("ms", "en"):
        t = json.loads((IAA / "teks" / f"{bahasa}.json").read_text())
        t["pintu_utama"] = "<script>x</script> & {butang}"
        t["mesej_butang"] = "<b>"
        (tmp_path / f"{bahasa}.json").write_text(json.dumps(t))
    b = pelayan.bina_pintu(teks=tmp_path).decode()
    assert "<script>" not in b and "<b>" not in b
    assert "&lt;script&gt;x&lt;/script&gt; &amp; <strong>&lt;b&gt;</strong>" in b


def test_pintu_kunci_ada_dalam_teks():
    templat = (IAA / "statik" / "pintu.html").read_text()
    kunci = set(re.findall(r"\{\{(?:ms|en)\.(\w+)\}\}", templat))
    assert kunci and "pintu_utama" in kunci
    for bahasa in ("ms", "en"):
        t = json.loads((IAA / "teks" / f"{bahasa}.json").read_text())
        assert kunci | {"mesej_butang"} <= set(t)
        assert all("{butang}" not in t[k] for k in t if isinstance(t[k], str) and k != "pintu_langkah" and not k.startswith("mesej_"))
