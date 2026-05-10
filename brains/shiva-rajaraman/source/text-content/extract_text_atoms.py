#!/usr/bin/env python3
"""One-shot atom extraction from selected high-yield text URLs for Shiva brain."""
import json
import os
import sys
from pathlib import Path
import httpx

SCRIPTS_DIR = Path(__file__).resolve().parents[4] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import importlib.util
spec = importlib.util.spec_from_file_location("auto_build", SCRIPTS_DIR / "auto-build-brain.py")
auto_build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_build)
from auto_build_config import CostTracker, DEFAULT_MODEL
import anthropic

BRAIN_DIR = Path(__file__).resolve().parents[2]
brain_json = json.load(open(BRAIN_DIR / "brain.json"))

client = anthropic.Anthropic()
cost = CostTracker()
firecrawl_key = os.environ["FIRECRAWL_API_KEY"]

# 4 voice-rich text sources (verified to contain real Shiva quotes, not just news about his products)
sources = [
    {"title": "Berkeley DDD Episode 008: Managing Products with Data", "type": "podcast-transcript",
     "url": "https://design.berkeley.edu/ddd-episode-008"},
    {"title": "Egon Zehnder: What's Next for Product", "type": "interview",
     "url": "https://www.egonzehnder.com/functions/technology-officers/insights/whats-next-for-product"},
    {"title": "Product School: Product Management at Spotify Q&A", "type": "interview",
     "url": "https://productschool.dev/blog/career-development/product-management-spotify-former-vp-product"},
    {"title": "Mind the Product 2015: Going from Meh to Awesome", "type": "talk-summary",
     "url": "https://www.mindtheproduct.com/learnings-from-london-going-from-meh-to-awesome-by-shiva-rajaraman/"},
]

def fetch(url):
    resp = httpx.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {firecrawl_key}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
        timeout=60,
    )
    if resp.status_code != 200:
        return None
    data = resp.json().get("data", {})
    return data.get("markdown", "")

all_atoms = []
for src in sources:
    print(f"Fetching: {src['title'][:60]}")
    content = fetch(src["url"])
    if not content or len(content) < 500:
        print(f"  SKIP: thin content ({len(content) if content else 0} chars)")
        continue
    print(f"  Got {len(content)} chars. Extracting...")
    atoms = auto_build.extract_atoms_from_text(
        brain_json, src, content, client, cost, DEFAULT_MODEL
    )
    print(f"  → {len(atoms)} atoms")
    all_atoms.extend(atoms)

out_path = BRAIN_DIR / "research" / "text-source-atoms.json"
json.dump(all_atoms, open(out_path, "w"), indent=2)
print(f"\nTotal: {len(all_atoms)} atoms saved to {out_path}")
