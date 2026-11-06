# ADR-003: Penjana negatif keras + slot alias untuk P1 (28 Okt 2026)

**Keputusan.** Penanda aras dev/latih ditambah 63 templat dan lima penjana BAHARU dalam `mypii/jana/nilai_palsu.py`
(`akaun_bank`, `invois12`, `telefon_tidak_sah`, `tarikh_angka`, `kod_produk`) serta `ssm_lama`. Slot baharu `{NEG_*}` tidak
dilabel; slot `{MY_SSM_LAMA}` dilabel `MY_SSM` melalui jadual `ALIAS` dalam `mypii/jana/jana.py`.

**Sebab.** Negatif sedia ada (`negatif()`) terlalu mudah dipisahkan. Fungsi lama TIDAK diubah: split ujian dijana dengan penjana
yang sama, jadi mengubah taburan `negatif()`/`ssm()` akan menukar `ujian.jsonl`. Hanya fungsi baharu ditambah; cincangan ujian
disahkan sama (`38d473fb…`) selepas `make jana`.

**Had yang diakui.** Separuh `akaun_bank` ialah 12 digit yang sah sebagai MyKad dari segi bentuk — hanya konteks (cth "akaun",
"acc") membezakannya; ini sengaja (kes sebenar). Angka dev sebelum/selepas P1 tidak boleh dibanding.

**Undur.** Buang templat P1 + `make jana` → dev kembali kepada cincangan Fasa 0 (`8e2e7eae…`).

**KUNCI.json tidak dikemas (28 Okt 2026).** `make jana` menulis semula `KUNCI.json`, tetapi fail itu dilarang disunting oleh
gelung automatik (gerbang autopilot menolak sebarang perubahan). Jadi selepas `make jana`, sesi autopilot memulihkannya
(`git checkout -- data/bench/KUNCI.json`). Hanya entri `ujian` yang berwibawa (diuji `test_kunci_ujian_sepadan`); entri
`latih`/`dev` dalam KUNCI.json kekal cincangan Fasa 0 dan BASI — cincangan dev semasa = `sha256sum data/bench/dev.jsonl`.
Keputusan manusia kelak: asingkan cincangan latih/dev daripada KUNCI.json.

**Diselesaikan (28 Okt 2026, sesi manusia).** `jana` kini menulis cincangan latih/dev ke `data/bench/CINCANGAN.json` (gelung
boleh mengemasnya) dan KUNCI.json memegang entri `ujian` SAHAJA. KUNCI.json yang wujud tidak pernah ditulis semula: cincangan ujian
berbeza = `SystemExit` dan fail tidak disentuh (`tests/test_kunci_jana.py`; sabotaj sebenar pada repo — KUNCI dirosakkan → `make jana`
gagal, KUNCI kekal). Cincangan ujian tidak berubah (`38d473fb…`).

**Had tambahan (disemak 28 Okt).** `ssm_lama()` mengikut bentuk contoh rasmi SSM `1312525-A` (pengumuman SSM ID=134), tetapi set
huruf semakan `ABCDEFGHKMPTUVWX` dan julat hingga 1,599,999 dipilih ejen, bukan dari sumber SSM. Format lama PERNIAGAAN (ROB,
milikan tunggal/perkongsian) belum disahkan dan tidak dijana.
