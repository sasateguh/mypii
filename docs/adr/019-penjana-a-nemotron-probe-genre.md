# ADR-019: Keluarga penjana A = NVIDIA Nemotron; probe v3 merentas 4 genre (5 Nov 2026)

**Masalah.** Probe rasmi latih3 (4 Nov) gagal kedua-dua calon pindaan 2026-11-04: StepFun 0/4 (`nombor_literal`, kualiti); Tencent
Hunyuan tidak menjawab (laluan penyedia tidak boleh dipanggil [disunting: butiran akaun penyedia API]). Pindaan itu
menyuruh berhenti sehingga pindaan baharu. Probe percubaan Nemotron (di luar repo) pula menunjukkan satu genre pada suhu 0.8 boleh
memberi 4/4 atau 1/4 untuk model yang sama — keputusan probe satu genre ialah lambungan.

**Keputusan.** Pindaan PRA-DAFTAR "2026-11-05 — MyPII v2: calon penjana keluarga A diganti + probe merentas genre":
- latih3 = `rv/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4`, `sandaran: []`; keluarga `nvidia` dalam `templat_llm.keluarga`.
- `templat_llm.probe.genre: 4`; `probe_v3` menjumlah templat sah merentas genre, lulus ≥ `min_nisbah_sah` × templat × genre (0.5 × 16).
  Rekod probe menambah `per_genre` (bilangan sah) — masih statistik sahaja.
- Ujian: `test_probe_ambang_jumlah_merentas_genre_bukan_satu_lambungan` (satu genre 0 tetapi jumlah cukup = lulus; jumlah kurang = gagal).

**Ditolak.** Menunggu laluan Hunyuan pulih (tarikh tidak diketahui); Grok untuk A (had kuota dan "Service temporarily unavailable", 5 Nov
[disunting: butiran akaun penyedia API]; dan Grok ialah sandaran B); menaikkan/menurunkan
`min_nisbah_sah` (mengubah kriteria selepas melihat percubaan); mengubah prompt supaya templat lebih panjang (perubahan reka bentuk data
selepas melihat output); mengulang probe satu genre sehingga lulus (memilih ikut nasib).

**Undur.** Kembalikan `latih3` + `probe.genre` dalam config dan `probe_v3` ke komit sebelum ADR ini; pindaan baharu diperlukan kerana
pindaan 2026-11-05 dikomit.
