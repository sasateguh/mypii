"""Ujian pelayar halaman semakan IAA — WebKit iPhone 13 + lebar 320 px (PELAN-IAA P4/P6, ADR-015).

Halaman pintu (PELAN-IAA-HALAMAN P2): `/` dan `/s/salah` (404 mesra) — tiada limpahan, BM + EN kelihatan, teks ≥ 16 px, tunggu
crash; PNG `<awalan>-pintu-{iphone,320}.png`. Hanya laluan TANPA token dibuka (tiada pautan penyemak sebenar disentuh).

Bukan `test_*`: pytest CI tidak mengutipnya (perlu WebKit + Playwright hos). Jalankan melalui kunci pelayar autopilot:

    ~/ops/autopilot/bin/ujian-pelayar.sh /usr/bin/python3 tests/pelayar/iaa_iphone.py            # tempatan, fixture DEV
    ~/ops/autopilot/bin/ujian-pelayar.sh /usr/bin/python3 tests/pelayar/iaa_iphone.py --url <pautan uji>   # P6 prod

Tempatan: bundel dibina dari dokumen `dev` di LUAR sampel IAA sahaja (tiada ujian2 dibaca), token rawak dalam folder
sementara, pelayan `python -m mypii.iaa.pelayan` dalam venv projek. Teks dokumen tidak pernah dicetak — kiraan sahaja.
Playwright = pakej pengguna hos (`~/.local`), jadi skrip ini TIDAK dijalankan dengan `-I` (ia mematikan site pengguna).
"""

import argparse
import json
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

AKAR = Path(__file__).resolve().parents[2]
UJI = {"dokumen": 4, "dijawab": 3, "tunggu_crash_s": 6, "sentuh_px": 48, "lebar_sempit": 320, "teks_min_px": 16}
PINTU = {"/": 200, "/s/salah": 404}   # laluan halaman pintu → status dijangka (badan sama)


class Gagal(AssertionError):
    pass


def semak(syarat: bool, mesej: str) -> None:
    if not syarat:
        raise Gagal(mesej)
    print(f"  ✓ {mesej}")


def bundel_dev(k: dict) -> dict:
    """Dokumen dev di luar sampel IAA: (n-1) berspan + 1 tanpa span, urutan id tetap. Hanya fail dev dibaca."""
    dalam = {d["id"] for d in json.loads((AKAR / k["sampel"]["fail"]).read_text(encoding="utf-8"))["dokumen"]}
    berspan, kosong = [], []
    with open(AKAR / k["sampel"]["split"]["dev"], encoding="utf-8") as f:
        for baris in f:
            if not baris.strip():
                continue
            r = json.loads(baris)
            if r["id"] in dalam:
                continue
            (berspan if r["spans"] else kosong).append(r)
    berspan.sort(key=lambda r: (-min(len(r["spans"]), 3), r["id"]))   # dokumen pertama ada beberapa span
    kosong.sort(key=lambda r: r["id"])
    pilih = berspan[:UJI["dokumen"] - 1] + kosong[:1]
    dok = [{"urutan": n, "id": r["id"], "split": "dev", "bahasa": r["bahasa"], "teks": r["teks"],
            "spans": [{"mula": s["mula"], "tamat": s["tamat"], "entiti": s["entiti"]}
                      for s in sorted(r["spans"], key=lambda s: s["mula"])]}
           for n, r in enumerate(pilih, 1)]
    return {"n": len(dok), "dokumen": dok, "uji": dok}


