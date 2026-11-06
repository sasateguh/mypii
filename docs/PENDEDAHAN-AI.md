# Pendedahan AI / AI disclosure

**BM** · Fail ini menerangkan apa yang dibuat oleh ejen AI dan apa yang dibuat oleh manusia dalam repo MyPII. Kiraan komit di bawah
dikira daripada `git log`, bukan daripada ingatan; perintahnya dipetik supaya sesiapa boleh mengulangnya.

**EN** · This file states what AI agents did and what humans did in the MyPII repository. The commit counts below come from
`git log`, not from memory; the commands are quoted so anyone can rerun them.

## Kiraan komit / Commit counts

Dikira pada komit `fb09b21` (3 Nov 2026), sebelum komit yang menambah fail ini. / Counted at commit `fb09b21` (3 Nov 2026), before the
commit that adds this file.

| Perkara / Item | Kiraan / Count |
|---|---|
| Jumlah komit / Total commits | 96 |
| Komit dengan trailer `Co-Authored-By` ejen / Commits with an agent `Co-Authored-By` trailer | 89 |
| ... `Claude Opus 5.5` | 88 |
| ... `Claude Fable 5.1` | 1 |
| Komit tanpa trailer / Commits without a trailer | 7 |
| Pengarang git / Git author (`%an`) | `Muhammad Aiman` pada 96 daripada 96 / on 96 of 96 |
| Julat tarikh / Date range | 2026-10-28 hingga / to 2026-11-03 |

**BM** · Ketujuh-tujuh komit tanpa trailer bertajuk `autopilot <projek>: fail perancang dipasang ...`: ia memasang fail pelan
(`PELAN-*.md`) yang ditulis oleh ejen perancang autopilot, dan dikomit oleh saluran autopilot tanpa trailer. Jadi "tanpa trailer" di
sini tidak bermaksud "ditulis manusia". Pengarang git `Muhammad Aiman` pada setiap komit datang daripada konfigurasi git mesin, bukan
tanda bahawa manusia menaip perubahan itu.

**EN** · All seven commits without a trailer are titled `autopilot <project>: fail perancang dipasang ...`: they install plan files
(`PELAN-*.md`) written by the autopilot planner agent, committed by the autopilot pipeline without a trailer. So "no trailer" here does
not mean "written by a human". The git author `Muhammad Aiman` on every commit comes from the machine's git configuration and does not
mean a human typed the change.

Perintah / Commands (jalankan dalam repo / run inside the repository):

```sh
git rev-list --count fb09b21
git log fb09b21 --format='%H %(trailers:key=Co-Authored-By,valueonly,separator=;)' | awk '{ if (NF>1) a++; else n++ } END {print a, n}'
git log fb09b21 --format='%(trailers:key=Co-Authored-By,valueonly,separator=;)' | grep -v '^$' | sort | uniq -c
git log fb09b21 --format='%an' | sort | uniq -c
for h in $(git log fb09b21 --format='%H'); do
  [ -z "$(git log -1 --format='%(trailers:key=Co-Authored-By,valueonly)' "$h")" ] && git log -1 --format='%h %ad %s' --date=short "$h"
done
```

Output pada `fb09b21` / output at `fb09b21`: `96` · `89 7` · `1 Claude Fable 5.1 <noreply@anthropic.com>`,
`88 Claude Opus 5.5 <noreply@anthropic.com>` · `96 Muhammad Aiman` · tujuh baris / seven lines (`0525220`, `9620a7a`, `eb4e815`,
`2f9b275`, `70fb8fa`, `cc5051c`, `4f993e2`).

## Peranan ejen / Agent roles

Alat: Claude Code, dengan model yang dinamakan dalam trailer di atas. / Tool: Claude Code, with the models named in the trailers above.

