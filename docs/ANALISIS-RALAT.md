# Analisis ralat MyPII (A3 P3, 28 Okt 2026) — bahan seksyen batasan kertas

**Cara ulang:** `make analisis` (`mypii/analisis.py`; keluaran `hasil/analisis-ralat.json`, tidak dikomit). Ia menyenaraikan
setiap ralat span tepat MyPII atas split `latih` + `dev` dan menjalankan **probe sintetik** `data/probe/ralat.yaml`
(8 kategori × 40 dokumen, benih 20261029). Split `ujian` tidak dibaca (alat menolak `--split ujian`).
Probe BUKAN sebahagian MyPII-Bench: semua nilai dari `mypii/jana/nilai_palsu.py`; nama syarikat probe ialah rekaan
baharu yang sengaja tiada dalam `data/nama.yaml`. Kod pengecam = komit P2-10 (dev F1 `*` 0.9987, `make nilai` 28 Okt). **⚠ 29 Okt: P2-10 DIUNDUR atas dapatan jadual ini** (LOG-ITERASI) — selepas undur: negatif_berkurung 0 FP, syarikat_luar_senarai 8/40 tepat, dev F1 `*` 0.9954; baris lain tidak berubah.

Jenis ralat: **fp** (ramalan tanpa emas bertindih) · **fn** (emas tanpa ramalan bertindih) · **keliru** (bertindih
dengan entiti lain, cth SSM diramal sebagai NRIC) · **sempadan** (entiti sama, span lain — tiada satu pun dijumpai).

## 1. Baki ralat dalam penanda aras (latih + dev)

| set | genre | ralat | punca |
|---|---|---|---|
| dev | aduan | 1 keliru (SSM baharu → NRIC) | nama syarikat dari senarai tertutup tanpa Sdn Bhd/Enterprise; 12 digit itu sah bentuk MyKad |
| dev | resit | 1 fn SSM | SSM lama `NNNNNNN-X` tanpa kurungan selepas nama yang sama — skor `lama` 0.1, tiada frasa konteks |
| latih | hr_email | 10 fp NRIC | no. akaun bank 12 digit sah bentuk MyKad selepas nama bank ("to CIMB …"); P2-7/P2-11 cuba nama bank — buang |
| latih | borang_kerajaan | 7 fp SSM | cap masa `YYYYMMDDhhmm` lulus semakan SSM baharu (tahun + "kod jenis" 01–06 = bulan); P2-9 — buang |
| latih | borang, resit | 2 + 2 keliru | SSM baharu selepas nama syarikat tanpa kata konteks (dalam kurungan atau dipisah paip; borang: "Majikan:" — P2-12 buang) → diramal NRIC |

Dev hanya tinggal 2 ralat daripada 1,000 dokumen: dev **di siling**, jadi ralat di atas bukan gambaran dunia sebenar —
seksyen 2 mengukur apa yang dev tidak uji.

## 2. Probe sintetik — batasan yang dev tidak uji

| kategori | emas | ramal | tepat | ralat | apa yang ia tunjukkan |
|---|---|---|---|---|---|
| negatif_berkurung | 0 | 40 | 0 | 40 fp SSM | peraturan P2-10 `(123456-X)` = SSM menangkap SETIAP kod produk dalam kurungan |
| negatif_tanpa_kata | 0 | 37 | 0 | 37 fp NRIC | 12 digit sah bentuk MyKad (no. ahli, polisi, akaun) tanpa kata negatif dalam senarai = MyKad |
| telefon_bukan_telefon | 0 | 26 | 0 | 26 fp PHONE | nombor dalam julat telefon sebagai no. siri / ID pelanggan; hanya "pesanan" (kata negatif) menyelamatkan 14 |
| ocr_digit | 40 | 0 | 0 | 40 fn NRIC | satu aksara OCR DALAM nombor (`O`↔0, `l`↔1, `S`↔5, `B`↔8) = sifar dikesan |
| patah_baris | 40 | 0 | 0 | 40 fn NRIC | MyKad dipecah merentas baris (salinan PDF) = sifar dikesan |
| syarikat_luar_senarai | 40 | 18 | 18 | 22 fn SSM | SSM lama selepas nama tanpa bentuk undang-undang (10/10 terlepas) atau selepas "Invoice from" (10/10); dalam kurungan 10/10 dan 12 digit baharu 8/8 dikesan (2 terlepas dalam templat itu = format lama) |
| konteks_jauh | 40 | 26 | 26 | 14 fn NRIC | lihat 3.2 — puncanya kata "pendaftaran", bukan jarak: templat yang sama dengan "permohonan" = 14/14 dikesan |
| jadual_tidak_teratur | 70 | 69 | 68 | 2 fn SSM, 1 keliru | pengepala "No. Daftar" (bukan "pendaftaran") dalam jadual paip; pengepala dua baris/bukan baris pertama lulus |

