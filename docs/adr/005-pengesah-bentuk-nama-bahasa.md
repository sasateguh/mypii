# ADR-005: Pengesah bentuk nama + bahasa untuk templat/nama LLM; ujian2 perlu dijana semula (30 Okt 2026, PELAN-B B1 dibuka semula)

**Masalah (penyemak autopilot, 30 Okt).** Penjana B1 (ADR-004) mengesahkan slot, nombor, panjang, jenama dan persilangan nama — tetapi
tidak BENTUK nama atau BAHASA templat. `jana.py` membina `NAMA = nama_pertama + " " + nama_akhir`, jadi senarai yang berisi nama penuh
menjadi dua nama penuh bercantum, dan syarikat dalam `nama_akhir` menjadi orang ("… Sdn Bhd" palsu bersebelahan negatif SSM). Templat
`en` yang ditulis dalam BM menjadikan pecahan ikut bahasa tidak sah.

**Keputusan.** `mypii/jana/templat_llm.py` menolak (ambang + senarai dalam `config/mypii.yaml` `templat_llm:`):
- `nama_pertama`: > `maks_token_pertama` token, ada penyambung (bin/binti/a/l…), atau token terakhir = nama keluarga calon
  (entri `nama_akhir` satu token / selepas a/l, a/p, anak — bukan bin/binti kerana nama bapa Melayu juga nama pertama biasa) → `nama_penuh` / `ada_nama_keluarga`.
- `nama_akhir`: mesti `penyambung + 1–2 token` ATAU tepat satu token → selain itu `nama_penuh`.
- kedua-duanya: akhiran syarikat (`akhiran_syarikat`, perkataan penuh) → `syarikat_sebagai_orang`.
- templat `en`/`ms`: bahagian kata fungsi bahasa sendiri < `bahasa_semak.min_nisbah` (0.6) daripada kata fungsi EN+BM yang dikenali →
  `bahasa`; < `min_kata_fungsi` kata fungsi = tidak dinilai; `manglish` tidak disemak (campuran memang dijangka).
- Prompt dikemas: huraian nama menuntut BAHAGIAN nama sahaja; "Write every document entirely in the language above".
- `--semak` = jalankan pengesah semasa atas fail sedia ada, cetak KIRAAN ikut sebab sahaja (selamat untuk ujian2 — tiada kandungan).

Kawalan positif: `data/nama.yaml` (tangan) 0 tolak; templat latih `data/templat/` 0 tolak bahasa (10 dinilai, 93 terlalu pendek).

**Ukuran atas ujian2 yang dikomit (`--semak`, kiraan sahaja).** Templat: en 34/79 tolak `bahasa`; ms 80/80 dan manglish 79/79 sah.
Nama: `nama_akhir` 49 `nama_penuh` + 8 `syarikat_sebagai_orang` (0 sah); `nama_pertama` 17 `nama_penuh` + 1 `ada_nama_keluarga`, 42 sah.
Ini mengesahkan dapatan penyemak — **ujian2 semasa cacat dan tidak boleh dipakai dalam kertas.**

**Belum dibuat — perlu pemilik.** Menjana semula `data/templat_ujian2/`, `data/nama_ujian2.yaml`, `data/bench/ujian2.jsonl` dan mencipta
semula `KUNCI2.json` = membuka meterai ADR-004 (gerbang autopilot menolak sebarang perubahan fail itu, dengan sengaja). Belum ada sesiapa
menilai ujian2 (harness menguncinya), jadi membuka meterai SEKALI tidak membocorkan apa-apa. Cadangan: pemilik membenarkan satu potongan
"B1b" — padam empat fail meterai, `templat_llm --sasaran ujian2` dengan pengesah ini, `make jana` (KUNCI2 baharu dicipta kerana tiada),
satu komit; gerbang dikemas untuk membenarkan komit itu sahaja (BASE = komit ini), kemudian meterai berkuat kuasa semula.

**Undur.** Buang `bentuk_orang`/`nisbah_bahasa`/`semak_fail` + kunci config `bahasa_semak`, `nama.maks_token_*`, `penyambung_*`,
`akhiran_syarikat` → pengesah ADR-004.

**Dilaksanakan (B1b, 30 Okt 2026).** Dibenarkan oleh penilai auto AP-T613 (`arahan.md` §B1b). Empat fail meterai dipadam dan dijana
semula dengan pengesah ini: `--semak ujian2` 0 tolak (templat 238/238, nama 120/120); KUNCI2 baharu `337820ee…` (dulu `0307a169…`).
Meterai ADR-004 berkuat kuasa semula atas fail baharu. Angka penuh: LOG-ITERASI baris B1b.
