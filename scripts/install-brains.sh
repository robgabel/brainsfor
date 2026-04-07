#!/usr/bin/env bash
set -euo pipefail

# BrainsForSale Installer
# Installs brain packs + universal skills into any project for use with Claude Code.
#
# Usage:
#   ./install-brains.sh /path/to/your/project                     # install all live brains
#   ./install-brains.sh /path/to/your/project scott-belsky         # install one brain
#   ./install-brains.sh /path/to/your/project scott-belsky paul-graham  # install specific brains
#
# What it does:
#   1. Copies brain data (brain-context.md, brain-atoms.json) to <project>/.brainsforsale/brains/<slug>/
#   2. Copies universal skills to <project>/.claude/skills/
#   3. Creates index.json with installed brain metadata
#
# After install, type / in Claude Code to see: advise, debate, brainfight, teach, etc.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BRAINS_DIR="$ROOT_DIR/brains"
TEMPLATES_DIR="$ROOT_DIR/templates"

# --- Parse args ---
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <target-project-dir> [brain-slug ...]"
    echo ""
    echo "Examples:"
    echo "  $0 ~/my-project                          # all live brains"
    echo "  $0 ~/my-project scott-belsky              # just Belsky"
    echo "  $0 ~/my-project scott-belsky paul-graham  # Belsky + PG"
    echo ""
    echo "Available brains:"
    if command -v python3 &>/dev/null && [[ -f "$BRAINS_DIR/index.json" ]]; then
        python3 -c "
import json
with open('$BRAINS_DIR/index.json') as f:
    data = json.load(f)
for b in data['brains']:
    status = '✓' if b['status'] == 'live' else '○'
    print(f\"  {status} {b['slug']:20s} {b['name']:20s} ({b['atom_count']} atoms, {b['status']})\")
"
    fi
    exit 1
fi

TARGET_DIR="$(cd "$1" && pwd)"
shift

# Determine which brains to install
if [[ $# -gt 0 ]]; then
    SLUGS=("$@")
else
    # Install all live brains
    SLUGS=()
    if [[ -f "$BRAINS_DIR/index.json" ]] && command -v python3 &>/dev/null; then
        while IFS= read -r slug; do
            SLUGS+=("$slug")
        done < <(python3 -c "
import json
with open('$BRAINS_DIR/index.json') as f:
    data = json.load(f)
for b in data['brains']:
    if b['status'] == 'live':
        print(b['slug'])
")
    fi
fi

if [[ ${#SLUGS[@]} -eq 0 ]]; then
    echo "ERROR: No brains to install. Check brains/index.json."
    exit 1
fi

echo "Installing BrainsForSale into: $TARGET_DIR"
echo "Brains: ${SLUGS[*]}"
echo ""

# --- 1. Copy brain data ---
INSTALL_DIR="$TARGET_DIR/.brainsforsale/brains"
mkdir -p "$INSTALL_DIR"

INSTALLED_BRAINS="[]"
for slug in "${SLUGS[@]}"; do
    PACK_DIR="$BRAINS_DIR/$slug/pack"
    if [[ ! -d "$PACK_DIR" ]]; then
        echo "  SKIP: $slug — no pack/ directory found"
        continue
    fi

    DEST="$INSTALL_DIR/$slug"
    mkdir -p "$DEST"

    # Copy the essential files
    for file in brain-context.md brain-atoms.json; do
        if [[ -f "$PACK_DIR/$file" ]]; then
            cp "$PACK_DIR/$file" "$DEST/"
            echo "  ✓ $slug/$file"
        else
            echo "  WARN: $slug/$file not found"
        fi
    done

    # Build index entry
    if [[ -f "$BRAINS_DIR/index.json" ]] && command -v python3 &>/dev/null; then
        INSTALLED_BRAINS=$(python3 -c "
import json
with open('$BRAINS_DIR/index.json') as f:
    data = json.load(f)
installed = json.loads('$INSTALLED_BRAINS')
for b in data['brains']:
    if b['slug'] == '$slug':
        installed.append(b)
        break
print(json.dumps(installed))
")
    fi
done

# Write index.json for installed brains
if command -v python3 &>/dev/null; then
    python3 -c "
import json
installed = json.loads('$INSTALLED_BRAINS')
index = {'brains': installed, 'installed_at': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'}
with open('$INSTALL_DIR/index.json', 'w') as f:
    json.dump(index, f, indent=2)
print('  ✓ index.json')
"
fi

# --- 2. Copy universal skills ---
echo ""
echo "Installing skills..."
SKILLS_SRC="$ROOT_DIR/pack/universal-skills"

# If universal skills haven't been rendered yet, render them
if [[ ! -d "$SKILLS_SRC" ]]; then
    echo "  Rendering universal skills from templates..."
    pushd "$ROOT_DIR" > /dev/null
    python3 -c "
import json
from pathlib import Path

TEMPLATES_DIR = Path('templates')
BRAINS_DIR = Path('brains')

universal_template_dir = TEMPLATES_DIR / 'universal-skills'
with open(universal_template_dir / '_brain-router.md.template') as f:
    router_content = f.read()

with open(BRAINS_DIR / 'index.json') as f:
    index_data = json.load(f)
available_brains = [b for b in index_data.get('brains', []) if b.get('status') == 'live']

brain_list = '\n### Currently Available Brains\n\n'
for b in available_brains:
    brain_list += f\"- \\\`--{b['slug']}\\\` — **{b['name']}** ({b['atom_count']} atoms from {b['source']})\n\"

router_with_brains = router_content + brain_list
output_dir = Path('pack/universal-skills')
output_dir.mkdir(parents=True, exist_ok=True)

for tf in sorted(universal_template_dir.glob('*.template')):
    if tf.name.startswith('_'):
        continue
    with open(tf) as f:
        content = f.read()
    content = content.replace('{{_brain-router}}', router_with_brains)
    skill_name = tf.stem.removesuffix('.md')
    skill_dir = output_dir / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    with open(skill_dir / 'SKILL.md', 'w') as f:
        f.write(content)
"
    popd > /dev/null
fi

# Copy skills to target project's .claude/skills/
SKILLS_DEST="$TARGET_DIR/.claude/skills"
mkdir -p "$SKILLS_DEST"

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    mkdir -p "$SKILLS_DEST/$skill_name"
    cp "$skill_dir/SKILL.md" "$SKILLS_DEST/$skill_name/SKILL.md"
    echo "  ✓ /$(basename "$skill_dir")"
done

# --- 3. Summary ---
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  BrainsForSale installed successfully!"
echo ""
echo "  Brains:  $INSTALL_DIR/"
echo "  Skills:  $SKILLS_DEST/"
echo ""
echo "  Open Claude Code in $TARGET_DIR and type /"
echo "  to see: advise, debate, brainfight, teach..."
echo ""
echo "  Try:  /advise --${SLUGS[0]} \"Your question\""
if [[ ${#SLUGS[@]} -gt 1 ]]; then
echo "  Try:  /brainfight --${SLUGS[0]} --${SLUGS[1]} \"topic\""
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
