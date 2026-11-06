#!/usr/bin/env bash
# Ujian muktamad SATU-TEMBAK — PRA-DAFTAR §7 (+ pindaan 2026-11-03 "§7 pelaksana"), PELAN-MODEL-LAIN P8, ADR-017.
#
#   bash scripts/ujian-muktamad.sh                       # larian SEBENAR (projek autopilot mypii-ujian SAHAJA, sekali)
#   bash scripts/ujian-muktamad.sh --kering              # semua semakan KECUALI sha256 split; tiada uv/harness → SEDIA / TIDAK SEDIA
#   bash scripts/ujian-muktamad.sh --ulang-crash "<sebab>"   # SEKALI, hanya bila MULA wujud tanpa SELESAI (larian crash)
#
# Menjalankan EMPAT perintah blok kod §7 TEPAT (ujian2 dahulu), sekali. Perintah ramalan yang mencetak `panggilan gagal`
# diulang SEKALI (§7: jawapan sedia ada dari cache, hanya yang gagal dipanggil semula). Semua semakan enggan berlaku SEBELUM
# uv/harness dipanggil. Kunci dimuat dari fail env dan tidak pernah dicetak (tiada `set -x`).
# Selepas: hasil + ramalan + cache LLM ujian + log disalin ke arkib LUAR repo (chmod 700, MANIFEST.sha256), cache dipulih
# dalam repo (`git restore` + `git clean` TERHAD hasil/cache/llm), tree mesti bersih → RINGKASAN.json + SELESAI.
# Env (untuk ujian sahaja): MYPII_ARKIB (lalai ~/ops/mypii/arkib-ujian), MYPII_ENV_DIR (lalai ~/ops/mypii), MYPII_PELAKSANA.
# Kod keluar: 0 SEDIA/SELESAI · 2 hujah salah · 4 enggan (tiada harness dipanggil) · 5 crash · 6 tree tidak bersih selepas pulih.
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
AKAR="$(pwd)"
ARKIB="${MYPII_ARKIB:-$HOME/ops/mypii/arkib-ujian}"
ENV_DIR="${MYPII_ENV_DIR:-$HOME/ops/mypii}"
PELAKSANA="${MYPII_PELAKSANA:-ejen autopilot mypii-ujian atas kebenaran pemilik 3 Nov 2026}"
FAIL_ENV=(9router.env anthropic.env)
CACHE=hasil/cache/llm
PRADAFTAR=docs/PRA-DAFTAR.md

# Blok kod §7 PRA-DAFTAR, bait sama (gerbang mypii-model-lain §20 + semakan masa larian di bawah). JANGAN sunting.
PERINTAH=(
'uv run --extra nilai --extra garis python -m mypii.nilai.harness --split ujian2 --sistem semua --benarkan-ujian'
'uv run python -m mypii.nilai.harness --split ujian2 --sistem semua --statistik --benarkan-ujian'
'uv run --extra nilai --extra garis python -m mypii.nilai.harness --split ujian  --sistem semua --benarkan-ujian'
'uv run python -m mypii.nilai.harness --split ujian  --sistem semua --statistik --benarkan-ujian'
)

MOD=sebenar SEBAB_ULANG=""
case "${1:-}" in
  "") ;;
  --kering) MOD=kering ;;
  --ulang-crash) MOD=ulang; SEBAB_ULANG="${2:-}"
    [ -n "$SEBAB_ULANG" ] || { echo "--ulang-crash perlukan sebab: --ulang-crash \"<sebab>\"" >&2; exit 2; } ;;
  *) echo "hujah tidak dikenali: $1 (pilihan: --kering | --ulang-crash \"<sebab>\")" >&2; exit 2 ;;
