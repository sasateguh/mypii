# ADR-007: Pra-daftar analisis ujian + analisis kuasa dari bootstrap dev (PELAN-C C4a, 30 Okt 2026)

**Masalah.** Penilai kertas akan bertanya "adakah angka dipilih selepas melihat ujian?". Tanpa pelan analisis yang dikomit SEBELUM
`ujian`/`ujian2` dibuka, setiap pilihan (metrik, garis dasar, pembetulan, ambang) boleh dituduh dipilih selepas data. Analisis kuasa
juga diperlukan supaya keputusan tidak signifikan tidak dibaca sebagai "tiada beza".

**Keputusan.**
- `docs/PRA-DAFTAR.md` (BM + English summary penuh), TAMBAH-SAHAJA; pindaan = bahagian bertarikh di §15. Cap masa = komit git
  (tiada OSF — had diakui); C4b menjadikan harness enggan `--benarkan-ujian` tanpa fail ini bersih dalam HEAD dan mencetak sha komitnya.
- **Utama = `ujian2`** (H1a–d, MyPII > setiap 4 garis dasar pada F1 tepat mikro `semua|*`), kerana `ujian` v1 berkongsi keluarga
  templat dengan dev lama yang ditala ke siling — ia pengesahan sekunder (H2, keluarga Holm berasingan). Per entiti = sekunder;
  per bahasa / separa / P/R = deskriptif.
- **Peraturan keputusan konservatif:** disokong hanya bila p Holm bootstrap DAN p Holm rawak kedua-duanya < α = 0.05 (sehala).
  Dua ujian sudah dilapor sejak C3a; memilih salah satu selepas data = laluan pemilihan, jadi kedua-duanya diwajibkan.
- **Analisis kuasa** `make kuasa` (`mypii/nilai/kuasa.py`, stdlib `statistics.NormalDist`): SE Δ dari lebar CI bootstrap Δ dev
  (`hasil/dev-statistik.json`) / (2·z), diskala √(n_dev/n_sasaran); MDE = (z_{1−α'} + z_kuasa)·SE untuk α' = α/k dan α. Config
  BAHARU `nilai.statistik.pradaftar` (`alfa`, `kuasa`, `dokumen_sasaran`). Skil `statistical-power` ditolak di C1 (imbasan HIGH), dan
  bootstrap harness sudah mengukur hingar dengan metrik sebenar — tiada formula kuasa F1 analitik yang lebih jujur.
- Kegagalan panggilan LLM atas split ujian: satu ulangan perintah sama (cache menyambung, jawapan sedia ada tidak berubah); selebihnya =
  ramalan kosong + dilapor. Cache LLM split ujian TIDAK dikomit.
- Semakan `scientific-writing` (`check_consistency.py`, `audit_claims.py`) memerlukan daftar JSON/CSV dakwaan + manifes sumber yang tidak
  wujud untuk dokumen pelan → tidak dijalankan; ganti: setiap baris jadual kuasa dalam PRA-DAFTAR dipadan tepat dengan output `make kuasa` (LOG).

**Akibat.** Anggapan SE ujian2 ≈ SE dev (saiz sama, taburan berlainan) mungkin optimis; dinyatakan dalam §9. pii-guard `MY_PHONE`
kurang berkuasa (Δ dev 0.0228 < MDE ketat 0.025).

**Undur.** Buang `mypii/nilai/kuasa.py`, `tests/test_kuasa.py`, sasaran `make kuasa`, kunci `nilai.statistik.pradaftar`. PRA-DAFTAR
sendiri tidak dipadam (tambah-sahaja); pelan baharu = pindaan bertarikh §15 yang menyatakan sebab, SEBELUM ujian dibuka.
