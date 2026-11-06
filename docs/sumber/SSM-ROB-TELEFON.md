# Sumber rasmi — nombor pendaftaran SSM (ROB lama, LLP) dan talian tetap Sabah/Sarawak

PELAN-V2 P1, 4 Nov 2026. Dokumen ini merekod **apa yang disahkan dari sumber rasmi** dan **apa yang TIDAK** sebelum
sebarang kod v3 ditulis (Keputusan reka bentuk 3). Data mesin = `config/ssm_rob.yaml` (tiada kod membacanya lagi; P3/P9).
Setiap URL di bawah dibuka dengan `curl` pada 4 Nov 2026 (HTTP 200); fail PDF dimuat turun dan teksnya diekstrak
(PyMuPDF) — sha256 16 aksara pertama direkod supaya penyemak boleh menyemak bahawa dokumen yang sama dibaca.

Peraturan: **nilai tanpa sumber rasmi tidak dijana dan tidak dikesan.** Sumber sekunder (firma perakaunan, forum)
disenaraikan untuk ketelusan sahaja dan TIDAK menjadi asas data.

## (a) Format nombor pendaftaran perniagaan (ROB) lama

### Disahkan (rasmi)
| fakta | sumber | petikan |
|---|---|---|
| Format 12 digit untuk syarikat, perniagaan **dan** LLP bermula **11 Oktober 2019**; nombor lama dipapar bersama dalam tempoh peralihan | SSM, pengumuman: https://www.ssm.com.my/Lists/Announcement/AnnouncementDetails.aspx?ID=134 | "a new format of registration number containing 12 digit characters for company, business and Limited Liability Partnership beginning 11 October 2019 … (Eg: … Registration No: 201901000005 (1312525-A)" |
| Nombor lama SYARIKAT (ROC) berbentuk digit + `-` + satu huruf | SSM, manual pengguna CRS (sha256 `6c78dfe4627a3e27`): https://www.ssm.com.my/bm/Pages/Services/Other-Services/document/SUPPORTING%20MODULE-%20LEARN%20ABOUT%20THE%20SYSTEM.pdf | "Old Registration No. (e.g: 123456-X)" — untuk ROB manual itu hanya menyebut medan "Business Registration No." **tanpa contoh bentuk** |

Bentuk lama syarikat (`NNNNNN-X`, `NNNNNNN-X`) sudah dikesan oleh pengecam v1 (`MY_SSM`) dan tidak berubah dalam v2.

### TIDAK disahkan — tidak dijana, tidak dikesan
Tiada dokumen rasmi (ssm.com.my, Akta Pendaftaran Perniagaan 1956, gazet) yang ditemui pada 4 Nov 2026 menyatakan
**bentuk nombor ROB lama** atau **senarai awalan huruf negeri**. Dicari: pengumuman + FAQ 12 digit SSM, manual CRS,
panduan ezBiz (pendaftaran baharu SPPP, pembaharuan — tangkapan skrin sahaja, tiada contoh nombor), panduan Kod QR
BizTrust, laman ROB ssm.com.my; PDF Akta 1956 di ssm.com.my = HTTP 404 pada `/acts/Registration%20of%20Businesses%20Act%201956.pdf`.

| dakwaan sekunder | sumber (BUKAN rasmi) | status |
|---|---|---|
| Perusahaan: `WW XXXXXXX-Y`; W = `00` (KL) atau huruf negeri; perniagaan lama 4–5 X | forum Lowyat 2011, kononnya dari panggilan ke SSM + carian e-Info: https://forum.lowyat.net/topic/1734602/all | tidak disahkan |
| Awalan: Perlis `AS`, Pulau Pinang `PG`, Kelantan `KT`, Terengganu `TR`, Perak `IP`, Pahang `CA`, KL `00`, Negeri Sembilan `NS`, Melaka `MA`, Johor `JM`, Labuan `LA` (Kedah, Selangor, Sabah, Sarawak = "??") | forum yang sama | tidak disahkan |
| Contoh nombor perniagaan `SA0000001-D`; LLP `LLP0000001-LGN` | Acclime (firma perkhidmatan): https://malaysia.acclime.com/guides/business-registration-number/ | tidak disahkan |
| Contoh nombor syarikat lama `123456-A` | MFCCI (dewan perniagaan): https://www.mfcci.com/publications/news/n/news/the-implementation-of-the-new-format-for-the-registration-number-of-business-entities.html | selaras dengan sumber rasmi CRS (bentuk syarikat), bukan ROB |

