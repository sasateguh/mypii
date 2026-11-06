# Kajian literatur MyPII — ringkasan (A3 P4, 28 Okt 2026)

Rujukan: `rujukan.bib` (24 entri, setiap DOI disahkan wujud — lihat kepala fail itu). Petikan di bawah ialah kunci fail itu bertanda @ dalam kurungan siku;
`tests/test_literatur.py` memastikan setiap petikan wujud dalam `.bib` dan setiap entri `.bib` dipetik.

## Kaedah (boleh diulang)
- **Calon:** `search_openalex.py` (skil `citation-management`, OpenAlex `/works?search=`, susunan relevan, 5–8 teratas) untuk 16 pertanyaan:
  Presidio PII; de-identifikasi klinikal; penanda aras PII sintetik; PII + LLM; NER Melayu; NER Melayu–Inggeris bercampur; regex
  de-identifikasi; sanitasi teks; TAB; i2b2 2014; ulasan de-identifikasi EHR; model anonimisasi teks; GLiNER; nombor kad pengenalan
  Malaysia; alat NLP Melayu; PII multibahasa sumber rendah. Dipilih tangan ikut kaitan dengan MyPII (bukan bilangan petikan).
- **Kandungan:** abstrak OpenAlex (`openalex_abstract.py`, skil `paper-lookup`) — **abstrak sahaja, bukan teks penuh.** Untuk
  [@Lison2021anonymisation], [@Zaratiana2024gliner] dan [@Savkin2025enhancing] OpenAlex tiada abstrak; dakwaan di bawah terhad pada tajuk/tempat terbit.
- **Pengesahan:** `doi_to_bibtex.py` (metadata dari pendaftar DOI, bukan OpenAlex) → `validate_citations.py --check-dois` (24/24 sah)
  + `https://doi.org/<doi>` (302 untuk 24/24). **Satu calon dibuang:** DOI ulasan skop teks Melayu bising yang dipulangkan OpenAlex
  (`10.24191/mij.v7i1.11574`) → 404 di doi.org dan Crossref. Bukti bahawa metadata OpenAlex sahaja tidak cukup.
- **Pengecam pihak ketiga** (perisian tanpa DOI, tidak dalam `.bib`): disemak melalui API GitHub + PyPI pada 28 Okt 2026.
- **Batasan kajian:** satu enjin carian (OpenAlex) + relevan teratas = bukan kajian sistematik. 8 entri ialah pracetak arXiv (6 daripadanya 2025–2026)
  yang belum tentu disemak rakan sebaya. Sebelum kertas: baca teks penuh entri yang dipetik untuk dakwaan berangka, dan ulang carian
  di Semantic Scholar/ACL Anthology.

## 1. De-identifikasi klinikal — asal-usul kaedah MyPII
- Pakej Perl [@Neamatullah2008automated] mencari PHI dengan **jadual carian leksikal + ungkapan nalar + heuristik ringkas** — susunan yang
  sama dengan pengecam Presidio berasaskan corak + konteks. Ulasan [@Meystre2010automatic] merangkum kaedah automatik untuk 18 unsur
  "Safe Harbor" HIPAA.
- Tugasan bersama i2b2/UTHealth 2014 [@Stubbs2015automated] meluaskan set PHI melebihi HIPAA; korpusnya [@Stubbs2015annotating]
  (1,304 rekod, 296 pesakit) dianotasi berganda + timbang tara, dan melaporkan **F1 token anotator berbanding emas = 0.927**.
  → MyPII belum ada angka persetujuan manusia (M4); tanpa itu siling sebenar penanda aras tidak diketahui.
- [@Dernoncourt2016identification] menunjukkan rangkaian neural (RNN) untuk nota pesakit — arah yang Presidio sokong melalui NER, bukan
  arah MyPII (pengecam corak untuk pengecam berstruktur).

## 2. Anonimisasi teks umum
- [@Lison2021anonymisation] (ACL 2021) memetakan model anonimisasi teks dan cabarannya. [@Pilan2022text] (TAB) membina korpus 1,268 kes
  ECHR **bahasa Inggeris** dengan metrik berorientasikan privasi, kerana sumber beranotasi berorientasikan privasi kurang.
- [@Patsakis2023machine] membandingkan anonimisasi manusia vs mesin dalam era LLM.
- → TAB menilai *dokumen* dan risiko pendedahan; MyPII menilai *pengesanan rentang* tiga pengecam berstruktur. Kertas MyPII tidak patut
  mendakwa "anonimisasi"; ia pengesanan PII.

## 3. PII dan model bahasa
- [@Lukas2023analyzing] (IEEE S&P 2023): penggosokan (scrubbing) **mengurangkan tetapi tidak menghalang** kebocoran PII dari LM, dan
  penggosokan sebenar tidak sempurna. → Hujah bahawa ketepatan pengesan (termasuk FN pada format tempatan) penting di hulu latihan LM.

## 4. Penanda aras PII sintetik dan model terkini (2023–2026)
- Dataset/penanda aras sintetik: SPY [@Savkin2025enhancing]; PIIBench [@Jha2026piibench] menggabungkan 10 set awam → 2,369,883 urutan,
  48 jenis entiti, kerana skema anotasi sedia ada tidak serasi; PII-TRACE [@Zhang2026trace] — 13,148 dialog sintetik berbilang giliran
  dalam 13 bahasa, dan menurut abstraknya tiada pengesan (termasuk LLM terdepan) yang menyelesaikannya.
