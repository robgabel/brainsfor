#!/usr/bin/env bash
# Re-finalize all 20 brains' Supabase to full pack parity + embeddings. Runs
# finalize per brain in FRESH processes (up to 5x) to beat the ~480-row/process
# rate ceiling; the only-missing upsert closes the gap each pass. Idempotent.
set -u
cd "$(dirname "$0")/.."
set -a; . ~/rob-ai/.env; set +a
LOG="brains/reload-all-supabase.log"
echo "=== reload-all started $(date) ===" | tee -a "$LOG"
BRAINS=(sun-tzu paul-graham charlie-munger gary-vee elon-musk jensen-huang brene-brown oprah-winfrey john-green hank-green yann-lecun kara-swisher peter-attia dario-amodei sara-blakely gokul-rajaram bill-harris shiva-rajaraman jeremy-utley peter-zeihan)
pack_count() { python3 -c "import json;print(len(json.load(open('brains/$1/pack/brain-atoms.json'))['atoms']))" 2>/dev/null||echo 0; }
db_count() { python3 -c "
import os,httpx
u=os.environ['SUPABASE_URL'].rstrip('/');k=os.environ['SUPABASE_SERVICE_KEY']
r=httpx.get(f'{u}/rest/v1/$1_atoms?select=id',headers={'apikey':k,'Authorization':f'Bearer {k}','Prefer':'count=exact','Range':'0-0'},timeout=30)
print(r.headers.get('content-range','*/0').split('/')[-1])" 2>/dev/null||echo 0; }
for slug in "${BRAINS[@]}"; do
  us=$(echo "$slug"|tr '-' '_'); pc=$(pack_count "$slug")
  for try in 1 2 3 4 5; do
    dc=$(db_count "$us")
    if [ "$dc" = "$pc" ]; then echo "[$(date +%H:%M)] $slug: $dc/$pc OK (try $try)" | tee -a "$LOG"; break; fi
    echo "[$(date +%H:%M)] $slug: $dc/$pc — finalize pass $try" | tee -a "$LOG"
    python3 scripts/finalize-supabase.py --brain "$slug" >> "$LOG" 2>&1
  done
done
echo "=== reload-all finished $(date) ===" | tee -a "$LOG"