| Kerja / Work | Siapa / Who | Rujukan / Reference |
|---|---|---|
| Kod pengecam, alat penilaian, pelayan semakan IAA / recognizer code, evaluation tooling, IAA review server | ejen / agent | `mypii/`, `git log` |
| Ujian / Tests | ejen / agent | `tests/` |
| Penjanaan data penanda aras / benchmark data generation | ejen menulis penjana; LLM menulis templat dan nama / agent wrote the generator; LLMs wrote templates and names | `config/mypii.yaml` (`ag/gemini-3.8-flash` latih dan dev / train and dev, `cbcn/kimi-k3` ujian2), ADR-002, ADR-004 |
| Larian garis dasar (termasuk LLM) / baseline runs (including LLMs) | ejen / agent | ADR-011, ADR-016, ADR-017, `hasil/` |
| Penyemak label LLM untuk IAA / LLM label reviewer for IAA | `cbcn/glm-5.3` | ADR-015, `hasil/iaa.json` |
| Pra-daftar dan pindaannya (draf teks) / pre-registration and its amendments (draft text) | ejen / agent | `docs/PRA-DAFTAR.md` §14 |
| Dokumen: README, ADR, LOG, CHANGELOG, metadata petikan, fail ini / documents: README, ADRs, log, changelog, citation metadata, this file | ejen / agent | `git log` |
| Pelan kerja autopilot / autopilot work plans | ejen perancang / planner agent | `PELAN-*.md` |
| Semakan setiap potongan autopilot / review of each autopilot step | ejen penyemak berasingan / separate reviewer agent | sejarah autopilot / autopilot history |
| Draf kertas (jika ada) / paper draft (if any) | ejen menulis rangka dan fakta sahaja; prosa ditulis manusia / agent writes outline and facts only; prose is written by a human | `docs/kertas/` |

## Peranan manusia / Human roles

| Kerja / Work | Rujukan / Reference |
|---|---|
| Keputusan reka bentuk M1 hingga M5 (nama, repo, pengarang, IAA, gelung autopilot) / design decisions M1 to M5 (name, repo, authorship, IAA, autopilot loop) | PRD projek / project PRD |
| Memulakan setiap pelan kerja dan arah projek, termasuk pindaan pra-daftar / commissioning each work plan and the project direction, including pre-registration amendments | `docs/PRA-DAFTAR.md` §14, §15 |
| Penandaan IAA oleh penyemak manusia p1: 300 daripada 300 dokumen / IAA labelling by human reviewer p1: 300 of 300 documents | `hasil/iaa.json` (`penyemak.p1.siap`) |
| Semakan sesi manusia 28 Okt: F1 dev dihasilkan semula, fail larangan dan split ujian disahkan tidak berubah / human session review on 28 Oct: dev F1 reproduced, protected files and test split confirmed unchanged | `NEXT.md` |
| Keputusan sesi manusia 29 Okt untuk mengundur P2-10 / human session decision on 29 Oct to revert P2-10 | `NEXT.md` |
| Keputusan terbit: bila repo menjadi awam, release, DOI / publication decisions: when the repository goes public, release, DOI | `PELAN-SEDIA-TERBIT.md` |

**BM** · Tiada rekod tandatangan berasingan bagi setiap pindaan pra-daftar; pindaan ditulis ejen dalam pelan yang dimulakan pemilik.
Penyemak manusia p1 menyemak label yang dijana mesin; ia bukan IAA dua manusia (lihat README §Had kajian).

**EN** · There is no separate sign-off record for each pre-registration amendment; amendments were written by agents inside plans the
owner commissioned. Human reviewer p1 checked machine-generated labels; this is not a two-human IAA (see README §Limitations).

## Cara menyemak / How to check

- Jalankan perintah di atas pada `fb09b21`, atau tukar `fb09b21` kepada `HEAD` untuk kiraan semasa. / Run the commands above at
  `fb09b21`, or replace `fb09b21` with `HEAD` for current counts.
- `git log --format='%h %s%n%(trailers:key=Co-Authored-By)' -- <fail>` menunjukkan siapa menyumbang kepada satu fail. / shows who
  contributed to one file.
- `docs/LOG-ITERASI.md` merekod setiap iterasi pengecam dan penanda aras; `docs/adr/` merekod keputusan. / records every recognizer
  and benchmark iteration; `docs/adr/` records decisions.
