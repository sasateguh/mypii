# ADR-001: Pengecam berstruktur, bukan regex longgar (28 Okt 2026)

**Keputusan.** Setiap pengecam = corak calon + `validate_result` yang menyemak struktur: MyKad (tarikh lahir sah dalam 1900/2000 +
86 kod tempat lahir dari JPN), SSM (tahun + kod jenis 01–06: 01 syarikat tempatan, 02 syarikat asing, 03 perniagaan, 04 PLT tempatan, 05 PLT asing, 06 PLT amalan profesional — pernyataan SSM, [Borneo Post/Bernama 9 Okt 2019](https://www.theborneopost.com/2019/10/09/ssm-introduces-new-format-for-registration-number-of-business-entities/); pengumuman SSM sendiri hanya memberi struktur 12 digit + contoh `201901000005`; format lama ROB belum disahkan), telefon (libphonenumber rantau MY). Kod JPN dalam `config/kod_pb.yaml`.

**Sebab.** MyKad tiada digit semak; tanpa pengesahan, setiap nombor 12 digit ialah calon (no. invois, no. siri). Presidio menolak
pengecam yang banyak positif palsu (developing_recognizers.md §Accuracy).

**Kesan.** Kesamaran sebenar kekal: nombor SSM 12 digit tahun 2001–2012 boleh juga sah sebagai MyKad (cth 2011-01-44…). Diselesaikan
oleh perkataan konteks, bukan regex. Jalan undur: setiap corak/kod/konteks dalam config.
