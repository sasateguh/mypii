# ADR-020: Keluarga penjana B (ujian3) = Mistral → Claude Sonnet; Haiku dilarang sebagai penjana (5 Nov 2026)

**Masalah.** Calon B pindaan 2026-11-04 (`cbai/minimax-m3` → `gcli/grok-4.7`) tidak boleh dipanggil (bukti dalam pindaan PRA-DAFTAR
2026-11-05 (c)). Setiap keluarga lain yang hidup berada dalam `keluarga_larangan`. Pemilik memutuskan
untuk tidak menunggu sehingga 1 Dis.

**Keputusan (pemilik, 5 Nov 2026).**
- `llm.penjana.ujian3` = `cf/@cf/mistralai/mistral-small-3.1-24b-instruct`, sandaran `anthropic/claude-sonnet-5-5`.
- `templat_llm.keluarga_larangan_kecuali: {ujian3: [mistral, anthropic]}` — `semak_keluarga` melangkau larangan bagi keluarga itu
  untuk ujian3 SAHAJA. `templat_llm.penjana_larangan_tepat: [anthropic/claude-haiku-5-5]` — ditolak untuk semua sasaran.
- `hantar_penjana` (templat_llm): model `anthropic/` → `klien_anthropic` (lejar + had keras, kos terburuk ditempah dahulu,
  `max_tokens` = `templat_llm.anthropic_max_tokens`); selain itu → 9router seperti dahulu.

**Ditolak.** Menunggu 1 Dis (pemilik); Haiku sebagai penjana (pembanding H4a); Opus/Fable (kos > baki selepas Haiku dev3 + ujian3);
GLM/Qwen/Kimi/DeepSeek/Llama (penjana atau garis dasar lepas, tiada keputusan pemilik); Nemotron (keluarga A, mesti A ≠ B).

**Akibat.** Dua had baharu (pindaan, (8) dan (9)): bias Anthropic → H4a lebih sukar untuk MyPII, bukan lebih mudah.

**Undur.** Kembalikan `llm.penjana.ujian3` + buang dua kunci baharu; pindaan baharu diperlukan kerana pindaan (c) dikomit.
