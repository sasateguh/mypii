# MyPII v2: bandingan dev3 + ujian3

<!-- DIJANA oleh `make bandingan-v2` (mypii/nilai/bandingan_v2.py); jangan sunting tangan. -->

Ujian3 dibuka sekali (sha `17bb5a1`, 1000 dokumen, penjana templat B = Claude Sonnet 5.5). dev3 ialah set penalaan (penjana A = Nemotron, sama dengan latih3), jadi angka dev3 deskriptif dan dijangka optimis.

## 1. Keputusan utama (ujian3, F1 tepat mikro `semua|*`, CI bootstrap 95%)

| sistem | F1 ujian3 | CI 95% | F1 dev3 | jurang dev3 → ujian3 |
|---|---|---|---|---|
| MyPII v2 | **0.9804** | [0.9733, 0.9868] | 0.9981 | -0.0177 |
| Claude Haiku 5.5 | **0.8714** | [0.8509, 0.8915] | 0.7907 | +0.0807 |
| MyPII v1 (tag) | **0.5872** | [0.5505, 0.6204] | 0.6149 | -0.0277 |
| Presidio asal | **0.3251** | [0.2967, 0.3515] | 0.2902 | +0.0349 |

## 2. Hipotesis pra-daftar (Holm k = 2, α = 0.05 sehala)

| hipotesis | lawan | δ | ΔF1 | CI 95% | p Holm (bootstrap) | p rawak × 2 | keputusan |
|---|---|---|---|---|---|---|---|
| H4a | Claude Haiku 5.5 | 0.01 | +0.109 | [0.0904, 0.1292] | < 0.001 | 0.002 (deskriptif) | disokong |
| H4b | MyPII v1 (tag) | 0 | +0.3932 | [0.3591, 0.429] | < 0.001 | 0.002 | disokong |

## 3. Setiap entiti (F1 tepat)

| sistem | split | MY_NRIC | MY_SSM | MY_PHONE |
|---|---|---|---|---|
| MyPII v2 | ujian3 | 0.9929 | 0.9431 | 1.0 |
| MyPII v2 | dev3 | 0.9953 | 1.0 | 0.9986 |
| Claude Haiku 5.5 | ujian3 | 0.7908 | 0.9101 | 0.8959 |
| Claude Haiku 5.5 | dev3 | 0.6749 | 0.8763 | 0.8217 |
| MyPII v1 (tag) | ujian3 | 0.3648 | 0.6516 | 0.7002 |
| MyPII v1 (tag) | dev3 | 0.3773 | 0.7575 | 0.6955 |
| Presidio asal | ujian3 | 0.0 | 0.0 | 0.4807 |
| Presidio asal | dev3 | 0.0 | 0.0 | 0.4385 |

## 4. Setiap kategori v3 (ujian3)

Kategori (a) ROB lama digugurkan (tiada sumber rasmi, pindaan 2026-11-04). (b)–(d): recall span tepat bagi span emas yang bertindih kategori. (e): bilangan ramalan yang jatuh atas nombor negatif 12 digit (positif palsu; lebih rendah lebih baik).

| sistem | (b) LLP | (c) Sabah/Sarawak | (d) OCR/patah baris | (e) FP / kawasan |
|---|---|---|---|---|
| MyPII v2 | 1.0 (162/162) | 1.0 (191/191) | 0.9975 (395/396) | 0 / 61 |
| Claude Haiku 5.5 | 0.8951 (145/162) | 0.9424 (180/191) | 0.899 (356/396) | 18 / 61 |
| MyPII v1 (tag) | 0.6235 (101/162) | 0.5707 (109/191) | 0.0 (0/396) | 57 / 61 |
| Presidio asal | 0.0 (0/162) | 0.7225 (138/191) | 0.0 (0/396) | 7 / 61 |

## 5. Setiap bahasa (ujian3, F1 tepat `*`)

| sistem | ms | en | manglish |
|---|---|---|---|
| MyPII v2 | 0.9816 | 0.9662 | 0.9905 |
| Claude Haiku 5.5 | 0.8556 | 0.8512 | 0.905 |
| MyPII v1 (tag) | 0.6231 | 0.5304 | 0.5973 |
| Presidio asal | 0.3218 | 0.3011 | 0.3499 |

## 6. Panggilan LLM dan kos

- Claude Haiku 5.5 ujian3: 1000 panggilan, 0 gagal, 1 jawapan rosak.
- Lejar Anthropic selepas ujian3 (arkib): USD 3.485583; had keras USD 20 tidak dinaikkan.

## 7. Had kajian (lapor bersama setiap angka)

1. Data sintetik: nilai kategori (b)–(e) dijana oleh `nilai_v3.py` yang ditulis pembina yang sama dengan pengecam v2, jadi ujian3 mengukur liputan bentuk yang dijangka, bukan realisme teks sebenar.
2. Pengelas konteks dilatih atas gaya penjana A (Nemotron); ujian3 (penjana B) menguji pemindahan gaya antara DUA keluarga LLM sahaja.
3. v1 tidak pernah melihat kategori baharu → H4b dijangka besar; ia bukan bukti generalisasi melebihi kategori itu.
4. Reka bentuk v2 ditulis selepas ujian v1 dibuka; kategori datang dari ANALISIS-RALAT (sebelum ujian v1).
5. Label telefon Sabah/Sarawak = julat libphonenumber (ADR-002), jadi recall telefon terlebih optimis.
6. Claude ialah keluarga pembantu yang menulis kod DAN penjana templat ujian3 (Sonnet) DAN pembanding H4a (Haiku). Teks ujian3 dari keluarga Anthropic dijangka memihak kepada Haiku, jadi arah bias menentang MyPII untuk H4a.
7. Satu split ujian3 dari satu penjana B; tiada replikasi. Calon B pertama (Mistral) gugur kerana pemotongan 256 token oleh kod pembina, bukan mutu (pindaan 2026-11-05 e).
8. Satu larian Haiku setiap split (tidak deterministik); 1 jawapan rosak dikira sebagai tiada ramalan.

## English summary

On the sealed test3 split (1000 synthetic documents, template generator family B = Claude Sonnet 5.5, opened once), MyPII v2 reaches exact micro F1 0.9804 versus Claude Haiku 5.5 0.8714 and MyPII v1 0.5872. Both pre-registered v2 hypotheses are supported (Holm k = 2): H4a non-inferiority to Haiku (Δ +0.109, margin 0.01) and H4b improvement over v1 (Δ +0.3932). The recogniser runs locally (regex + validation + a small logistic-regression context classifier, numpy only) with no API at prediction time. All data are synthetic; see the limitations above.
