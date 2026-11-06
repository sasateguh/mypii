# Pra-daftar analisis MyPII-Bench — split `ujian` + `ujian2` (PELAN-C C4a, ADR-007)

> **Status: dikomit SEBELUM mana-mana split ujian dibuka.** Tiada `--benarkan-ujian` pernah dijalankan oleh gelung atau autopilot.
> Fail ini **TAMBAH-SAHAJA** (gerbang autopilot): pindaan = bahagian bertarikh baharu di §15, tidak menyunting teks di atasnya.
> Sha komit fail ini dicetak oleh harness bila ujian dijalankan (C4b) — itu cap masa pendaftaran.
> Rangka: skil `hypothesis-generation` (`preregistration_scaffold_template.md`, K-Dense v2.72.0); ancaman kesahan: skil
> `scientific-critical-thinking` (`statistical_pitfalls.md`, `common_biases.md`). Pelaporan: skil `statistical-analysis`.

## 1. Rekod pentadbiran
- Projek: MyPII — pengecam PII Malaysia (MyKad/NRIC, nombor pendaftaran SSM, telefon) untuk Microsoft Presidio + penanda aras sintetik MyPII-Bench.
- Pemilik bertanggungjawab: Aiman Malib (Sasa Teguh — perniagaan milikan tunggal). Tiada pembiaya, tiada penaja luar.
- Repositori pendaftaran: repo git `sasateguh/mypii` (private sehingga terbit). Cap masa = komit git fail ini; tiada pendaftaran luar (OSF dll.) — ini had yang diakui.
- Akses terdahulu kepada data sasaran: **tiada** pengukuran pada `ujian` atau `ujian2` oleh sesiapa. `ujian` (v1) dijana dari templat simpanan
  (ADR-002) dan dikunci sha256 sejak Fasa 0; `ujian2` dijana LLM (ADR-004) dan **dimeterai** (`data/bench/UJIAN2-MUKTAMAD`, komit `2ecb14d`).
  Kandungan `ujian2` tidak pernah dibuka oleh pembina — hanya statistik pengesah (bilangan tolak). Ejen yang menulis fail ini juga tidak membukanya.

## 2. Kelulusan dan pengawasan
Tiada subjek manusia: semua dokumen sintetik, tiada nombor/nama orang sebenar (peraturan projek). Tiada data peribadi dikumpul.

## 3. Pemerhatian beku (sebelum ujian)
Pemerhatian yang mendorong hipotesis datang dari split **dev-v2** (`531532cf…`, 1,000 dok; `data/bench/CINCANGAN.json`) yang telah
**ditala** oleh gelung pengecam — jadi ia tidak membuktikan apa-apa tentang generalisasi. Angka dev (`hasil/dev-statistik.json`, `e7c3ebce…`,
`make statistik`): F1 `*` tepat mypii 0.8877 [0.8701, 0.9037] · deepseek 0.7479 · pii-guard 0.7209 · llama 0.706 · presidio-asal 0.4309.
Pengecam MyPII **BEKU** sejak dev-v2 diukur (PELAN-B/C); tiada perubahan pengecam selepas fail ini dikomit sehingga ujian dijalankan.

## 4. Soalan dan jenis dakwaan
Adakah pengecam MyPII mengesan entiti PII Malaysia (`MY_NRIC`, `MY_SSM`, `MY_PHONE`) dalam teks BM / EN / Manglish sintetik dengan F1
tepat yang lebih tinggi daripada setiap garis dasar yang tersedia? Dakwaan = **perbandingan prestasi atas penanda aras sintetik** (bukan
sebab-akibat, bukan prestasi atas data sebenar).

## 5. Hipotesis
| ID | Hipotesis (sehala) | Status |
|---|---|---|
| **H1a–H1d** | Atas `ujian2`, F1 tepat mikro `semua|*` MyPII > F1 setiap garis dasar: (a) `presidio-asal`, (b) `pii-guard`, (c) `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast`, (d) `llm:cbcn/deepseek-v4.1-flash` | **utama (pengesahan)** |
| H2a–H2d | Sama seperti H1, atas split `ujian` (v1) | pengesahan sekunder (keluarga Holm berasingan) |
| H3 | Atas `ujian2` dan `ujian`, MyPII > setiap garis dasar pada F1 `semua|<entiti>` untuk setiap entiti | sekunder |
| — | P/R per entiti, F1 separa, F1 per bahasa (`bahasa:ms|en|manglish`), `pii-guard (disokong)` | **deskriptif** (tiada ujian) |

Hipotesis nol bagi setiap perbandingan: ΔF1 = F1(MyPII) − F1(garis dasar) ≤ 0. Penjelasan saingan yang mesti ditimbang sebelum menerima
H1: (i) MyPII menang kerana penanda aras dijana dengan bentuk yang sama dengan pengecam (kitaran — lihat §11 ancaman 1–2); (ii) garis
dasar LLM kalah kerana prompt/penghuraian, bukan keupayaan (ancaman 4).

## 6. Data dan split
| split | dokumen | sha256 (fail sumber) | penjana |
|---|---|---|---|
| `ujian` (v1) | 1,000 | `38d473fb77bde2371e7d625f9de5d9bd3bf3c9c0280c712896c35682cb9a8657` (`data/bench/KUNCI.json`) | templat simpanan tulisan tangan (ADR-002) |
| `ujian2` | 1,000 | `83ff90b4ef40a7ac5c8a39bf17e54f9b94775010031fca3e17af739aec2de31a` (`data/bench/KUNCI2.json`, = `UJIAN2-MUKTAMAD`) | `cbcn/kimi-k3` (ADR-004, pengesah ADR-005/008/009) |

sha256 = cincangan BAIT fail `data/bench/<split>.jsonl` (`mypii/jana/jana.py`). Manusia mengesahkannya sebelum larian
(`sha256sum data/bench/ujian.jsonl data/bench/ujian2.jsonl` — cincangan sahaja, tanpa membuka kandungan); sha berbeza = larian tidak sah (jangan lapor). Tiada pengecualian dokumen; tiada data hilang
(setiap dokumen mesti ada ramalan — id hilang = ralat harness, bukan dianggap kosong).

## 7. Perintah tepat (manusia, SEKALI, selepas C4b)
Sebelum: `git status` bersih; `make uji` lulus; catat `git rev-parse HEAD`. LLM garis dasar atas split ujian TIADA cache → perlu 9router
(`set -a; . ~/ops/mypii/9router.env; set +a`).
```
uv run --extra nilai --extra garis python -m mypii.nilai.harness --split ujian2 --sistem semua --benarkan-ujian
uv run python -m mypii.nilai.harness --split ujian2 --sistem semua --statistik --benarkan-ujian
uv run --extra nilai --extra garis python -m mypii.nilai.harness --split ujian  --sistem semua --benarkan-ujian
uv run python -m mypii.nilai.harness --split ujian  --sistem semua --statistik --benarkan-ujian
```
- Output `hasil/ujian*-*.json` + `hasil/ramalan/` diabaikan git (tidak dikomit sehingga keputusan terbit). Entri cache LLM baharu
  (`hasil/cache/llm/`) mengandungi jawapan atas teks ujian → **JANGAN komit** (`git restore hasil/cache/llm` selepas menyalin ke arkib luar repo).
- Panggilan LLM yang gagal selepas `llm.ulang` cubaan (harness mencetak `<model>: N panggilan gagal`): perintah yang SAMA dijalankan
  semula SEKALI — jawapan yang sudah ada diambil dari cache (tidak berubah), hanya yang gagal dipanggil semula. Yang masih gagal =
  ramalan kosong untuk dokumen itu (tingkah laku `mypii/nilai/garis.py`) dan bilangannya dilapor (§10). Ini BUKAN larian kedua sistem lain.
- Tiada larian kedua. Larian yang crash separuh jalan boleh diulang SEKALI dengan kod yang sama; sebab dicatat dalam §15.

## 8. Metrik dan analisis
- **Metrik utama:** F1 tepat mikro `semua|*` (span sama tepat: mula, tamat, entiti — `harness.skor`, AST dikunci gerbang §4).
- **Sekunder:** F1 tepat `semua|<entiti>`; P, R; F1 separa (bertindih); F1 per bahasa.
- **Ketidakpastian** (`nilai.statistik`, ADR-006 — nilai disalin dari `config/mypii.yaml`): bootstrap persentil, unit sampel semula =
  **dokumen**, `ulangan: 1000`, `benih: 2026`, `aras: 0.95`; rujukan `mypii`; kunci utama `semua|*`.
