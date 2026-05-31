#!/usr/bin/env bash
# Chained Tier-2 supervisor. Waits until the Tier-1 batch (driver + supervisor +
# any build) is fully done, THEN runs the Tier-2 driver to rebuild the 10 remaining
# brains, re-running it until all 10 are phase-5-complete (or rounds run out).
# Sequential by construction — never builds while Tier-1 is still going, so no
# Anthropic rate-limit contention.
set -u
cd "$(dirname "$0")/.." || exit 1
set -a; . ~/rob-ai/.env; set +a

LOG="brains/batch-supervisor-tier2.log"
T2=(yann-lecun kara-swisher peter-attia dario-amodei sara-blakely gokul-rajaram bill-harris shiva-rajaraman jeremy-utley peter-zeihan)
echo "=== tier2 supervisor started $(date) ===" >> "$LOG"

# 1) Wait for ALL Tier-1 activity to finish (its supervisor, driver, and any build).
echo "[$(date +%H:%M)] waiting for Tier-1 to finish..." | tee -a "$LOG"
while pgrep -f "batch-supervisor.sh" >/dev/null 2>&1 \
   || pgrep -f "batch-rebuild-tier1.sh" >/dev/null 2>&1 \
   || pgrep -f "auto-build-brain.py --person" >/dev/null 2>&1; do
  sleep 120
done
echo "[$(date +%H:%M)] Tier-1 done — starting Tier-2 rebuilds" | tee -a "$LOG"

complete_count() {
  local n=0
  for b in "${T2[@]}"; do
    local p="brains/${b}-v2/build-progress.json"
    if [ -f "$p" ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$p'))['phases']['5']['status']=='complete' else 1)" 2>/dev/null; then
      n=$((n+1))
    fi
  done
  echo "$n"
}

for round in 1 2 3 4; do
  while pgrep -f "auto-build-brain.py --person" >/dev/null 2>&1; do sleep 60; done
  done_n=$(complete_count); total=${#T2[@]}
  echo "[$(date +%H:%M)] round $round: $done_n/$total complete" | tee -a "$LOG"
  [ "$done_n" -ge "$total" ] && { echo "[$(date +%H:%M)] ALL $total TIER-2 COMPLETE" | tee -a "$LOG"; break; }
  echo "[$(date +%H:%M)] running tier2 driver ($((total-done_n)) remaining)..." | tee -a "$LOG"
  bash scripts/batch-rebuild-tier2.sh
done

echo "=== tier2 supervisor finished $(date): $(complete_count)/${#T2[@]} complete ===" | tee -a "$LOG"