def port_bebas() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def mula_pelayan(folder: Path, k: dict) -> tuple[subprocess.Popen, str]:
    pk = k["pakej"]
    (folder / pk["bundel"]).write_text(json.dumps(bundel_dev(k), ensure_ascii=False), encoding="utf-8")
    token = secrets.token_urlsafe(k["pelayan"]["token_bait"])
    (folder / pk["penyemak"]).write_text(json.dumps({"uji": token}), encoding="utf-8")
    port = port_bebas()
    proses = subprocess.Popen(["uv", "run", "--quiet", "python", "-m", "mypii.iaa.pelayan", "--folder", str(folder),
                               "--port", str(port)], cwd=AKAR, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    asas = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            with urllib.request.urlopen(asas + "/sihat", timeout=1) as r:
                if r.status == 200:
                    return proses, f"{asas}/s/{token}"
        except OSError:
            if proses.poll() is not None:
                raise Gagal(f"pelayan keluar {proses.returncode}: {proses.stderr.read().decode()[-400:]}")
            time.sleep(0.2)
    raise Gagal("pelayan tidak menjawab /sihat")


def tiada_limpahan(page, nama: str) -> None:
    lebar = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
    semak(lebar[0] <= lebar[1], f"{nama}: tiada limpahan mendatar (scrollWidth {lebar[0]} ≤ clientWidth {lebar[1]})")


def butang_cukup_besar(page, nama: str) -> None:
    kecil = page.evaluate("""(had) => [...document.querySelectorAll('button')]
        .filter((b) => b.offsetParent !== null)
        .map((b) => b.getBoundingClientRect())
        .filter((r) => r.height < had || r.width < had)
        .map((r) => `${Math.round(r.width)}×${Math.round(r.height)}`)""", UJI["sentuh_px"])
    semak(not kecil, f"{nama}: setiap butang kelihatan ≥ {UJI['sentuh_px']} px {kecil or ''}".rstrip())


def tatal_penuh(page, nama: str) -> None:
    """Tatal ke bawah berperingkat; kandungan terakhir mesti berada di ATAS bar bawah yang melekat."""
    tinggi = page.evaluate("document.documentElement.scrollHeight")
    for y in range(0, tinggi + 400, 300):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(30)
    tiada_limpahan(page, f"{nama} selepas tatal")
    r = page.evaluate("""() => [document.querySelector('.privasi').getBoundingClientRect().bottom,
                                document.querySelector('.bawah').getBoundingClientRect().top]""")
    semak(r[0] <= r[1] + 0.5, f"{nama}: teks terakhir tidak dilindungi bar bawah ({r[0]:.0f} ≤ {r[1]:.0f})")
    page.evaluate("window.scrollTo(0, 0)")


def kemajuan(page) -> tuple[int, int]:
    return (int(page.get_attribute("#kemajuan", "aria-valuenow")), int(page.get_attribute("#kemajuan", "aria-valuemax")))


def no_dokumen(page) -> str:
    return page.text_content(".helaian-no")


def klik_simpan(page, locator) -> None:
    with page.expect_response(lambda r: r.request.method == "POST") as resp:
        locator.click()
    semak(resp.value.status == 200, f"POST {resp.value.url.rsplit('/', 1)[-1]} 200")
    page.wait_for_function("() => !document.querySelector('.hantar')")


def jawab_dokumen(page, guna_ada: bool) -> None:
    """(a) setiap span = pilihan pertama; (b) Tiada, atau Ada + satu baris; (c) pilihan pertama."""
    n_span = page.locator(".span-baris").count()
    for i in range(n_span):
        klik_simpan(page, page.locator(".span-baris").nth(i).locator(".pilihan").first)
    if guna_ada:
        page.locator(".segmen-b .pilihan").nth(1).click()
        semak(page.locator(".kotak-b").is_visible(), "(b) Ada membuka kotak teks")
        page.fill("#nilai-b", "012-345 6789")
        klik_simpan(page, page.locator(".butang-simpan"))
        semak(page.locator(".segmen-b .pilihan").nth(1).get_attribute("aria-pressed") == "true", "(b) Ada tersimpan")
    else:
        klik_simpan(page, page.locator(".segmen-b .pilihan").first)
    klik_simpan(page, page.locator(".segmen-c .pilihan").first)
    semak(page.is_enabled("#seterusnya"), f"dokumen siap ({n_span} span) → butang seterusnya aktif")


def semak_pintu(page, asas: str, nama: str, f: Path, langkah: dict) -> None:
    """`/` (200) dan `/s/salah` (404): badan pintu, kedua-dua bahasa kelihatan, teks ≥ had, tiada limpahan; PNG atas `/`."""
    for laluan, status in PINTU.items():
        resp = page.goto(asas + laluan, wait_until="networkidle")
        semak(resp.status == status, f"{nama} {laluan}: HTTP {resp.status}")
        semak(page.locator("body[data-pintu]").count() == 1, f"{nama} {laluan}: badan halaman pintu")
        for bahasa, tajuk in (("ms", "h1"), ("en", "h2")):
            kad = page.locator(f".pintu-kad[lang={bahasa}]")
            semak(kad.is_visible() and kad.locator(tajuk).is_visible() and bool(kad.locator(tajuk).text_content().strip()),
                  f"{nama} {laluan}: tajuk + kad {bahasa.upper()} kelihatan")
        kecil = page.evaluate("""(had) => [...document.querySelectorAll('.pintu-kad h1, .pintu-kad h2, .pintu-kad p')]
            .map((e) => parseFloat(getComputedStyle(e).fontSize)).filter((px) => px < had)""", UJI["teks_min_px"])
        semak(not kecil, f"{nama} {laluan}: semua teks ≥ {UJI['teks_min_px']} px {kecil or ''}".rstrip())
        tiada_limpahan(page, f"{nama} {laluan}")
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        tiada_limpahan(page, f"{nama} {laluan} selepas tatal")
        page.evaluate("window.scrollTo(0, 0)")
        if laluan == "/":
            langkah["nama"] = "tangkapan"
            page.screenshot(path=str(f), full_page=True, caret="initial")
            page.wait_for_timeout(200)   # mesej konsol tiba tak segerak
            langkah["nama"] = "halaman"
    page.wait_for_timeout(UJI["tunggu_crash_s"] * 1000)
    semak(page.evaluate("1 + 1") == 2, f"{nama}: halaman pintu masih hidup selepas {UJI['tunggu_crash_s']} s")


def jalan_pintu(asas: str, keluar: Path, awalan: str) -> list[str]:
    """iPhone 13 + 320 px atas halaman pintu. 404 dokumen utama `/s/salah` dijangka; ralat lain = GAGAL."""
    gambar, ralat, langkah = [], [], {"nama": "halaman"}
    with sync_playwright() as p:
        pelayar = p.webkit.launch()
        for nama, peranti in (("iphone", p.devices["iPhone 13"]),
                              (str(UJI["lebar_sempit"]), dict(p.devices["iPhone 13"],
                                                             viewport={"width": UJI["lebar_sempit"], "height": 640}))):
            ctx = pelayar.new_context(**peranti)
            page = ctx.new_page()
            page.on("console", lambda m: m.type == "error" and ralat.append((langkah["nama"], f"konsol: {m.text}")))
            page.on("pageerror", lambda e: ralat.append((langkah["nama"], f"halaman: {e}")))
            page.on("crash", lambda *_: ralat.append((langkah["nama"], "WebKit CRASH")))
            f = keluar / f"{awalan}-pintu-{nama}.png"
            semak_pintu(page, asas, f"pintu {nama}", f, langkah)
            gambar.append(f.name)
            ctx.close()
        pelayar.close()
    # Dua kecualian SEMPIT, dikira dan dicetak: 404 dokumen utama `/s/salah` (memang dijangka), dan penolakan CSP atas <style>
    # yang Playwright suntik HANYA semasa tangkapan skrin (corak sama `jalan`). Ralat lain = GAGAL.
    dijangka = [t for l, t in ralat if l == "halaman" and "Failed to load resource" in t and "404" in t]
    alat = [t for l, t in ralat if l == "tangkapan" and "Refused to apply a stylesheet" in t]
    lain = [f"[{l}] {t}" for l, t in ralat if t not in dijangka and t not in alat]
    print(f"  · pintu: 404 dokumen utama /s/salah dilog konsol: {len(dijangka)} (dijangka); "
          f"penolakan CSP <style> tangkapan Playwright: {len(alat)} (dikecualikan)")
    semak(not lain, f"pintu: tiada ralat konsol/halaman/crash {lain or ''}".rstrip())
    return gambar


def jalan(url: str, keluar: Path, awalan: str) -> list[str]:
    gambar, ralat = [], []
    langkah = {"nama": "halaman"}

    def tangkap(page, f: Path) -> None:
        langkah["nama"] = "tangkapan"
        page.screenshot(path=str(f), full_page=True, caret="initial")
        page.wait_for_timeout(200)   # mesej konsol tiba tak segerak
        langkah["nama"] = "halaman"

    with sync_playwright() as p:
        pelayar = p.webkit.launch()
        ctx = pelayar.new_context(**p.devices["iPhone 13"])
        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and ralat.append((langkah["nama"], f"konsol: {m.text}")))
        page.on("pageerror", lambda e: ralat.append((langkah["nama"], f"halaman: {e}")))
        page.on("crash", lambda *_: ralat.append((langkah["nama"], "WebKit CRASH")))
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector(".helaian")
        siap0, n = kemajuan(page)
        semak(n >= UJI["dijawab"] + 1, f"dimuat: {siap0}/{n} siap")
        semak(not page.is_enabled("#seterusnya"), "seterusnya tidak aktif sebelum dijawab")
        tiada_limpahan(page, "iPhone 13 awal")
        butang_cukup_besar(page, "iPhone 13")

        for i in range(UJI["dijawab"]):
            sebelum = no_dokumen(page)
            jawab_dokumen(page, guna_ada=(i == 1))
            if i == 0:
                tatal_penuh(page, "iPhone 13 dokumen dijawab")
                f = keluar / f"{awalan}-bm.png"
                tangkap(page, f)
                gambar.append(f.name)
            page.click("#seterusnya")
            page.wait_for_function(f"() => document.querySelector('.helaian-no')?.textContent !== {json.dumps(sebelum)}")
        siap1 = kemajuan(page)[0]
        semak(siap1 == siap0 + UJI["dijawab"], f"kemajuan {siap1}/{n} selepas {UJI['dijawab']} dokumen")

        semasa = no_dokumen(page)
        page.reload(wait_until="networkidle")
        page.wait_for_selector(".helaian")
        semak(kemajuan(page)[0] == siap1 and no_dokumen(page) == semasa, "muat semula → sambung di dokumen sama")

        klik_simpan(page, page.locator(".segmen-c .pilihan").first)
        semak(page.locator(".segmen-c [aria-pressed=true]").count() == 1, "(c) dijawab pada dokumen semasa")
        with page.expect_response(lambda r: r.url.endswith("/undur")) as resp:
            page.click("#undur")
        semak(resp.value.status == 200, "POST undur 200")
        page.wait_for_function("() => document.querySelectorAll('.segmen-c [aria-pressed=true]').length === 0")
        semak(no_dokumen(page) == semasa and kemajuan(page)[0] == siap1, "undur memadam jawapan terakhir sahaja")
        f = keluar / f"{awalan}-undur.png"
        tangkap(page, f)
        gambar.append(f.name)

        judul_bm, status_bm = page.text_content(".judul"), page.text_content("#status")
        semak(bool(status_bm), "status undur dipapar")
        page.click("#bahasa")
        page.wait_for_function("() => document.documentElement.lang === 'en'")
        semak(page.text_content(".judul") != judul_bm, "tukar ke EN: tajuk + teks bertukar")
        semak(page.text_content("#status") not in ("", status_bm), "tukar ke EN: baris status turut diterjemah")
        tiada_limpahan(page, "iPhone 13 EN")
        butang_cukup_besar(page, "iPhone 13 EN")
        tatal_penuh(page, "iPhone 13 EN")
        f = keluar / f"{awalan}-en.png"
        tangkap(page, f)
        gambar.append(f.name)
        page.reload(wait_until="networkidle")
        page.wait_for_selector(".helaian")
        semak(page.evaluate("document.documentElement.lang") == "en", "pilihan bahasa kekal selepas muat semula")
        page.click("#bahasa")
        page.wait_for_function("() => document.documentElement.lang === 'ms'")

        page.wait_for_timeout(UJI["tunggu_crash_s"] * 1000)
        semak(page.evaluate("1 + 1") == 2, f"halaman masih hidup selepas {UJI['tunggu_crash_s']} s (crash lambat WebKit)")
        ctx.close()

        sempit = dict(p.devices["iPhone 13"], viewport={"width": UJI["lebar_sempit"], "height": 640})
        ctx = pelayar.new_context(**sempit)
        page = ctx.new_page()
        page.on("pageerror", lambda e: ralat.append(("halaman", f"halaman 320: {e}")))
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector(".helaian")
        for b in ("ms", "en"):
            if page.evaluate("document.documentElement.lang") != b:
                page.click("#bahasa")
                page.wait_for_function(f"() => document.documentElement.lang === '{b}'")
            tiada_limpahan(page, f"{UJI['lebar_sempit']} px {b}")
            butang_cukup_besar(page, f"{UJI['lebar_sempit']} px {b}")
            tatal_penuh(page, f"{UJI['lebar_sempit']} px {b}")
        page.click("#bahasa")   # pulangkan ms untuk larian seterusnya
        ctx.close()
        pelayar.close()
    # Tangkapan skrin Playwright menyuntik <style> sendiri; CSP halaman (betul) menolaknya. HANYA penolakan stylesheet semasa
    # tangkapan dikecualikan — dikira dan dicetak, bukan disembunyikan. Ralat lain pada bila-bila masa = GAGAL.
    alat = [t for l, t in ralat if l == "tangkapan" and "Refused to apply a stylesheet" in t]
    lain = [f"[{l}] {t}" for l, t in ralat if not (l == "tangkapan" and "Refused to apply a stylesheet" in t)]
    print(f"  · penolakan CSP atas <style> suntikan tangkapan skrin Playwright: {len(alat)} (dikecualikan)")
    semak(not lain, f"tiada ralat konsol/halaman/crash {lain or ''}".rstrip())
    return gambar


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WebKit iPhone 13 — halaman semakan IAA")
    ap.add_argument("--url", help="pautan penyemak `uji` (prod, P6); tanpa = pelayan tempatan atas fixture dev")
    ap.add_argument("--keluar", type=Path, default=Path("~/portal/uploads").expanduser())
    ap.add_argument("--awalan", default=None, help="awalan nama PNG (lalai mypii-iaa / mypii-iaa-prod)")
    ap.add_argument("--pintu", action="store_true", help="halaman pintu sahaja (`/` + `/s/salah`), aliran semakan dilangkau")
    a = ap.parse_args(argv)
    k = yaml.safe_load((AKAR / "config/mypii.yaml").read_text(encoding="utf-8"))["iaa"]
    awalan = a.awalan or ("mypii-iaa-prod" if a.url else "mypii-iaa")
    a.keluar.mkdir(parents=True, exist_ok=True)
    folder, proses = None, None
    try:
        if a.url:
            url = a.url
        else:
            folder = Path(tempfile.mkdtemp(prefix="mypii-iaa-uji-"))
            proses, url = mula_pelayan(folder, k)
        gambar = jalan_pintu(url.split("/s/", 1)[0], a.keluar, awalan)
        if not a.pintu:
            gambar += jalan(url, a.keluar, awalan)
    except Gagal as e:
        print(f"GAGAL: {e}", file=sys.stderr)
        return 1
    finally:
        if proses:
            proses.terminate()
            proses.wait(timeout=10)
        if folder:
            shutil.rmtree(folder, ignore_errors=True)
    print(f"LULUS: {len(gambar)} PNG → {a.keluar}: {' '.join(gambar)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
