#!/usr/bin/env bash
# Creates the three pinned checkouts under /root/demo and installs their packages. Safe to re-run: an existing checkout is only verified.
# Writes ONLY under /root/demo (and the worktree list inside the dev repos' .git folders, which `git worktree add` always does).
# Prepared by Abdul Hadhee | IT Executive
set -euo pipefail
. "$(dirname "$0")/lib.sh"
mkdir -p "$DEMO"
add() {  # add <dev repo> <target> <sha>
  local repo=$1 target=$2 sha=$3
  if [ -e "$target/.git" ]; then
    got=$(git -C "$target" rev-parse --short=7 HEAD)
    [ "$got" = "$sha" ] || { echo "STOP: $target is at $got, expected $sha. Move the pin deliberately (RUNBOOK section Updating)."; exit 1; }
    echo "kept   $target at $sha"
  else
    git -C "$repo" worktree add --detach "$target" "$sha"
  fi
  ( cd "$target" && npm ci --omit=dev --no-audit --no-fund )
  node -e "require('$target/node_modules/better-sqlite3')" 2>/dev/null && echo "ok     better-sqlite3 loads in $target" \
    || { echo "STOP: better-sqlite3 does not load in $target. Try: cd $target && npm rebuild better-sqlite3"; exit 1; }
}
add "$GW_DEV" "$GW_DIR" "$GW_SHA"
add "$PT_DEV" "$PT_DIR" "$PT_SHA"
add "$DB_DEV" "$DB_DIR" "$DB_SHA"
[ -f "$DB_DIR/web/dist/index.html" ] && echo "ok     dashboard web/dist is in the checkout (committed, no build needed)" || { echo "STOP: $DB_DIR/web/dist/index.html missing"; exit 1; }
mkdir -p -m 700 "$PT_DIR/data" "$DB_DIR/data"
echo "DONE worktrees"
