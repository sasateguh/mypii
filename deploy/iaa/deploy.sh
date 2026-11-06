#!/usr/bin/env bash
# deploy.sh — halaman semakan IAA mypii (PELAN-IAA, ADR-015) di https://semak-mypii.sasateguh.com
#
#   deploy.sh [ref]                    bina dari git archive <ref> (lalai origin/main) → naik → sahkan; GAGAL = undur
#   deploy.sh --status                 imej hidup + kesihatan, imej undur, jawapan awam, kemajuan setiap penyemak (x/300)
#   deploy.sh --undur                  kembali ke imej yang dipegang mypii-iaa-undur
#   deploy.sh --penyemak tambah <id>   token rawak → penyemak.json (0600) + mula semula kontena (token dimuat semasa mula)
#   deploy.sh --penyemak pautan <id>   cetak pautan ke TERMINAL sahaja — jangan tampal ke log/komit/LOG-ITERASI
#   deploy.sh --penyemak senarai       nama penyemak (tiada token)
#   deploy.sh --penyemak mesej <id>    SATU mesej Telegram (teks BM+EN tanpa URL, pautan dalam BUTANG sahaja); penanda = enggan ulang
#   deploy.sh --help
#
# Ujian ganti arahan luar melalui env: IAA_PAUTAN (lalai `docker exec … penyemak pautan`), IAA_MESEJ, NOTIFY_BIN.
# Data = $DATA (luar repo, backup harian ~/ops): dokumen.json (bundel, `make iaa-pakej`), jawapan.sqlite, penyemak.json.
# Bina dari git archive, bukan folder kerja: hanya yang dikomit pergi ke pembina; .dockerignore = senarai benar.
# Imej undur dipegang kontena BERHENTI mypii-iaa-undur (pemangkasan Coolify memadam imej tanpa kontena).
# Nama hos/port: config/mypii.yaml iaa.pelayan + semak-mypii.traefik.yaml (diubah bersama).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
NAME=mypii-iaa
URL=https://semak-mypii.sasateguh.com
DATA="${MYPII_IAA_FOLDER:-$HOME/ops/mypii/iaa}"
HIST="${IAA_DEPLOY_LOG:-$HOME/ops/mypii/iaa-deploy.log}"
say()  { printf '\033[1m▸ %s\033[0m\n' "$*"; }
warn() { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; }
notify() { [ -x "$HOME/bin/notify.sh" ] && "$HOME/bin/notify.sh" "mypii IAA: $1" "${2:-info}" >/dev/null 2>&1 || true; }
bantuan() { sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; }

sedia_data() { # folder + token kosong 0600 (pelayan memerlukan penyemak.json semasa mula)
  mkdir -p "$DATA" && chmod 700 "$DATA"
  [ -f "$DATA/dokumen.json" ] || { warn "tiada $DATA/dokumen.json — jalankan \`make iaa-pakej\` dahulu"; return 1; }
  if [ ! -f "$DATA/penyemak.json" ]; then (umask 077 && echo '{}' >"$DATA/penyemak.json"); fi
  chmod 600 "$DATA/penyemak.json"
}
jalan() { # <imej>
  docker rm -fv "$NAME" >/dev/null 2>&1 || true
  docker run -d --name "$NAME" --network coolify --restart unless-stopped \
    --user "$(id -u):$(id -g)" \
    --read-only --tmpfs /tmp:size=8m --cap-drop ALL --security-opt no-new-privileges \
    --memory 192m --memory-swap 192m --cpus 0.5 --pids-limit 64 \
    --log-opt max-size=5m --log-opt max-file=2 \
    -v "$DATA:/data" -v "$DATA/dokumen.json:/data/dokumen.json:ro" \
    --label mypii.peranan=iaa "$1" >/dev/null
}
sihat_tempatan() { # kontena healthy dalam 60 s
  for _ in $(seq 30); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "$NAME" 2>/dev/null)" = healthy ] && return 0
    sleep 2
  done; return 1
}
sihat_awam() { # /sihat + robots melalui Cloudflare; / = 200 pintu + noindex; token rawak = 404 + badan pintu. Ulang ≥ 3 × 10 s.
  local n
  for n in 1 2 3 4; do
    if curl -fsS --max-time 15 -o /dev/null "$URL/sihat" \
       && curl -fsS --max-time 15 "$URL/robots.txt" | grep -q 'Disallow: /' \
       && curl -fsS --max-time 15 -D - -o /dev/null "$URL/" | grep -qi '^x-robots-tag:.*noindex' \
       && curl -fsS --max-time 15 "$URL/" | grep -aq 'data-pintu' \
       && [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$URL/s/bukan-token-$RANDOM")" = 404 ] \
       && curl -s --max-time 15 "$URL/s/bukan-token-$RANDOM" | grep -aq 'data-pintu'; then
      return 0
    fi
    [ "$n" -lt 4 ] && sleep 10
  done; return 1
}
pegang_undur() { # <imej>
  docker rm -fv "$NAME-undur" >/dev/null 2>&1 || true
  docker create --name "$NAME-undur" --network none --restart no --label mypii.peranan=iaa-undur "$1" >/dev/null
}
traefik() { docker cp "$HERE/semak-mypii.traefik.yaml" coolify-proxy:/traefik/dynamic/semak-mypii.yaml; }
operasi() { docker exec "$NAME" python -m mypii.iaa.operasi "$@"; }
mesej_penyemak() { # <id> — pautan hanya ke env NOTIFY_BUTANG (tidak dicetak/dilog); penanda 0600 ditulis HANYA bila notify rc 0
  local id="$1" penanda teks butang pautan
  [[ "$id" =~ ^[a-z][a-z0-9_]{0,15}$ ]] || { warn "guna: --penyemak mesej <id>"; exit 2; }
  penanda="$DATA/mesej-$id.dihantar"
  [ -e "$penanda" ] && { warn "mesej $id sudah dihantar ($penanda) — tiada mesej kedua"; exit 1; }
  local -a cari bina
  read -ra cari <<<"${IAA_PAUTAN:-docker exec $NAME python -m mypii.iaa.operasi penyemak pautan}"
  read -ra bina <<<"${IAA_MESEJ:-uv run --project $REPO python -m mypii.iaa.mesej}"
  pautan=$("${cari[@]}" "$id" 2>/dev/null) || { warn "tiada pautan untuk $id"; exit 1; }
  teks=$("${bina[@]}" teks) || { warn "teks mesej ditolak"; exit 1; }
  butang=$(printf '%s' "$pautan" | "${bina[@]}" butang) || { warn "butang mesej ditolak"; exit 1; }
  unset pautan
  if ! NOTIFY_BUTANG="$butang" NOTIFY_TERUS=1 NOTIFY_KOD_KELUAR=1 "${NOTIFY_BIN:-$HOME/bin/notify.sh}" "$teks" info >/dev/null 2>&1; then
    warn "notify gagal — tiada penanda, boleh cuba lagi"; exit 1
  fi
  (umask 077 && : >"$penanda")
  log "penyemak mesej $id dihantar"; say "mesej $id dihantar (butang sahaja)"
}
log() { mkdir -p "$(dirname "$HIST")" && echo "$(date -u +%FT%TZ) $*" >>"$HIST"; }

