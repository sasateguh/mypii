# ADR-015: Semakan label manusia (IAA) — protokol, halaman sendiri, penyemak sandaran LLM (PELAN-IAA, 31 Okt 2026)

**Masalah.** PRD §2.2 menjanjikan "300 contoh disemak dua orang … kappa/F1 persetujuan dilapor", dan M4 membenarkan "Aiman × LLM
berlainan" sebagai had kajian bila tiada penyemak manusia kedua. Label MyPII-Bench dijana kod (dev) dan LLM (`ujian2`); belum ada
sesiapa menyemak sama ada label emas betul atau teksnya terasa Malaysia sebenar. `ujian2` dimeterai dan pengecam BEKU, jadi semakan
mesti tidak mengubah apa-apa yang diukur oleh pra-daftar.

**Keputusan.**
- **Protokol dahulu.** Pindaan bertarikh `docs/PRA-DAFTAR.md` "2026-10-31 — IAA semakan label manusia (sebelum ujian dibuka)" ditambah
  di HUJUNG fail (gerbang §10 tambah-sahaja) dan dikomit SENDIRI tanpa kod (gerbang §11) — sebelum sampel, halaman atau jawapan.
  Pindaan IAA selepas anotasi pertama dikomit = dilarang; pembatalan = pindaan bertarikh baharu.
- **Sampel.** 300 = 150 `dev` + 150 `ujian2`; strata bahasa (ms/en/manglish) × berspan/negatif, 25 setiap sel; benih `iaa.sampel.benih`.
  Kiraan strata sebelum pindaan (kiraan sahaja, tiada teks): dev en 150/137 · manglish 162/157 · ms 186/208; ujian2 en 124/150 ·
  manglish 144/157 · ms 219/206 (berspan/negatif) — setiap sel ≥ 25.
  Pelaksanaan (P2): `mypii/iaa/sampel.py` — `random.Random(benih)` tunggal, strata dilawati ikut urutan config (split → bahasa →
  berspan, negatif), `rng.sample` atas id TERISIH, kemudian `rng.shuffle` seluruh senarai; `data/iaa/sampel.json` dikomit (sha256 dalam LOG).
- **Buta split:** urutan dikocok (benih sama) merentas dev/ujian2; halaman tidak memaparkan split atau id.
  Pelaksanaan (P3): `pakej.py` menyimpan id/split dalam bundel (untuk eksport) tetapi `pelayan.keadaan` hanya menghantar urutan, teks,
  span emas dan jawapan; ujian `test_get_tidak_menulis_dan_tiada_id_split` mengunci ini. Bundel ditulis di LUAR repo sahaja (`--keluar`
  dalam repo = exit 2). Penyemak `uji` = `iaa.uji.dokumen` dokumen dev di luar sampel (`random.Random(benih)` atas id terisih).
- **Stor + halaman (P3).** SQLite satu baris SETIAP ketikan (log tambah); jawapan semasa = baris terakhir setiap (penyemak, urutan, soalan);
  undur = padam baris terakhir penyemak itu, jadi nilai sebelumnya kembali (undur berbilang langkah, merentas dokumen). Soalan `a<n>`
  (span ke-n, 1-indeks) · `b` (`{pilih, nilai[]}`, 1–`had_nilai_b` baris ≤ `had_aksara_b` aksara) · `c`; disahkan pelayan sebelum simpan.
  Dokumen semasa = pertama yang belum siap; butang "Dokumen seterusnya" hanya aktif bila siap (tiada auto-lompat yang mengejutkan).
  POST mesti `Content-Type: application/json` (borang rentas-tapak = 415) + had badan; token dibanding `hmac.compare_digest` dengan
  SETIAP token; `log_message` dimatikan (token dalam laluan). Halaman: fon sistem, teks dokumen serif (rupa helaian), span ditanda
  seperti pen penyerlah ikut jenis (MyKad biru, SSM kuning, telefon hijau) bernombor; teks dimasukkan sebagai nod teks sahaja.
- **Soalan:** (a) setiap span emas `Betul` / `Salah` (bukan PII ini) / `Jenis lain`; (b) "Ada MyKad/SSM/telefon yang TIDAK bertanda?"
  `Tiada` / `Ada` → kotak teks (satu nilai setiap baris); (c) "Teks terasa Malaysia sebenar?" `Ya` / `Janggal`. Dokumen siap bila
  (a) semua span + (b) + (c) dijawab. Pilihan = `iaa.pilihan`.
