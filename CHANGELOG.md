# Changelog

**BM** · Semua perubahan penting projek ini direkod di sini. Format ikut [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
dan versi ikut [Semantic Versioning](https://semver.org/). Keputusan reka bentuk penuh ada dalam `docs/adr/`.
**EN** · All notable changes to this project are recorded here. The format follows
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).
Full design decisions live in `docs/adr/`.

## [1.1.0] - 2026-11-14

Pengecam v2.1 + split ujian baharu `ujian4` + penilaian model PII luar. / Recognizer v2.1, a new test split `ujian4` and an evaluation
of other PII models.

### Changed

- Recognizer **v2.1**: one rule changed in how the context classifier is combined with context phrases (`konteks.gabung.cara: frasa`,
  [ADR-021](https://github.com/sasateguh/mypii/blob/main/docs/adr/021-v21-frasa-dan-ujian4.md)). A context phrase right before the
  number (for example "My IC is 900101-08-1234", missed by 1.0.x) keeps it unless the classifier is nearly certain it is not PII; a
  closer negative phrase drops it unless the classifier is very confident; an old-format SSM number needs a context phrase. The
  classifier itself is unchanged. Tuned on `dev` and `dev3` only: `dev` 0.840 → 0.951, `dev3` 0.998 → 0.996. To get the 1.0.x
  behaviour back, set `konteks.gabung.cara: ganti`.

### Added

- Test split `ujian4` (1000 documents, `data/bench_v3/ujian4.jsonl`): templates and names written by Qwen3.8-27B, self-hosted, a
  model family used nowhere else in this study; registered in `docs/PRA-DAFTAR.md` (amendments 2026-11-14 (b) and (c)) before it was
  generated, sealed, then opened once. All four pre-registered hypotheses hold (Holm k = 4): v2.1 is not worse than v2 1.0.2
  (Δ +0.005) or Claude Haiku 5.5 (Δ +0.160), and beats Meddies PII v2 (Δ +0.470) and GLiNER multi PII v1 (Δ +0.332) on MyKad, SSM and
  phone numbers. v2.1 better than v2 also holds but the difference is small (Δ +0.005). Report:
  [`docs/BANDINGAN-V21.md`](https://github.com/sasateguh/mypii/blob/main/docs/BANDINGAN-V21.md); archive `hasil/arkib/ujian4-20261114T145032Z/`.
- Descriptive scores of Meddies PII v2 and GLiNER multi PII v1 on the already-opened splits:
  [`docs/BANDINGAN-LUAR.md`](https://github.com/sasateguh/mypii/blob/main/docs/BANDINGAN-LUAR.md). Raw predictions are in `hasil/luar/`.
- `data/probe/ayat_biasa.yaml`: 24 everyday sentences that must be flagged and 10 that must not, checked by
  `tests/test_ayat_biasa.py` (1.1.0: 24/24 and 0/10; 1.0.2: 20/24 and 3/10).
- Evaluation system `mypii-v2` (1.0.2, run from the git tag `mypii-v2-beku`), `make bandingan-v21`, `make statistik-v21` and
  `make ayat-biasa`.
- Scripts for the Modal runs: `scripts/penjana_modal.py` starts the temporary self-hosted vLLM server (OpenAI-compatible) that wrote
  the `ujian4` templates, called through `mypii.klien_llm` for model names that start with `modal/`; `scripts/luar_modal.py` runs the
  other PII models inside Modal containers, while label mapping and scoring stay in `mypii/nilai/luar.py`.

### Fixed

- The one-shot test scripts no longer fail at random on a long pre-registration file (`git show | grep -q` under `pipefail`).

## [1.0.2] - 2026-11-14

Kod pakej, pengecam v2 dan data penanda aras tidak berubah. / The package code, recognizer v2 and the benchmark data are unchanged.

### Fixed

- The label-review figure for documents with unlabelled PII now gives both halves of the 300-document sample: 0.067
  [0.027, 0.113] on `dev` and 0.167 [0.113, 0.227] on `ujian2`. Earlier text gave only the `dev` figure for the whole sample.
- The limitations now say the Claude family appears in four places: the held-out `ujian` templates were also written with the
  Claude development agent, and Claude Haiku and Claude Sonnet are comparators on `ujian`.

### Changed

- The label-review server image (`deploy/iaa/`) applies Debian security updates at build time and pulls the latest base image
  ([ADR-015](https://github.com/sasateguh/mypii/blob/main/docs/adr/015-iaa-semakan-label.md), addendum of 10 November 2026);
  `tests/test_iaa_imej.py` checks the build order.

### Added

- MyPII-Bench is also on Hugging Face as [`sasateguh/mypii-bench`](https://huggingface.co/datasets/sasateguh/mypii-bench), with
  the same data files, a dataset card and its own DOI, [10.57967/hf/11626](https://doi.org/10.57967/hf/11626).

## [1.0.1] - 2026-11-06

Dokumentasi sahaja; pengecam v2 tidak berubah. / Documentation only; recognizer v2 is unchanged.

### Changed

- README follows the Sasa Teguh open-source layout: logo, CI, PyPI, DOI and licence badges, English first and a complete Malay
  section at the end, and a "Work with Sasa Teguh" section.
- README links are absolute, so they work on the PyPI project page; the Zenodo DOI is in the README and `CITATION.cff`.

## [1.0.0] - 2026-11-06

Keluaran awam pertama; membawa pengecam v2. / First public release; ships recognizer v2.

### Added

- Three Presidio recognizers: `MY_NRIC` (MyKad number with birth date and official JPN place-of-birth code check), `MY_SSM`
  (SSM registration number: new 12-digit format, old format, LLP) and `MY_PHONE` (Malaysian phone numbers), with context words for
  Malay, English and Manglish text (ADR-001).
- Recognizer v2: OCR normalisation inside numbers, line-broken numbers, bracketed Sabah and Sarawak area codes, the LLP rule
  (year 2012 or later) and a small local context classifier (logistic regression, numpy only, sha256-checked artifact) (ADR-018).
- `all_recognizers()`, an English alias of `semua_pengecam()`.
- MyPII-Bench: 11,000 synthetic documents in seven splits, three of them sealed test splits locked by sha256 (`ujian`, `ujian2`,
  `ujian3`), with a dataset card and a canary string (`data/README.md`).
- Evaluation script with span-level precision, recall and F1, bootstrap intervals, Holm-corrected tests and an iteration log
  (ADR-006, ADR-007, ADR-014).
- Baselines scored by the same evaluation script: stock Presidio, `malaysia-pii-guard` and zero-shot LLMs, with LLM answers cached in the repo so
  scores reproduce offline (ADR-011, ADR-016, ADR-017).
- Pre-registration (`docs/PRA-DAFTAR.md`) and the archive of every test run with manifests (`hasil/arkib/`, `docs/PROVENANS.md`).
- Human label review protocol and results on a 300-document sample: one human plus one LLM reviewer (ADR-015).
- Comparison reports `docs/BANDINGAN.md` (dev, v1) and `docs/BANDINGAN-V2.md` (dev3 and `ujian3`, v2).

### Changed

- The wheel now carries `config/` and the classifier artifact inside the package, so `pip install mypii` works without a clone.
- Evaluation and training tools moved from extras to dependency groups (`uv sync --group nilai --group garis --group latih`),
  because PyPI rejects direct URL dependencies in package metadata.

### Known limitations

- All benchmark text is synthetic and labels are machine-generated; results on real text are not measured.
- On the older-style `dev` split, v2 scores lower than v1 (F1 0.840 versus 0.888), mostly `MY_SSM` precision.
- Phone recall is optimistic: synthetic phone labels only use number ranges that libphonenumber accepts (ADR-002).
- The label review has one human reviewer, not two.