- Model: GLiNER [@Zaratiana2024gliner]; GLiNER2-PII [@Zaratiana2026gliner] (0.3B, 42 jenis, korpus sintetik multibahasa 4,910 teks —
  abstraknya menyebut rentang PII "bergantung lokal"); pengesan pengekod 141M [@Hsu2026broad] yang menekankan **kadar positif palsu rendah**
  dan bahawa label antara set awam bercanggah walaupun skema dipetakan. PII-Codex [@Rosado2023codex] = pustaka pengelasan + keterukan PII.
- **Tidak disemak:** sama ada mana-mana set di atas mengandungi MyKad/SSM/telefon Malaysia atau teks BM. Abstrak tidak menyebutnya.
  Semak teks penuh/kad data sebelum kertas mendakwa "tiada penanda aras PII Malaysia".

## 5. Keteguhan di bawah anjakan taburan
- [@Zafar2026mind] membina ujian tekanan 7 kategori anjakan taburan semula jadi dan menilai spaCy (NER pengekod), **Presidio** (hibrid
  peraturan) dan Qwen2.5-3B; ketiga-tiganya merosot pada input luar taburan (bising, tidak berstruktur, tidak formal).
- → Sepadan dengan `docs/ANALISIS-RALAT.md`: dev MyPII di siling (F1 0.9987; 0.9954 selepas P2-10 diundur) tetapi probe di luar bench gagal pada OCR-dalam-nombor
  (40/40 FN) dan patah baris (40/40 FN). Kertas mesti melaporkan probe ini bersama angka bench.

## 6. Bahasa sumber rendah, BM dan Manglish
- PII sumber rendah: RECAP [@Rajgarhia2025evaluation] — regex deterministik + LLM berkonteks, 13 lokal, > 300 jenis entiti (abstrak
  tidak menyenaraikan lokal; **tidak diketahui sama ada ms_MY termasuk**); PII Luganda dengan pembelajaran dalam [@Africano2024detection].
  Kedua-duanya menyokong corak "regex + konteks" untuk bahasa tanpa data beranotasi.
- NER Melayu: berasaskan peraturan [@Alfred2014malay], CRF [@Salleh2017malay], dan dataset terbuka MYNER 28,991 ayat [@Fu2021open].
  Tiada satu pun menyasarkan pengecam berstruktur (MyKad/SSM/telefon) — entiti mereka orang/lokasi/organisasi.
- Manglish/campur kod: korpus X Melayu–Inggeris [@Maskat2024annotated]; tinjauan pemprosesan campur kod [@Sitaram2019survey] yang
  menyatakan data campur kod terhad. → Templat Manglish MyPII ialah sintetik; kertas mesti menyebut ia tidak mewakili taburan sebenar.

## 7. Pengecam pihak ketiga sedia ada (disemak 28 Okt 2026, bukan dalam `.bib`)
| Projek | Lesen | Apa yang dibuat | Keadaan |
|---|---|---|---|
| Microsoft Presidio (`data-privacy-stack/presidio`) | MIT | `predefined_recognizers/country_specific/` ada 18 negara — termasuk Singapura (FIN, UEN), Thai, Filipina — **tiada Malaysia** | aktif (tolak 27 Okt 2026) |
| `laizhenyoong/malaysia-pii-guard` | MIT | MyKad (tarikh lahir sah + kod negeri), telefon (pelan penomboran), pasport, akaun bank (10–16 digit + konteks), e-mel; enjin sendiri bergaya Presidio | ★8, tolak terakhir 1 Sep 2026, **belum di PyPI** (404) |
| `c0denician88/llm-guardrails-sea` | MIT | pagar LLM Asia Tenggara: suntikan prompt + penyamaran PII (NIK, NRIC, MyKad, ID Thai) | ★0 |
| `adamy/RedactWire` | Apache-2.0 | pengesanan PII .NET, peraturan bersemak checksum untuk 58 negara | ★0 |

**Jujur:** MyPII **bukan** pengesan MyKad pertama — `malaysia-pii-guard` sudah mengesahkan tarikh lahir + kod negeri. Ia dijadikan
garis dasar dan dikreditkan (PRD), bukan dilawan.

## Jurang yang MyPII isi (dakwaan yang boleh dipertahankan sekarang)
1. **Pengecam Malaysia dalam hulu Presidio** — direktori negara Presidio tiada Malaysia (disemak); MyPII ditulis sebagai `PatternRecognizer`
   Presidio supaya boleh dicadangkan ke hulu (isu dihantar pemilik).
2. **SSM (format baharu 12 digit + lama `123456-X`)** dan **negatif keras** (12 digit bukan MyKad: akaun, invois, SSM 2001–2012) —
   tiada dalam senarai ciri pihak ketiga di atas; literatur §4 menekankan FPR rendah, tetapi tidak untuk format Malaysia.
3. **Penanda aras BM/EN/Manglish dengan split ujian dikunci sha256** — sumbangan penilaian; bezanya dengan §4 belum disahkan dari teks penuh.

## Belum boleh didakwa
- "Penanda aras PII Malaysia pertama" — perlu semakan teks penuh PIIBench, PII-TRACE, GLiNER2-PII, RECAP (§4, §6).
- Prestasi berbanding `malaysia-pii-guard` / LLM — harness belum menilainya (NEXT.md #3).
- Persetujuan manusia — tiada (M4); bandingkan dengan 0.927 i2b2 [@Stubbs2015annotating] bila ada.