- **Persetujuan:** κ Cohen (a) per span, (c) per dokumen; % persetujuan mentah dilapor bersama (paradoks κ bila `Betul` dominan).
  (b): nilai dinormalkan (MyKad/telefon = digit sahaja; SSM = alnum huruf besar), F1 persetujuan = 2|A∩B| / (|A|+|B|) mikro atas
  dokumen; bilangan dokumen kedua-duanya `Tiada` dilapor berasingan. CI 95% bootstrap persentil atas dokumen
  (`statistik.indeks_bootstrap`/`persentil`; B dan benih = `nilai.statistik`).
- **Kadar ralat label** (setiap penyemak × split): span `Salah`+`Jenis lain` / span; dokumen dengan ≥ 1 PII tidak bertanda / dokumen;
  dokumen `Janggal` / dokumen; beza dev − ujian2 dengan CI. Deskriptif — tiada ujian hipotesis.
- **Pasangan:** p1×llm sentiasa; p1×p2 bila p2 wujud (UTAMA bila ada); hanya dokumen SIAP oleh kedua-dua pihak (`iaa.skor.pasangan`).
- **Penyemak sandaran LLM** `cbcn/glm-5.3` (Zhipu): berlainan keluarga dari penjana `ujian2` `cbcn/kimi-k3`, penjana latih/dev
  `ag/gemini-3.8-flash`, garis dasar Llama/DeepSeek; sandaran glm penjana ujian2 tidak pernah dipakai (LOG B1b). Suhu 0, prompt
  `iaa.llm.prompt`, TIADA model sandaran (gagal berulang = berhenti, pemilik memilih), cache `hasil/cache/iaa/cbcn_glm-5.3.jsonl` dikomit.
- **Tiada ramalan sistem** dipapar atau dihantar: `mypii/iaa/` tidak mengimport `mypii.pengecam`, `mypii.nilai.garis`, `harness` atau
  presidio (gerbang §12). Ralat `ujian2` = hingar label dilapor, TIDAK dibaiki; tiada dokumen dikecualikan/dijana semula.
- **Halaman sendiri** (Python stdlib `ThreadingHTTPServer` + SQLite, ≈ 600 baris): pautan bertoken `/s/<token>` setiap penyemak
  (`secrets.token_urlsafe`, banding `hmac.compare_digest`, token salah = 404 sama seperti laluan tiada), GET tanpa kesan sampingan
  (pratonton pautan Telegram), setiap jawapan disimpan serta-merta, sambung, undur jawapan terakhir, x/300, BM + EN dari fail bahasa,
  tiada skrip/fon/analitik pihak ketiga (gerbang §14). Kepala: CSP `default-src 'self'`, `X-Robots-Tag: noindex, nofollow`,
  `Cache-Control: no-store, no-transform`, `Referrer-Policy: no-referrer`, nosniff, frame-deny; had badan POST `iaa.pelayan.had_badan`.
- **Hos:** kontena `mypii-iaa` (rangkaian `coolify`, read-only, tmpfs, cap-drop ALL, had memori); data `~/ops/mypii/iaa/` (SQLite
  `journal_mode=DELETE` supaya backup harian ~/ops konsisten; bundel baca-sahaja; `penyemak.json` 0600, tidak pernah dikomit/dilog);
  traefik satu fail `deploy/iaa/semak-mypii.traefik.yaml` → `coolify-proxy:/traefik/dynamic/` dengan `compress: {}`; nama
  `semak-mypii.sasateguh.com` Cloudflare oren (kandungan sintetik; `no-store, no-transform` = CF tidak menyimpan/menyuntik beacon).
  Rekod DNS (P6, 31 Okt 2026): `A semak-mypii` → IP hos, proksi oren, zon `sasateguh.com` id `aeab7172c8ca6a897b6030578f69e06e`,
  rekod id `a1b5a3a87351fc25e24a4c41e3e9001f` (akaun CF label `sasateguh`; komen rekod "mypii IAA PELAN-IAA P6 (ADR-015)").
  Deploy pertama = tiada imej undur (`mypii-iaa-undur` diisi pada deploy kedua); undur pertama = tutup terus (lihat Undur).
