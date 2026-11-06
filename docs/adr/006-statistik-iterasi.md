# ADR-006: Rekod iterasi mesin + statistik ketidakpastian (PELAN-C, 30 Okt 2026)

Bahagian **Iterasi** = C2a, **Carta** = C2b, **Statistik** (bootstrap dokumen, ujian berpasangan, Holm) = C3a.

## Iterasi — `hasil/iterasi.tsv` (C2a)

**Masalah.** Sejarah cubaan gelung hanya wujud sebagai jadual prosa `docs/LOG-ITERASI.md`: lajurnya berubah antara fasa, cubaan yang
crash tidak direkod, dan tiada mesin boleh mencartanya atau menjawab "berapa cubaan dibuang sebelum angka ini?". Penilai kertas akan
bertanya soalan itu.

**Keputusan.**
- Setiap `make nilai STATUS=… KETERANGAN="…"` menambah SATU baris TSV (corak `results.tsv` karpathy/autoresearch — format sahaja, tiada
  kod/teks disalin; repo itu tiada lesen). Modul `mypii/nilai/iterasi.py`; harness `--iterasi STATUS --keterangan TEKS` memanggilnya
  selepas skor. Lajur (config `nilai.iterasi.lajur`): `tarikh` (UTC ISO) · `komit` (`git rev-parse --short HEAD`, `+` = tree kotor di luar `kotor_abai` = `hasil/`, supaya TSV ini sendiri tidak menanda) ·
  `dev_sha8` (dari `CINCANGAN.json` — baris dari dev berlainan TIDAK boleh dibanding) · `f1` (`semua|*` tepat `mypii`) · `status` ·
  `baris_kod` (`+tambah/-buang` `git diff --numstat HEAD` atas `mypii/pengecam` + `config/mypii.yaml` = kos kerumitan) · `keterangan`.
- Status: `simpan`, `buang`, `crash`, `ukur` (pengukuran tanpa keputusan — potongan dokumen/proses). `crash` tidak boleh dipilih
  tangan: harness yang melempar ralat menulis baris `crash` (keterangan = baris ralat terakhir, f1 kosong) dan kemudian gagal seperti
  biasa (exit ≠ 0) — cubaan gagal tidak hilang dari rekod.
- Medan dibersihkan (tab/baris baharu → ruang) dan keterangan dipotong pada `had_keterangan`; pengepala ditulis hanya bila fail tiada.
- **Tambah-sahaja**: gerbang autopilot menolak penyuntingan/pemadaman baris yang sudah dikomit. Pembetulan = baris baharu.
- **Isi semula sekali** (`scripts/iterasi_dari_log.py`, enggan menulis bila fail berisi): setiap baris jadual LOG → satu baris TSV,
  kronologi. Pemetaan jujur, tiada nilai direka: status = kata kunci TERAWAL dalam lajur Keputusan (simpan → `simpan`, buang/undur →
  `buang`, ukur/tiada → `ukur`); `f1` = lajur `F1 *` hanya bila baris format 9 lajur dan nombor (tidak dipetik dari prosa); `komit` =
  `-` (LOG tiada lajur komit); `dev_sha8` = `?` sehingga baris pertama yang menyebut cincangan dev (B2, `531532cf`), dibawa ke baris
  berikutnya kerana dev hanya berubah pada baris yang menyatakannya; `baris_kod` kosong; `tarikh` = tarikh LOG (tanpa masa).
- `.gitignore`: `hasil/*` dengan pengecualian BERNAMA (`iterasi.tsv`, `kemajuan.svg`, `dev-statistik.json`, cache LLM, `dev-masa.json`);
  `hasil/ramalan/` dan `hasil/*ujian*` kekal diabaikan.

**Akibat.** LOG-ITERASI kekal sebagai naratif (sebab, hipotesis); TSV ialah rekod mesin untuk carta (C2b) dan kiraan cubaan.
Baris isi semula tanpa `dev_sha8` sebenar (`?`) tidak boleh dibanding antara satu sama lain melainkan LOG menyatakan dev sama.

