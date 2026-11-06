# ADR-010: Latih/dev-v2 — templat LLM + nama tambahan (PELAN-B B2, 30 Okt 2026)

**Masalah.** Dev F1 0.9954 mengukur templat tangan sempit (`data/templat/`, 103 templat) yang ditulis ejen yang sama yang menala
pengecam (`docs/ANALISIS-RALAT.md`). Gelung pengecam seterusnya perlukan latih/dev yang lebih pelbagai, tanpa menyentuh ujian v1
(`38d473fb…`) atau ujian2 (dimeterai, `83ff90b4…`).

**Keputusan.**
- Penjana yang sama (`mypii.jana.templat_llm`), sasaran BAHARU `latih` (`config/mypii.yaml` `templat_llm.sasaran.latih`): model
  `ag/gemini-3.8-flash` (PELAN-B §Peranan model — keluarga berbeza dari penjana ujian2 `cbcn/kimi-k3` dan dari garis dasar LLM B3).
  PELAN-B tidak menyenarai sandaran untuk latih → `sandaran: []` (model gagal = tiada fail ditulis, bukan model lain).
- Fail: `data/templat/llm_<bahasa>.yaml` (awalan `jana.awalan_templat_llm`); `jana._templat` menggabungkannya ke bahasa yang sama dengan
  templat tangan. Folder ujian v1/ujian2 tiada fail berawalan → output sama (disahkan `make jana`).
- 12 genre BERBEZA daripada 10 genre ujian2 (perbankan, keahlian, polisi takaful bukan tuntutan, hotel, kenderaan, bil, pesanan online,
  farmasi, majlis, derma/zakat, acara sukan, B2B), supaya ujian2 kekal ukuran genre yang tidak dilatih. `min_templat` latih = 240.
- Negatif keras B2: slot BAHARU `{NEG_AHLI}` (`nilai_palsu.no_ahli12`: 12 digit rapat; separuh berbentuk MyKad sah, suku berbentuk
  SSM baharu) + `prompt_tambahan` sasaran latih yang menuntut no. ahli/polisi/akaun 12 digit, kod produk berkurung, cap masa, siri.
  Fungsi lama tidak diubah. Huraian slot dalam prompt dikongsi: prompt ujian2 yang SUDAH dijana tidak mengandungi `{NEG_AHLI}` (rekod).
- Pemisahan dari ujian2 (`elak_sasaran: [ujian2]`): penapis membaca templat + nama ujian2 di dalam kod SAHAJA (kiraan dicetak, kandungan
  tidak) — templat sama selepas normalisasi → `sama_sasaran_elak`; nama orang ikut TOKEN + syarikat/bandar ikut entri → ditolak, jadi
  `data/nama_tambahan.yaml` ∩ `nama_ujian2.yaml` = kosong. Nama ujian2 TIDAK dihantar ke penjana (prompt `elak` = nama.yaml sahaja).
  Ujian v1 (`data/templat_ujian/`) tidak dibaca (larangan); padanan tepat dengan templat LLM tidak mungkin dibuktikan, dicatat.
- `jana.gabung_nama` (latih/dev SAHAJA): syarikat + bandar = nama.yaml ∪ tambahan; `{NAMA}` dari fail berkumpulan tambahan dengan
  kebarangkalian `jana.nisbah_nama_tambahan` (0.5), selebihnya cara v1. Kamus tanpa `TAMBAHAN` tidak memakai rng tambahan → ujian v1
  dan ujian2 tidak berubah (ujian regresi).

**Akibat.** Dev-v2 ialah set BERBEZA (CINCANGAN.json baharu): F1 dev-v2 TIDAK boleh dibanding dengan dev lama (0.9954). Garis dasar
dev-v2 (mypii + presidio-asal) direkod dalam LOG-ITERASI.

**Undur.** `git rm data/templat/llm_*.yaml data/nama_tambahan.yaml` → `make jana` = dev lama (kod tanpa fail = tingkah laku lama).
