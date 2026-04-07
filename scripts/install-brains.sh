#!/bin/bash
# install-brains.sh — Install/uninstall BrainsForSale brain packs into a target workspace
#
# Usage:
#   ./scripts/install-brains.sh <target_dir> <slug1> [slug2 ...]     # Install brains
#   ./scripts/install-brains.sh --uninstall <target_dir> <slug1> ... # Remove brains
#   ./scripts/install-brains.sh --list <target_dir>                  # Show installed brains
#   ./scripts/install-brains.sh --dry-run <target_dir> <slug1> ...   # Preview without writing
#
# Examples:
#   ./scripts/install-brains.sh ~/rob-ai scott-belsky paul-graham
#   ./scripts/install-brains.sh --uninstall ~/rob-ai paul-graham
#   ./scripts/install-brains.sh --list ~/rob-ai

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BRAINS_DIR="$(cd "$SCRIPT_DIR/../brains" && pwd)"
INDEX_FILE="$BRAINS_DIR/index.json"
SKILL_NAMES=(advise apply brainfight connect debate deep-dive evolve mashup surprise teach)

# --- Helpers ---

usage() {
    echo "Usage:"
    echo "  $0 <target_dir> <slug1> [slug2 ...]"
    echo "  $0 --uninstall <target_dir> <slug1> [slug2 ...]"
    echo "  $0 --list <target_dir>"
    echo "  $0 --dry-run <target_dir> <slug1> [slug2 ...]"
    exit 1
}

validate_slug() {
    local slug="$1"
    if [ ! -f "$INDEX_FILE" ]; then
        echo "  WARN  index.json not found — skipping registry check"
        return 0
    fi
    # Check if slug appears in index.json
    if ! grep -q "\"slug\": \"$slug\"" "$INDEX_FILE"; then
        echo "  ERROR $slug not found in brains/index.json"
        return 1
    fi
    return 0
}

validate_pack() {
    local slug="$1"
    local pack_dir="$BRAINS_DIR/$slug/pack"
    local ok=true

    if [ ! -d "$pack_dir" ]; then
        echo "  ERROR $slug: pack/ directory not found at $pack_dir"
        return 1
    fi
    for f in SKILL.md brain-context.md brain-atoms.json; do
        if [ ! -f "$pack_dir/$f" ]; then
            echo "  ERROR $slug: missing pack/$f"
            ok=false
        fi
    done
    $ok && return 0 || return 1
}

# Resolve the skill subdirectory name inside pack/skills/
# Handles both "advise.md/" (with .md suffix) and "advise/" patterns
find_skill_dir() {
    local pack_dir="$1"
    local skill="$2"
    local skills_dir="$pack_dir/skills"

    if [ -f "$skills_dir/$skill.md/SKILL.md" ]; then
        echo "$skills_dir/$skill.md"
    elif [ -f "$skills_dir/$skill/SKILL.md" ]; then
        echo "$skills_dir/$skill"
    else
        echo ""
    fi
}

# --- Actions ---

install_brain() {
    local slug="$1"
    local target_dir="$2"
    local dry_run="${3:-false}"
    local skills_dir="$target_dir/skills"
    local pack_dir="$BRAINS_DIR/$slug/pack"
    local installed=0
    local skipped=0
    local warnings=0

    echo ""
    echo "--- Installing: $slug ---"

    # Validate
    validate_slug "$slug" || return 1
    validate_pack "$slug" || return 1

    # 1. Brain loader skill: {slug}-brain
    local brain_skill_dir="$skills_dir/${slug}-brain"
    if [ -d "$brain_skill_dir" ] || [ -L "$brain_skill_dir" ]; then
        echo "  SKIP  ${slug}-brain (already exists)"
        ((skipped++))
    else
        if [ "$dry_run" = "true" ]; then
            echo "  WOULD CREATE  ${slug}-brain/"
            echo "    SKILL.md         -> $pack_dir/SKILL.md"
            echo "    brain-context.md -> $pack_dir/brain-context.md"
            echo "    brain-atoms.json -> $pack_dir/brain-atoms.json"
        else
            mkdir -p "$brain_skill_dir"
            ln -s "$pack_dir/SKILL.md" "$brain_skill_dir/SKILL.md"
            ln -s "$pack_dir/brain-context.md" "$brain_skill_dir/brain-context.md"
            ln -s "$pack_dir/brain-atoms.json" "$brain_skill_dir/brain-atoms.json"
            echo "  CREATE  ${slug}-brain/"
        fi
        ((installed++))
    fi

    # 2. Thinking skills: {slug}-{skill}
    for skill in "${SKILL_NAMES[@]}"; do
        local skill_target_dir="$skills_dir/${slug}-${skill}"
        local source_skill_dir
        source_skill_dir=$(find_skill_dir "$pack_dir" "$skill")

        if [ -z "$source_skill_dir" ]; then
            echo "  WARN  ${slug}-${skill}: pack/skills/$skill not found"
            ((warnings++))
            continue
        fi

        if [ -d "$skill_target_dir" ] || [ -L "$skill_target_dir" ]; then
            echo "  SKIP  ${slug}-${skill} (already exists)"
            ((skipped++))
            continue
        fi

        if [ "$dry_run" = "true" ]; then
            echo "  WOULD CREATE  ${slug}-${skill}/"
            echo "    SKILL.md -> $source_skill_dir/SKILL.md"
        else
            mkdir -p "$skill_target_dir"
            ln -s "$source_skill_dir/SKILL.md" "$skill_target_dir/SKILL.md"
            echo "  CREATE  ${slug}-${skill}/"
        fi
        ((installed++))
    done

    echo "  Result: $installed created, $skipped skipped, $warnings warnings"
    return 0
}

