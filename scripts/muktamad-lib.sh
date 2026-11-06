# shellcheck shell=bash
# Pustaka ujian3 muktamad (PELAN-V2 P14) — di-`source` oleh `scripts/ujian3-muktamad.sh` SAHAJA.
# `scripts/ujian-muktamad.sh` (v1) ialah fail LARANGAN (rekod v1 muktamad) dan TIDAK memakai pustaka ini; logik di sini ialah
# pelaksanaan semula untuk v3 (bukan salinan baris), supaya pagar `pendua` lulus tanpa menyentuh skrip v1.
# Pemanggil menetapkan: ARKIB, PELAKSANA, PERINTAH[], CACHE, HASIL (glob), SKRIP, FAIL_ENV[], ENV_DIR.
# Ditetapkan di sini: MOD, SEBAB_ULANG, D, SHA, tamat. Kod keluar: 2 hujah · 4 enggan · 5 crash · 6 tree.

u3_hujah() {
  MOD=sebenar; SEBAB_ULANG=""
  local had=1
  if [ "${1:-}" = --kering ]; then MOD=kering
  elif [ "${1:-}" = --ulang-crash ]; then
    MOD=ulang; SEBAB_ULANG="${2:-}"; had=2
    if [ -z "$SEBAB_ULANG" ]; then echo "--ulang-crash perlukan sebab: --ulang-crash \"<sebab>\"" >&2; exit 2; fi
  elif [ -n "${1:-}" ]; then echo "hujah tidak dikenali: $1 (pilihan: --kering | --ulang-crash \"<sebab>\")" >&2; exit 2
  fi
  if [ $# -gt "$had" ]; then echo "hujah berlebihan" >&2; exit 2; fi
}

enggan() {
  [ "$MOD" = kering ] && echo "TIDAK SEDIA: $*" || echo "ENGGAN: $*" >&2
  exit 4
}

_u3_penanda() {  # $1 = nama fail penanda → senarai folder larian yang memilikinya
  [ -d "$ARKIB" ] || return 0
  find "$ARKIB" -mindepth 2 -maxdepth 2 -name "$1" -printf '%h\n' | sort
}

u3_semak_arkib() {
  git rev-parse --verify -q HEAD >/dev/null || enggan "$(pwd) bukan repo git dengan komit"
  SHA="$(git rev-parse HEAD)"
  local -a ada_mula ada_tamat
  mapfile -t ada_mula < <(_u3_penanda MULA)
  mapfile -t ada_tamat < <({ _u3_penanda SELESAI; _u3_penanda GAGAL; } | sort -u)
  D=""
  case "$MOD" in
    ulang)
      [ ${#ada_mula[@]} -eq 1 ] || enggan "--ulang-crash perlukan tepat satu MULA dalam $ARKIB (ada ${#ada_mula[@]})"
      [ ${#ada_tamat[@]} -eq 0 ] || enggan "larian sudah SELESAI/GAGAL — tiada ulangan"
      D="${ada_mula[0]}"
      local pid; pid="$(cat "$D/PID" 2>/dev/null || true)"
      if [ ! -f "$D/CRASH" ] && { [ -z "$pid" ] || kill -0 "$pid" 2>/dev/null; }; then
        enggan "MULA wujud tanpa CRASH dan proses larian ${pid:-?} masih hidup — larian mungkin masih berjalan"
      fi
      [ ! -e "$D/ULANG-CRASH" ] || enggan "--ulang-crash sudah digunakan SEKALI — tiada ulangan kedua" ;;
    *) [ ${#ada_mula[@]} -eq 0 ] || enggan "penanda MULA sudah wujud dalam arkib (${ada_mula[0]}) — ujian3 SEKALI sahaja" ;;
  esac
  local kotor; kotor="$(git status --porcelain)"
  if [ "$MOD" = ulang ]; then kotor="$(grep -v " $CACHE/" <<<"$kotor" || true)"; fi
  [ -z "$kotor" ] || enggan "tree git tidak bersih: $(head -3 <<<"$kotor" | tr '\n' ' ')"
}

_u3_hasil() {  # fail hasil + ramalan split yang wujud
  local g
  for g in "hasil/$HASIL" "hasil/ramalan/$HASIL"; do
    # shellcheck disable=SC2086
    compgen -G "$g" || true
  done
}

u3_semak_hasil() {
  [ "$MOD" = ulang ] && return 0
  local ada; ada="$(_u3_hasil)"
  [ -z "$ada" ] || enggan "hasil ujian3 sudah wujud: $(head -3 <<<"$ada" | tr '\n' ' ')"
}

_u3_tulis() {  # $1 = fail penanda; baris kekunci:nilai dari hujah seterusnya + tarikh UTC
  local f="$1"; shift
  { printf '%s\n' "$@"; echo "tarikh_utc: $(date -u +%FT%TZ)"; } >"$f"
}

u3_mula() {
  if [ "$MOD" = ulang ]; then
    mkdir -p "$D/separa"
    _u3_hasil | while IFS= read -r f; do mv "$f" "$D/separa/"; done
    [ ! -d "$D/log" ] || mv "$D/log" "$D/separa/log"
    _u3_tulis "$D/ULANG-CRASH" "sebab: $SEBAB_ULANG" "sha: $SHA"
    rm -f "$D/CRASH"
  else
    mkdir -p "$ARKIB" && chmod 700 "$ARKIB"
    D="$ARKIB/$(date -u +%Y%m%dT%H%M%SZ)"; mkdir "$D"
    _u3_tulis "$D/MULA" "sha: $SHA" "pelaksana: $PELAKSANA" "uv: $(uv --version 2>&1)" \
      "python: $(uv run python --version 2>&1)" "${PERINTAH[@]/#/perintah: }"
  fi
  mkdir -p "$D/log"; echo $$ >"$D/PID"
  tamat=0
  trap '[ "$tamat" = 1 ] || [ -e "$D/CRASH" ] || _u3_tulis "$D/CRASH" "keluar tanpa SELESAI (rc $?)"' EXIT
  local f
  set -a
  for f in "${FAIL_ENV[@]}"; do . "$ENV_DIR/$f"; done
  set +a
}

u3_arkib_pulih() {  # $1 = folder sasaran: salin hasil/ramalan/cache berubah, pulih cache repo
  local k="$1" f
  mkdir -p "$k/hasil/ramalan" "$k/cache"
  _u3_hasil | while IFS= read -r f; do cp -p "$f" "$k/$(dirname "$f")/"; done
  git ls-files -m -o --exclude-standard -- "$CACHE" | while IFS= read -r f; do
    [ ! -e "$f" ] || cp -p --parents "$f" "$k/cache/"
  done
  git restore -- "$CACHE"; git clean -fdq -- "$CACHE"
}

_u3_satu() {  # $1 perintah, $2 log
  local -a h; read -ra h <<<"$1"
  echo "+ $1" >>"$D/log/$2.log"
  "${h[@]}" >>"$D/log/$2.log" 2>&1
}

_u3_crash() {  # $1 nombor perintah, $2 rc
  tamat=1
  if [ "$MOD" = ulang ]; then
    u3_arkib_pulih "$D/gagal"
    _u3_tulis "$D/GAGAL" "perintah $1 rc $2 selepas --ulang-crash"
    echo "GAGAL: perintah $1 crash (rc $2) selepas --ulang-crash — larian tidak sah; arkib $D" >&2
  else
    _u3_tulis "$D/CRASH" "perintah $1 rc $2"
    echo "CRASH: perintah $1 (rc $2) — log $D/log/$1.log; ulang SEKALI: bash $SKRIP --ulang-crash \"<sebab>\"" >&2
  fi
  exit 5
}

u3_larian() {
  local i rc
  for i in "${!PERINTAH[@]}"; do
    local n=$((i + 1)) p="${PERINTAH[$i]}"
    rc=0; _u3_satu "$p" "$n" || rc=$?
    if [ $rc -eq 0 ] && [[ "$p" != *--statistik* ]] && grep -q "panggilan gagal" "$D/log/$n.log"; then
      rc=0; _u3_satu "$p" "$n-ulang" || rc=$?
    fi
    [ $rc -eq 0 ] || _u3_crash "$n" "$rc"
  done
  u3_arkib_pulih "$D"
  local kotor; kotor="$(git status --porcelain)"
  if [ -n "$kotor" ]; then
    tamat=1; echo "tree tidak bersih selepas pulih: $kotor" >"$D/GAGAL"
    echo "GAGAL: tree tidak bersih selepas pulih (hasil sudah dalam arkib $D): $kotor" >&2; exit 6
  fi
}

u3_selesai() {
  _u3_tulis "$D/SELESAI" "sha: $SHA"; tamat=1
  (cd "$D" && find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum >MANIFEST.sha256)
  chmod -R go-rwx "$D"
  echo "SELESAI: $D (RINGKASAN.json, MANIFEST.sha256)"
}
