# ADR-018: MyPII v2 — data v3, pengecam diperbaiki, ujian3 dimeterai (PELAN-V2, 4 Nov 2026)

**Masalah.** v1 sudah diuji sekali atas `ujian`/`ujian2` (tag `mypii-v1-muktamad` → `e846e49`; keputusan muktamad). Pemilik mahu
pengecam "lebih padu": `docs/ANALISIS-RALAT.md` §2–§3 menunjukkan kategori yang v1 tidak kesan (OCR dalam nombor, patah baris) atau
tersalah tangkap (12 digit tanpa kata negatif), dan dapatan baharu (LLP, talian Sabah/Sarawak). Dev-v2 dan split ujian v1 tiada kes ini,
dan ujian v1 tidak boleh dipakai semula untuk mengukur v2 (sudah dibuka). Perlu data baharu + split ujian baharu + pra-daftar baharu.

**Keputusan.**
- **Pra-daftar dahulu:** pindaan `docs/PRA-DAFTAR.md` "2026-11-04 — MyPII v2: dev3 + ujian3 (selepas ujian v1 dibuka)" dikomit SENDIRI
  sebelum kod/config/data v3 (gerbang autopilot §4). H4a (bukan-inferioriti vs Claude Haiku 5.5, δ = 0.01) + H4b (v2 > v1) atas ujian3,
  keluarga Holm baharu k = 2; MDE + pengecam beku = pindaan kedua sebelum ujian3 dibuka.
- **Data v3 berasingan:** `data/bench_v3/` (latih3 3000 / dev3 1000 / ujian3 1000; benih `jana.benih` + 3 / + 4), nilai baharu dalam
  `mypii/jana/nilai_v3.py` dengan rng sendiri — `nilai_palsu.py` dan susunan panggilan rng v1 tidak disentuh, jadi `make jana` v1 = tiada
  diff. Semua saiz/nisbah/had dalam config `jana_v3:`; fakta bentuk dari `config/ssm_rob.yaml` (sumber rasmi P1).
- **Kategori:** (a) ROB lama GUGUR (tiada sumber rasmi, P1); (b) LLP kod 04–06 tahun ≥ 2012; (c) talian 082–089; (d) OCR + patah baris
  (span emas = subrentetan asal); (e) negatif 12 digit tanpa kata negatif.
- **Penjana dua keluarga baharu:** A (latih3/dev3) StepFun → Tencent Hunyuan; B (ujian3) MiniMax → xAI Grok; bukan keluarga mana-mana
  penjana/garis dasar lepas; probe format sahaja; semua gagal = berhenti (tiada pilihan model di luar pindaan).
- **Pengelas konteks kecil, tempatan:** LogisticRegression (scikit-learn = extra `latih`, alat latih sahaja) atas latih3 SAHAJA →
  artifak JSON < 2 MB (sha dalam config) → ramalan numpy dalam `mypii/pengecam/`; tiada API/rangkaian semasa ramalan.
- **Ujian3 = corak ujian2:** templat + nama keluarga B, pembina tidak membaca kandungan, `KUNCI3.json` + `UJIAN3-MUKTAMAD` dikomit sendiri,
  dibuka SEKALI oleh `scripts/ujian3-muktamad.sh` (perintah = blok §7-v2 pindaan, bait sama) dengan arkib luar repo
  `~/ops/mypii/arkib-ujian3/`. MyPII-v1 untuk H4b dimuat dari `git worktree` pada tag.
- **Kos:** Haiku sahaja (bukan Sonnet/Opus/Fable); baki = had USD 20 − lejar repo − belanja ujian v1 tidak dikomit (USD 3.399903);
  tidak cukup = H4a "tidak diuji", had tidak dinaikkan.

**Ditolak.** Menilai v2 atas `ujian`/`ujian2` (sudah dibuka — dakwaan generalisasi tidak sah); mengubah split v1 atau `nilai_palsu.py`
(memecah kebolehhasilan semula v1); menjana bentuk ROB dari forum/firma (bukan sumber rasmi); GLiNER/LLM tempatan dalam pengecam (saiz,
bukan "kecil"; kerja masa depan); keluarga penjana lama (Gemini/Kimi/GLM) atau keluarga garis dasar (kitaran penjana = penilai);
memasukkan Sonnet/eksplorasi v1 ke ujian3 (kos + menambah k tanpa soalan pemilik); keluarga Holm gabungan dengan H1/H2 (kajian berbeza).

**Jalan undur.** `git checkout mypii-v1-muktamad -- mypii/pengecam config/mypii.yaml` = pengecam v1; buang `data/bench_v3/`,
`data/templat_v3/`, `data/templat_ujian3/`, `data/nama_ujian3.yaml`, `mypii/jana/nilai_v3.py`, `mypii/konteks_latih.py`, `model/` = repo v1
+ pindaan dokumen sahaja. Pindaan PRA-DAFTAR kekal (tambah-sahaja) sebagai rekod.

**Bukti (P2, 4 Nov 2026).** Pindaan dikomit tanpa kod/config/data (`git diff --stat` = docs + PELAN/NEXT); `make uji` + `make lint`
lulus; `make jana` → `data/bench` tiada diff.

**Keputusan pelaksanaan P4 (4 Nov 2026).** (1) `ujian3` dibaca harness hanya bila PRA-DAFTAR di HEAD ada ≥ 2 tajuk "MyPII v2" (pindaan P2
+ pindaan kuasa P13) — lebih ketat daripada ujian/ujian2, kerana ujian3 hanya dibuka selepas pengecam v2 dibekukan. (2) Probe penjana =
satu permintaan kecil (4 templat, 1 negatif) bahasa + genre pertama; lulus = diurai + ≥ 50% lulus pengesah; keputusan ditulis SEKALI ke
`data/probe/penjana-<sasaran>.json` (statistik sahaja) dan jana memakai `dipilih` SAHAJA (tiada sandaran semasa jana — "calon pertama
lulus dipakai; tiada calon lain"). (3) Pengesah templat v3 memetakan slot v3 ke slot v1 setara (`templat_llm.slot_v3.*.setara`) dan
memanggil pengesah v1 tanpa mengubahnya; panjang diukur atas teks dipetakan (beza ≤ 6 aksara setiap slot). (4) Genre ujian3 diperiksa kod
(kunci sahaja, tiada kandungan dicetak) atas `data/templat`, `templat_ujian`, `templat_ujian2`, `templat_v3` sebelum LLM dipanggil.