- **Ujian berpasangan:** p bootstrap sehala Berg-Kirkpatrick (#(δ* > 2δ)/B) DAN ujian rawak anggaran (p = (b+1)/(R+1)), R = B = 1000.
  Pembetulan **Holm** (`kaedah: holm`) atas k = 4 garis dasar, berasingan bagi setiap split, setiap kunci, setiap jenis p.
- **Ambang:** α = 0.05 keluarga (sehala; `nilai.statistik.pradaftar.alfa`). Sehala kerana hipotesis berarah ditulis sebelum data (§5).
- **Peraturan keputusan H1x / H2x:** disokong hanya jika **kedua-dua** p Holm (bootstrap DAN rawak) < 0.05. Jika satu sahaja < 0.05 =
  "tidak konsisten" → dilapor sebagai TIDAK disokong. Lantai p bootstrap = 0 dilapor "< 1/B" (bukan 0).
- **Saiz kesan** dilapor bersama setiap p: ΔF1 + CI 95% Δ. Signifikan ≠ penting: Δ < 0.02 F1 dilapor sebagai beza kecil walau signifikan.
- H3 (per entiti) ialah sekunder: Holm hanya atas k garis dasar dalam kunci itu; tiada pembetulan merentas 3 entiti × 2 split — dinyatakan
  dalam kertas sebagai penerokaan, bukan pengesahan.

## 9. Analisis kuasa (dari bootstrap DEV, bukan ujian)
Perintah: `make kuasa` (`mypii/nilai/kuasa.py`) atas `hasil/dev-statistik.json` (`e7c3ebce…`). SE Δ ≈ lebar CI 95% Δ / (2·1.96), diskala
√(1000/1000) = 1 (dev dan ujian2 sama saiz); MDE sehala = (z_{1−α'} + z_{0.80})·SE; α' = α/k (langkah Holm paling ketat) dan α' = α
(langkah terakhir). Config `nilai.statistik.pradaftar` (`alfa: 0.05`, `kuasa: 0.80`, `dokumen_sasaran: 1000`). Output larian (disalin tepat):

| garis dasar | kunci | ΔF1 dev | SE Δ | MDE α/k=0.0125 | MDE α=0.05 |
|---|---|---|---|---|---|
| llm:cbcn/deepseek-v4.1-flash | `*` | 0.1398 | 0.0109 | 0.0337 | 0.0272 |
| llm:cbcn/deepseek-v4.1-flash | `MY_NRIC` | 0.1202 | 0.0171 | 0.0528 | 0.0426 |
| llm:cbcn/deepseek-v4.1-flash | `MY_PHONE` | 0.1449 | 0.0135 | 0.0415 | 0.0335 |
| llm:cbcn/deepseek-v4.1-flash | `MY_SSM` | 0.1534 | 0.0227 | 0.0698 | 0.0563 |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `*` | 0.1817 | 0.0111 | 0.0344 | 0.0277 |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `MY_NRIC` | 0.1679 | 0.0182 | 0.0562 | 0.0454 |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `MY_PHONE` | 0.1527 | 0.0141 | 0.0434 | 0.035 |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `MY_SSM` | 0.2178 | 0.0198 | 0.061 | 0.0492 |
| pii-guard | `*` | 0.1668 | 0.0126 | 0.0388 | 0.0313 |
| pii-guard | `MY_NRIC` | 0.1533 | 0.0198 | 0.061 | 0.0492 |
| pii-guard | `MY_PHONE` | 0.0228 | 0.0081 | 0.025 | 0.0202 |
| pii-guard | `MY_SSM` | 0.8054 | 0.0188 | 0.0579 | 0.0467 |
| presidio-asal | `*` | 0.4568 | 0.0131 | 0.0404 | 0.0326 |
| presidio-asal | `MY_NRIC` | 0.8328 | 0.0171 | 0.0527 | 0.0425 |
| presidio-asal | `MY_PHONE` | 0.3753 | 0.0176 | 0.0543 | 0.0438 |
| presidio-asal | `MY_SSM` | 0.8054 | 0.0188 | 0.0579 | 0.0467 |

Tafsiran (sebelum data): untuk H1 (`*`), ujian2 mempunyai kuasa 80% untuk mengesan Δ ≥ 0.0337–0.0404 F1 (bergantung garis dasar) pada
langkah Holm paling ketat. Δ dev jauh lebih besar, tetapi dev ditala — Δ ujian2 dijangka LEBIH KECIL dan mungkin di bawah MDE.
**pii-guard `MY_PHONE`** (Δ dev 0.0228 < MDE ketat 0.025) **kurang berkuasa**: keputusan tidak signifikan di situ TIDAK bermaksud
"tiada beza". Anggapan: SE ujian2 ≈ SE dev (saiz sama, tetapi taburan ujian2 berlainan penjana) — kuasa sebenar boleh lebih rendah.
Analisis kuasa post-hoc atas keputusan ujian TIDAK akan dibuat (`statistical_pitfalls.md` Pitfall 10).

## 10. Apa yang dilapor walau buruk
- Setiap sistem (5) × setiap split (2) × setiap kunci (`*` + 3 entiti) × P/R/F1 tepat + separa + per bahasa — jadual penuh, termasuk
  `pii-guard (disokong)`.
- Setiap p (mentah + Holm, kedua-dua jenis) dan CI, **termasuk keputusan tidak signifikan dan negatif** (garis dasar menang).
- **F1 ujian2 < F1 dev** (dijangka, kerana dev ditala) dilapor bersama jurangnya; begitu juga ujian v1 lawan dev lama (0.9954, tidak setanding).
- Bilangan dokumen di mana LLM gagal menjawab; masa larian.
- Jika H1 tidak disokong untuk mana-mana garis dasar, abstrak kertas menyatakannya.

## 11. Ancaman kesahan (`scientific-critical-thinking`)
1. **Kitaran penjana–pengecam:** ujian v1 dari keluarga templat yang sama dengan dev lama (ditala ke siling 0.9954) → ujian v1 mengukur
   ingatan bentuk, bukan generalisasi. Itu sebab H1 (utama) = ujian2.
2. **Penjana ujian2 `kimi-k3`** berlainan keluarga dari penjana latih/dev-v2 (`gemini-3.8-flash`) dan garis dasar LLM (Llama, DeepSeek),
   tetapi nilai entiti dalam ujian2 masih dijana oleh kod MyPII (`mypii.jana`) — bentuk nombor sama dengan yang pengecam jangka. Had realisme ADR-004.
3. **Label telefon (ADR-002):** nombor telefon sintetik dalam julat sah libphonenumber, dan pengecam MyPII juga mengesahkan dengan
   libphonenumber → recall telefon MyPII terlebih optimis. Kertas menyebutnya pada setiap angka telefon.
4. **Garis dasar LLM:** satu prompt, suhu 0, tiada tala prompt untuk MyPII-Bench (ADR-011) — prestasi LLM mungkin dipandang rendah;
   tiada prompt diubah selepas fail ini.
5. **Data sintetik:** keputusan tidak terpakai terus pada teks sebenar (OCR, sembang, borang). `docs/ANALISIS-RALAT.md` mencatat batasan probe.
6. **Penulis = penala:** orang/ejen yang menala pengecam juga membina penanda aras dan pra-daftar ini. Mitigasi: split dikunci sha256, harness
   enggan tanpa bendera (C4b), statistik + jadual dijana mesin, rekod setiap cubaan `hasil/iterasi.tsv` (tambah-sahaja). Tiada penilai buta.
7. **Pemilihan hasil (Pitfall 36):** dihalang oleh §10 dan peraturan tiada larian kedua (§7).

## 12. Apa yang TIDAK akan dibuat
- Tiada tala pengecam, config `pengecam:`, prompt LLM, atau templat selepas ujian dibuka; tiada larian ujian kedua untuk "memperbaiki".
- Tiada garis dasar dibuang atau ditambah selepas data dilihat (garis dasar baharu = kajian baharu, dilapor berasingan).
- Tiada tukar metrik utama, aras α, kaedah Holm, ulangan/benih bootstrap, atau peraturan keputusan.
- Tiada pengecualian dokumen selepas melihat ramalan.

## 13. Perisian dan persekitaran
Python ≥3.11,<3.14 (`pyproject.toml`), `uv.lock` dikomit: presidio-analyzer 2.2.366, spaCy 3.8.18, `en_core_web_sm` 3.8.0,
`malaysia-pii-guard` git `75d6920…`. Statistik = stdlib (`mypii/nilai/statistik.py`), tiada SciPy. Benih tetap → keputusan statistik sama bait-demi-bait.

## 14. Bantuan AI
Pengecam, penanda aras, harness dan pra-daftar ini ditulis dengan bantuan ejen Claude (Claude Code) di bawah arahan pemilik; templat
ujian2 dijana `cbcn/kimi-k3` melalui 9router. Kertas akan mendedahkannya. Tiada data ujian dihantar ke mana-mana LLM selain garis dasar
LLM yang ditakrif (§7).

## 15. Pindaan
Prosedur: tambah bahagian `### YYYY-MM-DD — <ringkasan>` di bawah (sebab, apa berubah, sama ada ia sebelum atau selepas ujian dibuka).
Tiada pindaan setakat ini.

---

## English summary

**Preregistration of the MyPII-Bench test analysis, committed before either test split was opened.** Append-only; amendments are dated
sections under §15. The commit SHA of this file is printed by the harness when the test splits are run (C4b) and serves as the
registration timestamp. No external registry (OSF) is used — acknowledged limitation.

| Item | Plan |
|---|---|
| Primary hypotheses H1a–d | On `ujian2`, MyPII exact micro-F1 (`semua|*`) > each baseline: presidio-asal, pii-guard, llama-3.3-70b, deepseek-v4.1-flash (one-sided) |
| Secondary | H2a–d: same on `ujian` (v1), separate Holm family; H3: per-entity F1 on both splits (exploratory, no cross-entity correction) |
| Descriptive only | P/R per entity, partial-match F1, per-language F1 (ms/en/manglish), pii-guard on its supported entities |
| Splits | `ujian` 1,000 docs sha256 `38d473fb…8657`; `ujian2` 1,000 docs sha256 `83ff90b4…e31a` (sealed, `UJIAN2-MUKTAMAD`) |
| Runs | Once, by a human, exact commands in §7; no second run; one re-run allowed only for a mid-run crash with identical code, or once to retry failed LLM calls (cached answers reused) |
| Uncertainty | Percentile bootstrap over **documents**, B = 1000, seed 2026, 95% |
| Tests | Paired bootstrap (Berg-Kirkpatrick et al. 2012) and approximate randomization (R = 1000); Holm over k = 4 baselines per split/key/test |
| Decision rule | Hypothesis supported only if **both** Holm-adjusted p < 0.05; otherwise reported as not supported |
| Effect size | ΔF1 with 95% CI always reported; Δ < 0.02 called small even if significant |
| Power | From dev bootstrap (`make kuasa`): 80% power at α/k = 0.0125 to detect ΔF1 ≥ 0.0337–0.0404 on `*`; pii-guard MY_PHONE underpowered (dev Δ 0.0228 < MDE 0.025) |
| Reported regardless | Every system × split × key, all p-values, negative and non-significant results, test F1 below dev F1, LLM failures |
| Not done | No tuning after test; no baseline dropped/added; no metric, α, method or seed changes; no post-hoc document exclusion; no post-hoc power analysis |
| Threats | Generator–recognizer circularity (v1 shares template family with tuned dev); entity values generated by MyPII code; phone labels validated by libphonenumber as is the recognizer (recall optimistic); single untuned LLM prompt; synthetic data only; tuner = benchmark author |

The dev split (1,000 docs, tuned) shows MyPII 0.8877 [0.8701, 0.9037] vs best baseline 0.7479; because dev was tuned, these intervals do
not support the paper's claim — only `ujian2` does.

---

## 15. Pindaan (sambungan)
Pindaan bertarikh ditambah di sini (selepas English summary) kerana fail ini tambah-sahaja; §15 asal di atas tidak disunting.

### 2026-10-31 — IAA semakan label manusia (sebelum ujian dibuka)
**Status semasa pindaan:** `ujian` dan `ujian2` BELUM dibuka; tiada `--benarkan-ujian` pernah dijalankan; tiada sampel IAA dipilih dan
tiada jawapan dikumpul. Pindaan ini dikomit SENDIRI (tanpa kod) sebelum mana-mana kod pensampel/halaman (PELAN-IAA P1; ADR-015).
Hipotesis H1–H3, metrik, α, Holm, bootstrap dan peraturan keputusan §5–§8 **TIDAK berubah**. Ini kajian sampingan deskriptif.

**Tujuan.** Menjawab "siapa memeriksa bahawa label betul dan teksnya macam Malaysia sebenar?" (PRD §2.2 + M4): mengukur persetujuan
antara penyemak atas label EMAS sedia ada, dan kadar ralat label dalam `dev` (dev-v2) berbanding `ujian2`. Tiada hipotesis diuji.

**Sampel.** 300 dokumen = 150 `dev` + 150 `ujian2`. Setiap split berstrata bahasa (ms / en / manglish) × berspan (≥ 1 span emas) /
negatif (tiada span) = 6 strata × 25 dokumen. Dipilih oleh kod dengan benih tetap (`config/mypii.yaml` `iaa.sampel.benih`), tanpa
melihat teks; fail sampel memegang id + split + bahasa + berspan + urutan sahaja. Urutan paparan dikocok (benih sama) merentas split —
penyemak tidak diberitahu split atau id dokumen (buta split). Kiraan strata (bukan teks) dibaca dari `ujian2` untuk memastikan setiap
strata ≥ 25 sebelum pindaan ini (paling kecil: en berspan 124).

**Soalan (tepat, sama untuk setiap penyemak).**
- (a) Untuk setiap span emas (teks ditanda + jenisnya): `Betul` · `Salah` (bukan PII ini) · `Jenis lain` (PII tetapi jenis lain).
- (b) "Ada MyKad / SSM / telefon yang TIDAK bertanda?" `Tiada` · `Ada` → senarai nilai (satu setiap baris).
- (c) "Teks ini terasa Malaysia sebenar?" `Ya` · `Janggal`.
Dokumen dikira SIAP bila semua span (a) + (b) + (c) dijawab. Hanya teks + label emas dipapar.

**Penyemak.** p1 = Aiman Malib (pemilik, juga pengarang penanda aras — had diakui). p2 = penyemak manusia kedua bila ada (dicari pemilik;
pautan berasingan). Sandaran bila tiada p2: LLM `cbcn/glm-5.3` (Zhipu) melalui 9router — keluarga berlainan dari penjana `ujian2`
(`cbcn/kimi-k3`), penjana latih/dev (`ag/gemini-3.8-flash`) dan garis dasar LLM (Llama, DeepSeek); sandaran glm penjana `ujian2` tidak
pernah dipakai (LOG B1b). Prompt dalam `iaa.llm.prompt`, suhu 0, tiada model sandaran, cache jawapan dikomit. LLM sebagai penyemak kedua
= **had kajian** (bukan pengganti manusia) dan dilapor begitu.

**Metrik.** (a) κ Cohen per span + % persetujuan mentah (dilapor bersama — paradoks κ bila `Betul` dominan). (c) κ Cohen per dokumen
+ % persetujuan. (b) nilai dinormalkan (MyKad/telefon = digit sahaja; SSM = alfanumerik huruf besar); F1 persetujuan mikro
2|A∩B| / (|A|+|B|) atas dokumen; bilangan dokumen di mana kedua-dua menjawab `Tiada` dilapor berasingan. Kadar ralat label setiap
penyemak × split: span `Salah`+`Jenis lain` / span; dokumen dengan ≥ 1 PII tidak bertanda / dokumen; dokumen `Janggal` / dokumen;
beza dev − ujian2. Semua dengan CI 95% bootstrap persentil atas DOKUMEN, B dan benih = `nilai.statistik` (1000, 2026). Deskriptif —
tiada nilai p, tiada ambang lulus/gagal.

**Pasangan dilapor.** p1×llm sentiasa; p1×p2 bila p2 wujud (pasangan UTAMA bila ada); hanya dokumen SIAP oleh kedua-dua pihak.

**Pengecualian §14 (Bantuan AI).** 150 dokumen `ujian2` yang disampel (teks + label emas sahaja) (i) dihantar ke `cbcn/glm-5.3` melalui
9router, dan (ii) dipapar kepada penyemak manusia (termasuk pemilik, yang juga penala pengecam). **Tiada ramalan sistem** (MyPII atau
garis dasar) dipapar kepada sesiapa atau dihantar ke LLM. Pengecam KEKAL BEKU: semakan ini tidak membawa sebarang perubahan pengecam,
config `pengecam:`, data, templat atau prompt garis dasar. Dokumen yang disampel TIDAK dikecualikan daripada analisis H1–H3.

**Ralat yang dijumpai.** Ralat label `ujian2` = **hingar label, dilapor, TIDAK dibaiki** (split dimeterai, `UJIAN2-MUKTAMAD`). Ralat
`dev` juga dilapor sahaja dalam kajian ini; tiada dokumen dev/ujian2 dijana semula, dibaiki atau dikecualikan kerana hasil semakan.

**Dilapor walau buruk.** κ rendah, kadar ralat tinggi, beza dev − ujian2 ke mana-mana arah, jawapan LLM rosak/gagal (dikira, tidak
dibuang), dan n < 300 bila semakan berhenti (n sebenar setiap pasangan dinyatakan). Tiada dokumen ditukar ganti selepas sampel dikomit.

**Ancaman tambahan.** (1) Pemilik melihat 150 dokumen `ujian2` sebelum ujian dijalankan — dikawal oleh pengecam beku + §12, dan
diakui dalam kertas. (2) p1 = pengarang penanda aras (bias pengesahan ke arah `Betul`). (3) Penyemak kedua LLM boleh berkongsi bias
dengan penjana LLM walaupun keluarga berlainan.

**English summary of this amendment.** Before either test split is opened, we add a descriptive inter-annotator agreement (IAA) study
of the existing gold labels. A seeded, stratified sample of 300 documents (150 dev + 150 `ujian2`; language × has-span/negative, 25 per
cell) is shown blind to split, in shuffled order, to reviewer p1 (the author, Aiman Malib) and either a second human (p2, primary pair
when available) or, as an acknowledged limitation, the LLM `cbcn/glm-5.3` (a model family distinct from all generators and baselines;
temperature 0, prompt in config, cached answers committed). Questions: (a) is each gold span correct / not PII / wrong type; (b) is any
MyKad/SSM/phone left unlabelled; (c) does the text feel like real Malaysian text. Reported: Cohen's κ with raw agreement for (a) per span
and (c) per document, micro agreement-F1 on normalised values for (b), and per-reviewer label error rates for dev vs `ujian2` with
95% document-level percentile bootstrap CIs (B = 1000, seed 2026); no hypothesis tests. Exception to §14: the sampled `ujian2`
documents (text + gold labels only, never system predictions) are sent to the LLM reviewer and shown to human reviewers. The recognizer
stays frozen; errors found in `ujian2` are reported as label noise and never fixed; no document is excluded or regenerated; H1–H3 are
unchanged. Low κ, high error rates and n < 300 at stopping are reported regardless.

### 2026-11-03 — Garis dasar Claude (API Anthropic) ditambah (sebelum ujian dibuka)
**Status semasa pindaan:** `ujian` dan `ujian2` BELUM dibuka; tiada `--benarkan-ujian` pernah dijalankan (`ls hasil/ | grep ujian`
kosong; tiada `_pradaftar` dalam mana-mana `hasil/*.json`). Tiada model Claude pernah dinilai atas mana-mana split. Pindaan ini
dikomit SENDIRI (tanpa kod, config, ujian atau kebergantungan) sebelum klien Anthropic ditulis (PELAN-CLAUDE P1; ADR-016 menyusul).

**Sebab.** Pemilik (3 Nov 2026) mahu MyPII diuji berbanding model bahasa komersial terkini selain Llama dan DeepSeek. Dua model Claude
ditambah sebagai garis dasar, dipanggil melalui API Anthropic terus (bukan 9router): `anthropic/claude-sonnet-5-5` dan
`anthropic/claude-haiku-5-5`. Menurut §12, garis dasar ditambah SEBELUM data ujian dilihat — oleh itu pindaan ini, bukan kajian baharu.

**Hipotesis baharu (sehala, sama bentuk dengan §5).**

| ID | Hipotesis | Status |
|---|---|---|
| **H1e** | Atas `ujian2`, F1 tepat mikro `semua|*` MyPII > `llm:anthropic/claude-sonnet-5-5` | **utama (pengesahan)** |
| **H1f** | Atas `ujian2`, F1 tepat mikro `semua|*` MyPII > `llm:anthropic/claude-haiku-5-5` | **utama (pengesahan)** |
| H2e | Sama seperti H1e, atas `ujian` (v1) | pengesahan sekunder |
| H2f | Sama seperti H1f, atas `ujian` (v1) | pengesahan sekunder |

H3 (per entiti) dan analisis deskriptif §5 kini merangkumi dua model ini juga.

**Apa berubah dalam §8.** Keluarga Holm kini **k = 6** garis dasar (bukan 4), berasingan bagi setiap split, setiap kunci dan setiap jenis
p — termasuk H3. Metrik utama, α = 0.05 sehala, bootstrap (`ulangan: 1000`, `benih: 2026`, `aras: 0.95`), ujian rawak, peraturan
keputusan (kedua-dua p Holm < 0.05) dan label "beza kecil" untuk Δ < 0.02 **TIDAK berubah**. k = 6 menjadikan langkah Holm paling ketat
α/6 ≈ 0.0083 — keputusan untuk H1a–H1d/H2a–H2d mungkin lebih konservatif daripada di bawah k = 4; itu kos menambah garis dasar, diterima.

**§9 Analisis kuasa.** Jadual §9 (k = 4) kekal sebagai rekod. MDE untuk k = 6 dikira dengan `make kuasa` atas dev SELEPAS larian dev
Claude dan dilapor dalam `docs/BANDINGAN.md` + LOG. MDE ialah maklumat sahaja: ia TIDAK mengubah peraturan keputusan, hipotesis atau
pilihan garis dasar, walaupun Δ dev Claude ternyata di bawah MDE.

**Tetapan garis dasar Claude (sama dengan LLM lain kecuali yang dinyatakan).** Prompt = `garis_dasar.llm.prompt` sedia ada, tidak
diubah dan tidak ditala; satu mesej pengguna; jawapan = gabungan blok teks sahaja → penghurai span sedia ada. **Suhu tidak dihantar**:
API Anthropic menolak suhu bukan lalai untuk kedua-dua model ini, jadi larian TIDAK deterministik (berbeza dengan ancaman §11-4 "suhu 0");
kebolehhasilan semula datang dari cache jawapan yang dikomit (ADR-011) bagi dev. **Pemikiran lanjutan dimatikan** supaya setara dengan LLM
lain (jawapan terus). Semua parameter permintaan (model, `max_tokens`, tetapan pemikiran, harga) dalam `config/mypii.yaml`
`garis_dasar.llm.anthropic`; nilai yang dipakai dicatat dalam ADR-016 sebelum larian dev. Jika API menolak parameter yang dirancang,
pengganti direkod dalam ADR-016 SEBELUM sebarang larian, bukan selepas melihat skor.

**Had belanja.** Config `had_usd` (USD 20 untuk dev) ialah kawalan KOS, bukan sebahagian protokol statistik. Lejar belanja dikomit;
klien berhenti SEBELUM panggilan yang boleh melepasi had. Dokumen yang tidak dipanggil kerana had = panggilan gagal: diulang SEKALI ikut
§7 (selepas had dinaikkan oleh manusia), baki yang masih gagal = ramalan kosong dan bilangannya dilapor (§10). Had tidak boleh dijadikan
alasan memilih subset dokumen.

**§7 Perintah tepat (dikemas).** Perintah empat baris §7 TIDAK berubah (`--sistem semua` kini merangkumi dua model Claude). Sebelum
larian, selain `9router.env`, manusia juga memuat kunci Anthropic dalam shell larian SAHAJA: `set -a; . ~/ops/mypii/anthropic.env; set +a`,
dan memastikan `had_usd` mencukupi untuk dua split (anggaran dari lejar dev, dalam NEXT). Entri cache Anthropic atas teks ujian
(`hasil/cache/llm/anthropic*`) dan lejar ujian **JANGAN dikomit** — sama seperti cache LLM lain (§7).

**§14 Bantuan AI (pengecualian tambahan).** Teks dokumen `dev` (larian autopilot) dan `ujian`/`ujian2` (larian MANUSIA §7 sahaja) dihantar
ke API Anthropic. Semua teks sintetik; tiada data peribadi sebenar. Hanya teks dokumen + prompt dihantar; **tiada label emas dan tiada
ramalan sistem lain** dihantar.

**Ancaman tambahan.** (1) **Keluarga yang sama:** Claude ialah keluarga model yang sama dengan pembantu AI (Claude Code) yang menulis
pengecam, penanda aras dan pra-daftar ini (§14). Ini boleh condong ke mana-mana arah (bentuk data yang "dikenali" model, atau tiada
kesan) dan tidak boleh dipisahkan dalam reka bentuk ini — diakui dalam kertas. (2) **Tidak deterministik:** satu larian sahaja setiap split;
varians antara larian tidak diukur. (3) Versi model ialah apa yang dilayan API pada tarikh larian; tarikh dan nama model dicatat dalam
setiap fail hasil.

**Apa yang TIDAK berubah.** Garis dasar sedia ada (susunan, prompt, model), pengecam MyPII (beku), data, metrik, `nilai:`/`pengecam:`/
`jana:`/`iaa:` config, dan peraturan §10–§12. Tiada pindaan lanjut untuk "membaiki" H1e/H1f/H2e/H2f selepas angka dev Claude dilihat;
hanya pembetulan fakta bertarikh dengan sebab.

**English summary of this amendment.** Before either test split is opened, we add two Claude models as baselines, called through the
Anthropic API directly: `anthropic/claude-sonnet-5-5` and `anthropic/claude-haiku-5-5`. New one-sided primary hypotheses H1e/H1f
(MyPII > each Claude model on `ujian2`, exact micro F1 `semua|*`) and secondary H2e/H2f (same on `ujian`). The Holm family grows from
k = 4 to k = 6 per split, key and p-value type; α, bootstrap settings, seeds, the decision rule (both Holm p < 0.05) and the Δ < 0.02
"small" label are unchanged. MDE for k = 6 is computed on dev after the dev run and reported in `docs/BANDINGAN.md`; it does not change
the decision rule. The same unmodified prompt is used; temperature cannot be sent (the API rejects non-default values), so runs are
non-deterministic and dev reproducibility rests on committed response caches; extended thinking is disabled; all request parameters live
in config and are recorded in ADR-016 before the dev run. A USD spending cap is a cost control only: documents not called because of the
cap count as failed calls, are retried once under §7, and remaining failures are reported. Test-split commands in §7 are unchanged but
additionally require loading the Anthropic key; Anthropic caches on test text are never committed. Exception to §14: synthetic document
text (dev by the autopilot; test splits by the human run only) is sent to the Anthropic API — no gold labels or other systems'
predictions. Acknowledged threat: Claude is the same model family as the AI assistant that wrote this codebase and pre-registration.

### 2026-11-03 — Garis dasar eksplorasi (model lain) + pelaksana ujian (sebelum ujian dibuka)
**Status semasa pindaan:** `ujian` dan `ujian2` BELUM dibuka; tiada `--benarkan-ujian` pernah dijalankan (`ls hasil/ | grep ujian`
kosong; tiada `_pradaftar` dalam mana-mana `hasil/*.json`, diperiksa 3 Nov 2026 sebelum komit ini). Tiada satu pun daripada enam model
di bawah pernah dinilai atas mana-mana split MyPII-Bench. Lejar Anthropic = USD 2.066122 (larian dev Sonnet 5.5 + Haiku 5.5) daripada
had USD 20. Pindaan ini dikomit SENDIRI (tanpa kod, config, ujian, skrip atau kebergantungan) sebelum kod probe/eksplorasi ditulis
(PELAN-MODEL-LAIN P1; ADR-017 menyusul).

**Sebab.** Pemilik (3 Nov 2026) mahu MyPII dibandingkan dengan lebih banyak model bahasa, dan mahu ejen autopilot menjalankan ujian
muktamad §7 bagi pihaknya. Menambah enam model ke keluarga Holm (k = 6 → 12) akan menurunkan kuasa hipotesis utama (langkah paling ketat
α/12); pemilik memilih kuasa hipotesis utama kekal. Oleh itu model baharu ditambah sebagai **garis dasar EKSPLORASI**, bukan pengesahan.

**Calon (6) dan keluarga.**

| Sistem | Keluarga | Laluan |
|---|---|---|
| `llm:anthropic/claude-opus-5-5` | Anthropic Claude (Opus) | API Anthropic terus (klien ADR-016) |
| `llm:anthropic/claude-fable-5-1` | Anthropic Claude (Fable) | API Anthropic terus (klien ADR-016) |
| `llm:kr/gpt-5.6-sol` | OpenAI GPT | 9router, `stream: false`, nama model penuh |
| `llm:qd/qmodel` | Alibaba Qwen | 9router |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` | Mistral (berat terbuka kecil) | 9router |
| `llm:rv/zai-org/GLM-5.3-Flash` | Zhipu GLM | 9router |

**Pengecualian keluarga penjana DIKEKALKAN:** tiada Kimi (penjana `ujian2`, §6) dan tiada Gemini (penjana latih/dev-v2, §11-2) — model
yang menjana teks tidak dinilai atas teks itu.

**Status EKSPLORASI (tiada hipotesis).** Bagi setiap calon dan setiap split/kunci, dilapor: F1 + CI bootstrap 95%, ΔF1 (MyPII − calon)
+ CI, dan p mentah (bootstrap berpasangan + ujian rawak) — **TIADA pelarasan Holm, TIADA hipotesis, TIADA peraturan keputusan**. Keluarga
Holm kekal **k = 6** garis dasar pengesahan (presidio-asal, pii-guard, Llama, DeepSeek, Sonnet 5.5, Haiku 5.5); H1a–H1f, H2a–H2f, α = 0.05
sehala, bootstrap (`ulangan: 1000`, `benih: 2026`, `aras: 0.95`), ujian rawak, peraturan keputusan (kedua-dua p Holm < 0.05), label
Δ < 0.02 "kecil" dan MDE §9/pindaan Claude **TIDAK berubah**. Dapatan eksplorasi **tidak boleh dinaikkan menjadi dakwaan pengesahan**
dalam kertas (tiada "MyPII mengatasi X secara signifikan" bagi calon eksplorasi); ia dilapor sebagai deskriptif dengan label
"(eksplorasi)". p mentah eksplorasi tidak dibetulkan untuk perbandingan berganda dan mesti dibaca sedemikian.

**Kriteria probe (sebelum larian penuh; format sahaja).** Setiap calon dipanggil atas **5 dokumen PERTAMA split `dev`** ikut susunan
fail `data/bench/dev.jsonl`, melalui laluan larian penuh yang sama (`garis.ramal_llm`, prompt + suhu sedia ada, kunci cache sama).
**Lulus** = 5/5 panggilan berjaya selepas `llm.ulang` cubaan DAN 5/5 jawapan diurai oleh penghurai span sedia ada (bukan None). **F1
probe TIDAK dikira dan tidak dicetak** — gugur ikut format/kebolehcapaian sahaja, bukan prestasi. Calon yang gagal = **GUGUR** dan
dilapor dengan jenis ralat (cth suhu ditolak, JSON tidak diurai, refusal, tamat masa). **Tiada cubaan kedua** dengan prompt, parameter
atau penghurai lain; tiada prompt berbeza per model. Jawapan probe disimpan dalam cache dan diguna semula oleh larian penuh (bukan larian kedua).

**Parameter Opus 5.5 / Fable 5.1 (ditetapkan SEBELUM probe; fakta API dari dokumentasi Anthropic, 3 Nov 2026).** Kedua-dua model
**tidak boleh mematikan pemikiran** (`thinking: {type: disabled}` = HTTP 400) dan menolak `temperature` → `thinking` dan `temperature`
TIDAK dihantar; `output_config: {effort: "low"}` (paras pemikiran paling rendah yang sah); `max_tokens` **4096** setiap model (token
pemikiran dikira dalam keluaran; 1024 boleh memotong jawapan). **Tiada `fallbacks`** (jawapan dari model lain mencemar garis dasar).
`stop_reason: refusal` = jawapan **rosak** (ramalan kosong, dikira), bukan ralat yang diulang. Jawapan = blok `text` sahaja (blok
`thinking` diabaikan). Harga config: Opus 5.5 USD 4 / 20, Fable 5.1 USD 10 / 50 setiap juta token (masuk / keluar).
**Ancaman ketidaksetaraan tetapan:** Opus/Fable berfikir (effort low) sedangkan Sonnet 5.5 (`between_tools`) dan Haiku 5.5 (`disabled`)
menjawab terus, dan LLM 9router dipanggil tanpa pemikiran khusus. Perbandingan antara calon dan garis dasar pengesahan mencampur kesan
model dengan kesan tetapan pemikiran; ini diakui dan tidak boleh dipisahkan dalam reka bentuk ini.

**Peraturan kos Claude + susunan gugur.** Anggaran satu split bagi calon Claude = token masuk `count_tokens` dev × harga masuk +
(purata token keluar SEBENAR setiap panggilan dari lejar probe) × 1000 dokumen × `margin` (config, 1.5) × harga keluar. **Perlu** =
Σ garis dasar Claude sedia ada (Sonnet + Haiku: 2 × USD lejar dev, untuk `ujian` + `ujian2`, andaian saiz split = dev 1000 dok, §6) +
Σ calon Claude (3 × anggaran: dev + `ujian` + `ujian2`, tolak belanja probe). Bila Perlu > baki lejar (`had_usd` − `jumlah_usd`):
**gugur Fable 5.1 dahulu**, kira semula; masih tidak muat → **gugur Opus 5.5**. `had_usd` (20) **TIDAK dinaikkan** untuk memuatkan calon.
Keputusan ditulis mesin (`hasil/dev-kos-claude.json` blok `rancang_eksplorasi`: `dipilih`, `digugurkan` + sebab, `perlu_ujian_usd`)
SEBELUM larian dev penuh calon Claude. Model gugur (probe atau kos) **dilapor** dengan sebabnya dalam BANDINGAN dan kertas; ia tidak
dianggap "kalah".

**Larian dev.** SATU larian penuh atas `dev` bagi setiap calon yang lulus probe (dan kos, bagi Claude); panggilan gagal sementara =
perintah SAMA sekali lagi (cache disambung). Cache dev dikomit (ADR-011). Model masuk `garis_dasar.llm.model` (di HUJUNG senarai)
hanya bersama cache devnya; oleh itu `--sistem semua` pada §7 merangkumi calon eksplorasi yang lulus, dan hanya itu.

**§7 pelaksana (dikemas).** Pemilik (3 Nov 2026) **membenarkan ejen autopilot** (projek `mypii-ujian`) menjalankan §7 bagi pihaknya
— menggantikan "manusia" dalam tajuk §7 dan NEXT. Syarat: melalui `scripts/ujian-muktamad.sh` sahaja; EMPAT perintah §7 tepat (bait
sama dengan blok kod §7, susunan `ujian2` → `ujian`), SEKALI; ulang SEKALI hanya untuk `panggilan gagal` atau crash separuh jalan (§7,
sebab direkod); prasyarat disemak sebelum harness: tree bersih, tiada `hasil/ujian*`, sha256 split = §6, baki lejar ≥ `perlu_ujian_usd`;
sha HEAD + tarikh UTC + **pelaksana** ("ejen autopilot mypii-ujian atas kebenaran pemilik 3 Nov 2026") direkod SEBELUM larian dalam
arkib luar repo `~/ops/mypii/arkib-ujian/` (bersama hasil, cache ujian, log dan manifest sha256). Cache LLM atas teks ujian **tidak
dikomit** (dipulih dalam repo selepas disalin ke arkib). Skrip itu diuji dengan split palsu sahaja sebelum larian sebenar. **Selepas
keputusan ujian dilihat: tiada perubahan kod, config, prompt, parameter atau PRA-DAFTAR untuk "membaiki" keputusan**; apa-apa dapatan
atau kesilapan = pindaan bertarikh BAHARU yang menyatakan ia dibuat selepas ujian dibuka.

**§14 Bantuan AI (pengecualian tambahan).** Teks dokumen `dev` (larian autopilot) dan `ujian`/`ujian2` (larian §7 sahaja) kini juga
dihantar ke model eksplorasi: API Anthropic (Opus/Fable) dan 9router (penyedia GPT, Qwen, Mistral, GLM). Semua teks sintetik; tiada data
peribadi sebenar; hanya prompt + teks dokumen dihantar — tiada label emas, tiada ramalan sistem lain.

**Apa yang TIDAK berubah.** Garis dasar pengesahan (susunan, prompt, model, parameter, cache), pengecam MyPII (beku), data, metrik,
config `nilai:`/`pengecam:`/`jana:`/`iaa:`, §10–§12. Tiada pindaan lanjut untuk mengubah calon, probe, parameter atau peraturan kos
selepas jawapan probe atau angka dev dilihat; hanya pembetulan fakta bertarikh dengan sebab.

**English summary of this amendment.** Before either test split is opened, six additional LLMs are added as **exploratory baselines**:
`claude-opus-5-5` and `claude-fable-5-1` (Anthropic API direct), and via 9router `kr/gpt-5.6-sol` (GPT), `qd/qmodel` (Qwen),
`cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (Mistral) and `rv/zai-org/GLM-5.3-Flash` (GLM). Generator families stay excluded
(no Kimi, which generated `ujian2`; no Gemini, which generated train/dev). Exploratory systems get F1 with 95% CI, ΔF1 with CI and raw
(unadjusted) p-values only — no hypotheses, no Holm adjustment, no decision rule. The Holm family stays at k = 6 confirmatory baselines;
H1a–H1f/H2a–H2f, α, bootstrap settings, seed and decision rule are unchanged, and exploratory results may not be promoted to
confirmatory claims. A format-only probe on the first 5 `dev` documents (file order) decides inclusion: 5/5 calls succeed and 5/5
answers parse; probe F1 is never computed; failures are dropped and reported, with no retry using a different prompt or parameters.
Opus 5.5 / Fable 5.1 cannot disable thinking and reject temperature, so neither is sent; `effort: low`, `max_tokens` 4096, no
fallbacks, and a `refusal` stop counts as a broken (empty) answer — an acknowledged settings mismatch versus Sonnet/Haiku (thinking off).
Claude cost rule: projected need (existing Sonnet+Haiku for both test splits + 3 × each Claude candidate's estimate with a 1.5 margin
on measured output tokens) must fit the remaining ledger under the unchanged USD 20 cap; otherwise Fable is dropped first, then Opus.
One full dev run per surviving candidate; caches committed. §7 executor: the owner (3 Nov 2026) authorises the autopilot agent
(`mypii-ujian`) to run §7 on their behalf via `scripts/ujian-muktamad.sh` — identical four commands, once, preconditions checked, HEAD
SHA and executor recorded before the run in an off-repo archive, test-text caches not committed, and no code/config/prompt/
preregistration change after results are seen (any later finding is a new dated amendment). §14 exception extended: synthetic document
text is also sent to the exploratory models' providers (Anthropic, and via 9router).

### 2026-11-03 — Penyedia garis dasar DeepSeek (H1d/H2d): cbcn → rv (sebelum ujian dibuka)
**Status semasa pindaan:** `ujian` dan `ujian2` BELUM dibuka — tiada skor, F1 atau ramalan ujian pernah dilihat (`ls hasil/ | grep ^ujian`
kosong; tiada `_pradaftar` dalam mana-mana `hasil/*.json`, diperiksa 3 Nov 2026 22:08Z sebelum komit ini). Cubaan 1 §7 oleh ejen
`mypii-ujian` (MULA 3 Nov 18:24:55Z, sha `3472f21`) **dihentikan 19:06:29Z sebelum sebarang hasil**: perintah 1 sedang memanggil
`llm:cbcn/deepseek-v4.1-flash`, yang memulangkan 0 jawapan; proses dihentikan (CRASH, perintah 1 rc 143), cache ujian dibuang dari repo
(tidak dikomit), tiada `hasil/ujian*` ditulis. Pindaan ini dikomit SENDIRI (tanpa config, cache, hasil, kod atau ujian) sebelum id model
diubah dalam config (PELAN-PINDAAN-DEEPSEEK P1; config + garis dasar dev baharu = P2, komit berasingan).

**Sebab.** Laluan `cbcn/` (penyedia pertama melalui 9router) tidak lagi boleh dipanggil [disunting: butiran akaun penyedia API],
tanpa perubahan dalam ~23 jam, dan tidak pulih. Tanpa pindaan, DeepSeek akan menjadi ramalan kosong 1000/1000 pada kedua-dua split dan H1d/H2d hilang makna.

**Keputusan pemilik.** 3 Nov 2026 21:23Z, pilihan (2) daripada tiga ("2 tukar penyedia · Guna model river ai"; D-11): guna model
DeepSeek-V4.1-Flash yang SAMA melalui River AI (`rv/`) di 9router. Pilihan yang tidak diambil: (1) [disunting: pilihan akaun penyedia API],
(3) gugurkan H1d/H2d.

**Bukti (curl `POST /v1/chat/completions` 9router, `stream: false`, prompt "Jawab OK sahaja.", kunci khas mypii):**

| Tarikh UTC | Model | HTTP | `object` / ralat |
|---|---|---|---|
| 2026-11-03T22:07:57Z | `rv/deepseek-ai/DeepSeek-V4.1-Flash` | 200 | `chat.completion` (model dijawab `deepseek-ai/DeepSeek-V4.1-Flash`) |
| 2026-11-03T22:07:58Z | `cbcn/deepseek-v4.1-flash` (kawalan) | 404 | "No active credentials for provider: [disunting]" |

ID huruf kecil `rv/deepseek-v4.1-flash` = 503 (diukur 3 Nov 21:25Z, D-12) — ID PENUH dipakai.

**Apa berubah.** Id penyedia SAHAJA bagi garis dasar pengesahan H1d/H2d: `llm:cbcn/deepseek-v4.1-flash` → `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash`
(model DeepSeek-V4.1-Flash sama, River AI melalui 9router). Unsur itu kekal pada KEDUDUKAN yang sama dalam `garis_dasar.llm.model`, jadi
label H1d/H2d kekal DeepSeek. Garis dasar dev DeepSeek **dijana SEMULA** atas `rv/` (1000 dokumen dev, cache baharu dikomit) SEBELUM ujian
dibuka; cache `cbcn` lama tidak dipinjam dan tidak diubah (rekod sejarah). Angka dev baharu = nota fakta bertarikh susulan di bawah pindaan
ini (PELAN-PINDAAN-DEEPSEEK P2).

**Apa yang TIDAK berubah.** Prompt `garis_dasar.llm.prompt`, suhu 0, `stream: false`, satu mesej pengguna, penghurai span; hipotesis
H1a–H1f/H2a–H2f, arah sehala, α = 0.05, keluarga Holm k = 6, bootstrap (`ulangan: 1000`, `benih: 2026`, `aras: 0.95`), ujian rawak,
peraturan keputusan (kedua-dua p Holm < 0.05), label Δ < 0.02 "kecil"; §7 (empat perintah bait sama); split, sha256 §6 dan `KUNCI*.json`;
calon eksplorasi (Mistral Small 3.1, GLM-5.3-Flash). `llm.penjana` (`cbcn/kimi-k3`, penjana `ujian2` — sejarah, dimeterai) dan `iaa.model`
(`cbcn/glm-5.3`, cache 300/300 selesai) KEKAL `cbcn/`: kedua-duanya tidak dipanggil oleh §7, dan menukarnya membatalkan meterai/cache.

**Ancaman kesahan tambahan.** Model sama, penyedia berbeza: kuantisasi, templat sembang, versi pelayan atau had panjang di River AI boleh
berbeza daripada penyedia `cbcn/`. Diakui; oleh itu garis dasar dev dijana semula atas `rv/`, dan F1 dev DeepSeek baharu dilapor
BERSEBELAHAN angka `cbcn` lama (0.7479 [0.7197, 0.7742]) — beza besar dilapor seperti adanya, tidak "dibaiki" dan tidak menukar model lain
(pertukaran lain = pindaan baharu oleh pemilik).

**Larian ujian selepas pindaan.** Cubaan 1 crash sebelum hasil, jadi peraturan §7 "larian yang crash separuh jalan boleh diulang SEKALI"
terpakai: `scripts/ujian-muktamad.sh --ulang-crash` dijalankan SEKALI atas HEAD SELEPAS pindaan ini + config P2 (sha HEAD baharu direkod
dalam `ULANG-CRASH` arkib). Ini bukan larian kedua: tiada skor ujian wujud dari cubaan 1. Kod skrip dan harness tidak berubah.

**English summary of this amendment.** Before either test split is opened (no test score, F1 or prediction has been seen; attempt 1 of §7
was stopped at 19:06Z on 3 Nov before any result because the DeepSeek route returned nothing), the provider of confirmatory baseline
H1d/H2d changes from `cbcn/deepseek-v4.1-flash` (first provider via 9router; no longer callable [redacted: API provider account details]) to
`rv/deepseek-ai/DeepSeek-V4.1-Flash` — the same DeepSeek-V4.1-Flash model served by River AI via 9router — by owner decision on 3 Nov 2026
21:23Z (option 2, D-11). Evidence: curl at 22:07:57Z returned 200 `chat.completion` for `rv/` and 404 "No active credentials" for `cbcn/`.
Only the provider id changes (same list position, so H1d/H2d remain DeepSeek). Prompt, temperature 0, hypotheses, α, Holm k = 6,
bootstrap settings, seed, decision rule, the four §7 commands, splits and keys are unchanged; the generator (`cbcn/kimi-k3`) and IAA model
(`cbcn/glm-5.3`) entries stay as historical records. The dev DeepSeek baseline is regenerated on `rv/` before testing and reported next to
the old `cbcn` dev F1 (0.7479); a different-provider threat (quantisation, chat template, server version) is acknowledged. Because
attempt 1 crashed before results, `--ulang-crash` is run ONCE on the HEAD after this amendment.

#### Nota fakta 2026-11-03 — garis dasar dev DeepSeek atas `rv/` (dev SAHAJA; tiada perubahan hipotesis)
Dijana mengikut pindaan di atas (PELAN-PINDAAN-DEEPSEEK P2), sebelum `ujian`/`ujian2` dibuka. `make nilai-garis` dev 3 Nov 2026
22:17–22:24Z: `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` dokumen 1000, panggilan 1000, gagal 0, rosak 0; model lain semuanya dari cache
(panggilan 0), lejar Anthropic bait sama. Ulang tanpa kunci: dari cache 1000, angka sama. Prompt, suhu dan penghurai tidak berubah.

| dev (1000 dok) | `cbcn/` lama | `rv/` baharu |
|---|---|---|
| F1 tepat `*` [CI 95%] | 0.7479 [0.7197, 0.7742] | **0.7193** [0.6899, 0.7483] |
| P / R `*` (ramalan; emas 836) | 0.599 / 0.9952 (1389) | 0.5624 / 0.9976 (1483) |
| F1 MY_NRIC / MY_PHONE / MY_SSM | 0.7126 / 0.8551 / 0.652 | 0.6757 / 0.8359 / 0.627 |
| Δ MyPII − DeepSeek `*` [CI 95%], p Holm bootstrap | +0.1398 [0.1193, 0.1622], 0.0 | +0.1684 [0.1467, 0.1897], 0.0 |
| SE Δ · MDE α/k = 0.008333 · MDE α = 0.05 (`make kuasa`) | 0.0109 · 0.0354 · 0.0272 | 0.011 · 0.0355 · 0.0273 |

Beza F1 `*` rv − cbcn = −0.0286 (penyedia berbeza; terutamanya ketepatan lebih rendah, lebih banyak ramalan palsu). Dilapor seperti adanya;
tiada model, prompt atau peraturan diubah. *English:* on dev the DeepSeek-V4.1-Flash baseline served by River AI scores F1 0.7193 (old
`cbcn/` route 0.7479); MyPII − DeepSeek Δ = +0.1684, MDE 0.0355 at α/k. Dev only; hypotheses and decision rule unchanged.

### 2026-11-04 — MyPII v2: dev3 + ujian3 (selepas ujian v1 dibuka)
**Status semasa pindaan:** `ujian` dan `ujian2` (v1) **SUDAH DIBUKA** — sekali, oleh ejen autopilot `mypii-ujian` melalui
`scripts/ujian-muktamad.sh --ulang-crash` (larian bermula 2026-11-03T23:47:24Z, `SELESAI` 2026-11-04T04:14:40Z, sha `e846e49`, arkib
`~/ops/mypii/arkib-ujian/20261103T182455Z/`). Keputusan v1 (H1a–H1f, H2a–H2f; angka dalam `docs/LOG-ITERASI.md` dari `RINGKASAN.json`)
adalah **MUKTAMAD**: tidak dianalisis semula, tidak dijalankan semula, dan tiada pindaan di bawah ini mengubah §1–§15 atau pindaan
terdahulu bagi v1. Kod v1 = tag git `mypii-v1-muktamad` → `e846e49` (sha larian yang menghasilkan keputusan; pengecam sama dengan MULA
`3472f21`, `git diff` `mypii/pengecam` = 0 baris). Data v3 (`latih3`/`dev3`/`ujian3`) **BELUM WUJUD**; tiada sistem pernah dinilai
atasnya. Pindaan ini dikomit SENDIRI (dokumen sahaja: tiada kod, config, data, ujian, skrip atau kebergantungan) sebelum sebarang
kod/config/data v3 ditulis (PELAN-V2 P2; ADR-018). Ia ialah **kajian kedua** dengan split ujian baharu — bukan larian kedua v1.

**Sebab.** Pemilik (3 Nov 2026): «tambah baik sampai lebih padu». `docs/ANALISIS-RALAT.md` §2–§3 (28 Okt, atas dev + probe sintetik,
SEBELUM ujian dibuka) mencatat kategori yang pengecam v1 tidak kesan langsung atau tersalah tangkap. Dev-v2 dan ujian v1 tiada kes itu,
jadi pembaikan perlu data baharu dan split ujian baharu yang belum dilihat.

**Data v3 (Keputusan reka bentuk 3, PELAN-V2).**
- Folder `data/bench_v3/`; split v1 (`data/bench/*`, `data/templat*/`, `data/nama*.yaml` sedia ada) kekal bait-demi-bait sama
  (`make jana` → tiada diff, gerbang). Nilai baharu dalam modul baharu `mypii/jana/nilai_v3.py` dengan rng split v3 sendiri.
- Saiz: **latih3 3000, dev3 1000, ujian3 1000** dokumen. Benih = `jana.benih` (20261028) **+ 3** untuk latih3/dev3 (20261031) dan
  **+ 4** untuk ujian3 (20261032). Saiz, benih, nisbah dan kebarangkalian slot dalam `config/mypii.yaml` `jana_v3:` (P3).
- Cincangan: `data/bench_v3/CINCANGAN3.json` (latih3/dev3) dan `data/bench_v3/KUNCI3.json` (ujian3, sha256 bait fail jsonl);
  meterai `data/bench_v3/UJIAN3-MUKTAMAD` (kandungan = sha KUNCI3) dikomit SENDIRI selepas penyemak meluluskan penjanaan ujian3.
- **Kategori baharu dan peraturan label** (entiti kekal `MY_NRIC`, `MY_SSM`, `MY_PHONE`; label = span ASAL dalam teks, mula/tamat tepat):
  - (a) **ROB lama — GUGUR.** P1 (`docs/sumber/SSM-ROB-TELEFON.md`) tidak menemui sumber rasmi bagi bentuk ROB lama atau awalan negeri
    → `config/ssm_rob.yaml` `awalan_disahkan: []` → slot `{MY_ROB}` TIDAK dijana dan TIDAK dikesan dalam v2. Dilapor sebagai had.
  - (b) **SSM 12 digit LLP**: kod entiti 04–06, tahun ≥ 2012 (Akta LLP 2012 berkuat kuasa 26 Dis 2012, P.U. (B) 421/2012;
    `jana_v3.llp_tahun_min`) → `MY_SSM`.
  - (c) **Talian tetap Sabah/Sarawak** kod kawasan 082–089 (MCMC NEAP; julat sah libphonenumber, ADR-002) → `MY_PHONE`.
  - (d) **OCR dalam nombor** (satu aksara `O`↔0, `l`↔1, `S`↔5, `B`↔8 di dalam nombor) dan **patah baris** (nombor dipecah oleh
    `\n` di sempadan kumpulan) → entiti nombor asal; span emas = subrentetan tepat termasuk aksara OCR/patah baris.
  - (e) **Negatif 12 digit tanpa kata negatif** (no. ahli/polisi/akaun berbentuk MyKad sah; tiada kata dari `konteks_umum.negatif`)
    → TIADA label.
- **Templat:** latih3 + dev3 = templat LLM **keluarga A** (+ slot kategori b–e); ujian3 = templat LLM **keluarga B** sahaja
  (`data/templat_ujian3/`), genre berbeza daripada semua genre lama, nama dari `data/nama_ujian3.yaml` yang **bersilang kosong** dengan
  setiap fail nama lain. Templat mengandungi slot; nilai entiti dijana oleh kod MyPII (seperti v1).
- **Calon penjana dan susunan (calon pertama yang lulus probe dipakai; tiada calon lain):**

| peranan | calon 1 | sandaran |
|---|---|---|
| latih3 + dev3 (keluarga A) | `stp/step-3.7-flash` (StepFun Step) | `cbai/hy3-preview` (Tencent Hunyuan) |
| ujian3 (keluarga B) | `cbai/minimax-m3` (MiniMax) | `gcli/grok-4.7` (xAI Grok) |

  Keluarga A ≠ keluarga B, dan kedua-duanya ≠ mana-mana penjana lepas (Gemini latih/dev-v2, Kimi ujian2, GLM sandaran/IAA) atau garis
  dasar lepas (Llama, DeepSeek, Claude, Mistral, GLM, GPT, Qwen). **Probe = format sahaja** (permintaan penjanaan kecil; lulus = jawapan
  diurai dan lulus pengesah templat; tiada skor). Semua calon satu peranan gagal = projek BERHENTI (tiada model lain dipilih tanpa
  pindaan baharu).

**Pengecam v2 dan pengelas konteks (Keputusan 4).** Perubahan pengecam (normalisasi OCR bila diapit digit, patah baris, LLP ≥ 2012,
talian Sabah/Sarawak, pengelas konteks) ditala atas **dev3 sahaja**. Pengelas konteks (regresi logistik, scikit-learn sebagai alat
LATIH sahaja) dilatih atas **latih3 SAHAJA** — kod latih menolak split lain sebelum fail dibaca; artifak `model/konteks-v2.json` (sha256
dalam config). **Ramalan tanpa API/rangkaian**: pengecam v2 hanya numpy + Presidio tempatan; tiada klien LLM dalam `mypii/pengecam/`.
Pengecam v2 **BEKU** pada pindaan kedua (di bawah) sebelum ujian3 dibuka.

**Hipotesis v2 (keluarga Holm BAHARU, k = 2; berasingan daripada H1/H2/H3 v1).**

| ID | Hipotesis (sehala, atas `ujian3`, F1 tepat mikro `semua|*`) | Status |
|---|---|---|
| **H4a** | MyPII-v2 **bukan-inferior** kepada `llm:anthropic/claude-haiku-5-5`: Δ = F1(v2) − F1(Haiku) > −δ, **δ = 0.01** (H0: Δ ≤ −0.01) | **utama (pengesahan)** |
| **H4b** | MyPII-v2 > MyPII-v1 (kod tag `mypii-v1-muktamad`): Δ = F1(v2) − F1(v1) > 0 | **utama (pengesahan)** |
| — | per entiti, per kategori (b)–(e), per bahasa, P/R, F1 separa; `presidio-asal` | **deskriptif** (tiada ujian) |

- **Ujian dan peraturan keputusan.** Bootstrap persentil berpasangan, unit = **dokumen**, `ulangan: 1000`, `benih: 2026`, `aras: 0.95`
  (sama dengan v1). H4a: p bootstrap sehala atas Δ dianjak margin (Berg-Kirkpatrick dengan Δ+δ menggantikan Δ: p = #(Δ*+δ > 2(Δ̂+δ))/B);
  ujian rawak menguji Δ = 0 sahaja, jadi bagi H4a ia dilapor deskriptif dan TIDAK menjadi syarat. H4b: p bootstrap sehala DAN p ujian
  rawak (R = 1000), seperti §8. **Holm k = 2** atas p bootstrap {H4a, H4b}; p rawak H4b diselaraskan Bonferroni k = 2 (≥ Holm, lebih
  ketat). α = 0.05 keluarga, sehala. **Disokong:** H4a iff p Holm bootstrap < 0.05; H4b iff p Holm bootstrap < 0.05 DAN p rawak × 2 < 0.05.
  Lantai p bootstrap 0 dilapor "< 1/B". Δ + CI 95% dilapor bersama setiap p; Δ < 0.02 bagi H4b dilapor "beza kecil" walau disokong.
- Metrik, `harness.skor`/`_sama`/`_bertindih`, prompt `garis_dasar.llm.prompt` dan susunan garis dasar sedia ada **tidak berubah**.
  H4a/H4b, δ, α, metrik dan peraturan ini **tidak diubah selepas angka dev3 dilihat** (pembetulan fakta sahaja, bertarikh, dengan sebab).
  Pengubahan selepas melihat dev3 (termasuk Haiku dev3) dibenarkan HANYA pada pengecam — itu tujuan dev.
- **MDE** H4a/H4b dikira dengan `make kuasa` atas bootstrap dev3 (k = 2) dan ditambah sebagai **pindaan KEDUA bertarikh** (tajuk
  mengandungi "MyPII v2") SEBELUM ujian3 dibuka, bersama sha pengecam yang dibekukan, ambang pengelas dan sha artifak. MDE maklumat
  sahaja; ia tidak mengubah hipotesis atau peraturan keputusan.

**Claude Haiku 5.5 atas dev3 + ujian3.** Laluan sedia ada sahaja (`garis.ramal_llm`, klien ADR-016: prompt sama, pemikiran
`disabled`, suhu tidak dihantar, `max_tokens` config); model Claude lain TIDAK dinilai dalam v2. dev3: SATU larian penuh (gagal
sementara = perintah sama sekali lagi, cache disambung); cache dev3 + lejar dikomit. **Kos:** sebelum larian dev3, `make kos-claude`
(count_tokens) menganggar dev3 dan ujian3; **baki** = `had_usd` (20, TIDAK dinaikkan) − lejar repo − belanja ujian v1 yang tidak dikomit
(`RINGKASAN.json` v1 `lejar_usd_selepas` 5.535451 − lejar repo 2.135548 = USD 3.399903). Baki < anggaran dev3 + ujian3 × 1.5 = larian
dev3 TIDAK dibuat dan **H4a dilapor "tidak diuji"** (bukan had dinaikkan). Tidak deterministik: satu larian setiap split (ancaman §11-4
seperti pindaan Claude).

#### §7-v2 Perintah tepat ujian3
```
uv run --extra nilai --extra garis python -m mypii.nilai.harness --split ujian3 --sistem mypii mypii-v1 presidio-asal llm:anthropic/claude-haiku-5-5 --benarkan-ujian
uv run python -m mypii.nilai.harness --split ujian3 --sistem mypii mypii-v1 presidio-asal llm:anthropic/claude-haiku-5-5 --statistik --benarkan-ujian
```
- `mypii` = pengecam v2 (HEAD beku); `mypii-v1` = pengecam + config `pengecam:` dari tag `mypii-v1-muktamad`, dimuat dari `git worktree`
  sementara pada tag itu (harness enggan bila sha worktree ≠ tag), dibuang selepas larian. Rujukan statistik = `mypii`; keluarga Holm =
  {`llm:anthropic/claude-haiku-5-5`, `mypii-v1`}; `presidio-asal` deskriptif (di luar Holm). Flag `--split ujian3` + sistem `mypii-v1`
  dibina kemudian (PELAN-V2 P4/P14); perintah di atas ialah teks yang skrip mesti padankan bait-demi-bait.
- **Pelaksana:** ejen autopilot `mypii-v2` atas ayat pemilik 3 Nov 2026 («v2 atas ujian3»), melalui `scripts/ujian3-muktamad.sh`
  SAHAJA, **SEKALI**. Prasyarat sebelum harness: tree bersih; `make uji` lulus; tiada `hasil/*ujian3*` atau `MULA` arkib; sha256
  `ujian3.jsonl` = `KUNCI3.json` = `UJIAN3-MUKTAMAD`; pindaan kedua "MyPII v2" wujud dalam HEAD; baki lejar ≥ anggaran Haiku ujian3 × 1.5.
  sha HEAD + tarikh UTC + pelaksana direkod SEBELUM larian dalam arkib luar repo **`~/ops/mypii/arkib-ujian3/<ts>/`** (MULA, SELESAI,
  RINGKASAN.json, log, cache, manifest sha256). Ulang: `panggilan gagal` = perintah sama SEKALI (cache disambung); crash separuh jalan =
  `--ulang-crash "<sebab>"` SEKALI dengan kod sama (sebab dalam arkib). **Cache LLM atas teks ujian3 dan lejar ujian3 TIDAK dikomit.**
  Selepas keputusan dilihat: tiada perubahan kod, config, prompt, data atau pindaan untuk "membaiki"; dapatan = pindaan bertarikh BAHARU.

**Apa yang dilapor walau buruk.** H4a/H4b (Δ, CI, p mentah + Holm, kedua-dua jenis), termasuk tidak disokong; F1 setiap sistem × kunci
(`*` + 3 entiti) × kategori (b)–(e) × bahasa; jurang dev3 → ujian3 (dev3 ditala); kategori (a) gugur dan sebabnya; bilangan panggilan
Haiku gagal/rosak; kos sebenar.

**Apa yang TIDAK dibuat.** Tiada larian atau analisis semula `ujian`/`ujian2`; tiada perubahan `docs/BANDINGAN.md` v1 atau hasil v1;
tiada tala pengecam/pengelas atas ujian3 atau latih pengelas atas selain latih3; tiada larian ujian3 kedua; tiada garis dasar ditambah
atau dibuang selepas data dilihat (garis dasar eksplorasi v1 lain, Sonnet/Opus/Fable dan pii-guard TIDAK dijalankan atas v3); tiada
pengecualian dokumen; tiada analisis kuasa post-hoc; `had_usd` tidak dinaikkan.

**Ancaman kesahan tambahan.** (1) **Kitaran yang lebih kuat:** nilai kategori (b)–(e) dijana oleh `nilai_v3.py` yang ditulis oleh
pembina yang sama yang menulis pengecam v2 — ujian3 mengukur liputan bentuk yang dijangka, bukan realisme; penjana templat keluarga B
mengurangkan, tidak menghapus, kesan ini. (2) **Pengelas dari penjana A:** pengelas konteks belajar gaya keluarga A; ujian3 (B) menguji
pemindahan gaya, tetapi dua keluarga tidak mewakili teks sebenar. (3) **v1 tidak pernah melihat kategori baharu** → H4b dijangka besar
dan bukan bukti generalisasi melebihi kategori itu. (4) **Pengetahuan selepas ujian v1:** reka bentuk v2 ditulis selepas ujian v1 dibuka
dan keputusan ringkasnya dilihat oleh pembina; kategori datang dari ANALISIS-RALAT (sebelum ujian), dan ujian3 belum wujud. (5) Label
telefon Sabah/Sarawak = julat libphonenumber (ADR-002, recall optimis). (6) Claude Haiku = keluarga pembantu yang menulis kod (pindaan
Claude). (7) Satu split ujian3 dari satu penjana B — tiada replikasi.

**§14 Bantuan AI (pengecualian v2).** Teks sintetik `dev3` (autopilot) dan `ujian3` (§7-v2 sahaja) dihantar ke API Anthropic (Haiku 5.5).
Arahan penjanaan templat (genre, slot, contoh) dihantar ke penyedia penjana melalui 9router (StepFun/Tencent untuk A; MiniMax/xAI untuk B).
Tiada data peribadi sebenar; tiada label emas atau ramalan sistem lain dihantar. Pengecam, penjana, pengelas dan pindaan ini ditulis
dengan bantuan ejen Claude (Claude Code); kertas akan mendedahkannya.

**English summary of this amendment.** MyPII v1 test splits (`ujian`, `ujian2`) were opened once on 3–4 Nov 2026 (run start
23:47:24Z, finish 04:14:40Z, sha `e846e49`, tag `mypii-v1-muktamad`); those results are final and are not re-analysed. This amendment,
committed alone before any v3 code, config or data, registers a **second study**: new data v3 in `data/bench_v3/` — train3 3,000, dev3
1,000, test3 (`ujian3`) 1,000 documents, seeds base+3 (train3/dev3) and base+4 (test3), v1 splits byte-identical. New categories:
(a) old ROB numbers **dropped** (no official SSM source for their format; not generated, not detected); (b) 12-digit LLP SSM numbers,
entity codes 04–06, year ≥ 2012; (c) Sabah/Sarawak landlines 082–089 (libphonenumber-valid); (d) one OCR character inside a number and
numbers split across a line break, gold span = exact original substring; (e) 12-digit MyKad-shaped negatives without negative cue words
(no label). Templates: train3/dev3 from generator family A (`stp/step-3.7-flash`, fallback `cbai/hy3-preview`), test3 from family B
(`cbai/minimax-m3`, fallback `gcli/grok-4.7`); A ≠ B and neither matches any earlier generator or baseline family; format-only probe,
first passing candidate used, all failing = stop. Test3 names disjoint from every other name file; test3 sealed (`KUNCI3.json`,
`UJIAN3-MUKTAMAD`) and never read by the builder. The recognizer is tuned on dev3 only; a small local context classifier (logistic
regression) is trained on train3 only and predicts without any API or network. **H4a** (primary): on test3, MyPII-v2 exact micro F1 is
non-inferior to Claude Haiku 5.5 with margin δ = 0.01 (one-sided shifted paired bootstrap). **H4b** (primary): MyPII-v2 > MyPII-v1 (tagged
code) on test3 (paired bootstrap and approximate randomization). New Holm family k = 2 over bootstrap p; H4b's randomization p is
Bonferroni-adjusted (×2); α = 0.05 one-sided; bootstrap B = 1000, seed 2026, document resampling, 95% CI — unchanged from v1. Hypotheses,
δ, α and metrics are fixed before any dev3 number is seen. MDE from dev3 is added as a second dated amendment before test3 is opened,
together with the frozen recognizer SHA and classifier threshold/artifact SHA. Haiku runs through the existing client on dev3 (once,
cached, committed) and test3 (cache not committed); the USD 20 cap is not raised — remaining budget accounts for uncommitted v1 test spend
(USD 3.399903); insufficient budget means H4a is reported "not tested". The exact two test3 commands are in the §7-v2 block above; the
executor is the autopilot agent `mypii-v2` on the owner's 3 Nov instruction, once, through `scripts/ujian3-muktamad.sh`, with an off-repo
archive `~/ops/mypii/arkib-ujian3/`, one retry only for failed calls or a mid-run crash, and no change after results are seen. Reported
regardless: all hypotheses, per entity/category/language results, dev3→test3 gap, dropped category (a), Haiku failures and cost. Not
done: no re-run of v1 tests, no tuning on test3, no second test3 run, no baseline changes after data are seen. Threats: stronger
generator–recognizer circularity (values and recognizer by the same author), classifier trained on family-A style, v1 never saw the new
categories, design written after v1 test results were seen, libphonenumber-validated phone labels, Claude same family as the coding
assistant, a single test3 split.

### 2026-11-04 — Pembetulan fakta (rujukan config tahun minimum LLP, kategori (b))
Pembetulan rujukan sahaja, sebelum mana-mana angka dev3 dilihat; tiada hipotesis, δ, α, metrik, data atau nilai berubah. Pindaan v2
di atas (kategori (b)) merujuk tahun minimum LLP sebagai `jana_v3.llp_tahun_min`. Kunci pendua itu dibuang dari `config/mypii.yaml`
kerana semakan bebas mendapati ia boleh menyimpang daripada fakta rasmi tanpa ujian merah. Nilai kekal **2012** (Akta 743 berkuat
kuasa 26 Dis 2012, P.U. (B) 421/2012) dan kini dibaca dari SATU sumber: `config/ssm_rob.yaml` `llp.tahun_min`, diuji sama dengan tahun
`llp.berkuat_kuasa`.

### 2026-11-05 — MyPII v2: calon penjana keluarga A diganti + probe merentas genre (sebelum templat v3 dijana)
**Status semasa pindaan:** templat latih3/dev3/ujian3 BELUM dijana; `data/probe/` tiada fail penjana; tiada angka dev3 dilihat; ujian3
belum wujud. Hipotesis H4a/H4b, δ, α, Holm k = 2, metrik, saiz, benih, kategori (a)–(e) dan calon ujian3 **TIDAK berubah**. Pindaan ini
mengubah DUA perkara sahaja: calon keluarga A, dan cara probe dinilai. Diputuskan pemilik dalam sesi interaktif 5 Nov 2026.

**Apa yang berlaku (didedahkan penuh).**
- **4 Nov (probe rasmi pertama, `make templat-llm-probe SASARAN=latih3`, fail di luar repo
  `~/ops/autopilot/state/mypii-v2/probe-penjana-latih3-20261104.json`):** `stp/step-3.7-flash` sah 0/4 (4 × `nombor_literal` — gagal
  KUALITI); `cbai/hy3-preview` 3 × HTTPError → 429 [disunting: butiran akaun penyedia API] (tidak pernah menjawab; kualiti tidak diuji). Mengikut pindaan
  2026-11-04, kerja BERHENTI. Fail itu tidak dikomit, jadi `data/probe/penjana-latih3.json` tidak wujud dalam repo.
- **5 Nov:** laluan `cbai/` masih 403 [disunting: butiran akaun penyedia API] → Hunyuan **tidak boleh diuji**, bukan gagal
  kualiti.
- **5 Nov, probe PERCUBAAN di luar repo** (prompt + pengesah sama dengan probe rasmi; tidak menulis `data/probe/`; latih3 sahaja, bukan
  ujian) ke atas `rv/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4`, bahasa `ms`: penyata_bank 4/4 kemudian 1/4 (dua larian),
  keahlian 1/4, polisi_takaful 4/4, tempahan_hotel 3/4 — jumlah 13/20; setiap tolakan = `bahasa_tidak_dinilai` (templat terlalu ringkas
  untuk kata fungsi ≥ 3), tiada `nombor_literal`/`jenama`/`panjang`. Ini menunjukkan probe satu genre pada suhu 0.8 ialah satu lambungan.
  Percubaan ini dilihat SEBELUM pindaan ditulis; ia menilai format sahaja (tiada skor F1, tiada data v3).

**Perubahan 1 — calon keluarga A (latih3 + dev3).**

| peranan | calon 1 | sandaran |
|---|---|---|
| latih3 + dev3 (keluarga A) | `rv/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4` (NVIDIA Nemotron) | tiada |
| ujian3 (keluarga B) | `cbai/minimax-m3` (MiniMax) — tidak berubah | `gcli/grok-4.7` (xAI Grok) — tidak berubah |

StepFun dan Tencent dikeluarkan dari keluarga A. NVIDIA ≠ keluarga B, dan ≠ mana-mana penjana/garis dasar lepas (`keluarga_larangan`).
Had: Nemotron 3.5 ialah model NVIDIA sendiri; keluarga Nemotron lama (≤ 2025) diperhalusi dari Llama — disebut sebagai had kemungkinan
pertindihan gaya dengan garis dasar Llama 3.3 (garis dasar, bukan penjana).

**Perubahan 2 — probe merentas genre** (terpakai pada SEMUA probe v3 selepas tarikh ini, termasuk ujian3). Setiap calon diprobe atas
`probe.genre` = **4** genre pertama sasaran (bahasa pertama), satu permintaan setiap genre (`templat` 4 + `negatif` 1, seperti dahulu).
Lulus = JUMLAH templat sah ≥ `min_nisbah_sah` (**0.5**, tidak berubah) × 4 × 4 = **8/16**. Genre yang tidak menjawab = 0 sah. Fail
probe tetap SEKALI, tidak ditindih; semua calon gagal = BERHENTI seperti dahulu. Kod: `probe_v3` (`mypii/jana/templat_llm.py`); ADR-019.

**Apa yang TIDAK dibuat:** tiada perubahan pada pengesah templat, prompt penjanaan, ambang `min_nisbah_sah`, hipotesis, atau calon
ujian3; probe percubaan TIDAK dipakai sebagai keputusan (probe rasmi dijalankan selepas komit ini); tiada model lain dicuba untuk keluarga A.

**English summary.** Generator family A (train3/dev3) is replaced: StepFun failed the 4 Nov format probe on quality (0/4, literal
numbers); Tencent Hunyuan never answered (provider route unavailable [redacted: API provider account details], 5 Nov) and could not be
tested. New sole candidate: NVIDIA Nemotron 3.5 Super (`rv/`), no fallback. A pre-amendment trial probe outside the repo (format only,
train3 Malay; 13/20 valid across 4 genres, one genre 4/4 then 1/4 on rerun) showed a single-genre probe at temperature 0.8 is a coin
toss, so the probe now pools the first 4 genres: pass iff valid templates ≥ 0.5 × 16 = 8 (threshold unchanged). Hypotheses, test set
generator candidates, sizes, seeds and analysis are unchanged.

### 2026-11-05 (b) — MyPII v2: dua panggilan penjana setiap bahasa × genre latih3 (selepas dua kegagalan ambang)
**Status semasa pindaan:** probe rasmi latih3 dikomit (`64bb303`, Nemotron sah 15/16). `make templat-llm SASARAN=latih3` dijalankan DUA
kali dengan prompt, pengesah dan ambang yang sama: 216 dan 222 templat sah < `min_templat` 240; tiada fail ditulis (kod menolak
menulis bila ambang gagal); kategori b–e lulus kedua-dua kali. Bahasa Inggeris 28 setiap kali (templat notifikasi ringkas < 3 kata
fungsi → `bahasa_tidak_dinilai`); ms 74–76, manglish 112–120 (`docs/LOG-ITERASI.md`). Tiada angka dev3 dilihat; ujian3 belum wujud.

**Perubahan (satu sahaja).** `templat_llm.sasaran.latih3.panggilan: 2` — penjana dipanggil DUA kali bagi setiap pasangan bahasa × genre
(prompt sama, suhu sama), jawapan digabung SEBELUM pengesah, jadi pendua antara dua panggilan ditolak seperti biasa. Lalai sasaran lain
kekal 1 (ujian3 tidak berubah). Pengesah, prompt, `min_templat` 240, `min_kategori`, `min_genre_setiap_bahasa`, model dan semua
hipotesis TIDAK berubah. Larian ketiga dengan `panggilan: 2` dijalankan SEKALI; gagal ambang lagi = BERHENTI dan pindaan pemilik.

**Pilihan yang ditolak (dicatat kerana dibincang dengan pemilik):** menurunkan `min_templat` (mengubah kriteria selepas melihat hasil);
menambah arahan "ayat penuh" pada prompt (mengubah reka bentuk data selepas melihat output); mencuba lagi tanpa perubahan sehingga
lulus (memilih ikut nasib). Kesan yang diketahui: bahagian Inggeris latih3 kekal kecil berbanding ms/manglish — dilapor sebagai had
(pengelas konteks melihat lebih sedikit contoh Inggeris).

**English summary.** Train3 template generation with Nemotron missed `min_templat` 240 twice (216, 222; English 28 each time because
short notification-style templates have < 3 function words and fail the language check). Change: two generator calls per
language × genre for train3 (same prompt and temperature), pooled before the unchanged validator; one run only, failure = stop.
Thresholds, validator, prompt, model and hypotheses are unchanged; test3 keeps one call per pair.

### 2026-11-05 (c) — MyPII v2: keluarga B (ujian3) = Mistral → Claude Sonnet (keputusan pemilik)
**Status semasa pindaan:** templat latih3 + data latih3/dev3 dikomit (`00e28b8`); garis dasar dev3 mypii-v1 0.6149, presidio-asal 0.2902
(sahaja; tiada sistem v2 dinilai). `data/templat_ujian3/`, `data/nama_ujian3.yaml`, `data/probe/penjana-ujian3.json` dan ujian3 BELUM
wujud. H4a/H4b, δ, α, Holm k = 2, metrik, saiz, benih dan kategori TIDAK berubah.

**Sebab.** Kedua-dua calon B pindaan 2026-11-04 tidak boleh dipanggil (diukur 5 Nov): `cbai/minimax-m3` = 429/403
[disunting: butiran akaun penyedia API]; laluan ganti `oc/minimax-m3-free` = "Model is unavailable"; `gcli/grok-4.7` = had kuota
dan "Service temporarily unavailable" [disunting: butiran akaun penyedia API]; laluan `qd/*` 403.
Semua keluarga hidup yang lain ada dalam `keluarga_larangan`. Pemilik (5 Nov 2026) memutuskan untuk tidak menunggu 1 Dis.

**Perubahan.**

| peranan | calon 1 | sandaran |
|---|---|---|
| ujian3 (keluarga B) | `cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (Mistral, melalui 9router) | `anthropic/claude-sonnet-5-5` (Anthropic, API terus) |

- `templat_llm.keluarga_larangan_kecuali.ujian3 = [mistral, anthropic]` — pengecualian HANYA untuk ujian3; latih3 dan semua sasaran lain
  kekal tertakluk pada senarai larangan penuh. Keluarga A (`nvidia`) ∩ B = ∅ tetap disemak.
- **`anthropic/claude-haiku-5-5` DILARANG sebagai penjana mana-mana sasaran** (`templat_llm.penjana_larangan_tepat`): ia sistem
  pembanding H4a.
- Probe ujian3 = peraturan pindaan 2026-11-05 (4 genre pertama, lulus jumlah sah ≥ 8/16), sekali, fail tidak ditindih. Templat + nama
  ujian3 dijana oleh `dipilih` SAHAJA (`panggilan` 1); pembina tidak membaca kandungan; pengesah tidak berubah.
- Panggilan Claude memakai `mypii/klien_anthropic.py` (lejar + had keras USD 20 yang sama, `temperature` tidak dihantar);
  `templat_llm.anthropic_max_tokens` 4096 untuk penjanaan (senarai JSON lebih panjang daripada jawapan pengesan). Had dicapai = BERHENTI.

**Had baharu (dilapor dalam kertas).** (8) **Mistral** ialah garis dasar EKSPLORASI v1 (dev/ujian/ujian2; bukan hipotesis v2). (9)
**Anthropic** = keluarga sistem pembanding H4a (Haiku) dan pembantu yang menulis kod (had (6)). Jika Sonnet dipilih, teks ujian3 dari
keluarga yang sama dengan Haiku mungkin LEBIH MUDAH bagi Haiku → arah bias MENENTANG MyPII untuk H4a (bukan-inferioriti lebih sukar
dibuktikan), neutral untuk H4b (v2 vs v1, kedua-duanya MyPII). Penjana yang dipakai dilapor bersama setiap keputusan ujian3.

**English summary.** Neither pre-registered family-B generator could be called on 5 Nov (MiniMax: provider route
unavailable [redacted], free route withdrawn; Grok: quota-limited or unavailable [redacted]). Owner decision: family B for test3 = Mistral Small 3.1
(via 9router), fallback Claude Sonnet 5.5 (direct API), with a family-ban exception for test3 only; Claude Haiku (the H4a comparator)
is banned as a generator. Same 4-genre format probe, one call per pair, builder does not read test3 content, same USD 20 hard cap.
New limitations: Mistral was an exploratory v1 baseline; an Anthropic-generated test3 may favour Haiku, which biases H4a against MyPII.

### 2026-11-05 (d) — MyPII v2: empat panggilan nama ujian3 (selepas satu kegagalan ambang nama)
**Status:** probe ujian3 dikomit (`48b4b74`, Sonnet dipilih). Larian `templat-llm --sasaran ujian3` pertama: templat LULUS (204 ≥ 150;
kategori b 26 · c 28 · d 53 · e 22), tetapi `nama pertama_cina 5 < 15` → tiada fail ditulis. Tolakan nama Cina = `token_bersilang` 48
(nama pemberian Cina berkongsi suku kata dengan senarai nama sedia ada; ujian3 mesti bersilang kosong), `pendua` 5. Pembina membaca
statistik sahaja. Belanja lejar repo selepas larian: 2.644784 USD.

**Perubahan (satu sahaja).** `templat_llm.sasaran.ujian3.panggilan_nama: 4` — setiap kategori nama dipohon EMPAT kali (prompt sama),
jawapan digabung SEBELUM `tapis_nama` (pendua + persilangan ditolak seperti biasa). Templat ujian3 kekal `panggilan` 1 — tetapi kerana
penjanaan templat dan nama ialah satu larian, templat dijana SEMULA dalam larian ini (larian pertama tidak menulis apa-apa). Ambang
`nama.min`, penapis, prompt dan model TIDAK berubah. SATU larian; gagal ambang = BERHENTI.

**Ditolak:** menurunkan `nama.min.pertama_cina` (kriteria selepas melihat hasil); membenarkan persilangan token (memecah syarat
bersilang kosong ADR-008); memanggil hanya kategori yang gagal (penyesuaian ikut output).

**English summary.** First test3 generation run passed the template thresholds but produced only 5 valid Chinese given names (< 15;
48 rejected for token overlap with existing name lists); nothing was written. Change: four name-generation calls per category for
test3, pooled before the unchanged name filter; templates are regenerated in the same single run; thresholds unchanged; one run only.

### 2026-11-05 (e) — MyPII v2: kuasa + pengecam dibekukan (sebelum ujian3 dibuka)
**Status:** ujian3 DIMETERAI (`UJIAN3-MUKTAMAD` = `5658ebe3…`, `56bd011`) dan **BELUM DIBUKA** — tiada sistem pernah dinilai atasnya,
tiada `hasil/*ujian3*`, tiada arkib `~/ops/mypii/arkib-ujian3/`. Hipotesis, δ, α, Holm k = 2, metrik dan peraturan keputusan TIDAK berubah.

**Pengecam v2 DIBEKUKAN** pada komit `7ca74abbd344f0a45a0fcd956fabee2192aa9ef2`: pokok `mypii/pengecam` = `91e758c94da388865ea39d14caa3d64b51eebefa`;
sha256 JSON terisih {`pengecam`, `konteks`, `nilai.ambang_skor`} dari `config/mypii.yaml` = `07a2648f874082b5…`. Pengelas konteks:
artifak `model/konteks-v2.json` sha256 `02d7d9bd378597622b0829da1b527e38ce8e7fac283da4e9279deca1acb2a0d3` (latih3 sahaja), gabung
`cara: ganti`, ambang 0.5 setiap entiti (ditala atas dev3: tapis 0.3/0.5/0.7 = 0.9919/0.9925/0.9919, ganti 0.3/0.5/0.7 =
0.9957/0.9981/0.9981; 0.5 dipilih kerana seri dengan 0.7 dan recall 1.0). Selepas pindaan ini, `mypii/pengecam/`, `model/` dan bahagian
config itu tidak berubah sehingga ujian3 selesai (perubahan = pindaan baharu + keputusan dilapor sebagai v2.x, bukan v2).

**Angka dev3 (ditala — deskriptif, BUKAN ujian):** F1 tepat mikro `semua|*` — MyPII v2 **0.9981** · Claude Haiku 5.5 **0.7907** ·
MyPII v1 (worktree tag) **0.6149** · presidio-asal 0.2902. H4a Δ +0.2074 [0.1848, 0.2334]; H4b Δ +0.3832 [0.351, 0.4165]. dev3 dan
latih3 dari penjana A yang SAMA (Nemotron), jadi dev3 dijangka terlalu optimis untuk MyPII v2; ujian3 (penjana B, Claude Sonnet) ialah ukuran.

**MDE** (`python -m mypii.nilai.kuasa --fail hasil/dev3-statistik.json`; bootstrap dev3, n ujian3 = 1000, kuasa 0.8, sehala):

| hipotesis | kunci | SE Δ | MDE α/k = 0.025 | MDE α = 0.05 |
|---|---|---|---|---|
| H4a (lawan Haiku) | `*` | 0.0124 | 0.0347 | 0.0308 |
| H4b (lawan v1) | `*` | 0.0167 | 0.0468 | 0.0415 |

MDE maklumat sahaja; bagi H4a ia mengukur kepekaan terhadap Δ, bukan margin δ = 0.01.

**Pendedahan tambahan (penyemak bebas P6, LOG 5 Nov):** calon B pertama Mistral gugur pada probe ujian3 kerana `hantar_9router` tidak
menghantar `max_tokens` (Cloudflare lalai 256 token → JSON terpotong), sedangkan pindaan (c) menaikkan had untuk laluan Anthropic sahaja —
kecacatan pembina, bukan mutu Mistral; probe tidak diulang mengikut peraturan. Gerbang §6 autopilot "pengesah kod BASE" tidak dipenuhi
secara literal kerana `semak_fail` sebelum `e88c3d1` menyemak teks v3 dengan pengesah v1 (95/203 tolak palsu, semuanya slot v3 sah;
disahkan penyemak bebas). Nota: corak gerbang harness `pindaan_split.ujian3` (`MyPII v2`, min 2) sudah dipenuhi oleh pindaan (b)–(d)
sebelum pindaan ini; pelaksana §7-v2 memakai pindaan INI (tajuk "kuasa + pengecam dibekukan") sebagai syarat.

**Pelaksana §7-v2:** sesi interaktif pemilik 5 Nov 2026 (autopilot mypii dihentikan pemilik), melalui `scripts/ujian3-muktamad.sh`
SAHAJA, SEKALI. Perintah = blok §7-v2 bait sama.

**English summary.** Test3 is sealed and unopened. The v2 recogniser is frozen at commit `7ca74ab` (tree, config-section hash and
classifier artifact sha recorded above; combine = replace at threshold 0.5, tuned on dev3). Tuned dev3 (descriptive only): MyPII v2
0.9981, Claude Haiku 0.7907, MyPII v1 0.6149, Presidio 0.2902; dev3 shares generator family A with train3 and is expected to be
optimistic. MDE at n = 1000, power 0.8: H4a 0.0347, H4b 0.0468 (α/k). Disclosed: the first family-B candidate (Mistral) failed the
probe because of a builder bug (no `max_tokens` on the 9router path → 256-token truncation). Test3 will be opened once by the owner's
interactive session via `scripts/ujian3-muktamad.sh`, with the exact pre-registered commands.
