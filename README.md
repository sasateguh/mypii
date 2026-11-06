<p align="center"><img src="https://raw.githubusercontent.com/sasateguh/mypii/main/brand/logo-512.png" width="112" height="112" alt="MyPII"></p>

<h1 align="center">MyPII</h1>

<p align="center"><a href="https://github.com/sasateguh/mypii/actions/workflows/ci.yml"><img src="https://github.com/sasateguh/mypii/actions/workflows/ci.yml/badge.svg" alt="CI"></a> <a href="https://pypi.org/project/mypii/"><img src="https://img.shields.io/pypi/v/mypii" alt="PyPI"></a> <a href="https://doi.org/10.5281/zenodo.24014252"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.24014252.svg" alt="DOI"></a> <a href="https://github.com/sasateguh/mypii/blob/main/LICENSE"><img src="https://img.shields.io/badge/licence-MIT-blue" alt="Licence: MIT"></a></p>

<p align="center"><b>Find MyKad, SSM and phone numbers in Malaysian text, on your own machine.</b> · <i>Kesan nombor MyKad, SSM dan telefon dalam teks Malaysia, di mesin anda sendiri.</i><br>
<a href="https://pypi.org/project/mypii/">PyPI</a> · <a href="https://github.com/sasateguh/mypii/blob/main/data/README.md">benchmark</a> · <a href="https://doi.org/10.5281/zenodo.24014252">cite</a> · Built in Malaysia by <a href="https://aimanmalib.com">Aiman Malib</a> · <a href="https://sasateguh.com">Sasa Teguh</a></p>

MyPII detects Malaysian MyKad (NRIC) numbers, SSM company registration numbers and Malaysian phone numbers in Malay, English
and Manglish text, as add-on recognizers for [Presidio](https://github.com/data-privacy-stack/presidio). It runs entirely on your
machine: rules, validation (JPN birth date and place-of-birth codes, SSM format, libphonenumber) and one small context classifier
(logistic regression, numpy). There is no external API, so text never leaves the machine. The repo also ships MyPII-Bench, a synthetic
benchmark for evaluating recognizers like these, together with a pre-registration and the archive of every test run.

[Bahasa Melayu ↓](#bahasa-melayu)

## Install

```bash
pip install mypii
python -m spacy download en_core_web_sm
```

Python 3.11 to 3.13. The small spaCy model is the NLP engine Presidio uses in the example below.

## Example

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from mypii import semua_pengecam

nlp = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}).create_engine()
engine = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
for r in semua_pengecam():
    engine.registry.add_recognizer(r)

teks = "No IC saya 900101-08-1234, call 012-345 6789. Syarikat SSM 201901000005."
hasil = engine.analyze(teks, language="en", entities=["MY_NRIC", "MY_SSM", "MY_PHONE"])
for r in sorted(hasil, key=lambda r: r.start):
    print(r.entity_type, teks[r.start:r.end], r.score)
