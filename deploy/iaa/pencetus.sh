#!/usr/bin/env bash
# pencetus.sh — cron harian `# IAA-MYPII` (PELAN-IAA P10, ADR-015): bila penyemak MANUSIA (p1, p2, …) mencapai n/n,
# beratur autopilot `mypii` SEKALI (P11 = skor akhir). Penyemak `uji` (ujian pelayar) tidak dikira.
#
#   pencetus.sh            semak kemajuan → `autopilot mula mypii` bila ada penyemak baru selesai → penanda
#   pencetus.sh --help
#
# Penanda: $DATA/pencetus-<id>.selesai (ditulis HANYA bila `mula` keluar 0 → tiada cetusan berulang; gagal = cuba esok).
# Log: ~/ops/mypii/iaa-pencetus.log (KIRAAN sahaja — tiada token/teks). Cron PATH = /usr/bin:/bin: hanya docker + python3 hos.
# Undur: `crontab -l | grep -v IAA-MYPII | crontab -`.
# Ujian (tests/test_iaa_pencetus.py) menggantikan arahan luar melalui IAA_KEMAJUAN / IAA_MULA.
set -uo pipefail
DATA="${MYPII_IAA_FOLDER:-$HOME/ops/mypii/iaa}"
LOG="${IAA_PENCETUS_LOG:-$HOME/ops/mypii/iaa-pencetus.log}"
KEMAJUAN="${IAA_KEMAJUAN:-docker exec mypii-iaa python -m mypii.iaa.operasi kemajuan}"
MULA="${IAA_MULA:-python3 $HOME/ops/autopilot/autopilot.py mula mypii}"

case "${1:-}" in -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac
log() { mkdir -p "$(dirname "$LOG")" && echo "$(date -u +%FT%TZ) $*" >>"$LOG"; }

# "p1 12/300" setiap baris; arahan dipecah pada ruang (tiada eval)
read -ra arahan <<<"$KEMAJUAN"
if ! keadaan=$("${arahan[@]}" 2>/dev/null) || [ -z "$keadaan" ]; then
  log "kemajuan GAGAL (kontena tiada?) — cuba esok"; exit 1
fi

baru=()
while read -r id kiraan; do
  [[ "$id" =~ ^[a-z][a-z0-9_-]{0,15}$ && "$kiraan" =~ ^([0-9]+)/([0-9]+)$ ]] || continue
  [ "$id" = uji ] && continue
  siap=${BASH_REMATCH[1]}; n=${BASH_REMATCH[2]}
  if [ "$n" -gt 0 ] && [ "$siap" -ge "$n" ] && [ ! -e "$DATA/pencetus-$id.selesai" ]; then baru+=("$id"); fi
done <<<"$keadaan"

log "kemajuan: $(echo "$keadaan" | grep -v '^uji ' | tr '\n' ' ')"
[ "${#baru[@]}" -eq 0 ] && exit 0

read -ra mula <<<"$MULA"
if "${mula[@]}" >/dev/null 2>&1; then
  for id in "${baru[@]}"; do : >"$DATA/pencetus-$id.selesai"; done
  log "SELESAI ${baru[*]} → autopilot mula mypii (P11)"
else
  log "autopilot mula GAGAL (rc $?) untuk ${baru[*]} — tiada penanda, cuba esok"; exit 1
fi
