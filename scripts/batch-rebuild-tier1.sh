#!/usr/bin/env bash
# Sequential Tier-1 rebuild driver. Builds each brain as <slug>-v2 on the fixed
# factory. Sequential (not parallel) to avoid Anthropic rate-limit collisions
# during the unattended run. Resumable: skips brains whose v2 build already
# reached Phase 5. Promotion is done separately (promote-brain.py) after review.
set -u
cd "$(dirname "$0")/.." || exit 1
set -a; . ~/rob-ai/.env; set +a

BATCH_LOG="brains/batch-rebuild.log"
echo "=== batch-rebuild started $(date) ===" >> "$BATCH_LOG"

# slug|Person Name
BRAINS=(
  "sun-tzu|Sun Tzu"
  "paul-graham|Paul Graham"
  "charlie-munger|Charlie Munger"
  "gary-vee|Gary Vaynerchuk"
  "elon-musk|Elon Musk"
  "jensen-huang|Jensen Huang"
  "brene-brown|Brené Brown"
  "oprah-winfrey|Oprah Winfrey"
  # Hidden (Rob-only) old-factory brains — rebuilt too; promote-brain.py preserves
  # their hidden status so they stay off brainsforfree.com.
  "john-green|John Green"
  "hank-green|Hank Green"
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
  # Self-heal: a build that exits non-zero (transient API/network fault) is
  # retried via --resume up to 2x before being declared failed. Phases are
  # idempotent/resumable, so a retry picks up exactly where it died — no rework.
  rc=1
  for try in 1 2 3; do
    python3 scripts/auto-build-brain.py --person "$name" --slug "$vslug" --reference "$slug" $resume_flag \
      >> "brains/${vslug}-build.log" 2>&1
    rc=$?
    [ $rc -eq 0 ] && break
    # If phase 5 is already complete, treat as success regardless of exit code.
    if [ -f "$prog" ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$prog'))['phases']['5']['status']=='complete' else 1)" 2>/dev/null; then
      rc=0; break
    fi
    echo "[$(date +%H:%M)] RETRY $vslug (attempt $try failed rc=$rc, resuming)..." | tee -a "$BATCH_LOG"
    resume_flag="--resume"
    sleep 10
  done
  # capture result
  if [ -f "$prog" ]; then
    summary=$(python3 -c "import json;d=json.load(open('$prog'));p=d['phases'];print('p5='+p['5']['status'],'atoms='+str(p['2'].get('atoms','?')),'score='+str(p['5'].get('audit_score','?')),'cost=\$%.2f'%d.get('total_cost_usd',0))" 2>/dev/null)
  else
    summary="no progress file"
  fi
  echo "[$(date +%H:%M)] DONE  $vslug rc=$rc $summary" | tee -a "$BATCH_LOG"
done

echo "=== batch-rebuild finished $(date) ===" | tee -a "$BATCH_LOG"
