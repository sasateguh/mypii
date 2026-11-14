# ADR-021: MyPII v2.1 — frasa didahulukan atas pengelas; ujian4 dari penjana keluarga baharu dihos sendiri (14 Nov 2026)

**Masalah (diukur 14 Nov, `PELAN-V21.md` §Kenapa).** v2 (1.0.x) memakai `konteks.gabung.cara: ganti`: pengelas konteks (dilatih atas
latih3 = gaya Nemotron SAHAJA) memutuskan setiap calon, jadi frasa "IC" tepat di depan nombor diabaikan. 24 ayat biasa: v2 20/24,
v1 24/24 ("My IC is 900101-08-1234" p 0.49). Atas `dev` (gaya v1): 48 MyKad benar berfrasa positif dibuang; 142 FP SSM format lama
tanpa frasa disimpan (kod produk berkurung). Atas `dev3` pengelas memang perlu (negatif keras 12 digit tanpa kata, kategori e).
Langkah B (model luar) hanya deskriptif kerana semua split ujian sudah dibuka.

**Keputusan (sesi, atas arahan pemilik 14 Nov "buat yg terbaik, pelan → red team → bina").**
1. `konteks.gabung.cara: frasa` (`konteks._simpan_frasa`): frasa positif terdekat → simpan bila p ≥ `ambang_positif` (0.05); frasa
   negatif lebih dekat → simpan hanya calon disahkan struktur dengan p ≥ `ambang_negatif` (0.9); tiada frasa → p ≥
   `ambang_corak["NRIC (dashed)"]` (0.3) atau `ambang[entiti]` (0.5); calon tanpa pengesahan struktur (SSM lama) tanpa frasa positif
   → buang (`tanpa_sah_perlu_frasa`). Ditala atas dev + dev3 SAHAJA (simulasi calon + `hasil/iterasi.tsv`); pengelas tidak dilatih
   semula. Sebenar: dev 0.840 → 0.9506, dev3 0.9981 → 0.9956; ayat biasa 24/24 positif, 10/10 negatif.
2. Sistem `mypii-v2` = worktree tag `mypii-v2-beku` (8e2e6ea, sumber eksport 1.0.2; pengecam sama dengan beku 7ca74ab) melalui
   `v1_worktree.ramal_tag` + `nilai.sistem_beku`; ramalan dev3 = ramalan v2 tersimpan bait demi bait.
3. ujian4 = protokol ujian3 + empat beza (penjana, 10 genre, nama, benih + 5). Penjana `modal/Qwen/Qwen3.8-27B-FP8` (Apache-2.0,
   revisi dipin `scripts/penjana_modal.py`), sandaran `modal/aisingapore/Apertus-SEA-LION-v4-8B-IT` (MIT); vLLM 0.33.0 di Modal,
   imej `nvidia/cuda:13.0.3-devel` (JIT DeepGEMM/FlashInfer perlukan nvcc — imej slim gagal dua kali), pelayan `modal serve`
   sementara + kunci sesi + pengawal yang menamatkan kontena bila vLLM mati. `keluarga_larangan_kecuali` (ujian4: keluarga qwen): Qwen tidak
   pernah menghasilkan data/keputusan (calon `qd/qmodel` gugur probe, HTTPError). Keluarga setiap pasangan sasaran v3 bersilang kosong.
4. Hipotesis H5 (keluarga Holm baharu, k = 4) + susulan berhierarki H5a⁺ — `nilai.statistik.v21`, `statistik_v21.py`; model luar dalam
   metrik U1 (langkah B). `scripts/luar_modal.py` menuntut `--benarkan-ujian` + pra-daftar untuk `nilai.split_belum_dibuka`.

**Ditolak.** Melatih semula pengelas atas dev/latih (mengubah artifak + skop besar; frasa sudah cukup diukur); `ambang` tiada-frasa 0.6
(dev +0.003 sahaja — penalaan lebih); ujian4 bercampur protokol v1 + v3 (dua pemboleh ubah sekali gus; protokol ujian3 = satu
pemboleh ubah: penjana); Claude/Gemini/Kimi/GLM/Nemotron/Mistral sebagai penjana (keluarga lepas; Claude juga pembanding H5b);
API Qwen Cloud atau penghala pihak ketiga (terma API pihak ketiga; dihos sendiri = tiada terma output); menala ke probe `make analisis`
(A3 P3: alat analisis, bukan metrik gelung).

**Akibat.** Probe luar bench (dilapor, tidak ditala): FP kod produk berkurung 40 → 0, jadual tidak teratur 13 → 44 betul, konteks jauh
0 → 8; TETAPI SSM selepas nama perniagaan tanpa akhiran 16 → 2 dan 12 digit tanpa kata 0 → 5 FP. 37 SSM `dev` tiada calon = artifak
penjana v1 (kod LLP 04 sebelum 2012, mustahil — Akta 743), bukan regresi.

**Undur.** Pengecam: `konteks.gabung.cara: ganti` (= 1.0.x tepat). Data: buang `data/templat_ujian4/`, `data/nama_ujian4.yaml`,
`data/bench_v3/{ujian4.jsonl,KUNCI4.json,UJIAN4-MUKTAMAD}` + kunci config `ujian4` (pindaan baharu diperlukan selepas pindaan dikomit).
