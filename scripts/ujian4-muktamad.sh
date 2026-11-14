#!/usr/bin/env bash
# Ujian4 muktamad SATU-TEMBAK — PRA-DAFTAR pindaan "MyPII v2.1" §7-v21, PELAN-V21 P8/P9 (corak scripts/ujian3-muktamad.sh).
#
#   bash scripts/ujian4-muktamad.sh                          # larian SEBENAR, SEKALI
#   bash scripts/ujian4-muktamad.sh --kering                 # semua semakan KECUALI sha256 split + make uji → SEDIA / TIDAK SEDIA
#   bash scripts/ujian4-muktamad.sh --ulang-crash "<sebab>"  # SEKALI, hanya bila MULA wujud tanpa SELESAI (larian crash)
#
# Menjalankan perintah blok §7-v21 TEPAT (ramalan harness, model luar di Modal, statistik H5). Semua semakan enggan SEBELUM uv/harness
# dipanggil. Kunci dari fail env, tidak pernah dicetak (tiada `set -x`). Selepas: hasil + ramalan + cache/lejar LLM ujian4 + log →
# arkib LUAR repo (chmod 700, MANIFEST.sha256); cache + lejar dipulih dalam repo (TIDAK dikomit); tree mesti bersih → RINGKASAN.json.
# Env (ujian sahaja): MYPII_ARKIB (lalai ~/ops/mypii/arkib-ujian4), MYPII_ENV_DIR (lalai ~/ops/mypii), MYPII_PELAKSANA.
# Kod keluar: 0 SEDIA/SELESAI · 2 hujah salah · 4 enggan (tiada harness) · 5 crash · 6 tree tidak bersih selepas pulih.
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
AKAR="$(pwd)"
ARKIB="${MYPII_ARKIB:-$HOME/ops/mypii/arkib-ujian4}"
ENV_DIR="${MYPII_ENV_DIR:-$HOME/ops/mypii}"
PELAKSANA="${MYPII_PELAKSANA:-sesi interaktif 14 Nov 2026 atas arahan pemilik «buat yg terbaik, pelan → red team → bina» (PELAN-V21)}"
FAIL_ENV=(anthropic.env)
CACHE=hasil/cache/llm
HASIL='ujian4*'
HASIL_GLOB=('hasil/v21/ujian4*' 'hasil/v21/ramalan/ujian4*' 'hasil/luar/ujian4*')
SKRIP=scripts/ujian4-muktamad.sh
PRADAFTAR=docs/PRA-DAFTAR.md
BEKU='^### [0-9]{4}-[0-9]{2}-[0-9]{2}.*MyPII v2\.1'
TAG_BEKU=mypii-v21-beku

# Blok §7-v21 PRA-DAFTAR, bait sama (disemak semasa larian di bawah). JANGAN sunting.
PERINTAH=(
'uv run --group nilai --group garis python -m mypii.nilai.harness --split ujian4 --sistem mypii mypii-v2 mypii-v1 presidio-asal llm:anthropic/claude-haiku-5-5 --keluar hasil/v21 --benarkan-ujian'
'uv run --with modal==1.6.3 modal run scripts/luar_modal.py::main --model meddies --split ujian4 --benarkan-ujian'
'uv run --with modal==1.6.3 modal run scripts/luar_modal.py::main --model gliner --split ujian4 --benarkan-ujian'
'uv run python -m mypii.nilai.statistik_v21 --split ujian4 --benarkan-ujian'
)

. "$AKAR/scripts/muktamad-lib.sh"
u3_hujah "$@"

# ---- semakan (TIADA uv / harness sebelum semua lulus) ----
u3_semak_arkib

python3 -I - "$(git show "HEAD:$PRADAFTAR" 2>/dev/null)" "${PERINTAH[@]}" <<'PY' || enggan "perintah skrip ≠ blok §7-v21 $PRADAFTAR"
import re, sys
m = re.search(r"^#### §7-v21 Perintah tepat ujian4\n```\n(.*?)\n```", sys.argv[1], re.S | re.M)
sys.exit(0 if m and [b for b in m.group(1).splitlines() if b.strip()] == sys.argv[2:] else 1)
PY

grep -qE "$BEKU" <<<"$(git show "HEAD:$PRADAFTAR" 2>/dev/null)" || enggan "pindaan 'MyPII v2.1' tiada dalam HEAD"

# pengecam yang dinilai (HEAD) = v2.1 beku: kod + model + fakta + bahagian config pengecam sama dengan tag
git rev-parse -q --verify "$TAG_BEKU^{commit}" >/dev/null || enggan "tag $TAG_BEKU tiada"
git diff --quiet "$TAG_BEKU" HEAD -- mypii/pengecam model config/kod_pb.yaml config/ssm_rob.yaml || enggan "pengecam/model berubah sejak $TAG_BEKU"
python3 -I - "$(git show "$TAG_BEKU:config/mypii.yaml")" "$(git show HEAD:config/mypii.yaml)" <<'PY' || enggan "config pengecam berubah sejak tag beku"
import sys, yaml
a, b = (yaml.safe_load(x) for x in sys.argv[1:3])
bahagian = lambda c: (c["pengecam"], c["konteks"], c["nilai"]["ambang_skor"], c["nilai"]["entiti"])
sys.exit(0 if bahagian(a) == bahagian(b) else 1)
PY

