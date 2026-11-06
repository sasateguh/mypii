# Provenans / Provenance

## BM

**Apa repo awam ini.** Repo `sasateguh/mypii` ialah petikan keluaran. Pembangunan berlaku dalam repo git persendirian (lebih 140 komit,
28 Okt hingga 6 Nov 2026). Setiap keluaran awam menjadi satu komit di sini. Sejarah penuh tidak diterbitkan kerana ia membawa fail
pelan kerja dalaman. Editor atau penilai kertas boleh memintanya daripada pengarang.

**Apa yang boleh anda sahkan sendiri tanpa sejarah itu.** Setiap split ujian dikunci dengan sha256 sebelum dinilai, dan ujian dalam
repo ini gagal jika mana-mana bait berubah.

| Bahan | sha256 (16 aksara pertama) | Fail kunci | Dimeterai (UTC) | Dibuka (UTC) |
|---|---|---|---|---|
| `data/bench/ujian.jsonl` | `38d473fb77bde237` | `data/bench/KUNCI.json` | 28 Okt 2026 | 3 hingga 4 Nov 2026, sekali |
| `data/bench/ujian2.jsonl` | `83ff90b4ef40a7ac` | `data/bench/KUNCI2.json` | 30 Okt 2026 | 3 hingga 4 Nov 2026, sekali |
| `data/bench_v3/ujian3.jsonl` | `5658ebe3614f5b09` | `data/bench_v3/KUNCI3.json` | 5 Nov 2026 12:11 | 5 Nov 2026 13:00, sekali |
| `model/konteks-v2.json` (pengelas v2) | `02d7d9bd37859762` | `config/mypii.yaml` `konteks.sha256` | dibekukan 5 Nov 2026 12:48 | |

**Arkib larian ujian.** Keputusan, ramalan setiap dokumen dan jawapan LLM setiap larian ujian ada dalam `hasil/arkib/`, bersama
`MANIFEST.sha256`. Untuk menyemak, jalankan `cd hasil/arkib/<larian> && sha256sum -c MANIFEST.sha256`. Fail `MULA` merekod
perintah tepat dan komit pembangunan yang dijalankan.

| Larian | Split | Komit pembangunan | Mula hingga selesai (UTC) |
|---|---|---|---|
| `ujian-20261103T182455Z` | `ujian` + `ujian2` (v1) | `e846e49` | 3 Nov 18:24 hingga 4 Nov 04:14 (diulang sekali selepas crash, `ULANG-CRASH`) |
| `ujian3-20261105T130039Z` | `ujian3` (v2) | `17bb5a1` | 5 Nov 13:00 hingga 13:19 |

**Suntingan.** Dalam `docs/PRA-DAFTAR.md`, `docs/LOG-ITERASI.md`, ADR-019, ADR-020 dan satu komen `config/mypii.yaml`, butiran
operasi akaun penyedia API diganti dengan tanda `[disunting]`. Hipotesis, ambang, tarikh, angka, keputusan dan sebab saintifik tidak
diubah. Fail arkib dalam `hasil/arkib/` tidak disunting kerana ia dilindungi `MANIFEST.sha256`.

**Fail yang dirujuk tetapi tiada di sini.** Rujukan kepada `PELAN-*.md`, `NEXT.md`, `docs/kertas/` atau laluan `~/ops/...` menunjuk
kepada fail kerja dalam repo pembangunan atau hos pembina. Fail itu tidak diperlukan untuk menjana semula sebarang angka.

## EN

**What this public repository is.** `sasateguh/mypii` is a release snapshot. Development happened in a private git repository
(more than 140 commits, 28 Oct to 6 Nov 2026), and each public release becomes one commit here. The full history is not published because it
carries internal work-plan files. Paper editors or reviewers can request it from the author.

**What you can verify without that history.** Every test split was locked by sha256 before it was scored, and the tests in this
repository fail if any byte changes. See the table above for each split, its key file, and when it was sealed and opened (UTC).

**Test-run archives.** Results, per-document predictions and LLM answers for each test run live in `hasil/arkib/` with a
`MANIFEST.sha256`. To check one, run `cd hasil/arkib/<run> && sha256sum -c MANIFEST.sha256`. The `MULA` file records the exact
commands and the development commit that ran.

**Redactions.** In `docs/PRA-DAFTAR.md`, `docs/LOG-ITERASI.md`, ADR-019, ADR-020 and one comment in `config/mypii.yaml`, operational
details about API provider accounts are replaced with a `[redacted]` / `[disunting]` marker. Hypotheses, thresholds, dates, numbers,
decisions and scientific reasons are unchanged. Archive files in `hasil/arkib/` are not edited because `MANIFEST.sha256` covers them.

**Files referenced but absent here.** References to `PELAN-*.md`, `NEXT.md`, `docs/kertas/` or `~/ops/...` paths point to working
files in the development repository or on the build host. None of them is needed to regenerate any number.
