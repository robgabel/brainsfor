#!/usr/bin/env bash
# install-hooks.sh — symlink tracked hook scripts into .git/hooks/
#
# Run once after cloning the brainsfor repo. Idempotent — safe to re-run.
# Symlinks (not copies) so edits to scripts/hooks/* take effect immediately.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
SOURCE_DIR="$REPO_ROOT/scripts/hooks"

if [[ ! -d "$HOOKS_DIR" ]]; then
    echo "error: $HOOKS_DIR does not exist — is this a git repo?" >&2
    exit 1
fi

shopt -s nullglob
installed=0
for src in "$SOURCE_DIR"/*; do
    name="$(basename "$src")"
    dest="$HOOKS_DIR/$name"
    chmod +x "$src"
    ln -sf "$src" "$dest"
    echo "linked: $dest -> $src"
    installed=$((installed + 1))
done

if [[ $installed -eq 0 ]]; then
    echo "no hooks found in $SOURCE_DIR"
    exit 0
fi

echo ""
echo "installed $installed hook(s). bypass any check with: git commit --no-verify"