- **Penyemak LLM + eksport (P7).** `mypii/iaa/llm.py` membaca BUNDEL yang sama dengan halaman (sha256 sampel mesti sepadan), prompt =
  `iaa.llm.prompt` + span emas bernombor; jawapan mentah dicache (kunci sha256 model+prompt penuh) SEBELUM diurai. Urai ketat: bilangan
  span tepat, nilai dalam `iaa.pilihan`; selain itu = `rosak` (kekal dalam output, dikira — tidak diulang dengan prompt lain, tidak
  dibuang). Panggilan gagal = `gagal`, tidak dicache (larian semula mencuba lagi). Eksport manusia (`eksport.py`) dan LLM menulis bentuk
  SATU: `{urutan, status: siap|separa|rosak|gagal, jawapan: {a<n>, b: {pilih, nilai?}, c} | null}`, tanpa token/id/split (skor menyambung
  urutan dengan `sampel.json`). `skor` (P9) memakai `status == siap` sahaja. Nilai (b) disimpan mentah (strip); normalisasi di `skor`.
- **Larian LLM (P8, 31 Okt 2026).** 300/300 siap, rosak 0, gagal 0 dalam satu larian (serentak 2); cache + `llm.jsonl` dikomit dan dihasilkan semula tanpa kunci (bait sama). Cache = rekod kekal: jangan jalankan semula dengan prompt/model lain tanpa pindaan PRA-DAFTAR (kunci cache berubah = larian baharu).
- **Penyemak `uji`** (dev SAHAJA, dokumen dev di LUAR sampel, `iaa.uji.dokumen`) untuk ujian pelayar hidup — pembina tidak melihat ujian2.
- **Ujian pelayar (P4).** `tests/pelayar/iaa_iphone.py` (bukan `test_*`: perlu WebKit + Playwright hos, tidak dikutip pytest CI) melalui
  `~/ops/autopilot/bin/ujian-pelayar.sh /usr/bin/python3 tests/pelayar/iaa_iphone.py [--url <pautan uji>]`. Tempatan: bundel dibina dari
  dokumen dev di LUAR sampel sahaja + token rawak dalam folder sementara + `python -m mypii.iaa.pelayan` dalam venv; `--url` = P6 prod.
  Tidak dijalankan dengan `python3 -I` (seperti PELAN) kerana `-I` mematikan site pengguna tempat Playwright hos dipasang. Penolakan CSP
  atas `<style>` yang disuntik `page.screenshot` sendiri dikecualikan HANYA semasa tangkapan (dikira + dicetak); ralat lain = GAGAL.
  Dapatan yang dibaiki: butang bahasa 40 px → `--sentuh` 48 px; baris status kekal BM selepas tukar ke EN (kini kunci teks, ditulis semula).
- **Kontena (P5).** `deploy/iaa/Dockerfile`: `python:3.12-slim` + `pyyaml==6.0.3` (versi uv.lock; tiada kebergantungan baharu),
  pengguna bukan root, `HEALTHCHECK` = `python -m mypii.iaa.operasi sihat` (port dari config, bukan terkod). Imej menyalin HANYA
  `config/mypii.yaml`, `mypii/konfig.py`, `mypii/iaa/` — TANPA `mypii/__init__.py`, jadi `mypii` ialah pakej ruang nama dan
  `from mypii import konfig` tidak menarik `mypii.pengecam`/presidio (diuji `tests/test_iaa_operasi.py` dengan `python -I -S` atas
  susun atur imej). `.dockerignore` = senarai benar (`*` + empat laluan) supaya `.env`/`data/`/`hasil/`/`.venv` tidak sampai ke Depot.
  `deploy/iaa/deploy.sh` (corak bayarkit): bina `git archive origin/main | ~/bin/bina-imej.sh`; `docker run --user <uid hos>` (fail
  data milik `claude`), read-only + tmpfs + cap-drop ALL + 192 MB; `~/ops/mypii/iaa` → `/data` (rw untuk SQLite) + `dokumen.json` bind
  `:ro`; pengesahan awam `/sihat` + robots + token rawak = 404 diulang 4 × 10 s sebelum undur. Token penyemak dimuat semasa kontena
  mula → `--penyemak tambah` = `docker exec … operasi penyemak tambah` (tulis atomik 0600, id wujud = ditolak, tidak menindih) +
  `docker restart`. `--penyemak pautan` mencetak ke terminal sahaja. `--status` = imej, kesihatan, undur, kod awam, kemajuan x/n
  setiap penyemak (kiraan sahaja). Log deploy `~/ops/mypii/iaa-deploy.log` (luar repo, di luar folder data yang dilekap ke kontena).
