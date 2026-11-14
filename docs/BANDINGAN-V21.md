# MyPII v2.1: ujian4 dimeterai (penjana keluarga baharu) + bandingan

<!-- DIJANA oleh `make bandingan-v21` (mypii/nilai/bandingan_v21.py); jangan sunting tangan. -->

ujian4 dibuka sekali (sha `2b306b4`, 1000 dokumen; templat + nama oleh Qwen3.8-27B-FP8 dihos sendiri, keluarga yang tidak pernah menghasilkan data atau keputusan dalam kajian ini). Pra-daftar: PRA-DAFTAR pindaan 2026-11-14 (b) + (c), dikomit sebelum ujian4 dijana; pengecam v2.1 = tag `mypii-v21-beku`. dev3 = set penalaan (deskriptif).

## 1. Keputusan utama (ujian4, F1 tepat mikro `semua|*`, CI bootstrap 95%)

| sistem | F1 ujian4 | CI 95% | F1 dev3 | jurang dev3 → ujian4 |
|---|---|---|---|---|
| MyPII v2.1 | **0.9804** | [0.9724, 0.9872] | 0.9956 | -0.0152 |
| MyPII v2 (1.0.2) | **0.975** | [0.9665, 0.9826] | 0.9981 | -0.0231 |
| Claude Haiku 5.5 | **0.8207** | [0.796, 0.8429] | 0.7907 | +0.03 |
| MyPII v1 (tag) | **0.5918** | [0.5565, 0.6288] | 0.6149 | -0.0231 |
| Presidio asal | **0.3784** | [0.3443, 0.4136] | 0.2902 | +0.0882 |

## 2. Hipotesis pra-daftar H5 (Holm k = 4, α = 0.05 sehala)

| hipotesis | lawan | metrik | δ | F1 v2.1 | F1 lawan | ΔF1 [CI 95%] | p Holm (bootstrap) | p rawak (×k) | keputusan |
|---|---|---|---|---|---|---|---|---|---|
| H5a | MyPII v2 (1.0.2) | jenis | 0.01 | 0.9804 | 0.975 | +0.0054 [-0.0012, 0.0115] | < 0.001 | 0.036 (0.144) deskriptif | disokong |
| H5b | Claude Haiku 5.5 | jenis | 0.01 | 0.9804 | 0.8207 | +0.1597 [0.1372, 0.1839] | < 0.001 | 0.001 (0.004) deskriptif | disokong |
| H5c | Meddies PII v2 | u1 | 0 | 0.9804 | 0.5104 | +0.47 [0.4412, 0.5] | < 0.001 | 0.001 (0.004) | disokong |
| H5d | GLiNER multi PII v1 | u1 | 0 | 0.9804 | 0.6482 | +0.3322 [0.3028, 0.3626] | < 0.001 | 0.001 (0.004) | disokong |
| H5a+ | MyPII v2 (1.0.2) | jenis | 0 | 0.9804 | 0.975 | +0.0054 [-0.0012, 0.0115] | 0.041 (α penuh) | 0.036 | disokong (beza kecil) |

Kuasa (dari dev3, sebelum ujian4 dijana): H5a MDE 0.0046; H5b MDE 0.0393; H5c MDE 0.0433; H5d MDE 0.0364.

## 3. Model PII luar (U1 = ID ∪ telefon, F1 tepat; NRIC ketat = emas MyKad sahaja)

