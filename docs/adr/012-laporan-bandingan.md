# ADR-012: Laporan bandingan dev dijana dari kod — `docs/BANDINGAN.md` (PELAN-B B4, 30 Okt 2026)

**Masalah.** PELAN-B B4 menuntut jadual semua sistem × entiti × bahasa (P/R/F1 tepat + separa), ralat utama setiap sistem, masa/kos
dan had — dengan syarat setiap angka ialah output larian. Jadual yang disalin dengan tangan dari `hasil/dev-*.json` mudah tersalah
salin dan tidak boleh disemak semula oleh penyemak; harness pula tidak menyimpan ramalan per dokumen, jadi ralat tidak boleh dikumpul
dari fail hasil.

**Keputusan.**
- Modul `mypii/nilai/bandingan.py` (kira) + `bandingan_md.py` (markdown sahaja). `make bandingan` meramal semula semua sistem
  `harness.senarai_sistem(["semua"])` atas dev, menilai dengan `harness.skor()` SEDIA ADA (fungsi metrik tidak disentuh), dan menulis
  semula HANYA blok antara penanda `bandingan.penanda` dalam `docs/BANDINGAN.md`; prosa di luar blok ditulis manusia/ejen dan TIDAK
  boleh membawa angka yang tiada dalam blok. Split dikunci ditolak (exit 2).
- LLM dibaca dari cache dikomit dengan klien yang MELEMPAR ralat — dokumen tanpa cache = berhenti, bukan panggilan senyap. Jadi blok
  jana sama bait demi bait tanpa rangkaian.
- **Jenis ralat** (padanan tepat): palsu / sempadan / salah jenis (sisi ramalan) dan terlepas (emas tanpa ramalan bertindih langsung —
  emas yang hanya tersalah sempadan/jenis tidak dikira dua kali). Kiraan "dok negatif berisi ramalan / span" = definisi LOG B3.
- **Ralat utama** dikumpul ikut label sebelum span dalam baris yang sama (≤ `token_label` token), bukan ikut genre: label ialah apa yang
  pengecam/LLM nampak dan terus menunjukkan jenis nombor yang mengelirukan (no. ahli, kod diskaun, akaun). Susunan: bil menurun, label
  abjad; contoh = dokumen pertama ikut `id` — tentu.
- **Masa** berubah setiap larian → hanya `make bandingan-masa` mengukurnya ke `hasil/dev-masa.json` (dikomit: pengecualian
  `.gitignore`); `make bandingan` membacanya sahaja. Sistem tempatan: masa dinding `harness.ramal` atas 1,000 dok termasuk memuat
  enjin. LLM: `sampel_latensi` dok pertama ikut `id`, bersiri, panggilan terus (cache TIDAK ditulis, jadi angka skor tidak berubah).
- **Kos LLM:** wang tidak diukur (langganan 9router; tiada caj setiap panggilan). Saiz = aksara masuk/keluar dari cache — token tidak
  dianggar kerana tokenizer berbeza setiap model.
- Semua tetapan dalam `config/mypii.yaml` `bandingan:` (kunci baharu).

**Akibat.** Penyemak boleh `make bandingan` dan membanding `git diff docs/BANDINGAN.md` = kosong. Skor dalam blok = `hasil/dev-*.json`
harness (disemak sama semasa B4). Larian ~1 minit (Presidio × 2 + pii-guard); tiada dalam gerbang CI (perlu extra `nilai` + `garis`).

**Undur.** Buang dua modul, `tests/test_bandingan.py`, kunci `bandingan:`, sasaran Makefile, baris `.gitignore`, `hasil/dev-masa.json`
dan `docs/BANDINGAN.md`.
