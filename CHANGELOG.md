# Changelog

**BM** · Semua perubahan penting projek ini direkod di sini. Format ikut [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
dan versi ikut [Semantic Versioning](https://semver.org/). Keputusan reka bentuk penuh ada dalam `docs/adr/`.
**EN** · All notable changes to this project are recorded here. The format follows
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).
Full design decisions live in `docs/adr/`.

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