u3_semak_hasil

for f in "${FAIL_ENV[@]}"; do [ -r "$ENV_DIR/$f" ] || enggan "fail env tiada: $ENV_DIR/$f"; done
[ -r "$HOME/.modal.toml" ] || enggan "token Modal tiada (~/.modal.toml) — model luar tidak boleh dijalankan"

# baki = had − lejar repo − belanja luar repo (v1 + ujian3); anggaran Haiku ujian4 = USD purata Haiku × dokumen × nisbah saiz dev3
baki="$(python3 -I - <<'PY'
import json, pathlib, sys, yaml
c = yaml.safe_load(pathlib.Path("config/mypii.yaml").read_text(encoding="utf-8"))
a, v = c["garis_dasar"]["llm"]["anthropic"], c["nilai"]["statistik"]["v21"]
lejar = json.loads(pathlib.Path(a["lejar"]).read_text())
h = lejar["model"][v["hipotesis"]["H5b"]["sistem"].removeprefix("llm:")]
f = {s: pathlib.Path(c["nilai"]["split_fail"][s]["fail"]) for s in ("dev3", "ujian4")}
dok = sum(1 for _ in f["ujian4"].open(encoding="utf-8")) if f["ujian4"].is_file() else 1000
saiz = f["ujian4"].stat().st_size / f["dev3"].stat().st_size if f["ujian4"].is_file() else 1.0
anggar = h["usd"] / h["panggilan"] * dok * saiz
baki = float(a["had_usd"]) - float(lejar["jumlah_usd"]) - float(v["belanja_luar_usd"])
perlu = anggar * float(v["margin_kos"])
print(f"baki USD {baki:.6f}, perlu USD {perlu:.6f}")
sys.exit(0 if baki >= perlu else 1)
PY
)" || enggan "baki lejar tidak cukup atau tidak boleh dibaca (${baki:-ralat membaca config/lejar})"

if [ "$MOD" = kering ]; then
  echo "SEDIA: HEAD $SHA · tree bersih · §7-v21 sepadan · pindaan v2.1 ada · pengecam = $TAG_BEKU · tiada hasil ujian4 · tiada MULA · env + Modal ada · $baki (sha256 + make uji TIDAK disemak dalam --kering)"
  exit 0
fi

# sha256 ujian4.jsonl = KUNCI4.json = UJIAN4-MUKTAMAD (cincangan BAIT sahaja — kandungan tidak dibuka)
python3 -I - <<'PY' || enggan "sha256 ujian4 ≠ KUNCI4.json / UJIAN4-MUKTAMAD"
import hashlib, json, pathlib, sys
b = pathlib.Path("data/bench_v3")
f = b / "ujian4.jsonl"
s = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else ""
m = (b / "UJIAN4-MUKTAMAD").read_text().split()[0] if (b / "UJIAN4-MUKTAMAD").is_file() else None
sys.exit(0 if s and s == json.loads((b / "KUNCI4.json").read_text())["ujian4"]["sha256"] == m else 1)
PY

uv run pytest -q >/dev/null 2>&1 || enggan "make uji (uv run pytest -q) gagal"

# ---- larian ----
u3_mula
u3_larian

python3 -I - "$D" "$SHA" "$PELAKSANA" <<'PY' || echo "RINGKASAN.json gagal dijana — hasil mentah dalam arkib" >"$D/RINGKASAN-RALAT"
import json, pathlib, re, sys
d, sha, pelaksana = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
h = json.loads((d / "hasil/v21/ujian4-h5.json").read_text())
f1 = {}
for p in sorted((d / "hasil/v21").glob("ujian4-*.json")):
    if p.name == "ujian4-h5.json":
        continue
    v = json.loads(p.read_text()).get("semua|*")
    if v:
        f1[p.stem.removeprefix("ujian4-")] = {k: v["tepat"][k] for k in ("p", "r", "f1")}
llm = {}
for f in sorted((d / "log").glob("*.log")):
    for b in f.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(llm:\S+): (\{.*\})$", b)
        if m:
            st = json.loads(m.group(2))
            llm[m.group(1)] = {k: st.get(k) for k in ("dokumen", "panggilan", "gagal", "rosak")}
luar = {p.name: json.loads(p.read_text()) for p in sorted((d / "hasil/luar").glob("ujian4-*.versi.json"))}
lejar = d / "cache" / "hasil/cache/llm/anthropic-lejar.json"
r = {"sha": sha, "pelaksana": pelaksana, "split": "ujian4", "dokumen": h["dokumen"], "f1_jenis": f1,
     "hipotesis": h["hipotesis"], "susulan": h["susulan"], "holm_k": h["k"], "alfa": h["alfa"], "llm": llm, "luar": luar,
     "lejar_usd_selepas": json.loads(lejar.read_text())["jumlah_usd"] if lejar.exists() else None}
(d / "RINGKASAN.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
PY

u3_selesai
