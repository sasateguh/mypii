# program.md — gelung autoresearch MyPII (corak karpathy/autoresearch; manusia menyunting fail ini, ejen menyunting kod)

## Matlamat
Naikkan **F1 tepat makro (`semua|*`) atas split `dev`** tanpa menurunkan precision mana-mana entiti di bawah 0.95.

## Ejen BOLEH menyunting
- `mypii/pengecam/*.py` (corak, `validate_result`, pengendalian sempadan)
- `config/mypii.yaml` bahagian `pengecam:` (konteks, skor)
- `data/templat/*.yaml` — MENAMBAH templat yang lebih sukar (lebih banyak gaya, negatif keras, Manglish); tidak memadam

## Ejen DILARANG
- Membaca `data/templat_ujian/` atau `data/bench/ujian.jsonl`, atau menilai split ujian (`tests/test_bench.py` gagal bila cincangan berubah)
- Menyunting `mypii/nilai/`, `tests/test_bench.py`, `config/kod_pb.yaml`, bahagian `jana:` / `nilai:` dalam config
- Menurunkan `ambang_skor`, atau menambah corak yang menangkap SEMUA nombor
- Menulis nombor sebenar sesiapa (semua nilai mesti dari `mypii/jana/nilai_palsu.py`)

## Satu iterasi
1. `make uji` mesti lulus sebelum mula.
2. Satu perubahan kecil dengan hipotesis bertulis dalam mesej komit ("FN NRIC berjarak sebab lookbehind").
3. `make nilai` → bandingkan dengan `hasil/dev-mypii.json` sebelumnya.
4. SIMPAN (komit) hanya jika F1 `semua|*` naik ATAU sama dengan kod lebih ringkas, dan `make uji` lulus. Jika tidak → `git checkout -- .`.
5. Bila templat ditambah: `make jana` menjana semula latih/dev SAHAJA — split ujian dijana dari benih yang sama;
   jika `make jana` atau `test_kunci_ujian_sepadan` gagal, BERHENTI dan laporkan (jangan kemas kini KUNCI.json). Cincangan latih/dev
   = `data/bench/CINCANGAN.json` (dikemas sendiri oleh `make jana`, komit bersama).

## Rekod setiap cubaan — `hasil/iterasi.tsv` (PELAN-C C2a, ADR-006; tambahan kepada langkah 3–4 di atas)
- Langkah 3 dan 4 dijalankan dengan `make nilai STATUS=<simpan|buang|ukur> KETERANGAN="<hipotesis ringkas>"`: setiap larian menambah
  SATU baris TSV (komit, dev, F1 `semua|*`, status, `baris_kod` +tambah/−buang atas pengecam + config, keterangan). Cubaan yang
  dibuang JUGA direkod — fail itu tambah-sahaja; jangan sunting atau padam baris lama (pembetulan = baris baharu).
- Lazimnya: jalankan dahulu tanpa keputusan (`STATUS=ukur`), putuskan, kemudian rekod keputusan itu (`simpan` selepas komit, atau
  `buang` sebelum `git checkout -- .` supaya `baris_kod` masih menunjukkan apa yang dicuba).
- **Crash:** bila harness gagal, baris `crash` ditulis sendiri (keterangan = ralat terakhir) dan `make nilai` keluar bukan-sifar.
  Kalau puncanya remeh (salah taip, import tertinggal) baiki SEKALI dan jalankan semula; kalau tidak, cubaan itu `buang` — jangan
  bertungkus-lumus membaiki idea yang rosak.

## Kriteria kesederhanaan (bila memutuskan simpan atau buang)
- Bila semua lain sama, versi yang LEBIH RINGKAS menang. Kod pengecam ialah liabiliti: setiap baris mesti membayar sewanya dalam F1.
- Kenaikan kecil yang membawa kod rumit atau rapuh (pengecualian khas, senarai kata panjang yang menghafal templat) TIDAK berbaloi —
  ia hampir pasti menala dev, bukan dunia sebenar.
- Membuang kod sambil F1 kekal atau naik = kemenangan; simpan walaupun ΔF1 = 0.
- Timbang `baris_kod` lawan ΔF1. Contoh: `+3/-0` untuk +0.004 → wajar disimpan; `+45/-2` untuk +0.0008 → buang (hampir hingar,
  kos besar); `+0/-20` untuk −0.0003 → wajar disimpan (kod lebih kecil, kerugian dalam hingar); `+60/-0` untuk +0.02 → simpan
  hanya jika kod itu boleh dijelaskan dalam satu ayat hipotesis.
- Bila ragu: buang. Rekodnya tetap ada dalam TSV untuk dicuba semula dengan bukti baharu.

## Dapatan larian pertama (28 Okt 2026, dev, 40 templat)
- MyPII F1 0.976 vs Presidio asal 0.607.
- Baki: NRIC FP pada nombor SSM 12 digit tahun 2001–2012 (kedua-dua format sah — perlukan konteks); SSM format lama
  `859836-X` terlepas (skor 0.1 + konteks frasa berbilang perkataan tidak dipadan).
- ⚠ Angka hampir siling = penanda aras terlalu mudah. Keutamaan iterasi awal: **templat lebih pelbagai dan negatif lebih sukar**, bukan menala pengecam.