- **Skor (P9, 31 Okt 2026).** `mypii/iaa/skor.py` membaca `data/iaa/sampel.json` (split ikut `urutan`) + `data/iaa/jawapan/<p>.jsonl`
  SAHAJA — tiada bundel/teks, jadi ujian2 hanya menyumbang kiraan. Penyemak = id dalam `iaa.skor.pasangan`; fail tiada = "menunggu
  <id> (x/n)" (bukan ralat). Hanya `status == siap`; separa/rosak/gagal dikira dalam jadual penyemak. κ Cohen = (pₒ − pₑ)/(1 − pₑ),
  pₑ dari marginal kedua-dua penyemak; pₑ = 1 (satu kategori sahaja) → κ `null` (tidak tertakrif — tidak dipaksa 0 atau 1).
  Normalisasi (b) = `[^0-9A-Z]` dibuang selepas huruf besar (digit untuk MyKad/telefon/SSM baharu; alnum untuk SSM lama) — awalan
  `+60` TIDAK dipetakan ke `0` (kedua-dua penyemak menyalin nilai seperti tertulis; had dilapor). Set per dokumen (pendua dibuang).
  CI: metrik dikira semula atas sampel semula DOKUMEN (`statistik.indeks_bootstrap`, `persentil`, ulangan/benih/aras/perpuluhan =
  `nilai.statistik`); pasangan berkongsi satu set indeks; kadar ralat disampel semula DALAM setiap split (benih + indeks split) dan beza
  dev − ujian2 = beza replikat berpasangan ikut nombor ulangan. `utama` = `iaa.skor.utama` bila kedua-duanya ada, jika tidak pasangan
  pertama. Output `hasil/iaa.json` (sort_keys, tiada cap masa → bait sama) + blok `<!-- iaa:mula -->` `docs/BANDINGAN.md`.

**Ditolak (dicari 31 Okt 2026).**
| Calon | Lesen | Sebab |
|---|---|---|
| Label Studio (HumanSignal) | Apache-2.0 | akaun/log masuk, UI meja, telemetri lalai, bekas ~1 GB; soalan ya/tidak per span perlu XML; tiada pautan bertoken tanpa log masuk |
| doccano | MIT | akaun + Django + Postgres; anotasi span (bukan menilai label sedia ada); UI telefon lemah |
| Argilla | Apache-2.0 | Elasticsearch/OpenSearch + akaun; berat untuk 300 dokumen × 2 penyemak |
| `kldtz/bratiaa`, `savkov/bratutils` | MIT | format brat; κ Cohen + F1 span ringkas dalam stdlib — larangan kebergantungan baharu |
Dalaman yang DIGUNA terus: `mypii/nilai/statistik.py` (bootstrap atas dokumen), `mypii/klien_llm.py` (9router + urai), `bandingan.tulis_blok`
(blok jana `docs/BANDINGAN.md`, penanda `iaa.skor.penanda`).

**P10 — mesej + pencetus (31 Okt 2026).** `deploy/iaa/pencetus.sh` dijalankan cron harian `23 1 * * * … # IAA-MYPII` (dipasang idempoten
`crontab -l | grep -v IAA-MYPII`): membaca `operasi kemajuan` melalui `docker exec`, mengabaikan `uji`, dan bila penyemak manusia mencapai n/n
memanggil `autopilot.py mula mypii` SEKALI (satu panggilan walau p1 + p2 siap serentak); penanda `pencetus-<id>.selesai` ditulis hanya bila
`mula` keluar 0 (gagal = cuba esok, log `~/ops/mypii/iaa-pencetus.log`, kiraan sahaja). Arahan luar boleh diganti env (`IAA_KEMAJUAN`/`IAA_MULA`)
untuk ujian. SATU mesej Telegram kepada pemilik (CHAT_ID pemilik, butang URL ke pautan p1 — pautan tidak pernah dicetak/dilog) dengan
`NOTIFY_TERUS=1`: pintu notify boleh menahan mesej (senyap/pendua) sambil keluar 0, jadi tanpa itu kod keluar 0 tidak membuktikan mesej
sampai; penanda `mesej-p1.dihantar` (0600) = bukti tunggal, tiada mesej kedua. Kotak pasir autopilot membenarkan fail env Telegram sahaja
dalam folder notify, jadi log notify tidak dibaca pembina.

