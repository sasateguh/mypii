# ADR-002: Penanda aras sintetik dengan split ujian daripada templat simpanan (28 Okt 2026)

**Keputusan.** Templat bertanda slot → nilai rekaan → label span tepat. latih/dev dari `data/templat/`; ujian dari
`data/templat_ujian/` (gaya berbeza, benih sendiri), dikunci dengan sha256 (`tests/test_bench.py`). Dibuktikan: menambah templat
latih/dev tidak mengubah cincangan ujian.

**Sebab.** Tiada data PII sebenar boleh diguna (PDPA); label manual mahal. Split ujian yang tidak pernah dilihat gelung automatik
mengukur generalisasi kepada gaya teks baharu, bukan hafalan templat.

**Had yang diakui.** (1) Label telefon dijana dalam julat yang libphonenumber anggap sah, dan pengecam telefon juga mengesahkan dengan
libphonenumber — recall telefon terlebih optimis; kertas mesti menyebutnya. (2) Templat ditulis tangan: angka dev hampir siling
(F1 0.97) = penanda aras masih mudah; iterasi awal = templat lebih pelbagai. (3) IAA manusia (M4) belum dibuat.