**Undur.** Buang `mypii/nilai/iterasi.py`, `--iterasi/--keterangan` harness, `STATUS/KETERANGAN` Makefile, kunci `nilai.iterasi:`,
`tests/test_iterasi.py`, `scripts/iterasi_dari_log.py`; `program.md` (sejarah git). TSV boleh kekal sebagai data.

## Carta — `hasil/kemajuan.svg` (C2b)

**Masalah.** TSV boleh dibaca mesin tetapi tidak menjawab sekilas "adakah gelung masih maju, dan berapa cubaan dibuang?".

**Keputusan.**
- `make carta` → `mypii/nilai/carta.py` (stdlib — rentetan SVG + `xml.sax.saxutils.escape`; tiada matplotlib). Bait sama setiap larian:
  tiada cap masa, koordinat 1 titik perpuluhan. Paksi-x = nombor iterasi (baris TSV); paksi-y = `f1`, julat dibundar ke `langkah_y`.
- **Satu titik setiap baris TSV.** Status dikod dengan warna DAN bentuk (simpan bulat · buang segiempat · ukur berlian · crash pangkah)
  supaya identiti tidak bergantung pada warna sahaja. Baris tanpa F1 (crash, atau baris isi semula/dokumen tanpa skor) = penanda di
  LORONG DASAR di bawah paksi-x (berongga bila bukan crash) — bukan pada F1 = 0, yang akan menipu skala.
- **Garis "terbaik setakat ini" dari `simpan` SAHAJA**, langkah naik, dan **tidak pernah merentas segmen**. Segmen baharu bila
  `dev_sha8` berubah ATAU bernilai `?`: `?` bermaksud dev tidak diketahui (isi semula sebelum B2), dan dev memang berubah dalam tempoh
  itu (P1 menambah 63 templat) — menyambung dua titik `?` akan mendakwa kesinambungan yang tidak kita ketahui. Akibatnya, pada data
  semasa tiada garis dilukis (baris `?` = segmen sebaris; segmen `531532cf` belum ada `simpan`) dan legenda hanya menyenarai unsur yang
  ada. Pemisah putus-putus + label `dev <sha8>` pada setiap perubahan nilai `dev_sha8` (larian `?` dilabel sekali).
- Palet = skil dataviz `references/palette.md`, tiga slot kategori pertama (biru/oren/aqua — satu-satunya set yang lulus validator
  untuk semua pasangan, kerana titik bertaburan). `validate_palette.js --pairs all`: terang LULUS (CVD terburuk ΔE 9.2, normal 24.0;
  AMARAN kontras aqua 2.74:1 → dilegakan oleh bentuk + legenda + tooltip + jadual TSV), gelap LULUS (CVD 9.4, normal 20.9, kontras ≥ 3:1).
  Crash memakai dakwat sekunder, bukan warna status (warna status dikhaskan). Mod gelap = blok `prefers-color-scheme` dengan langkah
  gelap palet yang sama, bukan songsangan automatik.
- Setiap titik ada `<title>` (tooltip asli pelayar): nombor, status, F1, dev, komit, tarikh, keterangan dipotong `had_tooltip`.
- Semua teks (BM · EN), saiz, jidar, langkah, warna terang/gelap dan bentuk = config `nilai.iterasi.carta` — kod tidak menyimpan nilai.

**Akibat.** Carta dijana semula selepas setiap `make nilai` (manusia/pembina menjalankan `make carta`; tidak automatik supaya
`make nilai` kekal satu tujuan). SVG dikomit (pengecualian `.gitignore` C2a).

**Undur.** Buang `mypii/nilai/carta.py`, `tests/test_carta.py`, sasaran `carta` Makefile, kunci `nilai.iterasi.carta`, `hasil/kemajuan.svg`.

## Statistik — selang bootstrap + ujian berpasangan (C3a)

**Masalah.** Jadual F1 titik (B4) tidak menjawab "adakah beza ini nyata atau hingar sampel?". Penilai kertas memerlukan selang
keyakinan dan ujian kesignifikanan berpasangan, dengan pembetulan untuk beberapa garis dasar.

