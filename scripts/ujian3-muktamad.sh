#!/usr/bin/env bash
# Ujian3 muktamad SATU-TEMBAK — PRA-DAFTAR §7-v2 (pindaan 2026-11-04 "MyPII v2") + pindaan 2026-11-05 (e), PELAN-V2 P14/P15.
#
#   bash scripts/ujian3-muktamad.sh                          # larian SEBENAR, SEKALI
#   bash scripts/ujian3-muktamad.sh --kering                 # semua semakan KECUALI sha256 split + make uji → SEDIA / TIDAK SEDIA
#   bash scripts/ujian3-muktamad.sh --ulang-crash "<sebab>"  # SEKALI, hanya bila MULA wujud tanpa SELESAI (larian crash)
#
# Menjalankan DUA perintah blok §7-v2 TEPAT (ramalan, kemudian statistik). Ramalan yang mencetak `panggilan gagal` diulang SEKALI
# (cache disambung). Semua semakan enggan SEBELUM uv/harness dipanggil. Kunci dari fail env, tidak pernah dicetak (tiada `set -x`).
# Selepas: hasil + ramalan + cache/lejar LLM ujian3 + log → arkib LUAR repo (chmod 700, MANIFEST.sha256); cache + lejar dipulih
# dalam repo (TIDAK dikomit — §7-v2); tree mesti bersih → RINGKASAN.json + SELESAI.
# Env (ujian sahaja): MYPII_ARKIB (lalai ~/ops/mypii/arkib-ujian3), MYPII_ENV_DIR (lalai ~/ops/mypii), MYPII_PELAKSANA.
# Kod keluar: 0 SEDIA/SELESAI · 2 hujah salah · 4 enggan (tiada harness) · 5 crash · 6 tree tidak bersih selepas pulih.
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
AKAR="$(pwd)"
ARKIB="${MYPII_ARKIB:-$HOME/ops/mypii/arkib-ujian3}"
ENV_DIR="${MYPII_ENV_DIR:-$HOME/ops/mypii}"
PELAKSANA="${MYPII_PELAKSANA:-sesi interaktif pemilik 5 Nov 2026 (pindaan 2026-11-05 e)}"
FAIL_ENV=(anthropic.env)
CACHE=hasil/cache/llm
HASIL='ujian3*'
SKRIP=scripts/ujian3-muktamad.sh
PRADAFTAR=docs/PRA-DAFTAR.md
BEKU='^### [0-9]{4}-[0-9]{2}-[0-9]{2}.*MyPII v2: kuasa \+ pengecam dibekukan'

# Blok §7-v2 PRA-DAFTAR, bait sama (disemak semasa larian di bawah). JANGAN sunting.
PERINTAH=(
'uv run --extra nilai --extra garis python -m mypii.nilai.harness --split ujian3 --sistem mypii mypii-v1 presidio-asal llm:anthropic/claude-haiku-5-5 --benarkan-ujian'
'uv run python -m mypii.nilai.harness --split ujian3 --sistem mypii mypii-v1 presidio-asal llm:anthropic/claude-haiku-5-5 --statistik --benarkan-ujian'
)

. "$AKAR/scripts/muktamad-lib.sh"   # pustaka v3 (skrip v1 = fail larangan, tidak disentuh)
u3_hujah "$@"

# ---- semakan (TIADA uv / harness sebelum semua lulus) ----
u3_semak_arkib

# dua perintah = blok §7-v2 dalam PRA-DAFTAR di HEAD (bait sama, susunan sama)
python3 -I - "$(git show "HEAD:$PRADAFTAR" 2>/dev/null)" "${PERINTAH[@]}" <<'PY' || enggan "perintah skrip ≠ blok §7-v2 $PRADAFTAR"
import re, sys
m = re.search(r"^#### §7-v2 Perintah tepat ujian3\n```\n(.*?)\n```", sys.argv[1], re.S | re.M)
sys.exit(0 if m and [b for b in m.group(1).splitlines() if b.strip()] == sys.argv[2:] else 1)
PY

# pindaan pembekuan pengecam wujud dalam HEAD (§7-v2: "pindaan kedua 'MyPII v2'" = pindaan (e))
git show "HEAD:$PRADAFTAR" 2>/dev/null | grep -qE "$BEKU" || enggan "pindaan 'MyPII v2: kuasa + pengecam dibekukan' tiada dalam HEAD"

u3_semak_hasil

for f in "${FAIL_ENV[@]}"; do [ -r "$ENV_DIR/$f" ] || enggan "fail env tiada: $ENV_DIR/$f"; done

