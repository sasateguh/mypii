# MyPII-Bench: model PII luar (deskriptif)

> Dijana `python -m mypii.nilai.luar` daripada `hasil/luar/`; jangan sunting dengan tangan. Pindaan PRA-DAFTAR **2026-11-14**:
> semua split ujian sudah dibuka, jadi ini perbandingan **deskriptif selepas kejadian**, bukan dakwaan. ‡ = eksplorasi.

**U1** = F1 tepat mikro atas dua kelas yang semua sistem sokong: ID (MyKad ∪ SSM) dan TELEFON. **NRIC ketat** = emas MyKad
sahaja, ramalan ID yang bertindih SSM diabaikan. **Bertipe** = tiga entiti MyPII (Meddies tiada label SSM, jadi tiada baris).
CI = bootstrap dokumen 95% (1000, benih 2026). Δ = MyPII v2 − model.

## `ujian3` (1000 dokumen)

| Sistem | U1 F1 [CI] | Δ MyPII [CI] | ID | TELEFON | NRIC ketat | Bertipe `*` | SSM bertipe |
|---|---|---|---|---|---|---|---|
| MyPII v2 (1.0.x) | 0.981 [0.974, 0.987] | – | 0.966 | 1.000 | 0.938 | 0.980 | 0.943 |
| Meddies PII v2 | 0.452 [0.424, 0.480] | 0.529 [0.503, 0.556] | 0.318 | 0.784 | 0.166 | – | – |
| GLiNER multi PII v1 ‡ | 0.653 [0.631, 0.674] | 0.328 [0.307, 0.350] | 0.352 | 0.863 | 0.258 | 0.640 | 0.390 |

Setiap bahasa (U1): MyPII v2 (1.0.x): en 0.966, manglish 0.992, ms 0.982; Meddies PII v2: en 0.416, manglish 0.514, ms 0.430; GLiNER multi PII v1 ‡: en 0.613, manglish 0.677, ms 0.662.

Kategori sukar `ujian3` (b–d = span emas dikesan / n; e = nombor 12 digit tanpa label ditanda / n, lebih rendah lebih baik):
- MyPII v2 (1.0.x): b 162/162, c 191/191, d 395/396, e 0/61
- Meddies PII v2: b 162/162, c 187/191, d 388/396, e 61/61
- GLiNER multi PII v1 ‡: b 46/162, c 189/191, d 217/396, e 4/61

## `ujian2` (1000 dokumen)

| Sistem | U1 F1 [CI] | Δ MyPII [CI] | ID | TELEFON | NRIC ketat | Bertipe `*` | SSM bertipe |
|---|---|---|---|---|---|---|---|
| MyPII v2 (1.0.x) | 0.940 [0.928, 0.952] | – | 0.896 | 0.999 | 0.897 | 0.940 | 0.867 |
| Meddies PII v2 | 0.450 [0.424, 0.477] | 0.490 [0.463, 0.518] | 0.349 | 0.701 | 0.243 | – | – |
| GLiNER multi PII v1 ‡ | 0.555 [0.528, 0.582] | 0.385 [0.357, 0.413] | 0.277 | 0.735 | 0.145 | 0.553 | 0.411 |

Setiap bahasa (U1): MyPII v2 (1.0.x): en 0.945, manglish 0.901, ms 0.961; Meddies PII v2: en 0.438, manglish 0.443, ms 0.463; GLiNER multi PII v1 ‡: en 0.527, manglish 0.509, ms 0.602.

## `ujian` (1000 dokumen)

| Sistem | U1 F1 [CI] | Δ MyPII [CI] | ID | TELEFON | NRIC ketat | Bertipe `*` | SSM bertipe |
|---|---|---|---|---|---|---|---|
| MyPII v2 (1.0.x) | 0.870 [0.857, 0.883] | – | 0.748 | 1.000 | 0.780 | 0.868 | 0.682 |
| Meddies PII v2 | 0.754 [0.735, 0.771] | 0.116 [0.095, 0.140] | 0.640 | 0.984 | 0.529 | – | – |
| GLiNER multi PII v1 ‡ | 0.699 [0.675, 0.723] | 0.172 [0.144, 0.199] | 0.371 | 0.998 | 0.253 | 0.699 | 0.525 |

Setiap bahasa (U1): MyPII v2 (1.0.x): campur 0.870; Meddies PII v2: campur 0.754; GLiNER multi PII v1 ‡: campur 0.699.

## Had (baca sebelum memetik)

- Deskriptif selepas kejadian: ketiga-tiga split sudah dibuka (3–5 Nov); dakwaan bersih perlukan split ujian baharu (ujian4).
- Label emas tidak lengkap: semakan IAA mendapati dokumen dengan MyKad/SSM/telefon tidak berlabel 0.067 (`dev`) dan 0.167
  (`ujian2`). Sistem dengan dapatan semula tinggi (Meddies) kehilangan ketepatan atas nombor sebenar yang tidak dilabel, jadi
  ketepatan mereka di sini ialah had bawah. Arah sebaliknya juga mungkin: negatif keras sengaja tidak dilabel.
- Kelebihan rumah: MyPII v2 dilatih atas latih3 (penjana yang sama dengan bentuk v3); data sintetik, bukan dokumen sebenar.
- MyPII v2 atas `ujian` (templat v1) = 0.870, lebih rendah daripada v1 (0.993) di split itu: v2 kurang dapatan semula pada gaya v1.
- Meddies CC BY-NC 4.0: penilaian penyelidikan sahaja.

## Tidak dinilai

- PII Engineer Multi-NER v2.1: pelayan rasmi memulangkan HTTP 500 (Reshape span_rep) untuk setiap input (14 Nov 2026, PELAN-HF-E §B).
