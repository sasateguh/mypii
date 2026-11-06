# ADR-008: Nama ujian2 berkumpulan (komuniti × jantina) + pengesah bahasa ketat; ujian2 `337820ee…` cacat (30 Okt 2026)

*(Nombor 006/007 ditempah PELAN-C untuk statistik/iterasi dan pra-daftar.)*

**Masalah (penyemak autopilot menolak B1b, 30 Okt).** ujian2 `337820ee…` (dijana dengan pengesah ADR-005) masih cacat:
1. **Bahasa** — `nisbah_bahasa` memulangkan None bila templat ada < `min_kata_fungsi` kata fungsi, dan `sebab_tolak` menganggap None
   sebagai LULUS. Templat `en` yang BM penuh tetapi pendek ("Pinjaman perniagaan untuk … Sila hubungi …") lulus senyap.
2. **Nama** — `nama_akhir` huruf kecil ("bin zahidi", "cheah") → dokumen "Fiona yeoh"; dan `jana.py` menggabung nama_pertama × nama_akhir
   secara rawak, jadi penyambung tidak sepadan jantina/komuniti ("Irfan binti …", "Saging a/l …").

**Keputusan.**
- `sebab_tolak`: templat `en`/`ms` yang tidak boleh dinilai = TOLAK `bahasa_tidak_dinilai` (manglish tetap tidak disemak). Senarai
  `bahasa_semak.kata_fungsi` diperluas dengan kata dokumen lazim yang hanya wujud dalam satu bahasa (borang/permohonan/sewa/tarikh… ·
  form/application/rent/date…); nama tempat dan gelaran (jalan, encik, puan) sengaja tidak dimasukkan kerana muncul dalam teks EN Malaysia.
- Nama berkumpulan: fail nama sasaran LLM mempunyai senarai `pertama_<komuniti>[_l|_p]` (nama diri) + `keluarga_<komuniti>` (satu
  token), bukan senarai rata. `jana.nama_kumpulan` (config, kunci BAHARU) menyusun NAMA: kumpulan dipilih ikut `berat`; Melayu/India/Iban =
  `<diri> <bin|binti|a/l|a/p|anak> <nama diri LELAKI komuniti sama>` (nama bapa); Cina = keluarga dahulu ("Tan Jun Hao"); Cina-Inggeris
  dan Kadazan = diri + keluarga. Fail rata (data/nama.yaml v1) kekal cara lama TEPAT — jujukan rng sama, cincangan v1/dev tidak berubah.
- Huruf besar: penjana membetulkan setiap token selain penyambung (`huruf_besar`); pengesah menolak `huruf_kecil`. `--semak` juga menolak
  fail rata untuk sasaran berkumpulan (`format_rata`) dan senarai yang kurang daripada `nama.min` (`kurang_daripada_min`).

**Ukuran (`--semak ujian2` atas `337820ee…`, kiraan sahaja — kandungan tidak dibuka).** Templat: en 6 `bahasa` + 8 `bahasa_tidak_dinilai`
(66/80 sah), ms 3 `bahasa_tidak_dinilai` (77/80), manglish 78/78. Nama: `nama_akhir` 60/60 `huruf_kecil`, fail rata, 11 senarai kumpulan
tiada. Sepadan dengan dapatan penyemak (6/80 en BM penuh). Kawalan: `data/nama.yaml` v1 47/47 sah; `make jana` tanpa diff.

**Belum dibuat — perlu kebenaran.** Menjana semula ujian2 sekali lagi = membuka meterai ADR-004 kali kedua. Gerbang autopilot hanya
membenarkan pembukaan bila cincangan KUNCI2 di BASE tersenarai dalam `meterai-cacat.txt` (ditulis penilai/penyelia, bukan pembina);
`337820ee…` belum tersenarai. ujian2 belum pernah dinilai (harness menguncinya), jadi pembukaan tidak membocorkan keputusan.

**Dilaksanakan 30 Okt 2026** (arahan projek §ujian2 — jana semula dibenarkan sehingga `UJIAN2-MUKTAMAD`, `meterai-cacat.txt` tidak lagi
perlu): ujian2 `54cf318f…`, `--semak` 0 tolak (LOG-ITERASI baris B1b jana semula ke-2).

**Undur.** Buang `nama_orang` cabang kumpulan + `jana.nama_kumpulan` + `templat_llm.nama.huraian` `pertama_*`/`keluarga_*` (pulihkan
`nama_pertama`/`nama_akhir`) dan cabang `bahasa_tidak_dinilai` → pengesah ADR-005.