Contoh (semua nilai palsu, dari larian probe): `Model penapis air (560578-W) habis stok` → SSM ·
`Polisi takaful 510520 33 2615 akan diperbaharui` → NRIC · `Serial no. 03-3326 4907` → PHONE ·
`No. KP: S7l012 47 653l` → tiada · `No. Kad Pengenalan: 780629⏎848879` → tiada · `Klinik Gigi Senyum 1275281-X` → tiada.

## 3. Kategori ikut apa yang diperlukan untuk membaikinya

### 3.1 Boleh dengan regex/normalisasi (masih dalam skop pengecam corak)
- **OCR dalam nombor** dan **patah baris**: normalisasi aksara (`O`→0 hanya bila diapit digit) dan benarkan `\s*\n\s*`
  di sempadan kumpulan sebelum corak. Risiko: menaikkan FP pada kod alfanumerik — perlu negatif probe dahulu.
- **Cap masa sebagai SSM** (latih borang_kerajaan): semakan tambahan "6 digit siri ≠ HHMMSS/DDHHMM yang sah" mengurangkan
  FP tetapi tidak menghapusnya (siri SSM sebenar boleh kebetulan berbentuk masa).

### 3.2 Perlukan konteks yang lebih kaya (bukan senarai kata tetap)
- **Negatif tanpa kata** (no. ahli/polisi/akaun): senarai negatif sentiasa tidak lengkap. P2-7/P2-11 (nama bank) tidak
  menaikkan dev kerana dev tiada kes itu — probe menunjukkan 37/40 FP. Keputusan sama ada nombor ialah MyKad bergantung
  pada peranan nombor dalam ayat → pengelas konteks/NER, bukan regex.
- **Telefon bukan telefon**: corak + libphonenumber hanya menyemak julat sah; "ID pelanggan 019-…" ialah sah. Sama seperti di atas.
- **Kata konteks terlalu umum** (P2-4): "pendaftaran" ialah konteks SSM, dan peraturan `bersaing` (P2-3b) membatalkan NRIC
  bila konteks SSM lebih dekat. Ayat "Kad pengenalan pemohon … semasa pendaftaran awal ialah 600129-33-7186" kehilangan
  MyKad (14/14) — **walaupun nombor bersempang** yang biasanya lulus tanpa konteks. Kos ketepatan P2-4/P2-3b yang tidak
  kelihatan dalam dev.
- **"Enterprise" (nota P2-13)**: diukur dengan config sementara tanpa `enterprise` → dev F1 `*` tetap 0.9987, SSM R tetap
  0.9932. Selepas peraturan berkurung P2-10, sumbangan kata itu atas dev = **sifar**; ia dikekalkan kerana ia bentuk
  undang-undang ROB, bukan kerana angka.

### 3.3 Perlukan NER / susun atur dokumen
- **Nama perniagaan terbuka**: SSM lama tanpa kurungan selepas "Klinik Gigi Senyum" tidak boleh dibezakan daripada kod
  produk tanpa mengenali bahawa frasa sebelumnya ialah NAMA ORGANISASI (entiti ORG). Senarai akhiran (P2-13) menghafal
  bench; NER ORG ialah jalan yang jujur.
- **Kurungan dua hala**: peraturan P2-10 (`(123456-X)` = SSM) dan negatif berkurung (40/40 FP) bercanggah sepenuhnya —
  yang membezakannya ialah sama ada frasa sebelum kurungan ialah ORG atau barang. Sama: NER.
- **Jadual sebenar**: P2-8 menyelesaikan jadual teratur. Probe menunjukkan pengepala bukan baris pertama dan pengepala dua
  baris masih lulus; kegagalan tinggal pada kosa kata pengepala ("No. Daftar"). Jadual dengan sel bercantum/lajur tidak
  sejajar (PDF → teks) belum diuji — perlu pengurai susun atur, bukan corak.

## 4. Akibat untuk kertas dan gelung seterusnya
1. Angka dev (0.9987 semasa analisis; 0.9954 selepas P2-10 diundur 29 Okt) mesti dilapor bersama jadual seksyen 2 — ia mengukur liputan templat, bukan pengecam.
2. Penanda aras v2 patut menambah kategori probe sebagai templat (negatif berkurung, nombor ahli/polisi, ID bentuk telefon,
   nama syarikat terbuka, OCR dalam nombor) — **sebelum** gelung pengecam seterusnya, supaya pembaikan diukur, bukan dihafal.
3. Pengecam corak + konteks frasa ialah garis dasar yang jujur; kategori 3.2/3.3 = hujah untuk lapisan NER/LLM (NEXT #3).
