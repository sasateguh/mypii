# ADR-011: Garis dasar pesaing dalam harness — pii-guard + 2 LLM sifar-tembak (PELAN-B B3, 30 Okt 2026)

**Masalah.** Kertas membanding MyPII dengan Presidio asal sahaja. Pesaing sebenar: pustaka Malaysia sedia ada `malaysia-pii-guard`
(`docs/literatur/RINGKASAN.md`) dan LLM sifar-tembak. Angka mesti boleh dihasilkan semula tanpa rangkaian (Depot CI, penyemak, C3b).

**Keputusan.** Modul `mypii/nilai/garis.py`; harness memanggilnya bila `--sistem pii-guard` / `llm:<model>` (`semua` = mypii,
presidio-asal, pii-guard + setiap model config). Fungsi metrik `skor/_sama/_bertindih` TIDAK diubah. Semua nilai dalam
`config/mypii.yaml` `garis_dasar:` (kunci baharu). Larian atas dev-v2 SAHAJA.

- **pii-guard:** extra `garis` dari git dipin `75d6920…` (tiada di PyPI). `AnalyzerEngine(score_threshold=nilai.ambang_skor)` — ambang
  yang sama dengan MyPII/Presidio. Pertindihan diselesaikan dengan `malaysia_pii_guard.anonymizer.resolve()` pustaka itu SENDIRI (cara
  ia memutuskan semasa menyamarkan; 10 digit = telefon DAN akaun bank → skor lebih tinggi menang), ke atas SEMUA jenisnya, kemudian
  dipeta `MY_NRIC→MY_NRIC`, `PHONE_NUMBER→MY_PHONE`; jenis lain diabaikan. Tiada SSM → laporan tambahan `pii-guard (disokong)` =
  `skor()` atas emas yang ditapis ke `entiti_disokong` (fail `dev-pii-guard-disokong.json`) — adil kepada pustaka, bukan pengganti `*`.
- **LLM:** model = PELAN-B §Peranan model (`cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` berat terbuka + `cbcn/deepseek-v4.1-flash`;
  bukan keluarga penjana templat), model lain ditolak. Suhu 0, satu dokumen satu panggilan, prompt tetap dalam config (semua arahan
  dalam mesej `user`), ditulis SEKALI sebelum melihat skor dev dan TIDAK ditala (menala prompt atas dev = garis dasar tidak adil
  dalam arah sebaliknya; dicatat dalam kertas). Jawapan JSON `[{teks, entiti}]` → span = SEMUA kejadian `teks` tepat dalam dokumen
  (`re.finditer`), entiti di luar `nilai.entiti` diabaikan. Jawapan bukan senarai JSON = **rosak**: tiada ramalan, dikira.
  Panggilan gagal selepas `llm.ulang` = TIDAK dicache, dikira `gagal` (larian semula menyambungnya); angka akhir hanya bila gagal = 0.
- **Cache:** `hasil/cache/llm/<model>.jsonl`, satu baris `{kunci, jawapan}` (jawapan MENTAH sebelum diurai — pengurai boleh dibaiki
  tanpa memanggil semula), kunci = sha256 JSON `[model, prompt, teks]`. Ditambah serta-merta setiap jawapan (larian terputus
  disambung; baris terpotong diabaikan), ditulis semula tersusun ikut kunci di hujung → bait sama. DIKOMIT (`.gitignore`: `hasil/*` +
  `!hasil/cache/**`). Tiada kunci API dalam cache (env `MYPII_9ROUTER_KEY` dibaca oleh klien sahaja).
- `make nilai-garis` = semua sistem; `make nilai` (gelung) kekal mypii + presidio-asal.

**Akibat.** LLM sebagai pengecam span: kegagalan menyalin teks tepat (ruang, sengkang) = FN + FP dalam metrik tepat — itu sebahagian
daripada tugas, metrik separa melaporkannya juga. Satu prompt, satu suhu: angka LLM ialah satu titik, bukan had atas prestasi LLM.
Mengubah prompt/model = kunci cache baharu = panggilan baharu (rekod LOG).

**Undur.** Buang extra `garis`, `garis_dasar:` config, `mypii/nilai/garis.py`, cabang dalam `harness.ramal/main` dan `hasil/cache/`;
kunci 9router `mypii` dipadam (PELAN-B §Undur).
