# ADR-014: Harness menolak split dikunci tanpa pra-daftar bersih dalam `git HEAD` (PELAN-C C4b, 30 Okt 2026)

**Masalah.** `--benarkan-ujian` sahaja tidak membuktikan bahawa hipotesis, metrik dan peraturan keputusan (`docs/PRA-DAFTAR.md`,
ADR-007) ditetapkan SEBELUM ujian/ujian2 dibuka. Pra-daftar yang belum dikomit, atau disunting dalam salinan kerja ketika larian,
boleh ditukar selepas melihat angka tanpa jejak dalam sejarah git.

**Keputusan.**
- Modul `mypii/nilai/pradaftar.py`: `semak(akar)` menolak (`Ditolak`) bila (a) folder bukan repo git dengan komit, (b) fail
  pra-daftar tiada dalam `HEAD` (`git rev-parse HEAD:<fail>` — fail yang hanya di cakera atau di-stage tidak dikira), atau (c)
  `git status --porcelain -- <fail>` tidak kosong (disunting, di-stage, dipadam). Laluan fail = kunci config BAHARU
  `nilai.statistik.pradaftar.fail` (`docs/PRA-DAFTAR.md`).
- `harness.main()` memanggilnya untuk setiap split dalam `nilai.split_dikunci`, SELEPAS semakan `--benarkan-ujian` sedia ada dan
  SEBELUM `_dokumen()` membaca fail split — termasuk laluan `--statistik`. Ditolak → mesej BM ke stderr, exit 2, tiada output ditulis.
- Diterima → `fail @ komit <sha komit terakhir yang menyentuh fail> (blob <sha blob>)` dicetak ke stderr dan ditulis sebagai kunci
  `_pradaftar` dalam setiap `<split>-<sistem>.json` dan `<split>-statistik.json`. Split dev tidak disentuh (tiada `_pradaftar`).
- Fail lain yang kotor TIDAK menolak larian (komit `+` sudah direkod oleh `iterasi`); hanya pra-daftar yang mesti bersih.

**Ujian.** `tests/test_pradaftar.py` — repo git tmp; `_dokumen`/`ramal` harness dipalsukan supaya mana-mana bacaan split = gagal.
Tiada larian `--benarkan-ujian` atas data sebenar (larangan PELAN-C). Sabotaj 4/4 merah: semakan kotor dibuang · semakan HEAD dibuang ·
split dibaca sebelum semakan · `_pradaftar` tidak ditulis.

**Ditolak.** Menyemak cincangan kandungan yang disalin ke config (pendua yang mesti dikemas setiap pindaan §15); menolak bila
SEBARANG fail kotor (menghalang larian manusia yang sah tanpa menambah jaminan pada pra-daftar).

**Undur.** Buang blok `pradaftar.semak` dalam `main()` + `_pd()`; `docs/PRA-DAFTAR.md` KEKAL.