**Akibat untuk v2 (direkod sebelum kod):** `config/ssm_rob.yaml` `awalan_disahkan` = **kosong**. Kategori (a) ROB lama
dalam Keputusan reka bentuk 3 tidak boleh dijana dari awalan yang disahkan; P3 TIDAK menjana slot `{MY_ROB}` dan P9 TIDAK
menambah corak ROB berawalan. Ini dilapor dalam kertas sebagai had (format ROB lama tidak didokumenkan secara terbuka oleh
SSM). Pemilik memegang sijil pendaftaran perniagaannya sendiri (Sasa Teguh, milikan tunggal berdaftar SSM) — satu sijil
hanya boleh menunjukkan bentuk SATU nombor dan bukan sumber awam yang boleh dipetik, jadi ia TIDAK dipakai sebagai bukti
bentuk; tiada nombor sebenar direkod di mana-mana. Jalan ke hadapan (di luar v2): sumber rasmi baharu (cth. jawapan bertulis
SSM `enquiry@ssm.com.my`) → tambah entri dengan URL/rujukan → P3/P9 boleh dibuka semula melalui pindaan.

## (b) Kod jenis entiti 12 digit dan Akta Perkongsian Liabiliti Terhad 2012

| fakta | sumber | petikan |
|---|---|---|
| Struktur 12 digit = 4 digit tahun didaftarkan + 2 digit kod entiti + 6 digit siri (000001–999999) | SSM, risalah FAQ "Introduction of a new 12 digit registration number format" (bercap SSM + KPDNHEP, dicipta 8 Okt 2019; salinan dihoskan firma audit kerana tiada salinan ditemui di ssm.com.my — sha256 `b3a6b12db6c3a963`): https://mahwengkwai.com/wp-content/uploads/2019/11/FAQ-SSM-12-Digit-English-2-1.pdf | "i. 4 digits – The year the business entity was registered; ii. 2 digits – Business entity code; iii. 6 digits – The registration number sequence" |
| Kod entiti: `01` syarikat tempatan · `02` syarikat asing · `03` perniagaan · `04` LLP tempatan · `05` LLP asing · `06` LLP amalan profesional | risalah FAQ yang sama (jadual imej, halaman 2, dibaca dari imej) | "Local Limited Liability Partnership 04 · Foreign Limited Liability Partnership 05 · Limited Liability Partnership for Professional Practice 06" |
| Akta 743 berkuat kuasa **26 Disember 2012** (P.U. (B) 421/2012); Perkenan Diraja 2 Feb 2012 | Akta 743, cetakan KPDN (sha256 `7f730b9004035124`): https://www.kpdn.gov.my/images/2024/awam/akta/ssm/Act%20743.pdf | "[26 December 2012, P.U. (B) 421/2012]"; s.1(2) "This Act comes into operation on a date to be appointed by the Minister by notification in the Gazette." |
| Teks Akta (salinan SSM) | https://www.ssm.com.my/acts/Limited%20Liability%20Partnerships%20Act%202012.pdf (sha256 `5ecc64b51f06220a`) | s.1 "Short title and commencement" (salinan ini tanpa tarikh kuat kuasa — tarikh dari cetakan KPDN di atas). Cetakan KPDN juga: "The name and registration number of the limited liability partnership shall appear on every letterhead, invoice, bill …" |

