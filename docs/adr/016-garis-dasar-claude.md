# ADR-016: Garis dasar Claude melalui API Anthropic terus — klien, lejar had keras, penghala (PELAN-CLAUDE, 3 Nov 2026)

**Masalah.** Pemilik mahu MyPII dibandingkan dengan Claude (Sonnet 5.5 + Haiku 5.5) sebagai garis dasar LLM sifar-tembak, di sebelah
Llama dan DeepSeek (ADR-011). Claude mesti dipanggil melalui API Anthropic TERUS (bukan 9router), atas split dev sahaja, dengan had
belanja keras USD 20. Pindaan pra-daftar "2026-11-03 — Garis dasar Claude (API Anthropic) ditambah (sebelum ujian dibuka)" sudah dikomit
SENDIRI (P1) sebelum kod ini.

**Keputusan.**
- **Penghala ikut awalan.** `garis.ramal_llm` menghala model `anthropic/<id>` ke `mypii/klien_anthropic.py`; model lain kekal melalui
  `klien_llm` (9router) tanpa perubahan. Hanya `garis.py` (dan `kos_claude.py`, P3) mengimport klien itu — gerbang §17 menyemaknya —
  jadi teks yang dihantar ke API ialah `data/bench/*` (sintetik) sahaja.
- **SDK rasmi `anthropic`** (Apache-2.0) dalam extra `garis` (`uv lock`: `anthropic` 2.4.0 + kebergantungannya, tiada pakej sedia ada
  berubah versi), diimport MALAS dalam `hantar` — `pytest` tanpa extra tidak memerlukannya. Ulang 408/409/429/5xx = `max_retries` SDK
  (`ulang_sdk`); ralat sementara selepas itu = `OSError` → dokumen `gagal` (jalankan perintah sama semula; cache disambung).
  4xx lain (cth parameter ditolak) = `TolakAPI` → larian BERHENTI (benang lain tidak memanggil lagi) dengan mesej API; nilai lain tidak
  diteka tanpa ADR + pindaan.
- **Nilai dalam config** `garis_dasar.llm.anthropic`: `env_kunci`, `had_usd` (20), `lejar`, `max_tokens` (1024 — jawapan cache LLM sedia
  ada ≤ 460 aksara), `aksara_setiap_token` (3, untuk kos terburuk), `had_masa_saat`, `ulang_sdk`, dan setiap model: `harga` USD/MTok
  (Sonnet 5.5 2/10, Haiku 5.5 0.10/0.50 untuk prompt ≤ 100K token — dok Anthropic 3 Nov 2026) + `parameter` yang dihantar seperti adanya.
  Dua entri `anthropic/` di HUJUNG `garis_dasar.llm.model` (susunan sedia ada tidak berubah; `model[0]` ujian kekal Llama). `semua`
  melangkau entri `anthropic/` yang belum ada fail cache (amaran stderr) — lihat Pindaan 3 Nov.
- **Permintaan:** satu mesej `user` = `garis_dasar.llm.prompt` yang SAMA; medan lain = `max_tokens` + `parameter`. `temperature` TIDAK
  dihantar (API menolak nilai bukan lalai untuk Sonnet 5.5 / Haiku 5.5; SDK 2.x pun tiada parameternya) → larian tidak deterministik,
  cache dikomit = boleh dihasilkan semula. Pemikiran dimatikan supaya setara LLM lain: Sonnet 5.5 `thinking: {type: between_tools}`
  (ia menolak `disabled`; `between_tools` diterima pada effort lalai `high`), Haiku 5.5 `thinking: {type: disabled}` (diterima pada effort
  lalai `medium`). Jawapan = gabungan blok `text` sahaja (blok lain diabaikan); `refusal`/`max_tokens` = teks kosong/terpotong → `rosak`.
  Tiada `fallbacks` sisi pelayan: ia boleh menghala ke model lain, dan hanya dua model config dibenarkan.
- **Kunci cache `anthropic/`** = sha256(JSON `[model, prompt, JSON permintaan tersusun, teks]`); model lain kekal sha256(`[model, prompt,
  teks]`) — cache Llama/DeepSeek kekal sah (ujian `test_cache_dikomit_model_lama_masih_lengkap_atas_dev`). `garis.kunci_dok` = satu
  sumber kunci untuk harness dan `bandingan.kos_llm`.