**P11 — skor akhir (3 Nov 2026).** Pencetus P10 memulakan autopilot bila `deploy.sh --status` = p1 300/300. `make iaa-eksport` →
`data/iaa/jawapan/p1.jsonl` (siap 300, separa 0; dibaca dari stor hidup, tiada token) → `make iaa-skor` → `hasil/iaa.json` + blok iaa
BANDINGAN (dua larian `cmp` sama). Pasangan dilapor = **p1×llm sahaja** (p2 0/300 — p1×p2 kekal "menunggu"). Angka = LOG-ITERASI baris P11.
**Had yang WAJIB disebut bersama angka (keputusan pelaporan, bukan pindaan protokol):** (1) p1 memberi SATU nilai sahaja untuk soalan a
(semua span "Betul") dan c (tiada dokumen "Janggal"), jadi κ a tidak tertakrif dan κ c = 0 ialah kesan tiada varians (paradoks prevalens),
BUKAN bukti tidak setuju — lapor % setuju + kadar ralat, bukan κ, untuk a/c; (2) tempo p1 diukur dari cap masa stor sahaja: 269/300 dokumen
dijawab dalam satu hari, jurang median antara dokumen 8 s (p10 4 s, p90 20 s) — semakan pantas, mungkin kurang teliti; (3) satu penyemak
manusia + satu LLM (`cbcn/glm-5.3`) — bukan IAA dua manusia; p2 = kerja pemilik. Tiada dokumen/label dibaiki atau dikecualikan (hingar dilapor).

## Halaman pintu (PELAN-IAA-HALAMAN, 1 Nov 2026)

**Sebab.** Pemilik menaip nama laman sendiri (31 Okt) dan nampak `tiada / not found` → menyangka laman rosak. Kelas masalah: setiap
pelawat tanpa pautan lengkap mendapat badan teknikal.
- `GET/HEAD /` = 200 halaman pintu BM + EN ("buka dari butang mesej Telegram"); tiada senarai penyemak, token, id atau pautan `/s/`.
- **Setiap 404 GET/HEAD** (token salah, `/s/`, laluan tiada, `/statik/pintu.html`) = status 404 DIKEKALKAN, badan = bait yang SAMA dengan
  `/` → tiada oracle token (token salah tidak dibezakan dari laluan tiada; amalan sumber privat GitHub/Stripe). POST 404 kekal ringkas
  (`app.js` tidak membaca badan 404). `KEPALA` penuh pada semua.
- Dijana pelayan tanpa JS dari `statik/pintu.html` (`{{ms|en.<kunci>}}`) + `teks/{ms,en}.json` (kunci `pintu_*`, `judul`, `mesej_butang`;
  `{butang}` dalam teks → label butang mesej, supaya halaman dan butang memakai perkataan sama) dengan `html.escape`; dibaca SEKALI semasa
  mula (kunci hilang = gagal awal). Templat tidak dihidang mentah di `/statik/`. Gaya = `app.css` + `pintu.css` (token `:root` sahaja).
- `deploy.sh` `sihat_awam` menyemak `/` noindex + `data-pintu` dan 404 rawak + `data-pintu`.
- Undur: `git revert` + `deploy.sh`, atau `deploy.sh --undur` (imej lama dipegang).
- **Mesej butang-sahaja (P4).** `mypii/iaa/mesej.py` membina teks BM + EN dari kunci `mesej_*` dan MENOLAK (ValueError) teks/label yang
  mengandungi `http`, `://`, `www.`, corak domain atau `iaa.pelayan.nama_hos` — penerima tidak boleh menaip nama laman dari mesej, jadi
  pautan hanya dalam butang URL (`NOTIFY_BUTANG`). `deploy.sh --penyemak mesej <id>`: pautan dari `operasi penyemak pautan` terus ke env
  (stdin ke `mesej.py butang`, tidak dicetak/dilog; ralat tidak memetik pautan); `NOTIFY_TERUS=1` + `NOTIFY_KOD_KELUAR=1` (sebab sama P10);
  penanda `mesej-<id>.dihantar` 0600 hanya bila rc 0, wujud = enggan. Dibina di hos (`uv run`), jadi tiada deploy kontena diperlukan.
  Undur: `git revert`; tiada mesej dihantar dalam PELAN ini.

**Undur.** Halaman: `deploy/iaa/deploy.sh --undur` · tutup: `docker rm -f mypii-iaa` + buang `/traefik/dynamic/semak-mypii.yaml` + rekod
DNS (ID di atas). Pencetus: buang baris cron `# IAA-MYPII`. Kod: `git revert`. Pindaan PRA-DAFTAR TIDAK diundur (tambah-sahaja).
