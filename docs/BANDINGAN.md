# Bandingan sistem atas dev-v2 — MyPII lawan garis dasar (PELAN-B B4)

**Apa ini.** MyPII dibanding dengan enam garis dasar atas split **dev-v2** MyPII-Bench (ADR-010): Presidio asal (`presidio-asal`),
pustaka Malaysia sedia ada `malaysia-pii-guard` (`pii-guard`, git dipin `75d6920…`), dua LLM sifar-tembak melalui 9router (ADR-011)
dan dua model Claude melalui API Anthropic terus (`anthropic/claude-sonnet-5-5`, `anthropic/claude-haiku-5-5`; PELAN-CLAUDE, ADR-016). Dua LLM
lain melalui 9router — Mistral Small 3.1 24B dan GLM-5.3-Flash — ditambah sebagai garis dasar **eksplorasi** (pindaan PRA-DAFTAR
2026-11-03, ADR-017; berlabel "(eksplorasi)" dalam setiap jadual): selang + Δ + p mentah sahaja, di luar keluarga Holm (k kekal 6), tiada
hipotesis, dan tidak boleh dinaikkan menjadi dakwaan pengesahan. Setiap angka
dalam blok jana di bawah ialah output `make bandingan` (`mypii/nilai/bandingan.py`, ADR-012) — skor dikira dengan `harness.skor()`
yang sama, LLM dibaca dari cache dikomit (tiada rangkaian), jadi blok itu boleh dijana semula bait demi bait. Masa = `make bandingan-masa`
(fail `hasil/dev-masa.json`, berubah setiap larian).

**Apa ini BUKAN.** Bukan keputusan kertas. dev ialah split yang dipakai semasa menala pengecam MyPII, jadi angka MyPII di sini berat
sebelah ke atas. **Split `ujian` (v1) dan `ujian2` TIDAK dijalankan** — manusia menjalankannya SEKALI sebelum terbit, ikut pra-daftar
(PELAN-C C4). Selang keyakinan + ujian berpasangan: bahagian **Ketidakpastian** di hujung fail (PELAN-C C3b).

## Cara membaca

- **Tepat** = span ramalan sama mula, tamat dan entiti dengan span emas. **Separa** = bertindih dengan span emas entiti sama.
  `*` = semua entiti digabung (mikro). Precision dari sisi ramalan, recall dari sisi emas (`harness.skor`).
- `pii-guard` tiada pengecam SSM: baris `pii-guard` mengira SSM sebagai terlepas (adil kepada pengguna yang memerlukan SSM); baris
  `(disokong …)` menilai emas MyKad + telefon sahaja (adil kepada pustaka itu). Kedua-duanya dilapor; jangan petik satu sahaja.
- **Jenis ralat** (padanan tepat, `bandingan.kelaskan`): *palsu* = ramalan tanpa emas bertindih; *sempadan* = bertindih emas entiti
  sama tetapi mula/tamat lain; *salah jenis* = bertindih emas entiti lain sahaja; *terlepas* = emas tanpa sebarang ramalan bertindih.
  Lajur terakhir = ralat palsu dalam dokumen yang TIADA PII langsung (negatif keras: no. akaun, ahli, polisi, invois, kod produk).
- **Ralat utama** = ralat dikumpul ikut label sebelum span dalam baris yang sama (≤ 3 token terakhir, huruf kecil); lima kumpulan
  terbesar, satu contoh setiap kumpulan. Contoh dari dev sahaja; semua nombor dan nama sintetik.

## Tafsiran (merujuk blok jana; tiada angka baharu di sini)

- **MyPII TIDAK menang atas setiap garis dasar di dev.** Ia menang F1 `*` tepat lawan Presidio asal dan pii-guard (kerana recall)
  dan lawan Llama/DeepSeek (kerana precision; recall hampir sama). **Claude Haiku 5.5 mengatasi MyPII** di dev (F1 `*` lebih tinggi;
  selang Δ berpasangan di bawah sifar sepenuhnya — lihat Ketidakpastian), dan **Claude Sonnet 5.5 tidak boleh dibezakan** daripada
  MyPII di dev (selang Δ `*` merentas 0). Kedua-dua model Claude lebih kuat daripada MyPII untuk MyKad (MY_NRIC), lebih lemah untuk
  telefon; SSM bercampur (Haiku lebih tinggi, Sonnet lebih rendah). Kelemahan MyPII ialah **precision MyKad
  dan SSM**: ralat palsu berkumpul pada nombor ahli/kelab/polisi 12 digit yang diberi label sendiri ("No. Keahlian", "Club Member No.")
  — negatif keras baharu dev-v2 (`NEG_AHLI`) yang tidak pernah ditala (pengecam BEKU dalam PELAN-B). Ini sasaran gelung pengecam
  seterusnya, bukan sesuatu untuk disembunyikan.
- **Presidio asal** tiada pengecam Malaysia: MyKad dan SSM = 0; telefon generiknya menangkap cap masa, no. rujukan dan no. tuntutan 10
  digit sebagai telefon.
- **pii-guard** kuat pada telefon. MyKad: ia melabel nombor akaun bank berbentuk MyKad (`YYMMDD PB ####` selepas "akaun") sebagai MyKad
  dan terlepas MyKad 12 digit tanpa sengkang di bawah label BM ("No. KP", "No. K/P"). Tiada SSM.
- **LLM sifar-tembak** mempunyai recall tinggi tetapi precision rendah: prompt melarang no. akaun/ahli/invois/kod produk, tetapi
  model tetap melabel kod produk berkurung (`(738552-D)`) sebagai SSM dan no. ahli 12 digit sebagai MyKad. Teks Manglish dan BM lebih
  lemah daripada EN untuk Llama dan DeepSeek.
- **Claude** (prompt yang SAMA, tiada penalaan) jauh lebih sedikit ralat palsu MyKad berbanding Llama/DeepSeek — ia membezakan no.
  ahli/polisi 12 digit daripada MyKad lebih baik daripada MyPII. Ralat palsu utamanya ialah kod berkurung berbentuk SSM (kod kempen,
  nama pakej/item) dan, untuk Haiku, telefon di bawah label "tidak sah"/meja automatik. Sonnet tiada emas terlepas tetapi lebih banyak
  ralat palsu daripada Haiku. Haiku mempunyai 2 jawapan rosak (ayat + blok JSON yang penghurai tidak baca; dikira tiada ramalan — LOG
  CLAUDE P4). Suhu tidak boleh dihantar ke API ini (ADR-016) — satu larian, satu titik. Satu prompt + suhu 0 = satu titik, bukan had atas prestasi LLM (ADR-011); prompt TIDAK
  ditala atas dev.
- **Eksplorasi (Mistral Small 3.1, GLM-5.3-Flash; deskriptif sahaja, tiada Holm).** Prompt dan suhu SAMA dengan Llama/DeepSeek. Kedua-dua
  jauh lebih sedikit ralat palsu daripada Llama/DeepSeek (setara MyPII). Mistral: F1 `*` di bawah MyPII (selang Δ di atas 0) kerana
  recall SSM rendah — ia terlepas nombor SSM selepas nama syarikat ("Sdn Bhd (Reg: …)", "… Berhad (…-K)"); ralat palsunya kebanyakan
  telefon (talian/hotline pendek tidak sah) dan nombor rujukan 12 digit sebagai MyKad. GLM-5.3-Flash: F1 `*` tidak boleh dibezakan daripada
  MyPII (selang Δ merentas 0), tiada emas terlepas; lebih kuat daripada MyPII untuk MyKad dan SSM, lebih lemah untuk telefon — corak yang
  sama seperti Claude. Ralat palsu GLM: kod pakej berkurung berbentuk SSM dan telefon di bawah label "tidak sah"/talian. GLM-5.3 juga
  penyemak LLM semakan IAA (keluarga sama; `glm-5.3` ≠ `GLM-5.3-Flash`) — sebut bila memetik kedua-duanya. Opus 5.5 + Fable 5.1 tidak
  dijalankan (gugur kerana had kos USD 20, ADR-017); GPT-5.6-sol + `qd/qmodel` gagal probe (ralat HTTP / tamat masa).
- **Masa/kos.** MyPII dan Presidio asal memakai enjin spaCy yang sama (masa dikuasai NLP, bukan pengecam). pii-guard tanpa NLP — paling
  laju. LLM perlu rangkaian dan satu panggilan setiap dokumen; latensi diukur atas sampel kecil sahaja (Claude tidak diukur latensi —
  belanja tanpa nilai untuk dakwaan). Kos wang Llama/DeepSeek **tidak diukur**: panggilan melalui langganan 9router sedia ada (tiada caj
  setiap panggilan yang boleh dibaca); saiz panggilan dilapor dalam aksara, bukan token. Kos Claude **diukur** dari `usage` respons API
  (lejar dikomit `hasil/cache/llm/anthropic-lejar.json`): 1000 dokumen dev = Haiku 5.5 USD 0.081412 (413725 token masuk, 80079 keluar),
  Sonnet 5.5 USD 1.98471 (413725 masuk, 115726 keluar); jumlah USD 2.066122. MyPII tiada kos setiap panggilan (tempatan).

## Had

- **Sintetik.** Semua dokumen dijana dari templat (manusia + LLM `gemini-3.8-flash` untuk dev-v2); taburan sebenar tidak diketahui.
  Templat dev-v2 dan negatif keras ditulis selepas pengecam ditala atas dev lama — dev-v2 lebih jujur daripada dev lama, tetapi
  bukan set yang tidak pernah dilihat.
- **Label telefon** = julat sah libphonenumber (ADR-002): recall telefon semua sistem terlebih optimis.
- **LLM tidak berketentuan** walaupun suhu 0 (penghala, versi model di sebalik nama yang sama); Claude tanpa suhu langsung (API menolak). Angka LLM = cache dikomit
  `hasil/cache/llm/`; memanggil semula boleh memberi angka lain. Jawapan rosak = tiada ramalan untuk dokumen itu (dikira, ADR-011).
- **Penulis = penala.** Ejen yang menala MyPII juga menulis templat dev dan laporan ini; ujian2 (penjana keluarga berbeza, dimeterai)
  wujud untuk menyemak itu.
- Masa diukur atas hos dikongsi dengan beban lain; ia menunjukkan susunan magnitud sahaja.

## English summary