- **Lejar had keras** `hasil/cache/llm/anthropic-lejar.json` (dikomit; `{"jumlah_usd", "model": {m: {masuk, keluar, usd, panggilan}}}`,
  tiada teks/kunci). Sebelum setiap panggilan, di bawah kunci benang: `jumlah_usd + tempahan dalam penerbangan + kos_terburuk > had_usd`
  → TIDAK memanggil, dokumen itu `gagal`, dan tiada panggilan lagi dalam larian itu (`had_dicapai`). `kos_terburuk` = ⌈aksara prompt / 3⌉
  × harga masuk + `max_tokens` × harga keluar. Selepas jawapan: tempahan dilepas, kos SEBENAR dari `usage` ditambah, fail ditulis atomik
  (`.tmp` + `os.replace`). Panggilan gagal melepaskan tempahan tanpa rekod (permintaan yang gagal tidak dibilkan; kalau tamat masa selepas
  API memproses, belanja sebenar boleh melebihi lejar sedikit — sebab itu lejar disemak semula dengan papan pemuka bila larian P4 siap).
  Statistik harness bagi `anthropic/` += `usd` (larian ini), `jumlah_usd`, `had_dicapai`.
- **Sabotaj (P2, direkod LOG):** had tidak disemak · suhu dihantar · kunci model lama berubah · token keluar tidak direkod · tempahan
  gagal tidak dilepas → setiap satu MERAH.

**Akibat.** Sehingga P4 mencipta cache Claude, `semua` = 5 sistem (dua `anthropic/` dilangkau dengan amaran); `make statistik`/
`make bandingan` hijau atas cache dikomit tanpa rangkaian. Selepas P4, `semua` = 7 sistem; cache SEPARA tetap dimuatkan dan bandingan
berhenti "tiada dalam cache" (tiada angka separa senyap).

**Pindaan 3 Nov 2026 (penolakan penyemak P2).** Versi pertama P2 meletakkan dua entri dalam `garis_dasar.llm.model` serta-merta:
`make bandingan` merah (rc 2, "1000 dokumen tiada dalam cache") dan `ramal_llm` mencipta fail cache KOSONG tak dijejak (tree kotor →
pekerja autopilot seterusnya menolak). Lebih teruk, `make statistik` (`harness --sistem semua`, hantar lalai) dengan kunci dalam env
akan MEMANGGIL API di luar larian P4. Keputusan: (a) `harness.senarai_sistem(["semua"])` melangkau `anthropic/<id>` yang TIADA fail cache
(belum pernah dijalankan) dengan amaran — satu tempat, dipakai statistik + bandingan; `--sistem llm:anthropic/<id>` terang (P4) tidak
terjejas; (b) `ramal_llm` membuka fail cache secara MALAS — tiada jawapan ditulis = tiada fail dicipta/ditulis semula. Ditolak:
menangguhkan dua entri config ke P4 — gerbang projek menetapkan senarai model tambah-sahaja berbanding BASE potongan (diukur: gerbang
GAGAL "model garis dasar sedia ada diubah"). Ujian: `test_bandingan_llm_semua_luar_talian_atas_cache_dikomit_tanpa_fail_baharu`,
`test_semua_melangkau_claude_tanpa_cache_dengan_amaran`, `test_semua_memuatkan_claude_di_hujung_bila_cache_wujud`, dan dua ujian
gagal-rangkaian kini menegaskan fail TIDAK wujud (merah atas kod lama — LOG).

**Jalan undur.** Buang dua entri `anthropic/` dari `garis_dasar.llm.model` → `semua` kembali 5 sistem; blok `anthropic:`, cache dan
lejar kekal sebagai rekod. Buang `anthropic` dari extra `garis` + `uv lock` untuk membuang kebergantungan.

**Pindaan 3 Nov (P3) — anggaran kos `make kos-claude`.** `mypii/nilai/kos_claude.py` memanggil `messages.count_tokens` (percuma, tiada
penjanaan) untuk setiap dokumen dev × setiap model `anthropic/` dengan prompt + `parameter` yang sama seperti larian (`max_tokens` tidak
dihantar — titik akhir itu tidak menerimanya). Token keluar tidak boleh diukur tanpa penjanaan → dianggar dari panjang jawapan cache
9router sedia ada bagi dokumen YANG SAMA (median aksara = jangka, maksimum = atas, ÷ `aksara_setiap_token`), dan `max_tokens` penuh =
terburuk; keputusan "muat" diukur dengan TERBURUK berbanding baki lejar (exit 3 = melepasi). Split = config `anthropic.kos.split` (dev)
DAN bukan `nilai.split_dikunci` — disemak sebelum fail dibaca. Ulang ralat sementara (429/5xx) = config `kos.ulang`/`jeda_saat` di atas
`ulang_sdk`. Modul ini dan `garis.py` sahaja yang boleh mengimport klien Anthropic (gerbang 17). Ditolak: menganggar token masuk dari
aksara (aksara/3 hanya untuk tempahan lejar; count_tokens tepat dan percuma).
