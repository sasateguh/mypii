# ADR-017: Garis dasar EKSPLORASI di luar keluarga Holm (PELAN-MODEL-LAIN, 3 Nov 2026)

**Masalah.** Pemilik mahu MyPII dibandingkan dengan enam LLM lagi (Opus 5.5, Fable 5.1, GPT-5.6-sol, Qwen, Mistral Small 3.1,
GLM-5.3-Flash). Menambah mereka ke keluarga Holm (k = 6 → 12) menurunkan kuasa hipotesis utama (langkah paling ketat α/12). Pindaan
pra-daftar "2026-11-03 — Garis dasar eksplorasi (model lain) + pelaksana ujian" dikomit SENDIRI (P1) sebelum kod ini: model baharu =
EKSPLORASI — F1 + CI, Δ + CI, p mentah; tiada Holm, tiada hipotesis, tiada peraturan keputusan.

**Keputusan.**
- **Senarai dalam config, bukan kod:** `garis_dasar.llm.eksplorasi` (6 nama model). `statistik.sistem_eksplorasi()` memetakannya ke
  nama sistem `llm:<model>`; tiada kunci = set kosong = tingkah laku lama.
- **`statistik.jalankan`:** Δ, CI dan p mentah (bootstrap + rawak) dikira untuk SEMUA sistem dengan indeks bootstrap + benih yang sama;
  Holm hanya atas sistem BUKAN eksplorasi. Sistem eksplorasi: `p_holm_*` = `null`, `eksplorasi: true` dalam setiap kunci, dan senarai
  atas `eksplorasi` (ditulis hanya bila sistem itu hadir — `hasil/dev-statistik.json` sedia ada kekal sama bait-demi-bait). Sebab p
  setiap pasangan dikira bebas dari sistem lain, menambah sistem eksplorasi tidak mengubah satu bait pun output garis dasar pengesahan
  (ujian `tests/test_eksplorasi.py` + gerbang autopilot §18).
- **`statistik.pengesahan(h)`** = keluarga Holm; `kuasa` mengira k dan baris MDE atas set itu sahaja (k kekal 6, MDE tidak berubah;
  sistem eksplorasi tiada MDE kerana tiada hipotesis).
- **Laporan:** `ketidakpastian` dan `bandingan_md` melabel "(eksplorasi)"; ringkasan mekanikal keluarga Holm dikira atas pengesahan
  sahaja, dan eksplorasi mendapat SATU baris deskriptif (Δ + CI, "di luar keluarga Holm", p mentah tidak dibetulkan) tanpa
  perkataan menang/kalah/signifikan — dakwaan pengesahan tidak boleh dibuat (pindaan).

**Ditolak.** Keluarga Holm kedua untuk eksplorasi (memberi rupa dakwaan pengesahan yang pindaan larang); Bonferroni/BH atas eksplorasi
(tiada hipotesis dipra-daftar untuk dibetulkan); fail statistik berasingan untuk eksplorasi (dua sumber angka untuk satu jadual).

**Jalan undur.** Buang entri dari `garis_dasar.llm.eksplorasi` (dan dari `model` bila sudah ditambah P6) → output kembali seperti
sebelum; cache kekal sebagai rekod. Kod tanpa kunci config berkelakuan seperti sebelum ADR ini.

**Bukti (P2, 3 Nov 2026).** `make statistik` + `make bandingan` atas cache sedia ada: `git diff --exit-code hasil/dev-statistik.json
docs/BANDINGAN.md` kosong; `make kuasa` k = 6. Sabotaj 5/5 merah (LOG-ITERASI MODEL-LAIN P2).

**Tambahan P3 (3 Nov 2026) — probe + kos.** `mypii/nilai/probe_llm.py` memanggil setiap calon melalui `garis.ramal_llm` (kunci cache
sama; `ramal_llm` kini menerima model `eksplorasi` selain `model`) atas N dokumen pertama ikut susunan fail (`garis_dasar.llm.probe`);
output = kiraan + jenis ralat, tiada F1. `klien_anthropic`: `max_tokens` per model (lalai global → permintaan + kunci cache Sonnet/Haiku
tidak berubah, diuji atas cache dikomit), `refusal` → teks kosong (rosak). `kos_claude --rancang` = peraturan kos pindaan; susunan gugur
`kos.gugur` dan `kos.margin` dalam config. Ditolak: modul kos berasingan (pendua `count_tokens` + ulang); probe dengan prompt pendek
(kunci cache berbeza = larian kedua, dilarang pindaan).