MyPII is compared with six baselines on the **dev-v2** split of MyPII-Bench: stock Presidio, the existing Malaysian library
`malaysia-pii-guard` (pinned git commit), two zero-shot LLMs via 9router (Llama 3.3 70B and DeepSeek v4.1 Flash, temperature 0) and
two Claude models via the Anthropic API directly (Sonnet 5.5 and Haiku 5.5; temperature cannot be set, thinking disabled), all with
one fixed prompt and answers cached in the repo. Every number in the generated block below comes from `make bandingan`, which reuses the harness
scoring function and reads LLM answers from the committed cache, so it regenerates byte-for-byte without network access. On dev,
MyPII beats stock Presidio and `malaysia-pii-guard` (recall) and Llama/DeepSeek (precision), but **not Claude: Claude Haiku 5.5 scores
higher than MyPII on dev (paired interval entirely below zero), and Claude Sonnet 5.5 is statistically indistinguishable** (interval
spans zero). Both Claude models beat MyPII on MyKad and lose on phone numbers. Two further LLMs via 9router — Mistral Small 3.1 24B and
GLM-5.3-Flash, same prompt — are **exploratory** baselines (ADR-017): reported with intervals and raw p-values only, outside the Holm
family, no hypotheses, not claims. On dev MyPII scores above Mistral (Mistral misses SSM numbers after company names) and is
indistinguishable from GLM-5.3-Flash (interval spans zero; GLM is stronger on MyKad/SSM, weaker on phone). Opus 5.5 and Fable 5.1 were
dropped under the USD 20 cost cap; GPT-5.6-sol and `qd/qmodel` failed the probe. Claude's measured dev cost was USD 2.07 for both models
(ledger committed). MyPII's main weakness is precision on 12-digit membership/policy numbers that
look like MyKad or SSM numbers. Stock Presidio has no Malaysian recognizers. `malaysia-pii-guard` is strong on phone numbers, has no
SSM recognizer (reported both with SSM counted as missed and on supported entities only), and confuses MyKad-shaped bank account
numbers with MyKad. The LLMs have high recall but low precision, labelling product codes and member numbers despite the prompt.
**These are dev numbers, not paper results:** dev was used while tuning MyPII, so its scores are biased upward. The held-out `ujian`
and sealed `ujian2` splits have not been run; a human runs them once before publication, following the pre-registration (PELAN-C).
Limits: synthetic data, phone labels from libphonenumber validity (ADR-002), LLM non-determinism, and the same agent tuned the
recognizers and wrote the dev templates. 9router LLM monetary cost was not measured (existing subscription); call size is reported in characters.

---

<!-- jana:mula -->
<!-- dijana `make bandingan` (mypii/nilai/bandingan.py) — JANGAN sunting dengan tangan -->

Split `dev`: 1000 dok (502 tanpa PII), sha256 `531532cf82a4565b…`.

### Ringkasan — semua bahasa