case "${1:-}" in
  -h|--help) bantuan; exit 0 ;;
  --status)
    echo "hidup: $(docker inspect -f '{{.Config.Image}} {{.State.Status}} {{.State.Health.Status}}' "$NAME" 2>/dev/null | grep . || echo tiada)"
    echo "undur: $(docker inspect -f '{{.Config.Image}}' "$NAME-undur" 2>/dev/null | grep . || echo tiada)"
    echo "awam:  $(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$URL/sihat")"
    echo "kemajuan:"; operasi kemajuan 2>/dev/null | sed 's/^/  /' || echo "  (kontena tiada)"
    tail -3 "$HIST" 2>/dev/null || true
    exit 0 ;;
  --undur)
    img=$(docker inspect -f '{{.Config.Image}}' "$NAME-undur") || { warn "tiada imej undur"; exit 1; }
    sedia_data
    jalan "$img"
    if ! sihat_tempatan; then warn "$img tidak sihat selepas undur"; exit 1; fi
    say "undur ke $img"; log "undur $img"
    exit 0 ;;
  --penyemak)
    tindakan="${2:-}"
    case "$tindakan" in
      tambah)
        [ -n "${3:-}" ] || { warn "guna: --penyemak tambah <id>"; exit 2; }
        operasi penyemak tambah "$3"
        docker restart "$NAME" >/dev/null
        if ! sihat_tempatan; then warn "kontena tidak sihat selepas mula semula"; exit 1; fi
        log "penyemak tambah $3"; say "penyemak $3 aktif" ;;
      pautan|senarai) operasi penyemak "$tindakan" ${3:+"$3"} ;;
      mesej) mesej_penyemak "${3:-}" ;;
      *) warn "guna: --penyemak tambah|pautan|senarai|mesej [id]"; exit 2 ;;
    esac
    exit 0 ;;
  -*) warn "pilihan tidak dikenali: $1"; bantuan; exit 2 ;;
esac

ref="${1:-origin/main}"
df -h / | tail -1
git -C "$REPO" fetch -q origin
sha=$(git -C "$REPO" rev-parse --short=12 "$ref^{commit}")
img="$NAME:$sha"
lama=$(docker inspect -f '{{.Config.Image}}' "$NAME" 2>/dev/null || true)
sedia_data
say "bina $img dari $ref"
git -C "$REPO" archive --format=tar "$sha" | "$HOME/bin/bina-imej.sh" -f deploy/iaa/Dockerfile -t "$img" -
traefik
jalan "$img"
if sihat_tempatan && sihat_awam; then
  [ -n "$lama" ] && [ "$lama" != "$img" ] && pegang_undur "$lama"
  log "naik $img (sebelum: ${lama:-tiada})"
  say "HIDUP $img → $URL"
else
  warn "$img tidak sihat"
  docker logs --tail 30 "$NAME" >&2 || true
  if [ -n "$lama" ]; then jalan "$lama" && sihat_tempatan && warn "diundur ke $lama"; fi
  log "GAGAL $img (undur ke ${lama:-tiada})"
  notify "deploy $img GAGAL, undur ke ${lama:-tiada}" warn
  exit 1
fi