**Keputusan kos P5 (3 Nov 2026) — kedua-dua calon Claude GUGUR.** `make kos-claude ARG=--rancang` (count_tokens dev 1000 dok = 415 725
token masuk setiap model; purata keluar probe Opus 109, Fable 116; margin 1.5; harga config = skil `claude-api`: Opus 5.5 $4/$20,
Fable 5.1 $10/$50 setiap MTok): satu split Opus USD 4.9329, Fable USD 12.85725. Perlu = pengesahan ujian+ujian2 USD 4.132244 (Sonnet
3.96942 + Haiku 0.162824) + calon (3 × satu split − probe). Dengan kedua-dua: USD 57.433268 > baki 17.864452 → Fable gugur; Opus sahaja:
USD 18.911608 > baki → Opus gugur (terlebih USD 1.047156). `dipilih` = [], `perlu_ujian_usd` = 4.132244. Had USD 20 TIDAK dinaikkan
(peraturan pindaan). P6 = calon 9router lulus probe sahaja (Mistral Small 3.1, GLM-5.3-Flash). Jawapan probe Opus/Fable (5 dok) kekal
dalam cache sebagai rekod; tidak dilapor sebagai garis dasar. Blok `rancang_eksplorasi` dalam `hasil/dev-kos-claude.json`.

**Larian dev P6 (3 Nov 2026).** Mistral Small 3.1 + GLM-5.3-Flash masuk HUJUNG `garis_dasar.llm.model` bersama cache dev lengkap
(kekal dalam `eksplorasi` → di luar Holm). Akibat pasangan: (1) `semua` (dan §7 ujian muktamad) kini merangkumi kedua-dua model melalui
9router; (2) asas token keluar `kos_claude` (`panjang_jawapan_sedia`) mengecualikan model eksplorasi supaya anggaran kos pengesahan
kekal seperti P3/P5; (3) ujian config: eksplorasi dalam `model` mesti di hujung dan bercache dev lengkap. Angka = LOG MODEL-LAIN P6.

**Skrip ujian muktamad P8 (3 Nov 2026) — `scripts/ujian-muktamad.sh`, diuji dengan split palsu, TIDAK dijalankan.** Empat perintah
§7 tertanam bait sama DAN dibanding semasa larian dengan blok kod §7 `docs/PRA-DAFTAR.md` di HEAD (beza = enggan). Semua semakan enggan
(tree kotor, `hasil/ujian*` / `hasil/ramalan/ujian*` wujud, `MULA` dalam arkib, env tiada, baki lejar < `perlu_ujian_usd`, sha256 split ≠
`KUNCI*.json`, `uv run pytest -q` gagal = "make uji lulus" §7) berlaku SEBELUM harness; `--kering` = semua kecuali sha256 dan pytest, tanpa
`uv`. Keputusan teknikal: (1) **crash** = penanda `CRASH` (kod keluar / trap EXIT) atau `PID` larian yang sudah mati (SIGKILL tidak
menjalankan trap); `--ulang-crash "<sebab>"` SEKALI — hasil separa + log dipindah ke `separa/`, **cache LLM larian crash DIKEKALKAN**
(perintah sama menyambung cache, seperti ulangan `panggilan gagal` §7; panggilan berbayar tidak diulang dan lejar terus mengira belanja
sebenar); crash lagi = `GAGAL` (cache diarkib + dipulih, tiada ulangan lagi). (2) **Lejar selepas larian:** `git restore hasil/cache/llm`
memulihkan juga `anthropic-lejar.json` (belanja ujian tidak dikomit — ia mengandungi kiraan atas teks ujian); lejar sebenar disimpan dalam
arkib dan `RINGKASAN.json.lejar_usd_selepas`. (3) RINGKASAN H1a–f/H2a–f = susunan presidio-asal, pii-guard, kemudian `garis_dasar.llm.model`
bukan-eksplorasi (Llama, DeepSeek, Sonnet 5.5, Haiku 5.5 — sama dengan §5 + pindaan Claude); `disokong` = kedua-dua p Holm < `alfa` config.
(4) `tests/conftest.py` membuang `GIT_*` di satu tempat masuk suite (perangkap rumah). Jalan undur: buang skrip (tiada kesan lain).