| sistem | P `*` | R `*` | **F1 `*` tepat** | F1 `*` separa | F1 MY_NRIC | F1 MY_SSM | F1 MY_PHONE |
|---|---|---|---|---|---|---|---|
| `mypii` | 0.7996 | 0.9976 | 0.8877 | 0.8877 | 0.8328 | 0.8054 | 1.0 |
| `presidio-asal` | 0.4629 | 0.4031 | 0.4309 | 0.4412 | 0.0 | 0.0 | 0.6247 |
| `pii-guard` | 0.7617 | 0.6842 | 0.7209 | 0.7309 | 0.6795 | 0.0 | 0.9772 |
| `pii-guard (disokong: MY_NRIC, MY_PHONE)` | 0.7617 | 0.9152 | 0.8314 | 0.843 | 0.6795 | – | 0.9772 |
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 0.559 | 0.9581 | 0.706 | 0.706 | 0.6649 | 0.5876 | 0.8473 |
| `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` | 0.5624 | 0.9976 | 0.7193 | 0.7193 | 0.6757 | 0.627 | 0.8359 |
| `llm:anthropic/claude-sonnet-5-5` | 0.7828 | 1.0 | 0.8782 | 0.8782 | 0.932 | 0.7659 | 0.9176 |
| `llm:anthropic/claude-haiku-5-5` | 0.8501 | 0.9904 | 0.9149 | 0.9149 | 0.9363 | 0.8571 | 0.9357 |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi) | 0.8158 | 0.89 | 0.8513 | 0.8513 | 0.874 | 0.7535 | 0.8776 |
| `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi) | 0.8 | 1.0 | 0.8889 | 0.8889 | 0.8824 | 0.881 | 0.8988 |

### Setiap bahasa — F1 tepat / separa

| sistem | entiti | en (tepat / separa) | ms (tepat / separa) | manglish (tepat / separa) |
|---|---|---|---|---|
| `mypii` | * | 0.8826 / 0.8826 | 0.8784 / 0.8784 | 0.9043 / 0.9043 |
| `mypii` | MY_NRIC | 0.8163 / 0.8163 | 0.8392 / 0.8392 | 0.8406 / 0.8406 |
| `mypii` | MY_SSM | 0.8066 / 0.8066 | 0.7582 / 0.7582 | 0.859 / 0.859 |
| `mypii` | MY_PHONE | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| `presidio-asal` | * | 0.4481 / 0.4562 | 0.4177 / 0.438 | 0.4298 / 0.4298 |
| `presidio-asal` | MY_NRIC | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| `presidio-asal` | MY_SSM | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| `presidio-asal` | MY_PHONE | 0.6509 / 0.6627 | 0.5985 / 0.6277 | 0.6303 / 0.6303 |
| `pii-guard` | * | 0.7283 / 0.7362 | 0.6978 / 0.7185 | 0.74 / 0.74 |
| `pii-guard` | MY_NRIC | 0.7053 / 0.7053 | 0.626 / 0.626 | 0.7149 / 0.7149 |
| `pii-guard` | MY_SSM | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| `pii-guard` | MY_PHONE | 0.9825 / 1.0 | 0.9542 / 1.0 | 1.0 / 1.0 |
| `pii-guard (disokong: MY_NRIC, MY_PHONE)` | * | 0.8506 / 0.8598 | 0.7953 / 0.8189 | 0.8545 / 0.8545 |
| `pii-guard (disokong: MY_NRIC, MY_PHONE)` | MY_NRIC | 0.7053 / 0.7053 | 0.626 / 0.626 | 0.7149 / 0.7149 |
| `pii-guard (disokong: MY_NRIC, MY_PHONE)` | MY_PHONE | 0.9825 / 1.0 | 0.9542 / 1.0 | 1.0 / 1.0 |
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | * | 0.7815 / 0.7815 | 0.6841 / 0.6841 | 0.6658 / 0.6658 |
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | MY_NRIC | 0.7077 / 0.7077 | 0.658 / 0.658 | 0.6397 / 0.6397 |
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | MY_SSM | 0.7157 / 0.7157 | 0.5299 / 0.5299 | 0.5424 / 0.5424 |
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | MY_PHONE | 0.8924 / 0.8924 | 0.8459 / 0.8459 | 0.8047 / 0.8047 |
| `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` | * | 0.7841 / 0.7841 | 0.712 / 0.712 | 0.6701 / 0.6701 |
| `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` | MY_NRIC | 0.7111 / 0.7111 | 0.6859 / 0.6859 | 0.635 / 0.635 |
| `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` | MY_SSM | 0.7449 / 0.7449 | 0.5844 / 0.5844 | 0.5726 / 0.5726 |
| `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` | MY_PHONE | 0.8769 / 0.8769 | 0.8371 / 0.8371 | 0.7939 / 0.7939 |
| `llm:anthropic/claude-sonnet-5-5` | * | 0.9036 / 0.9036 | 0.8791 / 0.8791 | 0.8525 / 0.8525 |
| `llm:anthropic/claude-sonnet-5-5` | MY_NRIC | 0.9467 / 0.9467 | 0.9427 / 0.9427 | 0.9062 / 0.9062 |
| `llm:anthropic/claude-sonnet-5-5` | MY_SSM | 0.8249 / 0.8249 | 0.732 / 0.732 | 0.7444 / 0.7444 |
| `llm:anthropic/claude-sonnet-5-5` | MY_PHONE | 0.9306 / 0.9306 | 0.9291 / 0.9291 | 0.8908 / 0.8908 |
| `llm:anthropic/claude-haiku-5-5` | * | 0.9357 / 0.9357 | 0.9153 / 0.9153 | 0.8943 / 0.8943 |
| `llm:anthropic/claude-haiku-5-5` | MY_NRIC | 0.9341 / 0.9341 | 0.9683 / 0.9683 | 0.9016 / 0.9016 |
| `llm:anthropic/claude-haiku-5-5` | MY_SSM | 0.9091 / 0.9091 | 0.814 / 0.814 | 0.8535 / 0.8535 |
| `llm:anthropic/claude-haiku-5-5` | MY_PHONE | 0.954 / 0.954 | 0.9357 / 0.9357 | 0.9163 / 0.9163 |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi) | * | 0.8881 / 0.8881 | 0.8607 / 0.8607 | 0.8036 / 0.8036 |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi) | MY_NRIC | 0.8791 / 0.8791 | 0.8908 / 0.8908 | 0.85 / 0.85 |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi) | MY_SSM | 0.8438 / 0.8438 | 0.7541 / 0.7541 | 0.6408 / 0.6408 |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi) | MY_PHONE | 0.918 / 0.918 | 0.8819 / 0.8819 | 0.8333 / 0.8333 |
| `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi) | * | 0.902 / 0.902 | 0.9035 / 0.9035 | 0.8595 / 0.8595 |
| `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi) | MY_NRIC | 0.8511 / 0.8511 | 0.9386 / 0.9386 | 0.8488 / 0.8488 |
| `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi) | MY_SSM | 0.9182 / 0.9182 | 0.8659 / 0.8659 | 0.859 / 0.859 |
| `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi) | MY_PHONE | 0.9306 / 0.9306 | 0.8973 / 0.8973 | 0.8689 / 0.8689 |

### Jadual penuh setiap sistem

<details><summary><code>mypii</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 338 | 0.7899 | 1.0 | 0.8826 | 0.7899 | 1.0 | 0.8826 |
| bahasa:en · MY_NRIC | 80 | 116 | 0.6897 | 1.0 | 0.8163 | 0.6897 | 1.0 | 0.8163 |
| bahasa:en · MY_PHONE | 114 | 114 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| bahasa:en · MY_SSM | 73 | 108 | 0.6759 | 1.0 | 0.8066 | 0.6759 | 1.0 | 0.8066 |
| bahasa:manglish · * | 260 | 315 | 0.8254 | 1.0 | 0.9043 | 0.8254 | 1.0 | 0.9043 |
| bahasa:manglish · MY_NRIC | 87 | 120 | 0.725 | 1.0 | 0.8406 | 0.725 | 1.0 | 0.8406 |
| bahasa:manglish · MY_PHONE | 106 | 106 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| bahasa:manglish · MY_SSM | 67 | 89 | 0.7528 | 1.0 | 0.859 | 0.7528 | 1.0 | 0.859 |
| bahasa:ms · * | 309 | 390 | 0.7872 | 0.9935 | 0.8784 | 0.7872 | 0.9935 | 0.8784 |
| bahasa:ms · MY_NRIC | 107 | 148 | 0.723 | 1.0 | 0.8392 | 0.723 | 1.0 | 0.8392 |
| bahasa:ms · MY_PHONE | 131 | 131 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| bahasa:ms · MY_SSM | 71 | 111 | 0.6216 | 0.9718 | 0.7582 | 0.6216 | 0.9718 | 0.7582 |
| semua · * | 836 | 1043 | 0.7996 | 0.9976 | 0.8877 | 0.7996 | 0.9976 | 0.8877 |
| semua · MY_NRIC | 274 | 384 | 0.7135 | 1.0 | 0.8328 | 0.7135 | 1.0 | 0.8328 |
| semua · MY_PHONE | 351 | 351 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| semua · MY_SSM | 211 | 308 | 0.6786 | 0.9905 | 0.8054 | 0.6786 | 0.9905 | 0.8054 |

</details>

<details><summary><code>presidio-asal</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 224 | 0.4911 | 0.412 | 0.4481 | 0.5 | 0.4195 | 0.4562 |
| bahasa:en · MY_NRIC | 80 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| bahasa:en · MY_PHONE | 114 | 224 | 0.4911 | 0.9649 | 0.6509 | 0.5 | 0.9825 | 0.6627 |
| bahasa:en · MY_SSM | 73 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| bahasa:manglish · * | 260 | 224 | 0.4643 | 0.4 | 0.4298 | 0.4643 | 0.4 | 0.4298 |
| bahasa:manglish · MY_NRIC | 87 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| bahasa:manglish · MY_PHONE | 106 | 224 | 0.4643 | 0.9811 | 0.6303 | 0.4643 | 0.9811 | 0.6303 |
| bahasa:manglish · MY_SSM | 67 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| bahasa:ms · * | 309 | 280 | 0.4393 | 0.3981 | 0.4177 | 0.4607 | 0.4175 | 0.438 |
| bahasa:ms · MY_NRIC | 107 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| bahasa:ms · MY_PHONE | 131 | 280 | 0.4393 | 0.9389 | 0.5985 | 0.4607 | 0.9847 | 0.6277 |
| bahasa:ms · MY_SSM | 71 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| semua · * | 836 | 728 | 0.4629 | 0.4031 | 0.4309 | 0.4739 | 0.4127 | 0.4412 |
| semua · MY_NRIC | 274 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| semua · MY_PHONE | 351 | 728 | 0.4629 | 0.9601 | 0.6247 | 0.4739 | 0.9829 | 0.6395 |
| semua · MY_SSM | 211 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

</details>

<details><summary><code>pii-guard</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 241 | 0.7676 | 0.6929 | 0.7283 | 0.7759 | 0.7004 | 0.7362 |
| bahasa:en · MY_NRIC | 80 | 127 | 0.5748 | 0.9125 | 0.7053 | 0.5748 | 0.9125 | 0.7053 |
| bahasa:en · MY_PHONE | 114 | 114 | 0.9825 | 0.9825 | 0.9825 | 1.0 | 1.0 | 1.0 |
| bahasa:en · MY_SSM | 73 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| bahasa:manglish · * | 260 | 240 | 0.7708 | 0.7115 | 0.74 | 0.7708 | 0.7115 | 0.74 |
| bahasa:manglish · MY_NRIC | 87 | 134 | 0.5896 | 0.908 | 0.7149 | 0.5896 | 0.908 | 0.7149 |
| bahasa:manglish · MY_PHONE | 106 | 106 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| bahasa:manglish · MY_SSM | 67 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| bahasa:ms · * | 309 | 270 | 0.7481 | 0.6537 | 0.6978 | 0.7704 | 0.6731 | 0.7185 |
| bahasa:ms · MY_NRIC | 107 | 139 | 0.554 | 0.7196 | 0.626 | 0.554 | 0.7196 | 0.626 |
| bahasa:ms · MY_PHONE | 131 | 131 | 0.9542 | 0.9542 | 0.9542 | 1.0 | 1.0 | 1.0 |
| bahasa:ms · MY_SSM | 71 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| semua · * | 836 | 751 | 0.7617 | 0.6842 | 0.7209 | 0.7723 | 0.6938 | 0.7309 |
| semua · MY_NRIC | 274 | 400 | 0.5725 | 0.8358 | 0.6795 | 0.5725 | 0.8358 | 0.6795 |
| semua · MY_PHONE | 351 | 351 | 0.9772 | 0.9772 | 0.9772 | 1.0 | 1.0 | 1.0 |
| semua · MY_SSM | 211 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

</details>

<details><summary><code>pii-guard (disokong: MY_NRIC, MY_PHONE)</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 194 | 241 | 0.7676 | 0.9536 | 0.8506 | 0.7759 | 0.9639 | 0.8598 |
| bahasa:en · MY_NRIC | 80 | 127 | 0.5748 | 0.9125 | 0.7053 | 0.5748 | 0.9125 | 0.7053 |
| bahasa:en · MY_PHONE | 114 | 114 | 0.9825 | 0.9825 | 0.9825 | 1.0 | 1.0 | 1.0 |
| bahasa:manglish · * | 193 | 240 | 0.7708 | 0.9585 | 0.8545 | 0.7708 | 0.9585 | 0.8545 |
| bahasa:manglish · MY_NRIC | 87 | 134 | 0.5896 | 0.908 | 0.7149 | 0.5896 | 0.908 | 0.7149 |
| bahasa:manglish · MY_PHONE | 106 | 106 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| bahasa:ms · * | 238 | 270 | 0.7481 | 0.8487 | 0.7953 | 0.7704 | 0.8739 | 0.8189 |
| bahasa:ms · MY_NRIC | 107 | 139 | 0.554 | 0.7196 | 0.626 | 0.554 | 0.7196 | 0.626 |
| bahasa:ms · MY_PHONE | 131 | 131 | 0.9542 | 0.9542 | 0.9542 | 1.0 | 1.0 | 1.0 |
| semua · * | 625 | 751 | 0.7617 | 0.9152 | 0.8314 | 0.7723 | 0.928 | 0.843 |
| semua · MY_NRIC | 274 | 400 | 0.5725 | 0.8358 | 0.6795 | 0.5725 | 0.8358 | 0.6795 |
| semua · MY_PHONE | 351 | 351 | 0.9772 | 0.9772 | 0.9772 | 1.0 | 1.0 | 1.0 |

</details>

<details><summary><code>llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 383 | 0.6632 | 0.9513 | 0.7815 | 0.6632 | 0.9513 | 0.7815 |
| bahasa:en · MY_NRIC | 80 | 115 | 0.6 | 0.8625 | 0.7077 | 0.6 | 0.8625 | 0.7077 |
| bahasa:en · MY_PHONE | 114 | 137 | 0.8175 | 0.9825 | 0.8924 | 0.8175 | 0.9825 | 0.8924 |
| bahasa:en · MY_SSM | 73 | 131 | 0.5573 | 1.0 | 0.7157 | 0.5573 | 1.0 | 0.7157 |
| bahasa:manglish · * | 260 | 479 | 0.5136 | 0.9462 | 0.6658 | 0.5136 | 0.9462 | 0.6658 |
| bahasa:manglish · MY_NRIC | 87 | 160 | 0.4938 | 0.908 | 0.6397 | 0.4938 | 0.908 | 0.6397 |
| bahasa:manglish · MY_PHONE | 106 | 150 | 0.6867 | 0.9717 | 0.8047 | 0.6867 | 0.9717 | 0.8047 |
| bahasa:manglish · MY_SSM | 67 | 169 | 0.3787 | 0.9552 | 0.5424 | 0.3787 | 0.9552 | 0.5424 |
| bahasa:ms · * | 309 | 571 | 0.5271 | 0.9741 | 0.6841 | 0.5271 | 0.9741 | 0.6841 |
| bahasa:ms · MY_NRIC | 107 | 200 | 0.505 | 0.9439 | 0.658 | 0.505 | 0.9439 | 0.658 |
| bahasa:ms · MY_PHONE | 131 | 174 | 0.7414 | 0.9847 | 0.8459 | 0.7414 | 0.9847 | 0.8459 |
| bahasa:ms · MY_SSM | 71 | 197 | 0.3604 | 1.0 | 0.5299 | 0.3604 | 1.0 | 0.5299 |
| semua · * | 836 | 1433 | 0.559 | 0.9581 | 0.706 | 0.559 | 0.9581 | 0.706 |
| semua · MY_NRIC | 274 | 475 | 0.5242 | 0.9088 | 0.6649 | 0.5242 | 0.9088 | 0.6649 |
| semua · MY_PHONE | 351 | 461 | 0.7462 | 0.9801 | 0.8473 | 0.7462 | 0.9801 | 0.8473 |
| semua · MY_SSM | 211 | 497 | 0.4185 | 0.9858 | 0.5876 | 0.4185 | 0.9858 | 0.5876 |

</details>

<details><summary><code>llm:rv/deepseek-ai/DeepSeek-V4.1-Flash</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 414 | 0.6449 | 1.0 | 0.7841 | 0.6449 | 1.0 | 0.7841 |
| bahasa:en · MY_NRIC | 80 | 145 | 0.5517 | 1.0 | 0.7111 | 0.5517 | 1.0 | 0.7111 |
| bahasa:en · MY_PHONE | 114 | 146 | 0.7808 | 1.0 | 0.8769 | 0.7808 | 1.0 | 0.8769 |
| bahasa:en · MY_SSM | 73 | 123 | 0.5935 | 1.0 | 0.7449 | 0.5935 | 1.0 | 0.7449 |
| bahasa:manglish · * | 260 | 510 | 0.5059 | 0.9923 | 0.6701 | 0.5059 | 0.9923 | 0.6701 |
| bahasa:manglish · MY_NRIC | 87 | 187 | 0.4652 | 1.0 | 0.635 | 0.4652 | 1.0 | 0.635 |
| bahasa:manglish · MY_PHONE | 106 | 156 | 0.6667 | 0.9811 | 0.7939 | 0.6667 | 0.9811 | 0.7939 |
| bahasa:manglish · MY_SSM | 67 | 167 | 0.4012 | 1.0 | 0.5726 | 0.4012 | 1.0 | 0.5726 |
| bahasa:ms · * | 309 | 559 | 0.5528 | 1.0 | 0.712 | 0.5528 | 1.0 | 0.712 |
| bahasa:ms · MY_NRIC | 107 | 205 | 0.522 | 1.0 | 0.6859 | 0.522 | 1.0 | 0.6859 |
| bahasa:ms · MY_PHONE | 131 | 182 | 0.7198 | 1.0 | 0.8371 | 0.7198 | 1.0 | 0.8371 |
| bahasa:ms · MY_SSM | 71 | 172 | 0.4128 | 1.0 | 0.5844 | 0.4128 | 1.0 | 0.5844 |
| semua · * | 836 | 1483 | 0.5624 | 0.9976 | 0.7193 | 0.5624 | 0.9976 | 0.7193 |
| semua · MY_NRIC | 274 | 537 | 0.5102 | 1.0 | 0.6757 | 0.5102 | 1.0 | 0.6757 |
| semua · MY_PHONE | 351 | 484 | 0.7211 | 0.9943 | 0.8359 | 0.7211 | 0.9943 | 0.8359 |
| semua · MY_SSM | 211 | 462 | 0.4567 | 1.0 | 0.627 | 0.4567 | 1.0 | 0.627 |

</details>

<details><summary><code>llm:anthropic/claude-sonnet-5-5</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 324 | 0.8241 | 1.0 | 0.9036 | 0.8241 | 1.0 | 0.9036 |
| bahasa:en · MY_NRIC | 80 | 89 | 0.8989 | 1.0 | 0.9467 | 0.8989 | 1.0 | 0.9467 |
| bahasa:en · MY_PHONE | 114 | 131 | 0.8702 | 1.0 | 0.9306 | 0.8702 | 1.0 | 0.9306 |
| bahasa:en · MY_SSM | 73 | 104 | 0.7019 | 1.0 | 0.8249 | 0.7019 | 1.0 | 0.8249 |
| bahasa:manglish · * | 260 | 350 | 0.7429 | 1.0 | 0.8525 | 0.7429 | 1.0 | 0.8525 |
| bahasa:manglish · MY_NRIC | 87 | 105 | 0.8286 | 1.0 | 0.9062 | 0.8286 | 1.0 | 0.9062 |
| bahasa:manglish · MY_PHONE | 106 | 132 | 0.803 | 1.0 | 0.8908 | 0.803 | 1.0 | 0.8908 |
| bahasa:manglish · MY_SSM | 67 | 113 | 0.5929 | 1.0 | 0.7444 | 0.5929 | 1.0 | 0.7444 |
| bahasa:ms · * | 309 | 394 | 0.7843 | 1.0 | 0.8791 | 0.7843 | 1.0 | 0.8791 |
| bahasa:ms · MY_NRIC | 107 | 120 | 0.8917 | 1.0 | 0.9427 | 0.8917 | 1.0 | 0.9427 |
| bahasa:ms · MY_PHONE | 131 | 151 | 0.8675 | 1.0 | 0.9291 | 0.8675 | 1.0 | 0.9291 |
| bahasa:ms · MY_SSM | 71 | 123 | 0.5772 | 1.0 | 0.732 | 0.5772 | 1.0 | 0.732 |
| semua · * | 836 | 1068 | 0.7828 | 1.0 | 0.8782 | 0.7828 | 1.0 | 0.8782 |
| semua · MY_NRIC | 274 | 314 | 0.8726 | 1.0 | 0.932 | 0.8726 | 1.0 | 0.932 |
| semua · MY_PHONE | 351 | 414 | 0.8478 | 1.0 | 0.9176 | 0.8478 | 1.0 | 0.9176 |
| semua · MY_SSM | 211 | 340 | 0.6206 | 1.0 | 0.7659 | 0.6206 | 1.0 | 0.7659 |

</details>

<details><summary><code>llm:anthropic/claude-haiku-5-5</code></summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 293 | 0.8942 | 0.9813 | 0.9357 | 0.8942 | 0.9813 | 0.9357 |
| bahasa:en · MY_NRIC | 80 | 87 | 0.8966 | 0.975 | 0.9341 | 0.8966 | 0.975 | 0.9341 |
| bahasa:en · MY_PHONE | 114 | 125 | 0.912 | 1.0 | 0.954 | 0.912 | 1.0 | 0.954 |
| bahasa:en · MY_SSM | 73 | 81 | 0.8642 | 0.9589 | 0.9091 | 0.8642 | 0.9589 | 0.9091 |
| bahasa:manglish · * | 260 | 317 | 0.8139 | 0.9923 | 0.8943 | 0.8139 | 0.9923 | 0.8943 |
| bahasa:manglish · MY_NRIC | 87 | 106 | 0.8208 | 1.0 | 0.9016 | 0.8208 | 1.0 | 0.9016 |
| bahasa:manglish · MY_PHONE | 106 | 121 | 0.8595 | 0.9811 | 0.9163 | 0.8595 | 0.9811 | 0.9163 |
| bahasa:manglish · MY_SSM | 67 | 90 | 0.7444 | 1.0 | 0.8535 | 0.7444 | 1.0 | 0.8535 |
| bahasa:ms · * | 309 | 364 | 0.8462 | 0.9968 | 0.9153 | 0.8462 | 0.9968 | 0.9153 |
| bahasa:ms · MY_NRIC | 107 | 114 | 0.9386 | 1.0 | 0.9683 | 0.9386 | 1.0 | 0.9683 |
| bahasa:ms · MY_PHONE | 131 | 149 | 0.8792 | 1.0 | 0.9357 | 0.8792 | 1.0 | 0.9357 |
| bahasa:ms · MY_SSM | 71 | 101 | 0.6931 | 0.9859 | 0.814 | 0.6931 | 0.9859 | 0.814 |
| semua · * | 836 | 974 | 0.8501 | 0.9904 | 0.9149 | 0.8501 | 0.9904 | 0.9149 |
| semua · MY_NRIC | 274 | 307 | 0.886 | 0.9927 | 0.9363 | 0.886 | 0.9927 | 0.9363 |
| semua · MY_PHONE | 351 | 395 | 0.8835 | 0.9943 | 0.9357 | 0.8835 | 0.9943 | 0.9357 |
| semua · MY_SSM | 211 | 272 | 0.761 | 0.981 | 0.8571 | 0.761 | 0.981 | 0.8571 |

</details>

<details><summary><code>llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct</code> (eksplorasi)</summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 287 | 0.8571 | 0.9213 | 0.8881 | 0.8571 | 0.9213 | 0.8881 |
| bahasa:en · MY_NRIC | 80 | 102 | 0.7843 | 1.0 | 0.8791 | 0.7843 | 1.0 | 0.8791 |
| bahasa:en · MY_PHONE | 114 | 130 | 0.8615 | 0.9825 | 0.918 | 0.8615 | 0.9825 | 0.918 |
| bahasa:en · MY_SSM | 73 | 55 | 0.9818 | 0.7397 | 0.8438 | 0.9818 | 0.7397 | 0.8438 |
| bahasa:manglish · * | 260 | 295 | 0.7559 | 0.8577 | 0.8036 | 0.7559 | 0.8577 | 0.8036 |
| bahasa:manglish · MY_NRIC | 87 | 113 | 0.7522 | 0.977 | 0.85 | 0.7522 | 0.977 | 0.85 |
| bahasa:manglish · MY_PHONE | 106 | 146 | 0.7192 | 0.9906 | 0.8333 | 0.7192 | 0.9906 | 0.8333 |
| bahasa:manglish · MY_SSM | 67 | 36 | 0.9167 | 0.4925 | 0.6408 | 0.9167 | 0.4925 | 0.6408 |
| bahasa:ms · * | 309 | 330 | 0.8333 | 0.89 | 0.8607 | 0.8333 | 0.89 | 0.8607 |
| bahasa:ms · MY_NRIC | 107 | 122 | 0.8361 | 0.9533 | 0.8908 | 0.8361 | 0.9533 | 0.8908 |
| bahasa:ms · MY_PHONE | 131 | 157 | 0.8089 | 0.9695 | 0.8819 | 0.8089 | 0.9695 | 0.8819 |
| bahasa:ms · MY_SSM | 71 | 51 | 0.902 | 0.6479 | 0.7541 | 0.902 | 0.6479 | 0.7541 |
| semua · * | 836 | 912 | 0.8158 | 0.89 | 0.8513 | 0.8158 | 0.89 | 0.8513 |
| semua · MY_NRIC | 274 | 337 | 0.7923 | 0.9745 | 0.874 | 0.7923 | 0.9745 | 0.874 |
| semua · MY_PHONE | 351 | 433 | 0.7945 | 0.9801 | 0.8776 | 0.7945 | 0.9801 | 0.8776 |
| semua · MY_SSM | 211 | 142 | 0.9366 | 0.6303 | 0.7535 | 0.9366 | 0.6303 | 0.7535 |

</details>

<details><summary><code>llm:rv/zai-org/GLM-5.3-Flash</code> (eksplorasi)</summary>

| kumpulan · entiti | emas | ramal | P tepat | R tepat | F1 tepat | P separa | R separa | F1 separa |
|---|---|---|---|---|---|---|---|---|
| bahasa:en · * | 267 | 325 | 0.8215 | 1.0 | 0.902 | 0.8215 | 1.0 | 0.902 |
| bahasa:en · MY_NRIC | 80 | 108 | 0.7407 | 1.0 | 0.8511 | 0.7407 | 1.0 | 0.8511 |
| bahasa:en · MY_PHONE | 114 | 131 | 0.8702 | 1.0 | 0.9306 | 0.8702 | 1.0 | 0.9306 |
| bahasa:en · MY_SSM | 73 | 86 | 0.8488 | 1.0 | 0.9182 | 0.8488 | 1.0 | 0.9182 |
| bahasa:manglish · * | 260 | 345 | 0.7536 | 1.0 | 0.8595 | 0.7536 | 1.0 | 0.8595 |
| bahasa:manglish · MY_NRIC | 87 | 118 | 0.7373 | 1.0 | 0.8488 | 0.7373 | 1.0 | 0.8488 |
| bahasa:manglish · MY_PHONE | 106 | 138 | 0.7681 | 1.0 | 0.8689 | 0.7681 | 1.0 | 0.8689 |
| bahasa:manglish · MY_SSM | 67 | 89 | 0.7528 | 1.0 | 0.859 | 0.7528 | 1.0 | 0.859 |
| bahasa:ms · * | 309 | 375 | 0.824 | 1.0 | 0.9035 | 0.824 | 1.0 | 0.9035 |
| bahasa:ms · MY_NRIC | 107 | 121 | 0.8843 | 1.0 | 0.9386 | 0.8843 | 1.0 | 0.9386 |
| bahasa:ms · MY_PHONE | 131 | 161 | 0.8137 | 1.0 | 0.8973 | 0.8137 | 1.0 | 0.8973 |
| bahasa:ms · MY_SSM | 71 | 93 | 0.7634 | 1.0 | 0.8659 | 0.7634 | 1.0 | 0.8659 |
| semua · * | 836 | 1045 | 0.8 | 1.0 | 0.8889 | 0.8 | 1.0 | 0.8889 |
| semua · MY_NRIC | 274 | 347 | 0.7896 | 1.0 | 0.8824 | 0.7896 | 1.0 | 0.8824 |
| semua · MY_PHONE | 351 | 430 | 0.8163 | 1.0 | 0.8988 | 0.8163 | 1.0 | 0.8988 |
| semua · MY_SSM | 211 | 268 | 0.7873 | 1.0 | 0.881 | 0.7873 | 1.0 | 0.881 |

</details>

### Ralat (padanan tepat) — kiraan

| sistem | palsu | sempadan | salah jenis | terlepas | dok negatif berisi ramalan / span (daripada 502) |
|---|---|---|---|---|---|
| `mypii` | 208 (NRIC 109 · SSM 99 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 1 (NRIC 1 · SSM 0 · PHONE 0) | 2 (NRIC 0 · SSM 2 · PHONE 0) | 152 / 167 |
| `presidio-asal` | 353 (NRIC 0 · SSM 0 · PHONE 353) | 8 (NRIC 0 · SSM 0 · PHONE 8) | 30 (NRIC 0 · SSM 0 · PHONE 30) | 461 (NRIC 246 · SSM 209 · PHONE 6) | 208 / 262 |
| `pii-guard` | 171 (NRIC 171 · SSM 0 · PHONE 0) | 8 (NRIC 0 · SSM 0 · PHONE 8) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 256 (NRIC 45 · SSM 211 · PHONE 0) | 136 / 139 |
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 629 (NRIC 223 · SSM 289 · PHONE 117) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 3 (NRIC 3 · SSM 0 · PHONE 0) | 32 (NRIC 25 · SSM 1 · PHONE 6) | 357 / 565 |
| `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` | 649 (NRIC 263 · SSM 251 · PHONE 135) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 2 (NRIC 0 · SSM 0 · PHONE 2) | 339 / 597 |
| `llm:anthropic/claude-sonnet-5-5` | 232 (NRIC 40 · SSM 129 · PHONE 63) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 173 / 210 |
| `llm:anthropic/claude-haiku-5-5` | 146 (NRIC 35 · SSM 65 · PHONE 46) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 8 (NRIC 2 · SSM 4 · PHONE 2) | 103 / 132 |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi) | 168 (NRIC 70 · SSM 9 · PHONE 89) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 92 (NRIC 7 · SSM 78 · PHONE 7) | 119 / 143 |
| `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi) | 209 (NRIC 73 · SSM 57 · PHONE 79) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 0 (NRIC 0 · SSM 0 · PHONE 0) | 143 / 173 |