**Keputusan.**
- Harness menyimpan ramalan per dokumen setiap larian: `<keluar>/ramalan/<split>-<sistem>.jsonl`, satu baris `{id, spans}`
  (`folder_ramalan` config). `hasil/ramalan/` DIABAIKAN git (fail besar, boleh dijana semula). Split dikunci tidak pernah ditulis
  oleh gelung kerana gelung tidak boleh membacanya (`--benarkan-ujian` = manusia, C4b); bila manusia menjalankannya, ramalan ujian
  ditulis di bawah `hasil/` yang diabaikan (`hasil/*ujian*`/`hasil/ramalan/`).
- `--statistik` (`make statistik`) membaca ramalan tersimpan SAHAJA — tiada Presidio, spaCy atau rangkaian — dan menulis
  `<keluar>/<split>-statistik.json` (`sort_keys`, bait sama untuk benih sama) + jadual markdown. Id ramalan mesti sepadan tepat
  dengan split (id hilang/lebih = ralat, bukan dianggap kosong). `--statistik` tidak boleh digabung dengan `--iterasi` (ia tidak menilai).
- **Unit sampel semula = dokumen**, bukan span: span dalam dokumen yang sama berkongsi templat, gaya dan konteks, jadi ralatnya
  berkorelasi; menyampel span menganggapnya bebas dan menyempitkan selang secara palsu. Setiap sampel dinilai dengan `harness.skor()`
  SEDIA ADA (dipanggil, bukan disalin — gerbang §4 mengunci AST-nya; ujian memalsukannya dan mengira panggilan).
- **Selang** = persentil (interpolasi linear) F1 tepat atas `ulangan` sampel semula dengan ganti. Kunci: `kunci_utama` (`semua|*`,
  hipotesis utama) + `semua|<entiti>` untuk setiap `nilai.entiti` (sekunder). Sampel yang F1-nya tidak tertakrif (tiada emas DAN tiada
  ramalan entiti itu) dilangkau; bilangan sah dicatat `n_sah`.
- **Berpasangan** (rujukan `mypii` lawan setiap sistem lain): indeks sampel SAMA untuk kedua-dua sistem (benih sama → sampel dikongsi
  dengan selang). ΔF1 + selang persentil Δ*; **p bootstrap sehala** Berg-Kirkpatrick, Burkett & Klein (2012): p = #(δ* > 2δ)/B
  (sampel bootstrap berpusat pada δ, jadi 2δ mengalihkan taburan ke hipotesis nol); δ ≤ 0 → p = 1 (tiada bukti A > B). p = 0
  dilapor "< 1/B" dalam jadual. **Ujian rawak anggaran** (Noreen 1989; Yeh 2000): setiap pilih atur menukar ramalan A/B satu dokumen
  dengan kebarangkalian ½; p = (b+1)/(R+1), b = #(δ_r ≥ δ) — tidak pernah 0. Kedua-dua dilapor (F1 korpus bukan purata per dokumen,
  jadi ujian-t berpasangan tidak terpakai).
- **Holm-Bonferroni** (langkah turun) atas k garis dasar, berasingan untuk setiap kunci dan setiap jenis p; nilai mentah dan
  terlaras kedua-duanya disimpan. Kaedah lain ditolak (ralat) supaya config tidak menipu senyap.
- Config `nilai.statistik:` (ulangan 1000, benih 2026, aras 0.95, kaedah holm, rujukan, kunci utama, folder, perpuluhan) — kod membaca.
  Stdlib sahaja (`random.Random(benih)`), tiada numpy/scipy.

**Akibat.** Kos ≈ (sistem × B + garis dasar × 2R) panggilan `skor` (~24 ms setiap satu atas dev 1,000 dok). Selang DEV menerangkan
hingar sampel dev sahaja: dev ditala oleh gelung, jadi selangnya TIDAK menyokong dakwaan kertas — dakwaan datang dari ujian2 pra-daftar (C4a).

**Undur.** Buang `mypii/nilai/statistik.py`, `tests/test_statistik.py`, fungsi `_dokumen/fail_ramalan/simpan_ramalan/baca_ramalan/statistik`
dan bendera `--statistik` harness, sasaran `statistik` Makefile, kunci `nilai.statistik`. `hasil/ramalan/` boleh dipadam bila-bila.
