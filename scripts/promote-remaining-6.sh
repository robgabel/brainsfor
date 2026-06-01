#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
set -a; . ~/rob-ai/.env; set +a
LOG="brains/promote-remaining-6.log"
echo "=== promote-remaining-6 started $(date) ===" | tee -a "$LOG"
for slug in elon-musk brene-brown oprah-winfrey dario-amodei gokul-rajaram peter-zeihan; do
  echo "[$(date +%H:%M)] FORCE-PROMOTING $slug..." | tee -a "$LOG"
  out=$(python3 scripts/promote-brain.py --slug "$slug" --force 2>&1)
  echo "$out" >> "$LOG"
  if echo "$out" | grep -q "DONE"; then
    a=$(python3 -c "import json;print([b['atom_count'] for b in json.load(open('brains/index.json'))['brains'] if b['slug']=='$slug'][0])" 2>/dev/null||echo '?')
    echo "[$(date +%H:%M)] OK    $slug ($a atoms)" | tee -a "$LOG"
  else
    echo "[$(date +%H:%M)] FAIL  $slug" | tee -a "$LOG"; echo "$out" | tail -4 >> "$LOG"
  fi
done
echo "=== done $(date) ===" | tee -a "$LOG"
