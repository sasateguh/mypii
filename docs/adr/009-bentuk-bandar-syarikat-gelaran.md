# ADR-009: Bentuk `bandar`/`syarikat` + gelaran sepadan jantina; ujian2 `54cf318f…` cacat (30 Okt 2026)

**Masalah (penyemak autopilot menolak B1b jana semula ke-2, 30 Okt).** Dalam `data/nama_ujian2.yaml` (KUNCI2 `54cf318f…`), 60/60 entri
`bandar` ialah triplet `Nama | Syarikat | Bandar, Negeri`; 543/1000 dokumen ujian2 mengandungi ` | `. `tapis_nama` hanya menyemak
pendua/jenama/digit untuk `bandar` + `syarikat`, dan `--semak` tidak menyemak bentuknya langsung — jadi "0 tolak" tidak meliputi
kecacatan ini. Token nama orang di dalam triplet itu juga bertindih dengan `data/nama.yaml` (semakan token hanya untuk `pertama_*`/
`keluarga_*`). Kecacatan kecil dari sampel penyemak: gelaran tidak sepadan jantina ("En. <nama perempuan> binti …") dan nama bapa = nama diri.

**Keputusan.**
- Pengesah `bentuk_bukan_orang` (config `templat_llm.nama.bentuk_bukan_orang`), dipakai penjana (`tapis_nama`) DAN `--semak` sebagai
  kategori `bandar:*` / `syarikat:*`:
  - `bandar` = SATU nama tempat: tiada pemisah (`| , ; :` tab, baris baharu) → `bukan_satu_nama`; tiada akhiran syarikat →
    `syarikat_sebagai_bandar`; ≤ 3 token → `terlalu_panjang`; setiap token berhuruf besar → `huruf_kecil`; tiada token yang wujud dalam
    senarai nama orang (`data/nama.yaml` + senarai orang fail calon, selain penyambung) → `token_nama_orang`.
  - `syarikat` = SATU nama: tiada pemisah; ≤ 6 token; berakhiran `akhiran_syarikat` (selaras prompt `huraian.syarikat`) → `tiada_akhiran_syarikat`.
- Penjana nama berkumpulan (`jana.nama_orang`, fail berkumpulan SAHAJA — nama.yaml v1 rata kekal tepat, cincangan v1/dev tidak berubah):
  gelaran tepat sebelum `{NAMA}` (`jana.gelaran_jantina`, kunci BAHARU) mengehadkan kumpulan kepada `jana.kumpulan_jantina` jantina itu;
  gelaran kabur (cik, dato', dr) sengaja tiada; nama bapa dipilih ≠ nama diri. Dilaksanakan dalam komit jana semula (mengubah ujian2).

**Ukuran (`--semak ujian2` atas `54cf318f…`, kiraan sahaja — kandungan tidak dibuka).** Templat 219, 0 tolak; nama orang 0 tolak;
`bandar:bukan_satu_nama` 60/60, `syarikat:sah` 60/60 — sepadan dengan dapatan penyemak. Kawalan: `data/nama.yaml` v1 `bandar` 10/10 +
`syarikat` 10/10 sah (dengan token nama orang nama.yaml sendiri).

**Prompt (komit jana semula).** Dengan huraian lama `kimi-k3` memulangkan triplet untuk SETIAP bandar (jana pertama dengan pengesah
ini: `bandar:bukan_satu_nama` 61, `nama bandar 0 < 10` → tiada fail ditulis). Huraian `bandar` + `syarikat` kini menyatakan setiap
elemen = nama itu SAHAJA (1–3 / 2–6 perkataan, tiada orang/negeri/pemisah); cubaan kecil (statistik sahaja): bandar 97/97 sah, syarikat 60/60 sah.

**Dilaksanakan 30 Okt 2026:** ujian2 `83ff90b4…` — `--semak` 225 templat / 0 tolak, 13 senarai nama / 0 tolak (LOG-ITERASI). Baki
` | ` dalam 14/1000 dokumen datang dari 4 templat yang memakai `|` sebagai pemisah medan borang (gaya sama dengan `data/templat/`
tangan: 9 templat, dev 61/1000 dokumen) — 0 entri nama/syarikat/bandar mengandungi `|`. Ia sengaja tidak ditolak.

**Undur.** Buang `bentuk_bukan_orang` + cabangnya dalam `tapis_nama`/`semak_fail` + kunci config `bentuk_bukan_orang`, `gelaran_jantina`,
`kumpulan_jantina` dan argumen `sebelum` `nama_orang` → pengesah/penjana ADR-008.
