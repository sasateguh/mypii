# ADR-004: Split `ujian2` dari templat LLM keluarga berbeza, dimeterai (30 Okt 2026, PELAN-B B1)

**Keputusan.** Split ujian kedua (1,000 dok, benih + 2) dijana dari templat dan nama yang ditulis `cbcn/kimi-k3` melalui 9router
(`python -m mypii.jana.templat_llm --sasaran ujian2`), bukan oleh ejen yang menala pengecam. Fail: `data/templat_ujian2/{ms,en,manglish}.yaml`,
`data/nama_ujian2.yaml`, `data/bench/ujian2.jsonl`, `data/bench/KUNCI2.json`. Selepas komit pertama keempat-empatnya DIMETERAI (gerbang
autopilot menolak sebarang perubahan); `KUNCI2.json` dicipta hanya bila tiada, berbeza = `jana` BERHENTI (corak KUNCI v1, ADR-003).
Harness: `--split ujian2` perlukan `--benarkan-ujian` (config `nilai.split_dikunci`).

**Pengesah (sebelum fail ditulis; semua ambang dalam `config/mypii.yaml` `templat_llm:`).** Slot sedia ada sahaja (set slot = slot yang
dikenali `jana.py`), tiada kurungan liar, sekurang-kurangnya satu slot nombor (entiti/`NEG*`/`TARIKH`), tiada nombor literal ≥ 4 digit
(termasuk berpemisah), panjang 40–600, tiada jenama larangan (perkataan penuh), buang pendua teks dinormal — termasuk pendua templat latih.
Ambang: ≥ 150 templat, ≥ 8 genre setiap bahasa, ≥ 25% negatif sahaja setiap bahasa. Nama: bersilang KOSONG dengan `data/nama.yaml` —
nama orang ikut TOKEN (selain bin/binti/a/l/a/p/anak), syarikat + bandar ikut entri penuh. Gagal mana-mana ambang = tiada fail ditulis.

**Pembina tidak membaca kandungan.** Penjana mencetak statistik sahaja (kiraan, genre, nisbah, sebab tolak, model); mesej ralat
klien = jenis ralat sahaja. Ujian ke atas fail ujian2 melaporkan KIRAAN (span rosak, persilangan nama), bukan teks.

**Sebab.** Dev F1 0.9954 mengukur templat yang ditulis ejen yang sama yang menala pengecam (`docs/ANALISIS-RALAT.md`). Model
keluarga berbeza (bukan penjana latih B2 `ag/gemini-3.8-flash`, bukan garis dasar B3) + genre berbeza (10 genre, tiada yang sama
nama dengan `data/templat/`) + nama berasingan mengurangkan kebocoran gaya. Sandaran `cbcn/glm-5.3` (PELAN-B §Fakta) tidak dipakai.

**Had yang diakui.** Templat LLM tidak disemak manusia (sengaja — sesiapa yang membacanya tidak lagi buta terhadap ujian); kualiti
dinilai hanya oleh pengesah mekanikal. Penjana NILAI (`nilai_palsu.py`) sama dengan split lain — taburan bentuk nombor tidak berubah,
hanya konteks. Nisbah dokumen tanpa PII ≈ 0.25 + 0.75 × nisbah templat negatif (diukur 480/1,000). Templat dijana dengan suhu 0.8 —
tidak boleh dihasilkan semula dari LLM; fail yang dikomit ialah artifak, dan `make jana` daripadanya berketentuan.

**Undur.** Buang empat fail di atas + `templat_llm.py`/`klien_llm.py` + kunci config `templat_llm:`/`llm:`/`jana.*ujian2` → `make jana`
= split lama (latih/dev/ujian tidak pernah bergantung pada ujian2).

**Meterai + had diketahui (30 Okt 2026).** Penyemak meluluskan jana semula ke-3 (KUNCI2 `83ff90b4…`, `d2176a3`; sampel tangan 30 dok:
label 30/30 tepat, salah realisme 2/30); `data/bench/UJIAN2-MUKTAMAD` dikomit sendiri (`2ecb14d`) — tiada lagi jana semula. Had realisme
yang dilaporkan penyemak (BUKAN ralat label; pembina tidak membaca kandungan) — wajib disebut dalam kertas/kad data:
(1) sebahagian templat `en` pusat panggilan memakai `{NAMA}` dua kali untuk orang yang sama → dua nama berbeza (penyemak: 4/1,000 dok);
(2) jumlah wang dibuang oleh larangan nombor literal → frasa seperti "RM sebulan" tanpa angka (5 templat manglish, 17/1,000 dok);
(3) label bahasa `manglish` tidak disahkan pengesah — sekurang-kurangnya satu dok berlabel manglish ialah BM formal (angka per bahasa
`manglish` perlu ditafsir dengan berhati-hati).