esac
[ $# -le $([ "$MOD" = ulang ] && echo 2 || echo 1) ] || { echo "hujah berlebihan" >&2; exit 2; }

enggan() {
  if [ "$MOD" = kering ]; then echo "TIDAK SEDIA: $*"; else echo "ENGGAN: $*" >&2; fi
  exit 4
}

# ---- semakan (TIADA uv / harness sebelum semua lulus) ----
git rev-parse --verify -q HEAD >/dev/null || enggan "$AKAR bukan repo git dengan komit"
SHA="$(git rev-parse HEAD)"

# MULA/SELESAI dalam arkib: larian sebenar = tiada MULA langsung; ulang = tepat satu MULA tanpa SELESAI dan belum pernah diulang
mula=() selesai=()
if [ -d "$ARKIB" ]; then
  while IFS= read -r f; do mula+=("$(dirname "$f")"); done < <(find "$ARKIB" -mindepth 2 -maxdepth 2 -name MULA | sort)
  while IFS= read -r f; do selesai+=("$f"); done < <(find "$ARKIB" -mindepth 2 -maxdepth 2 \( -name SELESAI -o -name GAGAL \) | sort)
fi
D=""
if [ "$MOD" = ulang ]; then
  [ ${#mula[@]} -eq 1 ] || enggan "--ulang-crash perlukan tepat satu MULA dalam $ARKIB (ada ${#mula[@]})"
  [ ${#selesai[@]} -eq 0 ] || enggan "larian sudah SELESAI/GAGAL — tiada ulangan"
  D="${mula[0]}"
  pid="$(cat "$D/PID" 2>/dev/null || true)"
  [ -f "$D/CRASH" ] || { [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; } \
    || enggan "MULA wujud tanpa CRASH dan proses larian ${pid:-?} masih hidup — larian mungkin masih berjalan"
  [ ! -e "$D/ULANG-CRASH" ] || enggan "--ulang-crash sudah digunakan SEKALI (§7) — tiada ulangan kedua"
else
  [ ${#mula[@]} -eq 0 ] || enggan "penanda MULA sudah wujud dalam arkib (${mula[0]}) — ujian muktamad SEKALI sahaja"
fi

# tree bersih (ulang: hanya perubahan cache LLM larian yang crash dibenarkan — jawapan itu disambung, bukan dipanggil semula)
kotor="$(git status --porcelain)"
[ "$MOD" != ulang ] || kotor="$(grep -v " $CACHE/" <<<"$kotor" || true)"
[ -z "$kotor" ] || enggan "tree git tidak bersih: $(head -3 <<<"$kotor" | tr '\n' ' ')"

# empat perintah = blok kod §7 dalam PRA-DAFTAR di HEAD (bait sama, susunan sama)
python3 -I - "$(git show "HEAD:$PRADAFTAR" 2>/dev/null)" "${PERINTAH[@]}" <<'PY' || enggan "perintah skrip ≠ blok kod §7 $PRADAFTAR"
import re, sys
m = re.search(r"^## 7\..*?\n```\n(.*?)\n```", sys.argv[1], re.S | re.M)
sys.exit(0 if m and [b for b in m.group(1).splitlines() if b.strip()] == sys.argv[2:] else 1)
PY

# tiada hasil split ujian dari larian lain (ulang: hasil separa dipindah ke separa/ di bawah)
if [ "$MOD" != ulang ]; then
  ada="$(ls -d hasil/ujian* hasil/ramalan/ujian* 2>/dev/null || true)"
  [ -z "$ada" ] || enggan "hasil ujian sudah wujud: $(head -3 <<<"$ada" | tr '\n' ' ')"
fi

for f in "${FAIL_ENV[@]}"; do [ -r "$ENV_DIR/$f" ] || enggan "fail env tiada: $ENV_DIR/$f"; done

# baki lejar Anthropic (had_usd − jumlah_usd) ≥ perlu_ujian_usd (PELAN-MODEL-LAIN P5, blok rancang kos dev)
baki="$(python3 -I - <<'PY'
import json, pathlib, sys, yaml
a = yaml.safe_load(pathlib.Path("config/mypii.yaml").read_text(encoding="utf-8"))["garis_dasar"]["llm"]["anthropic"]
kos = json.loads(pathlib.Path(a["kos"]["fail"].format(split="dev")).read_text())[a["kos"]["blok_rancang"]]
lejar = pathlib.Path(a["lejar"])
jumlah = json.loads(lejar.read_text())["jumlah_usd"] if lejar.exists() else 0.0
baki, perlu = float(a["had_usd"]) - float(jumlah), float(kos["perlu_ujian_usd"])
print(f"baki USD {baki:.6f}, perlu USD {perlu:.6f}")
sys.exit(0 if baki >= perlu else 1)
PY
)" || enggan "baki lejar tidak cukup atau tidak boleh dibaca (${baki:-ralat membaca config/lejar/kos})"

if [ "$MOD" = kering ]; then
  echo "SEDIA: HEAD $SHA · tree bersih · §7 sepadan · tiada hasil ujian · tiada MULA · env ada · $baki (sha256 split TIDAK disemak dalam --kering)"
  exit 0
fi

# sha256 split = KUNCI*.json (cincangan BAIT sahaja, §6 — kandungan tidak dibuka)
python3 -I - <<'PY' || enggan "sha256 split ≠ KUNCI*.json (§6: larian tidak sah)"
import hashlib, json, pathlib, sys
b = pathlib.Path("data/bench")
for split, kunci in (("ujian", "KUNCI.json"), ("ujian2", "KUNCI2.json")):
    f = b / f"{split}.jsonl"
    if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != json.loads((b / kunci).read_text())[split]["sha256"]:
        print(f"{split}: sha256 tidak sepadan / fail tiada", file=sys.stderr); sys.exit(1)
PY

# §7 "Sebelum": make uji lulus (perintah sama dengan Makefile `uji`)
uv run pytest -q >/dev/null 2>&1 || enggan "make uji (uv run pytest -q) gagal"

# ---- larian ----
if [ "$MOD" = ulang ]; then
  mkdir -p "$D/separa"
  for f in hasil/ujian* hasil/ramalan/ujian*; do if [ -e "$f" ]; then mv "$f" "$D/separa/"; fi; done
  if [ -d "$D/log" ]; then mv "$D/log" "$D/separa/log"; fi
  { echo "sebab: $SEBAB_ULANG"; echo "tarikh_utc: $(date -u +%FT%TZ)"; echo "sha: $SHA"; } >"$D/ULANG-CRASH"
  rm -f "$D/CRASH"
else
  mkdir -p "$ARKIB"; chmod 700 "$ARKIB"
  D="$ARKIB/$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir "$D"
  { echo "sha: $SHA"; echo "tarikh_utc: $(date -u +%FT%TZ)"; echo "pelaksana: $PELAKSANA"
    echo "uv: $(uv --version 2>&1)"; echo "python: $(uv run python --version 2>&1)"
    printf 'perintah: %s\n' "${PERINTAH[@]}"; } >"$D/MULA"
fi
mkdir -p "$D/log"
echo $$ >"$D/PID"
tamat=0  # keluar tanpa SELESAI/GAGAL (isyarat, ralat) = CRASH → --ulang-crash SEKALI dibenarkan
trap '[ "$tamat" = 1 ] || [ -e "$D/CRASH" ] || { echo "keluar tanpa SELESAI (rc $?)"; date -u +%FT%TZ; } >"$D/CRASH"' EXIT

set -a
for f in "${FAIL_ENV[@]}"; do . "$ENV_DIR/$f"; done
set +a

# salin hasil + ramalan + cache LLM berubah/baharu ke $1, kemudian pulih cache dalam repo (TERHAD hasil/cache/llm)
arkib_dan_pulih() {
  local k="$1"; mkdir -p "$k/hasil/ramalan" "$k/cache"
  for f in hasil/ujian*; do if [ -e "$f" ]; then cp -p "$f" "$k/hasil/"; fi; done
  for f in hasil/ramalan/ujian*; do if [ -e "$f" ]; then cp -p "$f" "$k/hasil/ramalan/"; fi; done
  { git diff --name-only -- "$CACHE"; git ls-files --others --exclude-standard -- "$CACHE"; } | sort -u | while IFS= read -r f; do
    if [ -e "$f" ]; then cp -p --parents "$f" "$k/cache/"; fi
  done
  git restore -- "$CACHE"
  git clean -fdq -- "$CACHE"
}

n=0
jalan() {  # $1 = perintah (teks §7), $2 = nama log
  local -a hujah; read -ra hujah <<<"$1"
  echo "+ $1" >>"$D/log/$2.log"
  "${hujah[@]}" >>"$D/log/$2.log" 2>&1
}
for p in "${PERINTAH[@]}"; do
  n=$((n + 1))
  rc=0; jalan "$p" "$n" || rc=$?
  if [ $rc -eq 0 ] && [[ "$p" != *--statistik* ]] && grep -q "panggilan gagal" "$D/log/$n.log"; then
    rc=0; jalan "$p" "$n-ulang" || rc=$?   # SEKALI sahaja (§7); yang masih gagal = ramalan kosong, dilapor
  fi
  if [ $rc -ne 0 ]; then
    if [ "$MOD" = ulang ]; then
      tamat=1; arkib_dan_pulih "$D/gagal"
      { echo "perintah $n rc $rc selepas --ulang-crash"; echo "tarikh_utc: $(date -u +%FT%TZ)"; } >"$D/GAGAL"
      echo "GAGAL: perintah $n crash (rc $rc) selepas --ulang-crash — larian tidak sah, tiada ulangan lagi; arkib $D" >&2
    else
      tamat=1; { echo "perintah $n rc $rc"; echo "tarikh_utc: $(date -u +%FT%TZ)"; } >"$D/CRASH"
      echo "CRASH: perintah $n (rc $rc) — log $D/log/$n.log; ulang SEKALI: bash scripts/ujian-muktamad.sh --ulang-crash \"<sebab>\"" >&2
    fi
    exit 5
  fi
done

arkib_dan_pulih "$D"
kotor="$(git status --porcelain)"
if [ -n "$kotor" ]; then
  tamat=1; echo "tree tidak bersih selepas pulih: $kotor" >"$D/GAGAL"
  echo "GAGAL: tree tidak bersih selepas pulih (hasil sudah dalam arkib $D): $kotor" >&2; exit 6
fi

python3 -I - "$D" "$SHA" "$PELAKSANA" <<'PY' || echo "RINGKASAN.json gagal dijana — hasil mentah dalam arkib" >"$D/RINGKASAN-RALAT"
import json, pathlib, re, sys, yaml
d, sha, pelaksana = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
c = yaml.safe_load(pathlib.Path("config/mypii.yaml").read_text(encoding="utf-8"))
alfa = c["nilai"]["statistik"]["pradaftar"]["alfa"]
model = c["garis_dasar"]["llm"]["model"]
# llm:<m>: {json} = statistik ramal_llm (gagal/rosak); log ulang (jika ada) menindih log pertama
llm, split_log = {}, {"1": "ujian2", "2": "ujian2", "3": "ujian", "4": "ujian"}   # nombor perintah dalam PERINTAH
for f in sorted((d / "log").glob("*.log"), key=lambda f: (f.stem.split("-")[0], f.stem)):  # "<n>-ulang" SELEPAS "<n>"
    for b in f.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(llm:\S+): (\{.*\})$", b)
        if m:
            st = json.loads(m.group(2))
            split = split_log[f.stem.split("-")[0]]
            llm.setdefault(split, {})[m.group(1)] = {k: st.get(k) for k in ("dokumen", "panggilan", "gagal", "rosak")}
r = {"sha": sha, "pelaksana": pelaksana, "alfa": alfa, "split": {}}
for split, h in (("ujian2", "H1"), ("ujian", "H2")):
    s = json.loads(pathlib.Path(f"hasil/{split}-statistik.json").read_text())
    ku, eks = s["kunci_utama"], set(s.get("eksplorasi") or [])
    sah = [x for x in ["presidio-asal", "pii-guard"] + ["llm:" + m for m in model] if x in s["banding"] and x not in eks]
    hip = {}
    for i, x in enumerate(sah):
        b = s["banding"][x][ku]
        hip[f"{h}{chr(97 + i)}"] = {"sistem": x, **{k: b[k] for k in ("delta", "bawah", "atas", "p_holm_bootstrap", "p_holm_rawak")},
                                    "disokong": b["p_holm_bootstrap"] < alfa and b["p_holm_rawak"] < alfa}
    r["split"][split] = {
        "kunci": ku, "dokumen": s["dokumen"],
        "f1": {x: {k: v[ku][k] for k in ("f1", "bawah", "atas")} for x, v in s["sistem"].items()},
        "hipotesis": hip,
        "eksplorasi": {x: {k: s["banding"][x][ku][k] for k in ("delta", "bawah", "atas", "p_bootstrap", "p_rawak")}
                       for x in sorted(eks) if x in s["banding"]},
        "llm": llm.get(split, {}),
    }
lejar = d / "cache" / c["garis_dasar"]["llm"]["anthropic"]["lejar"]
r["lejar_usd_selepas"] = json.loads(lejar.read_text())["jumlah_usd"] if lejar.exists() else None
(d / "RINGKASAN.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
PY

{ echo "tarikh_utc: $(date -u +%FT%TZ)"; echo "sha: $SHA"; } >"$D/SELESAI"; tamat=1
(cd "$D" && find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum >MANIFEST.sha256)
chmod -R go-rwx "$D"
echo "SELESAI: $D (RINGKASAN.json, MANIFEST.sha256)"