| sistem | split | U1 F1 [CI] | ID | telefon | NRIC ketat |
|---|---|---|---|---|---|
| MyPII v2.1 | ujian4 | 0.9804 [0.9724, 0.9872] | 0.9631 | 1.0 | 0.9409 |
| MyPII v2 (1.0.2) | ujian4 | 0.9757 [0.9672, 0.9831] | 0.9539 | 1.0 | 0.93 |
| Meddies PII v2 | ujian4 | 0.5104 [0.4812, 0.5396] | 0.3763 | 0.7902 | 0.2657 |
| GLiNER multi PII v1 | ujian4 | 0.6482 [0.6185, 0.6767] | 0.3794 | 0.816 | 0.2222 |
| MyPII v2.1 | dev3 | 0.9963 [0.993, 0.9988] | 0.9945 | 0.9986 | 0.9977 |
| MyPII v2 (1.0.2) | dev3 | 0.9994 [0.9981, 1.0] | 1.0 | 0.9986 | 1.0 |
| Meddies PII v2 | dev3 | 0.4801 [0.4506, 0.5063] | 0.3685 | 0.7639 | 0.2067 |
| GLiNER multi PII v1 | dev3 | 0.6471 [0.6236, 0.6689] | 0.415 | 0.8085 | 0.246 |

## 4. Setiap entiti (F1 tepat)

| sistem | split | MY_NRIC | MY_SSM | MY_PHONE |
|---|---|---|---|---|
| MyPII v2.1 | ujian4 | 0.9409 | 1.0 | 1.0 |
| MyPII v2.1 | dev3 | 0.9977 | 0.9896 | 0.9986 |
| MyPII v2 (1.0.2) | ujian4 | 0.9321 | 0.9854 | 1.0 |
| MyPII v2 (1.0.2) | dev3 | 0.9953 | 1.0 | 0.9986 |
| Claude Haiku 5.5 | ujian4 | 0.7757 | 0.8399 | 0.8481 |
| Claude Haiku 5.5 | dev3 | 0.6749 | 0.8763 | 0.8217 |
| MyPII v1 (tag) | ujian4 | 0.3124 | 0.7313 | 0.7615 |
| MyPII v1 (tag) | dev3 | 0.3773 | 0.7575 | 0.6955 |
| Presidio asal | ujian4 | 0.0 | 0.0 | 0.5532 |
| Presidio asal | dev3 | 0.0 | 0.0 | 0.4385 |

## 5. Setiap kategori v3 (ujian4)

(b)–(d): recall span tepat bagi span emas yang bertindih kategori. (e): ramalan atas nombor negatif 12 digit (lebih rendah lebih baik).

| sistem | (b) LLP | (c) Sabah/Sarawak | (d) OCR/patah baris | (e) FP / kawasan |
|---|---|---|---|---|
| MyPII v2.1 | 1.0 (76/76) | 1.0 (183/183) | 0.9464 (300/317) | 10 / 131 |
| MyPII v2 (1.0.2) | 0.9737 (74/76) | 1.0 (183/183) | 0.9274 (294/317) | 3 / 131 |
| Claude Haiku 5.5 | 0.9079 (69/76) | 0.8852 (162/183) | 0.8233 (261/317) | 57 / 131 |
| MyPII v1 (tag) | 0.75 (57/76) | 0.6175 (113/183) | 0.0 (0/317) | 91 / 131 |
| Presidio asal | 0.0 (0/76) | 0.7596 (139/183) | 0.0 (0/317) | 17 / 131 |

## 6. Setiap bahasa (ujian4, F1 tepat `*`)

| sistem | ms | en | manglish |
|---|---|---|---|
| MyPII v2.1 | 0.9816 | 0.9672 | 0.9879 |
| MyPII v2 (1.0.2) | 0.9889 | 0.9483 | 0.9776 |
| Claude Haiku 5.5 | 0.7776 | 0.861 | 0.8413 |
| MyPII v1 (tag) | 0.5466 | 0.6394 | 0.615 |
| Presidio asal | 0.3509 | 0.4984 | 0.3176 |

## 7. Pembangunan v2.1 (bukan dakwaan: set penalaan + bahan sesi)