### Ralat utama setiap sistem

#### `mypii`

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `no keahlian` | 11 | MY_NRIC 3, MY_SSM 8 | …a Unggul Services Trading ⏎ No. Keahlian: «111031613598» ⏎ Kod Diskaun: (914207-D) ⏎ No. Rujukan: 16… (mypii-00128) |
| `club member no` | 9 | MY_NRIC 8, MY_SSM 1 | …Kuala Selangor ⏎ Loyalty Club Member No.: «202002596383» ⏎ Deposit paid via online transfer to ban… (mypii-00022) |
| `club member id` | 7 | MY_NRIC 6, MY_SSM 1 | …ah: ⏎ Guest Name: Tan Lee ⏎ Club Member ID: «201704581830» ⏎ Receipt Ref: 201603623219 ⏎ Emergency con… (mypii-00453) |
| `luput polisi pembekal` | 7 | MY_NRIC 6, MY_SSM 1 | …23 sebelum tarikh luput polisi pembekal «720523984174». ⏎ Penghantaran dijadualkan pada 250715 2… (mypii-00546) |
| `no keahlian rebat` | 6 | MY_NRIC 4, MY_SSM 2 | …Kontrak: 7895098029 ⏎ No. Keahlian Rebat: «470414056927» ⏎ Hubungi talian aduan: 03-615 26 ⏎ Bacaan … (mypii-00015) |