uninstall_brain() {
    local slug="$1"
    local target_dir="$2"
    local skills_dir="$target_dir/skills"
    local removed=0

    echo ""
    echo "--- Uninstalling: $slug ---"

    # Remove brain loader
    local brain_skill_dir="$skills_dir/${slug}-brain"
    if [ -d "$brain_skill_dir" ] || [ -L "$brain_skill_dir" ]; then
        rm -rf "$brain_skill_dir"
        echo "  REMOVE  ${slug}-brain/"
        ((removed++))
    fi

    # Remove thinking skills
    for skill in "${SKILL_NAMES[@]}"; do
        local skill_target_dir="$skills_dir/${slug}-${skill}"
        if [ -d "$skill_target_dir" ] || [ -L "$skill_target_dir" ]; then
            rm -rf "$skill_target_dir"
            echo "  REMOVE  ${slug}-${skill}/"
            ((removed++))
        fi
    done

    if [ "$removed" -eq 0 ]; then
        echo "  Nothing to remove — $slug not installed"
    else
        echo "  Removed $removed skill(s)"
    fi
}

list_brains() {
    local target_dir="$1"
    local skills_dir="$target_dir/skills"

    echo ""
    echo "=== Installed Brain Packs in $skills_dir ==="
    echo ""

    # Find all *-brain directories
    local found=0
    for brain_dir in "$skills_dir"/*-brain; do
        [ -d "$brain_dir" ] || [ -L "$brain_dir" ] || continue
        local dir_name
        dir_name=$(basename "$brain_dir")
        local slug="${dir_name%-brain}"

        # Count matching thinking skills
        local skill_count=0
        for skill in "${SKILL_NAMES[@]}"; do
            if [ -d "$skills_dir/${slug}-${skill}" ] || [ -L "$skills_dir/${slug}-${skill}" ]; then
                ((skill_count++))
            fi
        done

        echo "  $slug — ${slug}-brain + $skill_count thinking skills"
        ((found++))
    done

    if [ "$found" -eq 0 ]; then
        echo "  (none)"
    fi
    echo ""
}

# --- Main ---

if [ $# -lt 1 ]; then
    usage
fi

MODE="install"
DRY_RUN="false"

# Parse flags
case "${1:-}" in
    --uninstall)
        MODE="uninstall"
        shift
        ;;
    --list)
        MODE="list"
        shift
        ;;
    --dry-run)
        DRY_RUN="true"
        shift
        ;;
    --help|-h)
        usage
        ;;
esac

# List mode only needs target dir
if [ "$MODE" = "list" ]; then
    [ $# -lt 1 ] && usage
    TARGET_DIR="$1"
    list_brains "$TARGET_DIR"
    exit 0
fi

# All other modes need target dir + at least one slug
[ $# -lt 2 ] && usage
TARGET_DIR="$1"
shift
SLUGS=("$@")

echo "=== BrainsForSale Installer ==="
echo "Brains dir: $BRAINS_DIR"
echo "Target:     $TARGET_DIR/skills/"
echo "Mode:       $MODE"
[ "$DRY_RUN" = "true" ] && echo "Dry run:    yes"

# Ensure target skills directory exists
mkdir -p "$TARGET_DIR/skills"

errors=0
for slug in "${SLUGS[@]}"; do
    if [ "$MODE" = "install" ]; then
        install_brain "$slug" "$TARGET_DIR" "$DRY_RUN" || ((errors++))
    elif [ "$MODE" = "uninstall" ]; then
        uninstall_brain "$slug" "$TARGET_DIR"
    fi
done

# Run sync-skills.sh if we made changes (not dry run, not uninstall-only)
if [ "$DRY_RUN" = "false" ]; then
    SYNC_SCRIPT="$TARGET_DIR/scripts/sync-skills.sh"
    if [ -f "$SYNC_SCRIPT" ]; then
        echo ""
        echo "=== Running sync-skills.sh ==="
        bash "$SYNC_SCRIPT"
    else
        echo ""
        echo "WARN: sync-skills.sh not found at $SYNC_SCRIPT — run it manually to propagate to ~/.claude/skills/"
    fi
fi

echo ""
if [ "$errors" -gt 0 ]; then
    echo "Completed with $errors error(s)"
    exit 1
else
    echo "Done."
fi
