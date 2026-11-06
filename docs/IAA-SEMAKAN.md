# Semakan IAA / IAA label review

> Dipindah dari `README.md` (PELAN-SEDIA-TERBIT P2). Skor: `docs/BANDINGAN.md` bahagian Semakan label (IAA). / Moved from `README.md`; scores in `docs/BANDINGAN.md`.

**BM** · Label penanda aras dijana mesin, jadi manusia menyemak sampel 300 dokumen (150 dev + 150 ujian2, protokol
`docs/PRA-DAFTAR.md` §15 pindaan 2026-10-31, ADR-015) untuk mengukur hingar label dan persetujuan antara penyemak.
- **Cara menyemak:** buka pautan peribadi di telefon (tiada akaun, tiada log masuk). Setiap dokumen ada tiga soalan:
  (a) setiap nombor bertanda: `Betul` / `Salah` / `Jenis lain`; (b) ada MyKad/SSM/telefon yang tidak bertanda?: `Tiada` / `Ada`
  (salin nombor itu); (c) teks terasa Malaysia sebenar?: `Ya` / `Janggal`. Kira-kira 1.5–2 jam semuanya; boleh sikit-sikit:
  setiap jawapan tersimpan serta-merta di pelayan dan pautan yang sama menyambung di tempat terakhir. `Undur` membatalkan jawapan terakhir.
- **Buka dari butang Telegram:** menaip nama laman sahaja (atau pautan rosak) membuka halaman pintu BM + EN yang menerangkan langkah ini;
  ia tidak memaparkan apa-apa dokumen, dan jawapan yang sudah disimpan tidak terjejas.
- **Privasi:** semua teks sintetik. Halaman tidak memaparkan split, id dokumen atau ramalan mana-mana sistem; tiada analitik, fon atau
  skrip pihak ketiga; `noindex`. Pautan = kunci; jangan kongsi. Jawapan disimpan di luar repo; eksport (`make iaa-eksport`) tanpa token.
- **Selepas siap:** cron harian `# IAA-MYPII` (`deploy/iaa/pencetus.sh`) mengesan 300/300 dan memulakan autopilot sekali untuk skor
  (`make iaa-skor` → `hasil/iaa.json` + `docs/BANDINGAN.md`). Kemajuan: `deploy/iaa/deploy.sh --status`.

**EN** · Benchmark labels are machine-generated, so humans review a 300-document sample (150 dev + 150 ujian2; protocol in
`docs/PRA-DAFTAR.md` §15 amendment 2026-10-31, ADR-015) to measure label noise and inter-annotator agreement.
- **How:** open the personal link on a phone (no account, no login). Three questions per document: (a) each marked number:
  `Correct` / `Wrong` / `Other type`; (b) any unmarked MyKad/SSM/phone?: `None` / `Yes` (copy the numbers); (c) does the text read
  like a real Malaysian document?: `Yes` / `Awkward`. About 1.5–2 hours in total, in as many sittings as you like: every answer is
  saved on the server immediately and the same link resumes where you stopped. `Undo` removes the last answer.
- **Open it from the Telegram button:** typing the site name alone (or a broken link) shows a BM + EN door page explaining this step;
  it shows no documents, and answers already saved are unaffected.
- **Privacy:** all text is synthetic. The page never shows the split, document ids or any system's predictions; no analytics, third-party
  fonts or scripts; `noindex`. The link is the key; do not share it. Answers live outside the repo; exports carry no tokens.
- **After completion:** a daily `# IAA-MYPII` cron (`deploy/iaa/pencetus.sh`) detects 300/300 and starts autopilot once for scoring.

## Tambah penyemak kedua / Add a second reviewer

```bash
deploy/iaa/deploy.sh --penyemak tambah p2    # token rawak baharu / new random token (penyemak.json, 0600)
deploy/iaa/deploy.sh --penyemak mesej p2     # satu mesej Telegram, pautan dalam butang sahaja / one message, link in a button only
deploy/iaa/deploy.sh --penyemak pautan p2    # (pilihan) cetak pautan ke terminal sahaja / (optional) prints the link to the terminal only
```

**BM** · `--penyemak mesej` menghantar satu mesej BM + EN ke Telegram pemilik untuk dipanjangkan: teks tanpa nama laman/URL (ditolak oleh
kod), pautan hanya dalam butang "Buka semakan"; dihantar sekali sahaja (penanda `mesej-<id>.dihantar`; notify gagal = boleh cuba lagi).
Teks = `mypii/iaa/teks/{ms,en}.json` kunci `mesej_*`. Atau pemilik menghantar pautan itu sendiri kepada penyemak kedua (pautan berasingan; jawapan p1 tidak kelihatan). p1×p2 menjadi
pasangan utama bila p2 siap; tanpa p2, p1×llm (`cbcn/glm-5.3`) dilapor sebagai had kajian.
**EN** · `--penyemak mesej` sends one BM + EN message to the owner's Telegram to forward: the text never contains the site name or a
URL (rejected in code), the link lives only in the "Open review" button; sent once only (marker `mesej-<id>.dihantar`; a failed notify
can be retried). Text = `mypii/iaa/teks/{ms,en}.json` keys `mesej_*`. Or the owner sends that link personally (separate link; p1's answers are not visible). p1×p2 becomes the primary pair once p2
finishes; without p2, p1×llm (`cbcn/glm-5.3`) is reported as a study limitation.