*Emas terlepas — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `(tiada label)` | 1 | MY_SSM 1 | …TARAN ⏎ Kencana Unggul Services Trading ⏎ ( «296402-X» ) (mypii-03327) |
| `impian rekabentuk trading` | 1 | MY_SSM 1 | …h: Cemerlang Impian Rekabentuk Trading («30402-F») ⏎ Untuk: En/Puan Maisarah Maryam binti T… (mypii-02715) |

#### `presidio-asal`

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `timestamp` | 15 | MY_PHONE 15 | … for weekend stay in Chukai. ⏎ Timestamp: «260426 0254» ⏎ Promo voucher applied: (775189-B) ⏎ For u… (mypii-00033) |
| `no rujukan` | 8 | MY_PHONE 8 | …70 ⏎ Kod Diskaun: (738552-D) ⏎ No. Rujukan: «3361830217» ⏎ Nikmati diskaun 15% untuk penginapan di… (mypii-00092) |
| `(tiada label)` | 5 | MY_PHONE 5 | «[02-11-2025»] admin: parents yg belum send ic anak p… (mypii-00897) |
| `no tuntutan` | 5 | MY_PHONE 5 | …an Gemilang Logistics PLT ⏎ No. Tuntutan: «9315339723» ⏎ No. Bil Pembelian: 319642210577 ⏎ No. Dih… (mypii-00718) |
| `ref no` | 5 | MY_PHONE 5 | …race Toh ⏎ No K/P: 030411-71-4329 ⏎ Ref No: «9010084099» ⏎ Deposit elektrik RM 200 akan dipulangka… (mypii-00496) |

