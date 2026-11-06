.PHONY: bandingan-v2 latih-konteks semua jana jana-v3 uji nilai carta statistik kuasa nilai-garis bandingan bandingan-masa lint analisis sahkan-rujukan templat-llm templat-llm-probe iaa-sampel iaa-pakej iaa-pelayan iaa-llm iaa-eksport iaa-skor kos-claude probe-llm

semua: jana uji nilai

jana:
	uv run python -m mypii.jana.jana

# MyPII v2 (PELAN-V2 P3): data/bench_v3/ latih3 + dev3 (+ ujian3 bila templat/nama ujian3 wujud). Split v1 tidak disentuh.
jana-v3:
	uv run python -m mypii.jana.jana --v3

uji:
	uv run pytest -q

lint:
	uv run ruff check mypii tests

# Setiap larian = satu baris `hasil/iterasi.tsv` (ADR-006 §Iterasi; tambah-sahaja). STATUS ∈ simpan|buang|ukur; harness gagal → baris `crash` + exit ≠ 0.
# SPLIT = dev (v1) atau dev3 (PELAN-V2; laluan dari config nilai.split_fail). Split dikunci ditolak oleh harness.
STATUS ?= ukur
KETERANGAN ?= make nilai
SPLIT ?= dev
nilai:
	uv run python -m mypii.nilai.harness --split $(SPLIT) --iterasi $(STATUS) --keterangan "$(KETERANGAN)"

# hasil/iterasi.tsv → hasil/kemajuan.svg (PELAN-C C2b; stdlib, bait sama setiap larian). Teks/warna/saiz = config nilai.iterasi.carta.
carta:
	uv run python -m mypii.nilai.carta

# Selang bootstrap + ujian berpasangan + Holm (ADR-006 §Statistik) dari hasil/ramalan/ (ditulis oleh nilai/nilai-garis); tiada Presidio/rangkaian.
# Kemudian blok "Ketidakpastian" docs/BANDINGAN.md dijana dari hasil/dev-statistik.json (ADR-013).
statistik:
	uv run python -m mypii.nilai.harness --split dev --sistem semua --statistik
	uv run python -m mypii.nilai.ketidakpastian

# Analisis kuasa pra-daftar (ADR-007): SE Δ dari selang bootstrap hasil/dev-statistik.json → MDE untuk ujian2. Config nilai.statistik.pradaftar.
kuasa:
	uv run python -m mypii.nilai.kuasa

# Semua sistem + garis dasar pesaing (ADR-011). LLM dari cache dikomit `hasil/cache/llm/`; dokumen tanpa cache perlu 9router.
nilai-garis:
	uv run --group nilai --group garis python -m mypii.nilai.harness --split $(SPLIT) --sistem semua

# docs/BANDINGAN.md blok jana (ADR-012); LLM dari cache dikomit, tiada rangkaian. `-masa` juga mengukur masa (perlu 9router).
bandingan:
	uv run --group nilai --group garis python -m mypii.nilai.bandingan

bandingan-masa:
	uv run --group nilai --group garis python -m mypii.nilai.bandingan --ukur-masa

# PELAN-CLAUDE P3 (ADR-016): token masuk SEBENAR (count_tokens, percuma) × model anthropic/ atas dev SAHAJA → hasil/dev-kos-claude.json.
# Perlu `set -a; . ~/ops/mypii/anthropic.env; set +a`. Exit 3 = anggaran terburuk melepasi baki had lejar.
# `make kos-claude ARG=--rancang` (PELAN-MODEL-LAIN P5): keputusan kos calon Claude eksplorasi → blok rancang_eksplorasi.
ARG ?=
kos-claude:
	nice uv run --group garis python -m mypii.nilai.kos_claude --split dev $(ARG)

# PELAN-MODEL-LAIN P4 (pindaan PRA-DAFTAR 2026-11-03): probe FORMAT 6 calon eksplorasi atas N dokumen dev pertama (tiada F1) →
# hasil/dev-probe-llm.json. Perlu 9router.env + anthropic.env; jawapan masuk cache yang sama dengan larian penuh.
probe-llm:
	nice uv run --group garis python -m mypii.nilai.probe_llm --split dev

analisis:
	uv run python -m mypii.analisis

# Perlu rangkaian (Crossref/DataCite); bukan sebahagian gerbang CI.
sahkan-rujukan:
	uv run --no-project python .claude/skills/citation-management/scripts/validate_citations.py docs/literatur/rujukan.bib --check-dois

# Perlu 9router (`set -a; . ~/ops/mypii/9router.env; set +a`). Sekali setiap sasaran; ujian2 DIMETERAI (ADR-004). Cetak statistik sahaja.
templat-llm:
	uv run python -m mypii.jana.templat_llm --sasaran $(SASARAN)

# PELAN-V2 P4: probe format calon penjana v3 (latih3 / ujian3) ikut susunan config, SEKALI → data/probe/penjana-<sasaran>.json; rc 3 = semua gagal
templat-llm-probe:
	uv run python -m mypii.jana.templat_llm --sasaran $(SASARAN) --probe

# PELAN-IAA P2 (ADR-015): sampel berstrata 300 → data/iaa/sampel.json (id/split/bahasa/berspan/urutan; TIADA teks). Cetak kiraan sahaja.
iaa-sampel:
	uv run python -m mypii.iaa.sampel

# PELAN-IAA P3 (ADR-015): bundel teks + span emas → iaa.pakej.folder (LUAR repo; cetak kiraan + sha256 sahaja); pelayan halaman semakan.
iaa-pakej:
	uv run python -m mypii.iaa.pakej

iaa-pelayan:
	uv run python -m mypii.iaa.pelayan

# PELAN-IAA P7/P8 (ADR-015): penyemak sandaran LLM (perlu MYPII_9ROUTER_KEY bila cache belum penuh; cetak kiraan sahaja) + eksport SQLite → data/iaa/jawapan/.
iaa-llm:
	uv run python -m mypii.iaa.llm

iaa-eksport:
	uv run python -m mypii.iaa.eksport

# PELAN-IAA P9 (ADR-015 §Skor): κ/F1 persetujuan + kadar ralat label (CI bootstrap atas dokumen) → hasil/iaa.json + blok iaa BANDINGAN.
iaa-skor:
	uv run python -m mypii.iaa.skor

# PELAN-SEDIA-TERBIT P1: blok jadual dev README (antara penanda jadual-dev) dari hasil/dev-*.json; tiada rangkaian, tiada skor dikira.
.PHONY: readme
readme:
	uv run python scripts/jana_readme.py

# PELAN-V2 P10 (ADR-018): pengelas konteks atas konteks.split_latih SAHAJA → model/konteks-v2.json (sha256 dicetak → config)
latih-konteks:
	nice uv run --group latih python -m mypii.konteks_latih

# PELAN-V2 P16: laporan v2 dijana (dev3 dikomit + arkib ujian3 luar repo) → docs/BANDINGAN-V2.md; docs/BANDINGAN.md v1 tidak disentuh
bandingan-v2:
	uv run python -m mypii.nilai.bandingan_v2