```

Output:

```text
MY_NRIC 900101-08-1234 1.0
MY_PHONE 012-345 6789 1.0
MY_SSM 201901000005 1.0
```

`all_recognizers()` is the English name for the same function as `semua_pengecam()`. The `en_core_web_sm` configuration is
deliberate: a default `AnalyzerEngine()` downloads `en_core_web_lg` (382 MB). Without `entities=`, stock Presidio recognizers also
return other types (for example `UK_NHS`, `DATE_TIME`) on the same numbers.

## Entities

| Entity | Example (synthetic) | Validation |
|---|---|---|
| `MY_NRIC` | `900101-08-1234` | Valid birth date + official JPN place-of-birth code (86 codes, [JPN](https://www.jpn.gov.my/my/kod-negeri)) |
| `MY_SSM` | `201901000005` | Year + entity type code 01 to 06 (SSM format since 11 October 2019), old format, LLP |
| `MY_PHONE` | `+60 12-345 6789` | libphonenumber, region MY |

## Results

Exact-match micro F1, all entities. Releases 1.0.x ship recognizer **v2** (1.0.1 changed the documentation only).

| Split | Text | MyPII v1 | MyPII v2 (1.0.x) | Claude Haiku 5.5 | Claude Sonnet 5.5 | Stock Presidio |
|---|---|---|---|---|---|---|
| `dev` | v1 development | 0.888 | 0.840 | 0.915 | 0.878 | 0.431 |
| `ujian` † | held-out v1 templates | **0.993** | – | 0.965 | 0.982 | 0.526 |
| `ujian2` † | Kimi K3 templates | **0.940** | – | 0.873 | 0.885 | 0.419 |
| `dev3` | v2 development, Nemotron templates | 0.615 | 0.998 | 0.791 | – | 0.290 |
| `ujian3` † | Claude Sonnet 5.5 templates | 0.587 | **0.980** | 0.871 | – | 0.325 |

† Test split: locked by sha256 before scoring, opened once, hypotheses registered in advance in
[`docs/PRA-DAFTAR.md`](https://github.com/sasateguh/mypii/blob/main/docs/PRA-DAFTAR.md). `dev` and `dev3` were used during development, so MyPII's numbers there are
optimistic. – = not run.

How to read this table:
- Every pre-registered hypothesis tested so far is supported after Holm correction: v1 beats six baselines on `ujian2` (H1a to H1f,
  primary) and on `ujian` (H2a to H2f, secondary); v2 is not worse than Haiku (Δ +0.109) and beats v1 (Δ +0.393) on `ujian3` (H4a,
  H4b). The v1 margin over Sonnet on `ujian` is small (Δ +0.0115) although significant. The secondary per-entity hypothesis H3 is not
  reported yet.
- v2 adds OCR normalisation inside numbers, line-broken numbers, bracketed Sabah and Sarawak area codes, the LLP rule and the context
  classifier. On new-style text (`dev3`, `ujian3`) it is far better. On old-style text (`dev`) it is lower than v1 (0.840 versus
  0.888), mostly `MY_SSM` (precision 0.51). No version wins on every text style, so evaluate on your own data first.
- v2 was not scored on `ujian` and `ujian2` because both splits were already opened for v1. A v2 run there now would be a post-hoc
  analysis, not a test.
- Confidence intervals and per-entity, per-language and per-category precision and recall are in
  [`docs/BANDINGAN-V2.md`](https://github.com/sasateguh/mypii/blob/main/docs/BANDINGAN-V2.md) and [`docs/BANDINGAN.md`](https://github.com/sasateguh/mypii/blob/main/docs/BANDINGAN.md). The `ujian` and `ujian2`
  results are in [`docs/LOG-ITERASI.md`](https://github.com/sasateguh/mypii/blob/main/docs/LOG-ITERASI.md) and the `hasil/arkib/` archive.

## Limitations

- **Fully synthetic.** Text is written by LLMs with marked slots and filled with invented values, so labels are known without manual
  annotation. The same builder wrote the data generator and the recognizer. Results on real text are not measured and may be lower.
- **The Claude family appears in three places.** The code was written with Claude agents, the `ujian3` templates were generated by
  Claude Sonnet, and Claude Haiku is the H4a comparator. That bias runs against MyPII for H4a.
- **Label review = one human + one LLM, not two humans.** On a 300-document sample the human reviewer found 0.000 wrong spans and
  0.067 [0.027, 0.113] of documents with unmarked PII. κ is not meaningful because there is almost no variance.
- **Phone recall is optimistic.** Phone labels are drawn from libphonenumber's valid ranges, the same library the recognizer uses
  ([ADR-002](https://github.com/sasateguh/mypii/blob/main/docs/adr/002-penanda-aras-sintetik.md)).
- **MyPII finds spans; it does not assess risk.** It is not a complete anonymisation tool and not evidence of PDPA compliance.

## Benchmark

MyPII-Bench (`data/`, CC-BY-4.0) has five 1000-document splits (`dev`, `ujian`, `ujian2`, `dev3`, `ujian3`) plus training
splits. Dataset card: [`data/README.md`](https://github.com/sasateguh/mypii/blob/main/data/README.md). The test splits are now public, so models trained after the release date
may have seen them; the canary string in the dataset card helps model builders filter them out.

## Reproduce

```bash
git clone https://github.com/sasateguh/mypii.git && cd mypii
uv sync --all-groups      # evaluation tools: spaCy model, malaysia-pii-guard, Anthropic SDK, scikit-learn
make uji                  # unit tests + sha256 lock of every split
make bandingan-v2         # docs/BANDINGAN-V2.md from the ujian3 archive, no network
make bandingan            # docs/BANDINGAN.md from the committed LLM cache, no network
```

LLM answers are stored in the committed cache, so baseline scores regenerate without API keys. Seal evidence, test-run archives and
document redactions are explained in [`docs/PROVENANS.md`](https://github.com/sasateguh/mypii/blob/main/docs/PROVENANS.md).

## Documents

- [`docs/PRA-DAFTAR.md`](https://github.com/sasateguh/mypii/blob/main/docs/PRA-DAFTAR.md): hypotheses, splits, statistical tests and amendments.
- [`docs/BANDINGAN-V2.md`](https://github.com/sasateguh/mypii/blob/main/docs/BANDINGAN-V2.md), [`docs/BANDINGAN.md`](https://github.com/sasateguh/mypii/blob/main/docs/BANDINGAN.md): comparison reports.
- [`docs/LOG-ITERASI.md`](https://github.com/sasateguh/mypii/blob/main/docs/LOG-ITERASI.md): log of every step and measurement.
- [`docs/ANALISIS-RALAT.md`](https://github.com/sasateguh/mypii/blob/main/docs/ANALISIS-RALAT.md): v1 error analysis.
- [`docs/adr/`](https://github.com/sasateguh/mypii/tree/main/docs/adr): decision records.
- [`docs/IAA-SEMAKAN.md`](https://github.com/sasateguh/mypii/blob/main/docs/IAA-SEMAKAN.md): how the human label review works.
- [`docs/PENDEDAHAN-AI.md`](https://github.com/sasateguh/mypii/blob/main/docs/PENDEDAHAN-AI.md): what AI agents did and what humans did.
- [`docs/PROVENANS.md`](https://github.com/sasateguh/mypii/blob/main/docs/PROVENANS.md): seals, archives and redactions.

The pre-registration, comparison reports, iteration log and error analysis are mainly in Malay; their tables and code read the
same in either language.

## v1 dev results (history)

This table was generated before v2 existed, so the `mypii` row is **MyPII v1**. Six baselines are confirmatory (Holm k = 6);
Mistral Small 3.1 and GLM-5.3-Flash are exploratory (ADR-017), not claims.

<!-- jadual-dev:mula -->
<!-- dijana `make readme` (scripts/jana_readme.py) dari hasil/dev-*.json; jangan sunting dengan tangan -->

Split `dev`, 1000 dokumen / documents, padanan tepat / exact match, `semua|*`. Selang = bootstrap 95% (1000 ulangan / resamples, unit `dokumen`). Δ = F1 MyPII tolak F1 sistem / MyPII minus system (negatif = sistem lebih baik / negative = system is better). P/R: `docs/BANDINGAN.md`.

| Sistem / System | F1 | Selang F1 / F1 interval | Δ F1 [selang / interval] |
|---|---|---|---|
| `mypii` | **0.8877** | [0.8701, 0.9037] | rujukan / reference |
| `anthropic/claude-haiku-5-5` | **0.9149** | [0.8979, 0.9312] | -0.0272 [-0.0465, -0.0094] |
| `anthropic/claude-sonnet-5-5` | **0.8782** | [0.8578, 0.8966] | +0.0095 [-0.0086, 0.0268] |
| `cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | **0.7060** | [0.6777, 0.7335] | +0.1817 [0.1591, 0.2028] |
| `cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi / exploratory) | **0.8513** | [0.8290, 0.8710] | +0.0364 [0.0165, 0.0583] |
| `rv/deepseek-ai/DeepSeek-V4.1-Flash` | **0.7193** | [0.6899, 0.7483] | +0.1684 [0.1467, 0.1897] |
| `rv/zai-org/GLM-5.3-Flash` (eksplorasi / exploratory) | **0.8889** | [0.8699, 0.9059] | -0.0012 [-0.0197, 0.0169] |
| `pii-guard` | **0.7209** | [0.6977, 0.7434] | +0.1668 [0.1415, 0.1908] |
| `presidio-asal` | **0.4309** | [0.4078, 0.4554] | +0.4568 [0.4299, 0.4813] |
<!-- jadual-dev:tamat -->

## Cite

Citation metadata lives in [`CITATION.cff`](https://github.com/sasateguh/mypii/blob/main/CITATION.cff) (GitHub shows it as "Cite this repository"). Zenodo DOI for all
versions: [10.5281/zenodo.24014252](https://doi.org/10.5281/zenodo.24014252); version 1.0.0:
[10.5281/zenodo.24014253](https://doi.org/10.5281/zenodo.24014253).

## Bahasa Melayu

MyPII mengesan nombor MyKad, nombor pendaftaran SSM dan nombor telefon Malaysia dalam teks BM, EN dan Manglish, sebagai pengecam
tambahan untuk [Presidio](https://github.com/data-privacy-stack/presidio). Ia berjalan sepenuhnya pada mesin anda: peraturan,
pengesahan (tarikh lahir dan kod tempat lahir JPN, format SSM, libphonenumber) dan satu pengelas konteks kecil (regresi logistik,
numpy). Tiada API luar, jadi teks tidak keluar dari mesin. Repo ini juga membawa MyPII-Bench, penanda aras sintetik untuk menilai
pengecam seperti ini, berserta pra-daftar hipotesis dan arkib setiap larian ujian.

**Pasang dan guna.** `pip install mypii` dan `python -m spacy download en_core_web_sm` (Python 3.11 hingga 3.13), kemudian contoh di
[atas](#example). `semua_pengecam()` dan `all_recognizers()` ialah fungsi yang sama. Konfigurasi `en_core_web_sm` itu sengaja:
`AnalyzerEngine()` lalai memuat turun `en_core_web_lg` (382 MB). Tanpa `entities=`, pengecam asal Presidio turut memulangkan jenis
lain (contohnya `UK_NHS`, `DATE_TIME`) atas nombor yang sama.

**Cara membaca keputusan** (jadual [Results](#results) di atas):
- Hipotesis pra-daftar yang diuji semuanya disokong selepas pembetulan Holm: v1 mengatasi enam garis dasar atas `ujian2` (H1a hingga
  H1f, utama) dan atas `ujian` (H2a hingga H2f, sekunder); v2 tidak kalah kepada Haiku (Δ +0.109) dan mengatasi v1 (Δ +0.393) atas
  `ujian3` (H4a, H4b). Beza v1 dengan Sonnet atas `ujian` kecil (Δ +0.0115) walaupun signifikan. Hipotesis sekunder H3 (setiap
  entiti) belum dilapor.
- v2 menambah normalisasi OCR dalam nombor, nombor yang dipecah baris, kod kawasan Sabah dan Sarawak berkurung, peraturan LLP dan
  pengelas konteks. Atas teks gaya baharu (`dev3`, `ujian3`) ia jauh lebih baik. Atas teks gaya lama (`dev`) ia lebih rendah daripada
  v1 (0.840 lawan 0.888), terutamanya `MY_SSM` (ketepatan 0.51). Tiada versi yang menang di setiap gaya teks, jadi nilai atas data anda
  sendiri dahulu.
- v2 tidak dinilai atas `ujian` dan `ujian2` kerana kedua-dua split itu sudah dibuka untuk v1. Larian v2 di situ sekarang ialah
  analisis selepas kejadian, bukan ujian.

**Had kajian:**
- **Sintetik sepenuhnya.** Teks ditulis LLM dengan slot bertanda, kemudian diisi nilai rekaan, jadi label diketahui tanpa anotasi
  manual. Pembina yang sama menulis penjana data dan pengecam. Keputusan atas teks sebenar belum diukur dan mungkin lebih rendah.
- **Keluarga Claude terlibat di tiga tempat.** Kod ditulis dengan ejen Claude, templat `ujian3` dijana Claude Sonnet, dan Claude Haiku
  ialah pembanding H4a. Arah bias itu menentang MyPII bagi H4a.
- **Semakan label = satu manusia + satu LLM, bukan dua manusia.** Atas sampel 300 dokumen, penyemak manusia mendapati 0.000 span
  salah dan 0.067 [0.027, 0.113] dokumen ada PII yang tidak bertanda. κ tidak bermakna kerana hampir tiada varians.
- **Dapatan semula telefon optimistik.** Label telefon dijana dalam julat sah libphonenumber, pustaka yang sama dipakai pengecam
  ([ADR-002](https://github.com/sasateguh/mypii/blob/main/docs/adr/002-penanda-aras-sintetik.md)).
- **MyPII mengesan span, bukan menilai risiko.** Ia bukan alat anonimisasi lengkap dan bukan bukti pematuhan PDPA.

**Penanda aras.** MyPII-Bench (`data/`, CC-BY-4.0) ada lima split 1000 dokumen setiap satu serta split latihan; kad set data
[`data/README.md`](https://github.com/sasateguh/mypii/blob/main/data/README.md). Split ujian kini awam, jadi model yang dilatih selepas tarikh keluaran mungkin pernah melihatnya;
rentetan canary dalam kad set data membantu pembina model menapisnya. Jawapan LLM disimpan dalam cache yang dikomit, jadi skor garis
dasar boleh dijana semula tanpa kunci API ([`docs/PROVENANS.md`](https://github.com/sasateguh/mypii/blob/main/docs/PROVENANS.md)).

**Petik.** DOI Zenodo semua versi [10.5281/zenodo.24014252](https://doi.org/10.5281/zenodo.24014252); metadata dalam
[`CITATION.cff`](https://github.com/sasateguh/mypii/blob/main/CITATION.cff).

## Licence

Code: MIT ([`LICENSE`](https://github.com/sasateguh/mypii/blob/main/LICENSE)). Dataset (`data/`): CC-BY-4.0. © 2026 Aiman Malib (Sasa Teguh).

Made by [Aiman Malib](https://aimanmalib.com) at [Sasa Teguh](https://sasateguh.com), Malaysia.

## Work with Sasa Teguh

[![Work with Sasa Teguh: book a call](https://raw.githubusercontent.com/sasateguh/.github/main/assets/work-with-sasa-teguh.png)](https://sasateguh.com/book)

This project is built and maintained by [Sasa Teguh](https://sasateguh.com), a studio in Malaysia. We build websites that are found on Google and in AI answers, and we set up systems like this one for businesses.

[Book a call](https://sasateguh.com/book) · hello@sasateguh.com · [More from Sasa Teguh](https://github.com/sasateguh)