# baki = had − lejar repo − belanja luar repo (ujian v1); anggaran Haiku ujian3 = USD purata setiap panggilan Haiku × dokumen × nisbah saiz
baki="$(python3 -I - <<'PY'
import json, pathlib, sys, yaml
c = yaml.safe_load(pathlib.Path("config/mypii.yaml").read_text(encoding="utf-8"))
a, v2 = c["garis_dasar"]["llm"]["anthropic"], c["nilai"]["statistik"]["v2"]
lejar = json.loads(pathlib.Path(a["lejar"]).read_text())
h = lejar["model"][v2["hipotesis"]["H4a"]["sistem"].removeprefix("llm:")]
f = {s: pathlib.Path(c["nilai"]["split_fail"][s]["fail"]) for s in ("dev3", "ujian3")}
dok = sum(1 for _ in f["ujian3"].open(encoding="utf-8"))
anggar = h["usd"] / h["panggilan"] * dok * f["ujian3"].stat().st_size / f["dev3"].stat().st_size
baki = float(a["had_usd"]) - float(lejar["jumlah_usd"]) - float(v2["belanja_luar_usd"])
perlu = anggar * float(v2["margin_kos"])
print(f"baki USD {baki:.6f}, perlu USD {perlu:.6f}")
sys.exit(0 if baki >= perlu else 1)
PY
)" || enggan "baki lejar tidak cukup atau tidak boleh dibaca (${baki:-ralat membaca config/lejar})"

if [ "$MOD" = kering ]; then
  echo "SEDIA: HEAD $SHA · tree bersih · §7-v2 sepadan · pindaan beku ada · tiada hasil ujian3 · tiada MULA · env ada · $baki (sha256 + make uji TIDAK disemak dalam --kering)"
  exit 0
fi

# sha256 ujian3.jsonl = KUNCI3.json = UJIAN3-MUKTAMAD (cincangan BAIT sahaja — kandungan tidak dibuka)
python3 -I - <<'PY' || enggan "sha256 ujian3 ≠ KUNCI3.json / UJIAN3-MUKTAMAD"
import hashlib, json, pathlib, sys
b = pathlib.Path("data/bench_v3")
f = b / "ujian3.jsonl"
s = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else ""
m = (b / "UJIAN3-MUKTAMAD").read_text().split()[0] if (b / "UJIAN3-MUKTAMAD").is_file() else None
sys.exit(0 if s and s == json.loads((b / "KUNCI3.json").read_text())["ujian3"]["sha256"] == m else 1)
PY

uv run pytest -q >/dev/null 2>&1 || enggan "make uji (uv run pytest -q) gagal"

# ---- larian ----
u3_mula
u3_larian

python3 -I - "$D" "$SHA" "$PELAKSANA" <<'PY' || echo "RINGKASAN.json gagal dijana — hasil mentah dalam arkib" >"$D/RINGKASAN-RALAT"
import json, pathlib, re, sys, yaml
d, sha, pelaksana = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
c = yaml.safe_load(pathlib.Path("config/mypii.yaml").read_text(encoding="utf-8"))
s = json.loads(pathlib.Path("hasil/ujian3-statistik.json").read_text())
ku = s["kunci_utama"]
llm = {}
for f in sorted((d / "log").glob("*.log"), key=lambda f: (f.stem.split("-")[0], f.stem)):
    for b in f.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(llm:\S+): (\{.*\})$", b)
        if m:
            st = json.loads(m.group(2))
            llm[m.group(1)] = {k: st.get(k) for k in ("dokumen", "panggilan", "gagal", "rosak")}
lejar = d / "cache" / c["garis_dasar"]["llm"]["anthropic"]["lejar"]
r = {"sha": sha, "pelaksana": pelaksana, "split": "ujian3", "kunci": ku, "dokumen": s["dokumen"],
     "f1": {x: {k: v[ku][k] for k in ("f1", "bawah", "atas")} for x, v in s["sistem"].items()},
     "hipotesis": s["v2"]["hipotesis"], "holm_k": s["v2"]["k"], "alfa": s["v2"]["alfa"],
     "deskriptif": {x: {k: s["banding"][x][ku][k] for k in ("delta", "bawah", "atas", "p_bootstrap", "p_rawak")}
                    for x in sorted(s.get("eksplorasi") or []) if x in s["banding"]},
     "llm": llm, "lejar_usd_selepas": json.loads(lejar.read_text())["jumlah_usd"] if lejar.exists() else None}
(d / "RINGKASAN.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
PY

u3_selesai
