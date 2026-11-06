# ADR-013: Blok "Ketidakpastian" `docs/BANDINGAN.md` dijana dari fail statistik (PELAN-C C3b, 30 Okt 2026)

**Masalah.** C3b menuntut setiap sistem × entiti dengan F1 + CI 95%, dan MyPII lawan setiap garis dasar (ΔF1, CI Δ, p bootstrap,
p rawak, p Holm) dalam `docs/BANDINGAN.md`, dengan syarat setiap angka = `hasil/dev-statistik.json` dan penyemak boleh menjana semula.
Itu 20 selang + 16 baris perbandingan — menyalin dengan tangan mudah silap, dan ayat tafsiran ("CI tidak bertindih") yang ditulis
tangan boleh tersasar dari angka bila statistik dijalankan semula.

**Keputusan.**
- Modul `mypii/nilai/ketidakpastian.py` membaca `hasil/<split>-statistik.json` SAHAJA (tiada pengiraan statistik, tiada Presidio/
  rangkaian) dan menulis semula blok antara penanda `nilai.statistik.penanda` dalam `nilai.statistik.laporan` (kunci config BAHARU).
  `make statistik` menjalankannya selepas `harness --statistik`, jadi satu arahan = JSON + blok. `bandingan.tulis_blok` menerima
  penanda pilihan (lalai = penanda B4) — blok jana B4 dan blok statistik tidak saling menindih.
- Blok: konfigurasi (dokumen, unit, ulangan, benih, aras, kaedah, k), jadual F1 [CI] sistem × kunci, jadual berpasangan + dua lajur
  logik (*CI F1 bertindih*, *CI Δ > 0*), tanda † bila selang garis dasar = [0, 0] (Δ = F1 MyPII sendiri — pii-guard SSM, Presidio
  asal MyKad/SSM), dan **ringkasan mekanikal** yang dikira (bilangan selang bertindih pada kunci utama, selang Δ yang menyentuh 0,
  Δ terkecil, bilangan p rawak di lantai 1/(R+1) — dibanding atas nilai DIBUNDAR `perpuluhan`, kerana p disimpan dibundar).
- Prosa di luar blok (cara membaca, tafsiran, English summary) TIDAK membawa angka; ia menyatakan had: bootstrap dev mengukur hingar
  persampelan, bukan kecondongan sistematik kerana dev ditala → selang dev tidak menyokong dakwaan kertas (ujian2 + pra-daftar C4).
- `hasil/dev-statistik.json` dikomit (pengecualian `.gitignore` C2a); `hasil/ramalan/` kekal diabaikan (penyemak menjana semula
  dengan `make nilai-garis` → `make statistik`).

**Ditolak.** Menyalin `statistik.jadual_md` (output konsol C3a) terus: tiada lajur logik/ringkasan, dan baris panjang per kunci sukar
dibaca dalam laporan. Meletakkan blok dalam `make bandingan`: ia meramal semula semua sistem (lama) dan tidak perlu untuk statistik.

**Akibat.** Prosa tafsiran merujuk ringkasan mekanikal, jadi bila angka berubah ayat yang menyokongnya berubah bersama. `make statistik`
kini menulis ke `docs/` — dijalankan atas dev sahaja (split dikunci = exit 2).

**Undur.** Buang `mypii/nilai/ketidakpastian.py`, `tests/test_ketidakpastian.py`, baris kedua sasaran `statistik` Makefile, kunci
`nilai.statistik.laporan/penanda`, parameter `penanda` `bandingan.tulis_blok`, dan bahagian "Ketidakpastian" BANDINGAN.