*Emas terlepas — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `no kad pengenalan` | 30 | MY_NRIC 30 | …Penuh: Aisyah Chong ⏎ No. Kad Pengenalan: «871031 79 9114» ⏎ Majikan: Intan Gemilang Logistics PLT (… (mypii-00087) |
| `no k/p` | 29 | MY_NRIC 29 | …: Saiful Bahari bin Aniq Hazim ⏎ No. K/P: «581206 31 4029» ⏎ No. Sijil: 901029632352 ⏎ Penama baharu t… (mypii-00101) |
| `no kp` | 9 | MY_NRIC 9 | …aris Zulhilmi bin Rayyan Zafran ⏎ No. KP: «540208358202» ⏎ No. Telefon: +60 199038918 ⏎ Tarikh Dafta… (mypii-01676) |
| `sdn bhd ssm` | 9 | MY_SSM 9 | …Inovasi Utuh Kejuruteraan Sdn Bhd (SSM: «494751-M») ⏎ Employee Name: Tay Tian Le ⏎ NRIC: 07122… (mypii-01015) |
| `ic` | 7 | MY_NRIC 7 | …firm ya. ⏎ Contact person: Rajesh Tan ⏎ IC: «930129626905» ⏎ No fon: 016 417 2573 ⏎ Deposit dah transf… (mypii-00085) |

#### `pii-guard`

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `(tiada label)` | 6 | MY_NRIC 6 | Acct No           Amount ⏎ «631028 61 2849»    RM 1,200 ⏎ 64132598318566    RM 640 (mypii-00327) |
| `ke akaun pembekal` | 6 | MY_NRIC 6 | …la buat bayaran terus ke akaun pembekal «000815 46 4123» sebelum tarikh luput polisi pembekal 72… (mypii-00546) |
| `to bank account` | 6 | MY_NRIC 6 | …aid via online transfer to bank account «740101 23 8234». Ref: 697612-08-2786. ⏎ For catering pack… (mypii-00022) |
| `ke nombor akaun` | 5 | MY_NRIC 5 | …n akan disalurkan terus ke nombor akaun «970721 68 8948». (mypii-00718) |
| `bayaran akaun bank` | 4 | MY_NRIC 4 | …728-922-6222 ⏎ Kaedah Bayaran: Akaun Bank «010504 32 7828» ⏎ No. Khidmat Pelanggan: 03-488 51 ⏎ Status… (mypii-00671) |

*Emas terlepas — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `sdn bhd ssm` | 9 | MY_SSM 9 | …Inovasi Utuh Kejuruteraan Sdn Bhd (SSM: «494751-M») ⏎ Employee Name: Tay Tian Le ⏎ NRIC: 07122… (mypii-01015) |
| `no kp` | 7 | MY_NRIC 7 | …aris Zulhilmi bin Rayyan Zafran ⏎ No. KP: «540208358202» ⏎ No. Telefon: +60 199038918 ⏎ Tarikh Dafta… (mypii-01676) |
| `sdn bhd reg` | 7 | MY_SSM 7 | …n Rangkaian Maya Infiniti Sdn Bhd (Reg: «699754-X») ⏎ Nama Pemilik: Awang bin Abdullah ⏎ No K/… (mypii-00348) |
| `no k/p` | 6 | MY_NRIC 6 | …se: ⏎ Nama Pelanggan: Hafiz Chong ⏎ No K/P: «810117848230» ⏎ Ref No: 930715-20-5067 ⏎ Deposit elektrik… (mypii-00793) |
| `no kad pengenalan` | 6 | MY_NRIC 6 | …amu: Chow Chao Feng ⏎ No. Kad Pengenalan: «680201223519» ⏎ No. Telefon: 0111976 0573 ⏎ Lokasi: Dewan… (mypii-00313) |

#### `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast`

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `ganti model x` | 9 | MY_SSM 9 | … 201703633351 ⏎ Item: Alat Ganti Model X («203455-D») - 50 unit ⏎ Sila buat bayaran terus ke a… (mypii-00546) |
| `kod diskaun` | 9 | MY_SSM 9 | …o. Keahlian: 313263847370 ⏎ Kod Diskaun: («738552-D») ⏎ No. Rujukan: 3361830217 ⏎ Nikmati diskau… (mypii-00092) |
| `no keahlian` | 9 | MY_NRIC 9 | …a Unggul Services Trading ⏎ No. Keahlian: «111031613598» ⏎ Kod Diskaun: (914207-D) ⏎ No. Rujukan: 16… (mypii-00128) |
| `tag item code` | 9 | MY_SSM 9 | … Acc: 6403134999763 ⏎ Bib tag item code: («879083-C»). See you at the flag-off line! (mypii-00494) |
| `item` | 8 | MY_SSM 8 | item «178193-P» x1 rm5, item 859091-B x2 rm9 (mypii-00585) |

*Emas terlepas — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `lc n0` | 2 | MY_NRIC 2 | lC N0 «870413723476» HP 012 4754108 (mypii-01770) |
| `no kad pengenalan` | 2 | MY_NRIC 2 | …emohon: Koh Tian Le ⏎ No. Kad Pengenalan: «031114 88 9160» ⏎ No. Telefon: 0172662408 ⏎ Alamat: Kuala S… (mypii-03340) |
| `anak malang ic` | 1 | MY_NRIC 1 | …cation ⏎ Patient: Selung anak Malang (IC: «991118563922») ⏎ Employer: Mekar Wangi Perabot Berhad \|… (mypii-03151) |
| `bin affan hanif` | 1 | MY_NRIC 1 | …8505520089	Thaqif Ezzat bin Affan Hanif	«590819 02 7278» (mypii-01146) |
| `bin hassan nric` | 1 | MY_NRIC 1 | …hor Bahru: ⏎ Hi Kok Wai bin Hassan (NRIC: «721207840249»), your vehicle inspection certificate e… (mypii-02145) |

#### `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash`

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `tarikh transaksi` | 9 | MY_NRIC 8, MY_SSM 1 | …. Resit: 818084318487 ⏎ Tarikh Transaksi: «250529-154-5889» ⏎ Saluran Bayaran: Pindahan Bank ke Akaun… (mypii-00182) |
| `kod diskaun` | 8 | MY_SSM 8 | …o. Keahlian: 313263847370 ⏎ Kod Diskaun: («738552-D») ⏎ No. Rujukan: 3361830217 ⏎ Nikmati diskau… (mypii-00092) |
| `processed on` | 8 | MY_NRIC 7, MY_SSM 1 | … Services Sdn Bhd Sri Aman ⏎ Processed on «250629-971-8133». Helplink call 04235700 for verificatio… (mypii-00488) |
| `katering pakej melur` | 7 | MY_SSM 7 | …ngesahan Tempahan Katering Pakej Melur («266643-C») ⏎ No. Invois: 211844365653 ⏎ Bayaran depos… (mypii-00534) |
| `ke akaun pada` | 7 | MY_NRIC 7 | …ipindahkan ke akaun 950522 26 3179 pada «31102025-563». ⏎ Status: Tempahan disahkan untuk 150 ke… (mypii-00500) |

*Emas terlepas — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `contact me at` | 1 | MY_PHONE 1 | …all branch Sibu or direct contact me at «03-8318 6366» ya. Ref: INV202310991538. (mypii-00742) |
| `la bro cuba` | 1 | MY_PHONE 1 | … 03-200 55 tu no tak cukup la bro, cuba «09-791 3627» (mypii-00799) |

#### `llm:anthropic/claude-sonnet-5-5`

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `kod kempen` | 8 | MY_SSM 8 | …t ke akaun: 790428 50 0345 ⏎ Kod Kempen: («476044-U») ⏎ Timestamp: 250304 2356 ⏎ Semoga murah re… (mypii-00800) |
| `katering pakej melur` | 7 | MY_SSM 7 | …ngesahan Tempahan Katering Pakej Melur («266643-C») ⏎ No. Invois: 211844365653 ⏎ Bayaran depos… (mypii-00534) |
| `ganti model x` | 6 | MY_SSM 6 | … 201703633351 ⏎ Item: Alat Ganti Model X («203455-D») - 50 unit ⏎ Sila buat bayaran terus ke a… (mypii-00546) |
| `kod tag` | 6 | MY_SSM 6 | …p Masa Acara Berbasikal Kapit: ⏎ Kod Tag («473544-C») diterima pada 202604299162. ⏎ No. Siri P… (mypii-03267) |
| `item insulin glargine` | 5 | MY_SSM 5 | …INV201781612765 ⏎ Item: Insulin Glargine («948223-F») qty 10 box. ⏎ Branch: Citra Perkasa PLT … (mypii-00102) |

*Emas terlepas: tiada.*

#### `llm:anthropic/claude-haiku-5-5`

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `katering pakej melur` | 7 | MY_SSM 7 | …ngesahan Tempahan Katering Pakej Melur («266643-C») ⏎ No. Invois: 211844365653 ⏎ Bayaran depos… (mypii-00534) |
| `dihubungi tidak sah` | 5 | MY_PHONE 5 | …: 319642210577 ⏎ No. Dihubungi Tidak Sah: «018-545 833057» ⏎ Bayaran pampasan akan disalurkan terus … (mypii-00718) |
| `kod kempen` | 5 | MY_SSM 5 | …t ke akaun: 790428 50 0345 ⏎ Kod Kempen: («476044-U») ⏎ Timestamp: 250304 2356 ⏎ Semoga murah re… (mypii-00800) |
| `no meter` | 4 | MY_SSM 4 | …R AIR - Bina Jaya Resources ⏎ No. Meter: («961646-K») ⏎ No. Kontrak: 610918746076 ⏎ No. Keahlian… (mypii-00783) |
| `automated desk at` | 3 | MY_PHONE 3 | …fication, contact our automated desk at «019-564 427761» or log on to Harmoni Cipta Teknik Sdn B… (mypii-00768) |

*Emas terlepas — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `enterprise reg no` | 2 | MY_SSM 2 | …anga Mekar Landskap Enterprise (Reg No: «125644-X»), hereby appoint Nabila Anis binti Hazi… (mypii-01382) |
| `anak jalong nric` | 1 | MY_NRIC 1 | …hereby appoint Priya anak Jalong (NRIC: «700511099238») as our authorized tender representativ… (mypii-01642) |
| `duitnow id` | 1 | MY_PHONE 1 | …! ⏎ To: Mei Ling bin Abdullah ⏎ DuitNow ID: «04-920 3107» ⏎ Acc no: 660526157730 ⏎ Tarikh trf: 24 Feb… (mypii-03896) |
| `duitnow id mobile` | 1 | MY_PHONE 1 | …ima: Woon Pei Shan ⏎ DuitNow ID (Mobile): «09-248 7512» ⏎ Recipient IC: 531201 71 3232 ⏎ Ref No: 12… (mypii-02268) |
| `emas kejuruteraan berhad` | 1 | MY_SSM 1 | …Balik Saujana Emas Kejuruteraan Berhad («43026-F») ⏎ Nama: Toh Guan Peng ⏎ No. MyKad: 500312 … (mypii-01620) |

#### `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi)

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `donor reference` | 6 | MY_NRIC 6 | … Receipt: 201604125582 ⏎ Donor Reference: «791105661169» ⏎ Credited into Account: 620717605462 ⏎ Tim… (mypii-00115) |
| `hubungi talian teknikal` | 5 | MY_PHONE 5 | … 202306106042. ⏎ Hubungi talian teknikal: «03184989». (mypii-00421) |
| `on helplink call` | 5 | MY_PHONE 5 | …rocessed on 20092025-060. Helplink call «012-30682» for verification. (mypii-00102) |
| `try call number` | 5 | MY_PHONE 5 | …ince 260324 1147. Rider try call number «015-949 6509» but line cut off. If barang pecah, plea… (mypii-00936) |
| `call hotline office` | 4 | MY_PHONE 4 | …080. ⏎ Kalu ada issue call hotline office «03-653 82» masa office hours. (mypii-00268) |

*Emas terlepas — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `sdn bhd reg` | 4 | MY_SSM 4 | …under Bitara Maya Inovasi Sdn Bhd (Reg: «1562139-A»). ⏎ Lead traveler: Rajesh Ng ⏎ Emergency co… (mypii-01077) |
| `bhd reg no` | 3 | MY_SSM 3 | …aya Terbilang Services Sdn Bhd (Reg No: «545903-K») ⏎ Tarikh debit: 27-03-2025 11102025-933 ⏎ … (mypii-00331) |
| `bhd travel tours` | 3 | MY_SSM 3 | …rsatu Solutions Sdn Bhd Travel & Tours («202306507921») ⏎ Booking Confirmation for Azimah Anis b… (mypii-03015) |
| `kasturi resources berhad` | 3 | MY_SSM 3 | Selasih Kasturi Resources Berhad («841647-K») d0kumen sah (mypii-00810) |
| `murni hardware berhad` | 3 | MY_SSM 3 | Serantau Murni Hardware Berhad («757986-H») d0kumen sah (mypii-01232) |

#### `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi)

*Ramalan palsu (tiada emas bertindih) — label sebelum span, kumpulan teratas:*

| label | bil | entiti | contoh (dev) |
|---|---|---|---|
| `katering pakej melur` | 7 | MY_SSM 7 | …ngesahan Tempahan Katering Pakej Melur («266643-C») ⏎ No. Invois: 211844365653 ⏎ Bayaran depos… (mypii-00534) |
| `dihubungi tidak sah` | 5 | MY_PHONE 5 | …: 319642210577 ⏎ No. Dihubungi Tidak Sah: «018-545 833057» ⏎ Bayaran pampasan akan disalurkan terus … (mypii-00718) |
| `hubungi talian aduan` | 5 | MY_PHONE 5 | …bat: 470414056927 ⏎ Hubungi talian aduan: «03-615 26» ⏎ Bacaan semasa menunjukkan penggunaan 32… (mypii-00015) |
| `hubungi talian teknikal` | 5 | MY_PHONE 5 | … 202306106042. ⏎ Hubungi talian teknikal: «03184989». (mypii-00421) |
| `try call number` | 5 | MY_PHONE 5 | …ince 260324 1147. Rider try call number «015-949 6509» but line cut off. If barang pecah, plea… (mypii-00936) |

*Emas terlepas: tiada.*

### Masa dan saiz panggilan

Diukur 2026-10-30T09:06:58Z (hos dikongsi — angka kasar, bukan penanda aras prestasi).

| sistem | dokumen | saat (termasuk memuat enjin) | ms / dok |
|---|---|---|---|
| `mypii` | 1000 | 24.12 | 24.1 |
| `presidio-asal` | 1000 | 20.6 | 20.6 |
| `pii-guard` | 1000 | 0.4 | 0.4 |

Latensi LLM — sampel dokumen dev pertama ikut `id`, bersiri, satu panggilan setiap dokumen (cache tidak ditulis):

| sistem | sampel | gagal | median s | maks s |
|---|---|---|---|---|
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 20 | 0 | 0.93 | 1.59 |
| `llm:cbcn/deepseek-v4.1-flash` | 20 | 0 | 1.67 | 2.27 |

Saiz panggilan LLM atas 1000 dok (dari cache dikomit; aksara, bukan token):

| sistem | aksara masuk | aksara keluar |
|---|---|---|
| `llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 985670 | 69768 |
| `llm:rv/deepseek-ai/DeepSeek-V4.1-Flash` | 985670 | 73234 |
| `llm:anthropic/claude-sonnet-5-5` | 985670 | 264938 |
| `llm:anthropic/claude-haiku-5-5` | 985670 | 174643 |
| `llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct` (eksplorasi) | 985670 | 58492 |
| `llm:rv/zai-org/GLM-5.3-Flash` (eksplorasi) | 985670 | 50276 |
<!-- jana:tamat -->

## Ketidakpastian (PELAN-C C3b)

**Apa ini.** Berapa banyak skor dev di atas akan bergoyang jika 1,000 dokumen dev diganti dengan 1,000 dokumen lain dari taburan
yang sama. Blok di bawah dijana oleh `make statistik` (ADR-006 §Statistik, ADR-013) dari ramalan per dokumen yang ditulis `make nilai-garis`
(LLM dari cache dikomit, tanpa kunci 9router) — setiap angka ialah `hasil/dev-statistik.json`, dikomit; tiada angka ditulis tangan.

**Cara membaca.**
- **CI** = selang persentil bootstrap: dokumen (bukan span) disampel semula dengan ganti, setiap sampel dinilai dengan `harness.skor()`.
  Span dalam satu dokumen berkongsi templat, jadi menyampel span akan menyempitkan selang secara palsu.
- **Berpasangan** = MyPII dan garis dasar dinilai atas sampel yang SAMA. **p bootstrap** = Berg-Kirkpatrick dkk. (2012), sehala;
  **p rawak** = ujian rawak anggaran (tukar ramalan dua sistem per dokumen). **p Holm** = dilaras untuk enam garis dasar (k = 6, pindaan PRA-DAFTAR 2026-11-03).
- **CI F1 bertindih** ialah semakan kasar sahaja: dua selang yang bertindih masih boleh berbeza secara signifikan. Ujian yang
  betul ialah lajur berpasangan (CI Δ dan p).
- `pii-guard` hanya dibanding pada emas penuh (SSM dikira terlepas); baris `(disokong …)` di atas tiada selang kerana ia ramalan
  yang sama atas emas yang ditapis.

**Tafsiran — jujur.** Ringkasan mekanikal di hujung blok menyatakan, dari angka, sama ada selang bertindih dan sama ada mana-mana
selang Δ menyentuh 0. Itu menjawab satu soalan sahaja: *adakah jurang di dev lebih besar daripada hingar persampelan dev?* Ia
**tidak** menjawab sama ada MyPII lebih baik di luar dev. dev ialah set yang dipakai menala MyPII (dan templat dev-v2 ditulis oleh
ejen yang sama), jadi kecondongan ke atas MyPII adalah ralat SISTEMATIK — bootstrap hanya mengukur ralat RAWAK. **Selang dev tidak
menyokong dakwaan kertas**; dakwaan datang hanya dari `ujian2` (dimeterai, penjana keluarga lain), dijalankan SEKALI ikut pra-daftar
(PELAN-C C4). Jurang kecil (cth telefon lawan `pii-guard`) adalah yang paling mungkin hilang di sana.

**English summary.** Document-level bootstrap 95% CIs and paired tests (Berg-Kirkpatrick et al. 2012 bootstrap; approximate
randomization; Holm correction over the six baselines) for every system and entity on dev-v2, generated by `make statistik` from
committed predictions (`hasil/dev-statistik.json`); the mechanical summary at the end of the block is computed, not hand-written.
These intervals capture sampling noise on dev only. Dev was used to tune MyPII, so its advantage there is biased upward by a
systematic error that the bootstrap cannot see: **dev intervals do not support paper claims** — those come only from the sealed
`ujian2` split, run once by a human under the pre-registration.

<!-- statistik:mula -->
<!-- dijana `make statistik` (mypii/nilai/ketidakpastian.py) dari `hasil/dev-statistik.json` — JANGAN sunting dengan tangan -->

Split `dev`, 1000 dokumen; unit sampel semula = dokumen; ulangan 1000, benih 2026, aras 0.95, pembetulan holm atas 6 garis dasar (setiap kunci berasingan). 2 garis dasar eksplorasi di luar keluarga Holm: p mentah sahaja, tanpa pembetulan.

### F1 tepat + selang bootstrap 95% (persentil)

| sistem | `*` | `MY_NRIC` | `MY_PHONE` | `MY_SSM` |
|---|---|---|---|---|
| llm:anthropic/claude-haiku-5-5 | 0.9149 [0.8979, 0.9312] | 0.9363 [0.9148, 0.9553] | 0.9357 [0.915, 0.9542] | 0.8571 [0.8206, 0.8913] |
| llm:anthropic/claude-sonnet-5-5 | 0.8782 [0.8578, 0.8966] | 0.932 [0.9097, 0.9525] | 0.9176 [0.8964, 0.9369] | 0.7659 [0.7249, 0.8031] |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | 0.706 [0.6777, 0.7335] | 0.6649 [0.6219, 0.7073] | 0.8473 [0.8182, 0.8734] | 0.5876 [0.5439, 0.6309] |
| llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct (eksplorasi) | 0.8513 [0.829, 0.871] | 0.874 [0.8454, 0.9021] | 0.8776 [0.8514, 0.9] | 0.7535 [0.6984, 0.797] |
| llm:rv/deepseek-ai/DeepSeek-V4.1-Flash | 0.7193 [0.6899, 0.7483] | 0.6757 [0.6319, 0.7164] | 0.8359 [0.806, 0.8626] | 0.627 [0.5813, 0.6733] |
| llm:rv/zai-org/GLM-5.3-Flash (eksplorasi) | 0.8889 [0.8699, 0.9059] | 0.8824 [0.8555, 0.9082] | 0.8988 [0.8748, 0.9197] | 0.881 [0.8454, 0.9102] |
| mypii | 0.8877 [0.8701, 0.9037] | 0.8328 [0.8, 0.867] | 1.0 [1.0, 1.0] | 0.8054 [0.7667, 0.8403] |
| pii-guard | 0.7209 [0.6977, 0.7434] | 0.6795 [0.6391, 0.7193] | 0.9772 [0.9596, 0.9914] | 0.0 [0.0, 0.0] |
| presidio-asal | 0.4309 [0.4078, 0.4554] | 0.0 [0.0, 0.0] | 0.6247 [0.5905, 0.6596] | 0.0 [0.0, 0.0] |

### `mypii` lawan setiap garis dasar (berpasangan)

| mypii lawan | kunci | ΔF1 | CI 95% Δ | p bootstrap | p rawak | p Holm (bootstrap) | p Holm (rawak) | CI F1 bertindih | CI Δ > 0 |
|---|---|---|---|---|---|---|---|---|---|
| llm:anthropic/claude-haiku-5-5 | `*` | -0.0272 | [-0.0465, -0.0094] | 1.0 | 0.995 | 1.0 | 0.995 | ya | tidak |
| llm:anthropic/claude-haiku-5-5 | `MY_NRIC` | -0.1035 | [-0.1376, -0.0716] | 1.0 | 1.0 | 1.0 | 1.0 | tidak | tidak |
| llm:anthropic/claude-haiku-5-5 | `MY_PHONE` | 0.0643 | [0.0458, 0.085] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:anthropic/claude-haiku-5-5 | `MY_SSM` | -0.0517 | [-0.0948, -0.0109] | 1.0 | 0.991 | 1.0 | 0.991 | ya | tidak |
| llm:anthropic/claude-sonnet-5-5 | `*` | 0.0095 | [-0.0086, 0.0268] | 0.145 | 0.1309 | 0.29 | 0.2618 | ya | tidak |
| llm:anthropic/claude-sonnet-5-5 | `MY_NRIC` | -0.0992 | [-0.1315, -0.0678] | 1.0 | 1.0 | 1.0 | 1.0 | tidak | tidak |
| llm:anthropic/claude-sonnet-5-5 | `MY_PHONE` | 0.0824 | [0.0631, 0.1036] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:anthropic/claude-sonnet-5-5 | `MY_SSM` | 0.0395 | [-0.0025, 0.0791] | 0.027 | 0.018 | 0.054 | 0.036 | ya | tidak |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `*` | 0.1817 | [0.1591, 0.2028] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `MY_NRIC` | 0.1679 | [0.1324, 0.2039] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `MY_PHONE` | 0.1527 | [0.1266, 0.1818] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | `MY_SSM` | 0.2178 | [0.1777, 0.2553] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct (eksplorasi) | `*` | 0.0364 | [0.0165, 0.0583] | 0.001 | 0.001 | – | – | ya | ya |
| llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct (eksplorasi) | `MY_NRIC` | -0.0412 | [-0.0756, -0.0069] | 1.0 | 0.994 | – | – | ya | tidak |
| llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct (eksplorasi) | `MY_PHONE` | 0.1224 | [0.1, 0.1486] | < 0.001 | 0.001 | – | – | tidak | ya |
| llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct (eksplorasi) | `MY_SSM` | 0.0519 | [-0.009, 0.1172] | 0.053 | 0.047 | – | – | ya | tidak |
| llm:rv/deepseek-ai/DeepSeek-V4.1-Flash | `*` | 0.1684 | [0.1467, 0.1897] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:rv/deepseek-ai/DeepSeek-V4.1-Flash | `MY_NRIC` | 0.1571 | [0.1255, 0.1889] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:rv/deepseek-ai/DeepSeek-V4.1-Flash | `MY_PHONE` | 0.1641 | [0.1374, 0.194] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:rv/deepseek-ai/DeepSeek-V4.1-Flash | `MY_SSM` | 0.1784 | [0.139, 0.2185] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| llm:rv/zai-org/GLM-5.3-Flash (eksplorasi) | `*` | -0.0012 | [-0.0197, 0.0169] | 1.0 | 0.5534 | – | – | ya | tidak |
| llm:rv/zai-org/GLM-5.3-Flash (eksplorasi) | `MY_NRIC` | -0.0496 | [-0.0834, -0.0155] | 1.0 | 0.998 | – | – | ya | tidak |
| llm:rv/zai-org/GLM-5.3-Flash (eksplorasi) | `MY_PHONE` | 0.1012 | [0.0803, 0.1252] | < 0.001 | 0.001 | – | – | tidak | ya |
| llm:rv/zai-org/GLM-5.3-Flash (eksplorasi) | `MY_SSM` | -0.0756 | [-0.1181, -0.0373] | 1.0 | 1.0 | – | – | tidak | tidak |
| pii-guard | `*` | 0.1668 | [0.1415, 0.1908] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| pii-guard | `MY_NRIC` | 0.1533 | [0.1161, 0.1936] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| pii-guard | `MY_PHONE` | 0.0228 | [0.0086, 0.0404] | 0.007 | 0.007 | 0.007 | 0.007 | tidak | ya |
| pii-guard | `MY_SSM` † | 0.8054 | [0.7667, 0.8403] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| presidio-asal | `*` | 0.4568 | [0.4299, 0.4813] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| presidio-asal | `MY_NRIC` † | 0.8328 | [0.8, 0.867] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| presidio-asal | `MY_PHONE` | 0.3753 | [0.3404, 0.4095] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |
| presidio-asal | `MY_SSM` † | 0.8054 | [0.7667, 0.8403] | < 0.001 | 0.001 | < 0.001 | 0.006 | tidak | ya |

† Selang F1 garis dasar = [0, 0] untuk entiti ini (tiada ramalan betul langsung): Δ = F1 `mypii` sendiri.

### Ringkasan mekanikal (dikira dari jadual di atas)

- `semua|*`: selang F1 `mypii` bertindih dengan 2/6 garis dasar (llm:anthropic/claude-haiku-5-5, llm:anthropic/claude-sonnet-5-5).
- Selang Δ yang menyentuh atau melepasi 0: 6/24 (llm:anthropic/claude-haiku-5-5 `*`, llm:anthropic/claude-haiku-5-5 `MY_NRIC`, llm:anthropic/claude-haiku-5-5 `MY_SSM`, llm:anthropic/claude-sonnet-5-5 `*`, llm:anthropic/claude-sonnet-5-5 `MY_NRIC`, llm:anthropic/claude-sonnet-5-5 `MY_SSM`).
- Δ terkecil: -0.1035 (mypii lawan llm:anthropic/claude-haiku-5-5, `MY_NRIC`).
- p rawak terkecil yang boleh dilapor dengan R = 1000 ialah 1/(R+1) ≈ 0.001; 17/24 perbandingan berada di lantai itu — di situ p rawak (dan p Holm rawak ≤ 6 × lantai) ialah had resolusi ujian, bukan ukuran saiz kesan.
- Eksplorasi (2 sistem, `semua|*`, mypii − sistem): llm:cf/@cf/mistralai/mistral-small-3.1-24b-instruct Δ 0.0364 [0.0165, 0.0583]; llm:rv/zai-org/GLM-5.3-Flash Δ -0.0012 [-0.0197, 0.0169]. Deskriptif sahaja — di luar keluarga Holm, tiada hipotesis, p mentah tidak dibetulkan untuk perbandingan berganda (PRA-DAFTAR pindaan 2026-11-03).
<!-- statistik:tamat -->

## Kuasa untuk `ujian2` dengan k = 6 (pindaan PRA-DAFTAR 2026-11-03)

Disalin dari output `make kuasa` (3 Nov 2026; `mypii/nilai/kuasa.py` atas `hasil/dev-statistik.json`, dev 1000 dokumen → sasaran 1000;
kuasa 0.8, sehala; Holm k = 6). Baris `*` sahaja — jadual penuh setiap entiti: jalankan `make kuasa`. **MDE TIDAK mengubah peraturan
keputusan** pra-daftar; ia menunjukkan jurang terkecil yang `ujian2` boleh kesan dengan kuasa 80%.
Baris DeepSeek dikemas 3 Nov 2026 selepas pindaan PRA-DAFTAR "Penyedia garis dasar DeepSeek (H1d/H2d): cbcn → rv": `rv/` dev (lama
`cbcn/deepseek-v4.1-flash`: Δ 0.1398, SE 0.0109, MDE 0.0354 / 0.0272).

| garis dasar | ΔF1 dev `*` | SE Δ | MDE α/k=0.008333 | MDE α=0.05 |
|---|---|---|---|---|
| presidio-asal | 0.4568 | 0.0131 | 0.0424 | 0.0326 |
| pii-guard | 0.1668 | 0.0126 | 0.0407 | 0.0313 |
| llm:cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast | 0.1817 | 0.0111 | 0.0361 | 0.0277 |
| llm:rv/deepseek-ai/DeepSeek-V4.1-Flash | 0.1684 | 0.011 | 0.0355 | 0.0273 |
| llm:anthropic/claude-sonnet-5-5 | 0.0095 | 0.009 | 0.0292 | 0.0225 |
| llm:anthropic/claude-haiku-5-5 | -0.0272 | 0.0095 | 0.0306 | 0.0235 |

**Bacaan jujur.** Δ dev MyPII − Sonnet (+0.0095) lebih kecil daripada MDE (0.0292), dan Δ dev MyPII − Haiku negatif: jika `ujian2`
berkelakuan seperti dev, H1e (MyPII > Sonnet) dan H1f (MyPII > Haiku) dijangka **tidak** disokong. Ini dilapor SEBELUM ujian2 dibuka;
peraturan keputusan dan hipotesis tidak dipinda kerananya. *English:* on dev the MyPII−Sonnet gap is below the detectable effect and the
MyPII−Haiku gap is negative, so H1e/H1f are expected not to hold on `ujian2` if it behaves like dev; the pre-registered rule is unchanged.

## Semakan label (IAA) — persetujuan penyemak dan kadar ralat label

**Apa ini.** 300 dokumen (150 dev + 150 ujian2, berstrata, ADR-015) disemak oleh penyemak manusia `p1` (pemilik), `p2` bila ada, dan
penyemak mesin sandaran `llm` (`cbcn/glm-5.3`, keluarga berlainan daripada penjana data). Soalan: (a) setiap span emas betul / salah /
jenis lain; (b) PII yang tidak bertanda; (c) teks terasa Malaysia sebenar. Hanya label emas dipapar — tiada ramalan sistem.

**Cara membaca.** κ Cohen (a) per span dan (c) per dokumen, dengan % persetujuan mentah bersebelahan (κ boleh rendah walau % tinggi
bila satu jawapan dominan). F1 (b) = 2|A∩B| / (|A|+|B|) mikro atas nilai dinormalkan (digit; SSM alnum huruf besar); dokumen yang
kedua-duanya tiada nilai dikira berasingan. Kadar ralat = pecahan menurut SATU penyemak; ralat ujian2 ialah hingar label yang
DILAPOR, tidak dibaiki (set dimeterai). CI = bootstrap persentil atas dokumen. Pasangan `p1×llm` hanyalah had kajian bila tiada `p2`.

**English summary.** Inter-annotator agreement on a stratified 300-document sample (150 dev, 150 ujian2): Cohen's κ and raw agreement
for per-span label verdicts (a) and per-document realism (c), micro F1 agreement on normalised unlabelled-PII values (b), and per-annotator
label error rates by split with document-level bootstrap CIs. Generated by `make iaa-skor` from `hasil/iaa.json`; no hand-written numbers.

<!-- iaa:mula -->
<!-- dijana `make iaa-skor` (mypii/iaa/skor.py) dari `hasil/iaa.json` — JANGAN sunting dengan tangan -->

Sampel n = 300 dokumen; CI 95% bootstrap persentil atas dokumen (ulangan 1000, benih 2026).

| Penyemak | siap | separa | rosak | gagal |
|---|---|---|---|---|
| llm | 300/300 | 0 | 0 | 0 |
| p1 | 300/300 | 0 | 0 | 0 |
| p2 | 0/300 | 0 | 0 | 0 |

**Persetujuan** (dokumen siap oleh kedua-dua penyemak sahaja)

| Pasangan | keadaan | dokumen | span | κ (a) | % setuju (a) | κ (c) | % setuju (c) | F1 (b) | kedua-dua tiada (b) |
|---|---|---|---|---|---|---|---|---|---|
| **p1×llm** (utama) | lengkap | 300 | 258 | — | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.793 [0.747, 0.837] | 0.420 [0.304, 0.523] | 224 |
| p1×p2 | menunggu p2 (0/300) | — | — | — | — | — | — | — | — |

**Kadar ralat label** (pecahan; menurut setiap penyemak — deskriptif, tiada ujian hipotesis)

| Penyemak | split | dokumen | span | span salah/jenis lain | dokumen PII tidak bertanda | dokumen janggal |
|---|---|---|---|---|---|---|
| llm | dev | 150 | 132 | 0.000 [0.000, 0.000] | 0.227 [0.167, 0.300] | 0.227 [0.160, 0.300] |
| llm | ujian2 | 150 | 126 | 0.000 [0.000, 0.000] | 0.220 [0.153, 0.287] | 0.187 [0.127, 0.247] |
| llm | beza dev-ujian2 | — | — | 0.000 [0.000, 0.000] | 0.007 [-0.087, 0.107] | 0.040 [-0.053, 0.140] |
| p1 | dev | 150 | 132 | 0.000 [0.000, 0.000] | 0.067 [0.027, 0.113] | 0.000 [0.000, 0.000] |
| p1 | ujian2 | 150 | 126 | 0.000 [0.000, 0.000] | 0.167 [0.113, 0.227] | 0.000 [0.000, 0.000] |
| p1 | beza dev-ujian2 | — | — | 0.000 [0.000, 0.000] | -0.100 [-0.180, -0.027] | 0.000 [0.000, 0.000] |

Belum dikira — p1×p2: menunggu p2 (0/300). Baris LLM sahaja ialah pandangan SATU penyemak mesin, bukan persetujuan.
<!-- iaa:tamat -->
