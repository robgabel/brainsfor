#!/usr/bin/env bash
# Promote all 20 rebuilt brains sequentially (no commit/push — operator reviews diff).
set -u
cd "$(dirname "$0")/.."
set -a; . ~/rob-ai/.env; set +a

LOG="brains/promote-all.log"
echo "=== promote-all started $(date) ===" | tee -a "$LOG"

BRAINS=(
  sun-tzu paul-graham charlie-munger gary-vee elon-musk
  jensen-huang brene-brown oprah-winfrey john-green hank-green
  yann-lecun kara-swisher peter-attia dario-amodei sara-blakely
  gokul-rajaram bill-harris shiva-rajaraman jeremy-utley peter-zeihan
)

ok=0; fail=0
for slug in "${BRAINS[@]}"; do
  echo "[$(date +%H:%M)] PROMOTING $slug..." | tee -a "$LOG"
  out=$(python3 scripts/promote-brain.py --slug "$slug" 2>&1)
  echo "$out" >> "$LOG"
  if echo "$out" | grep -q "DONE"; then
    atoms=$(python3 -c "import json;d=json.load(open('brains/index.json'));print([b['atom_count'] for b in d['brains'] if b['slug']=='$slug'][0])" 2>/dev/null || echo "?")
    echo "[$(date +%H:%M)] OK    $slug ($atoms atoms)" | tee -a "$LOG"
    ok=$((ok+1))
  else
    echo "[$(date +%H:%M)] FAIL  $slug" | tee -a "$LOG"
    echo "$out" | grep -E "ERR|error|WARN|Traceback" | tail -4 >> "$LOG"
    fail=$((fail+1))
  fi
done

echo "=== done $(date): ok=$ok fail=$fail ===" | tee -a "$LOG"