**Akibat untuk v2:** tiada LLP boleh didaftarkan sebelum 26 Dis 2012, jadi nombor 12 digit dengan kod `04`–`06` dan
tahun < 2012 tidak wujud → `config/ssm_rob.yaml` `llp.tahun_min: 2012` (SATU sumber; `nilai_v3.llp_tahun_min()` membacanya terus, tiada salinan dalam `mypii.yaml`). Kod `01`–`06` sama
dengan `pengecam.MY_SSM.kod_jenis` v1 — kini dengan sumber; v1 tidak disunting.

## (c) Talian tetap Sabah, Sarawak dan Labuan

| fakta | sumber | petikan |
|---|---|---|
| NDC dua digit untuk Sabah, Sarawak, Labuan; `08X` Sarawak (X = 2–6), `08Y` Sabah (Y = 7–9), `087` Labuan | MCMC, *Numbering and Electronic Addressing Plan* (© 2023, sha256 `fecd36d356eedaa9`): https://www.mcmc.gov.my/skmmgovmy/media/General/registers/Numbering-and-Electronic-Addressing-Plan.pdf | §6.3.3 "All NDC have one (1) digit except for Sabah, Sarawak and Labuan which have two (2) digits." · Rajah 6.2 "0 8X Sarawak · 0 8Y Sabah · 0 87 Labuan … X = 2 to 6 … Y = 7 to 9" |
| Nombor pelanggan 6 digit bila NDC dua digit; digit pertama 2–9 | NEAP yang sama, §6.4.1.3 + §6.4.2 | "FIGURE 6.7: NUMBER STRUCTURE FOR SIX DIGIT SUBSCRIBER NUMBERS … 0 8A X1 XXXXX"; "In geographical areas where the six (6) digit Subscriber Number is applicable, the NDC comprises of two (2) digits." |
| Migrasi ke 8 digit seragam = niat masa depan, belum berlaku | NEAP §6.4.3 | "The Commission intends to convert all existing seven (7) and six (6) digit Subscriber Numbers to a uniform eight (8) digits in the future" |

Perhatian: NEAP meletakkan `087` di bawah Labuan (Rajah 6.2) — `087` juga meliputi Pedalaman Sabah dalam sumber sekunder;
v2 menganggap 082–089 sebagai satu kumpulan "talian tetap Sabah/Sarawak/Labuan" dan tidak bergantung pada pemetaan negeri.

### Metadata libphonenumber (diukur, `phonenumbers` 9.0.42 dalam `.venv`, 4 Nov 2026)
Corak `fixed_line` MY untuk awalan `8`: `8(?:[24][2-8]|3[2-5]|5[2-7]|6[2-589]|7[2-578]|[89][2-9])\d{5}` → NSN 8 digit
(NDC 2 + pelanggan 6). Digit pertama pelanggan yang SAH (dari corak, disemak dengan sampel rawak 400/kod):

| kod | digit pertama sah | 6 digit sah (sampel 400, digit pertama 2–9) | 7 / 8 digit |
|---|---|---|---|
| 082 | 2–8 | 354/400 | 0/400 · 0/400 |
| 083 | 2–5 | 199/400 | 0/400 · 0/400 |
| 084 | 2–8 | 349/400 | 0/400 · 0/400 |
| 085 | 2–7 | 304/400 | 0/400 · 0/400 |
| 086 | 2–5, 8, 9 | 329/400 | 0/400 · 0/400 |
| 087 | 2–5, 7, 8 | 290/400 | 0/400 · 0/400 |
| 088 | 2–9 | 400/400 | 0/400 · 0/400 |
| 089 | 2–9 | 400/400 | 0/400 · 0/400 |

**Akibat untuk v2:** P3 menjana `{MY_PHONE_BS}` sebagai `08K` + 6 digit dengan digit pertama dari jadual di atas (julat sah
libphonenumber, ADR-002 — recall telefon kekal terlebih optimis, disebut dalam kertas). Nilai disimpan dalam
`config/ssm_rob.yaml` `talian_tetap_bs`, bukan dalam kod.
