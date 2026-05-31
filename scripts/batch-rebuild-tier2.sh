#!/usr/bin/env bash
# Tier-2 rebuild driver: the 10 remaining brains, full rebuild on the hardened
# factory, ranked worst-first. Same self-heal pattern as tier1 (retry via --resume
# up to 2x). Sequential to avoid Anthropic rate-limit collisions.
set -u
cd "$(dirname "$0")/.." || exit 1
set -a; . ~/rob-ai/.env; set +a

BATCH_LOG="brains/batch-rebuild-tier2.log"
echo "=== tier2 rebuild started $(date) ===" >> "$BATCH_LOG"

# slug|Person Name  — worst-first (yann/kara have real defects; rest for uniformity)
BRAINS=(
  "yann-lecun|Yann LeCun"
  "kara-swisher|Kara Swisher"
  "peter-attia|Peter Attia"
  "dario-amodei|Dario Amodei"
  "sara-blakely|Sara Blakely"
  "gokul-rajaram|Gokul Rajaram"
  "bill-harris|Bill Harris"
  "shiva-rajaraman|Shiva Rajaraman"
  "jeremy-utley|Jeremy Utley"
  "peter-zeihan|Peter Zeihan"
)

for entry in "${BRAINS[@]}"; do
  slug="${entry%%|*}"; name="${entry##*|}"; vslug="${slug}-v2"
  prog="brains/${vslug}/build-progress.json"
  if [ -f "$prog" ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$prog'))['phases']['5']['status']=='complete' else 1)" 2>/dev/null; then
    echo "[$(date +%H:%M)] SKIP $vslug (already complete)" | tee -a "$BATCH_LOG"
    continue
  fi
  echo "[$(date +%H:%M)] BUILD $vslug ($name) starting..." | tee -a "$BATCH_LOG"
  resume_flag=""
  [ -f "$prog" ] && resume_flag="--resume"
  rc=1
  for try in 1 2 3; do
    python3 scripts/auto-build-brain.py --person "$name" --slug "$vslug" --reference "$slug" $resume_flag \
      >> "brains/${vslug}-build.log" 2>&1
    rc=$?
    [ $rc -eq 0 ] && break
    if [ -f "$prog" ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$prog'))['phases']['5']['status']=='complete' else 1)" 2>/dev/null; then
      rc=0; break
    fi
    echo "[$(date +%H:%M)] RETRY $vslug (attempt $try failed rc=$rc, resuming)..." | tee -a "$BATCH_LOG"
    resume_flag="--resume"; sleep 10
  done
  if [ -f "$prog" ]; then
    summary=$(python3 -c "import json;d=json.load(open('$prog'));p=d['phases'];print('p5='+p['5']['status'],'atoms='+str(p['2'].get('atoms','?')),'score='+str(p['5'].get('audit_score','?')),'cost=\$%.2f'%d.get('total_cost_usd',0))" 2>/dev/null)
  else
    summary="no progress file"
  fi
  echo "[$(date +%H:%M)] DONE  $vslug rc=$rc $summary" | tee -a "$BATCH_LOG"
done

echo "=== tier2 rebuild finished $(date) ===" | tee -a "$BATCH_LOG"