- `dev` (gaya v1) F1 `*`: v2.1 0.9506, v2 (1.0.2) 0.84, v1 0.8877.
- Ayat biasa (`data/probe/ayat_biasa.yaml`): MyPII v2.1 positif 24/24, negatif tersalah tanda 0/10; MyPII v2 (1.0.2) positif 20/24, negatif tersalah tanda 3/10; MyPII v1 (tag) positif 24/24, negatif tersalah tanda 0/10.
- Probe luar bench `make analisis` (alat analisis A3 P3, tidak ditala):

| probe | emas | v2 (1.0.2) betul / ramal | v2.1 betul / ramal |
|---|---|---|---|
| jadual_tidak_teratur | 70 | 13 / 13 | 44 / 44 |
| konteks_jauh | 40 | 0 / 0 | 8 / 8 |
| negatif_berkurung | 0 | 0 / 40 | 0 / 0 |
| negatif_tanpa_kata | 0 | 0 / 0 | 0 / 5 |
| ocr_digit | 40 | 20 / 20 | 20 / 20 |
| patah_baris | 40 | 28 / 28 | 28 / 28 |
| syarikat_luar_senarai | 40 | 16 / 16 | 2 / 2 |
| telefon_bukan_telefon | 0 | 0 / 40 | 0 / 38 |

## 8. Panggilan LLM dan kos

- Claude Haiku 5.5 ujian4: 1000 panggilan, 0 gagal, 3 jawapan rosak.
- Lejar Anthropic selepas ujian4 (arkib): USD 3.467458; had keras USD 20 tidak dinaikkan.

## 9. Had kajian (lapor bersama setiap angka)

1. Data sintetik: nilai (termasuk kategori b–e) dijana `nilai_v3.py` yang ditulis pembina yang sama dengan pengecam, jadi ujian4 mengukur liputan bentuk yang dijangka, bukan realisme teks sebenar.
2. v2.1 dibina selepas ujian, ujian2 dan ujian3 dibuka (pembaikan dimotivasikan red team demo + split dev); ujian4 dijana selepas pengecam dibekukan dan pra-daftar dikomit, jadi hanya ujian4 yang bersih untuk v2.1.
3. Satu penjana ujian4 (Qwen3.8-27B); bersama ujian3 (Claude Sonnet) = dua keluarga ujian v3 sahaja.
4. Pengelas konteks dilatih atas gaya penjana latih3 (Nemotron) sahaja.
5. Ambang nisbah templat negatif ujian4 = 0.20 (pindaan c, selepas satu kegagalan ambang); bahagian dokumen negatif keras tetap 0.25, tetapi kepelbagaian templat negatif lebih rendah daripada ujian3.
6. Label telefon = julat sah libphonenumber (ADR-002), jadi recall telefon terlebih optimis.
7. Model luar dinilai dengan label/ambang pengeluar tanpa penalaan; Meddies CC BY-NC 4.0 (penyelidikan sahaja); PII Engineer v2.1 tidak dinilai (pelayan rasmi HTTP 500).
8. Satu larian Haiku (tidak deterministik); jawapan rosak dikira sebagai tiada ramalan.
9. Pembantu yang menulis kod ialah keluarga Claude; penjana ujian4 bukan Claude, jadi bias keluarga ujian3 tiada untuk H5b.

## English summary

On the sealed ujian4 split (1000 synthetic documents; templates and names written by Qwen3.8-27B, a model family that produced no other data or result in this study; opened once after the recogniser was frozen and the hypotheses registered), MyPII v2.1 reaches exact micro F1 0.9804, versus 0.975 for MyPII v2 (1.0.2) and 0.8207 for Claude Haiku 5.5. Pre-registered H5 (Holm k = 4): v2.1 − v2 = +0.0054 (non-inferiority, margin 0.01), v2.1 − Haiku = +0.1597 (non-inferiority, margin 0.01), U1 v2.1 − Meddies PII v2 = +0.47, U1 v2.1 − GLiNER multi PII v1 = +0.3322 (superiority). Supported: H5a, H5b, H5c, H5d, H5a+. All data are synthetic; see the limitations above.
