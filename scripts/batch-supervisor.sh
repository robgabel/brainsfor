#!/usr/bin/env bash
# "Keep building brains" supervisor. Waits for any in-flight batch driver / build
# to finish, then re-runs the batch driver to retry any brain that isn't yet
# phase-5-complete (the driver skips completed brains and --resumes the rest with
# the resilient code). Loops until all Tier-1 brains are complete or rounds run out.
# Sequential by construction — it never launches a build while one is running, so
# no API contention.
set -u
cd "$(dirname "$0")/.." || exit 1
set -a; . ~/rob-ai/.env; set +a

LOG="brains/batch-supervisor.log"
BRAINS=(sun-tzu paul-graham charlie-munger gary-vee elon-musk jensen-huang brene-brown oprah-winfrey john-green hank-green)
echo "=== supervisor started $(date) ===" >> "$LOG"

complete_count() {
  local n=0
  for b in "${BRAINS[@]}"; do
    local p="brains/${b}-v2/build-progress.json"
    if [ -f "$p" ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$p'))['phases']['5']['status']=='complete' else 1)" 2>/dev/null; then
      n=$((n+1))
    fi
  done
  echo "$n"
}

for round in 1 2 3 4; do
  # Wait for any running driver or build to finish before acting.
  while pgrep -f "batch-rebuild-tier1.sh" >/dev/null 2>&1 || pgrep -f "auto-build-brain.py --person" >/dev/null 2>&1; do
    sleep 60
  done
  done_n=$(complete_count); total=${#BRAINS[@]}
  echo "[$(date +%H:%M)] round $round: $done_n/$total complete" | tee -a "$LOG"
  [ "$done_n" -ge "$total" ] && { echo "[$(date +%H:%M)] ALL $total COMPLETE" | tee -a "$LOG"; break; }
  echo "[$(date +%H:%M)] re-running driver to finish the remaining $((total-done_n))..." | tee -a "$LOG"
  bash scripts/batch-rebuild-tier1.sh
done

echo "=== supervisor finished $(date): $(complete_count)/${#BRAINS[@]} complete ===" | tee -a "$LOG"
