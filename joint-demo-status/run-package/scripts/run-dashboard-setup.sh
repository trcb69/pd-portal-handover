#!/usr/bin/env bash
# Runs the dashboard demo set-up (or its undo) against the RUNNING demo dashboard. Asks for the dashboard admin password (hidden).
# Usage: run-dashboard-setup.sh <admin username> <pairs.json>      (set-up)
#        run-dashboard-setup.sh <admin username> --undo            (undo)
# Prepared by Abdul Hadhee | IT Executive
set -eu
. "$(dirname "$0")/lib.sh"
user=${1:?usage: run-dashboard-setup.sh <admin username> <pairs.json | --undo>}; arg=${2:?second argument: pairs.json or --undo}
read -rsp "Dashboard admin password: " DEMO_ADMIN_PASSWORD; echo
export DEMO_ADMIN_USER=$user DEMO_ADMIN_PASSWORD
cd "$DB_DIR"
if [ "$arg" = "--undo" ]; then
  node cli/demo-setup.js --undo
else
  [ -f "$arg" ] || { echo "pairs file not found: $arg"; exit 1; }
  W=$RP/dashboard-setup-files; mkdir -p "$W"
  cp "/root/Project Management/reports/2026-10-08-pd-zoho-study/routes.csv" "$W/routes.csv"
  cp "$DB_DIR/test/fixtures/routes/unit-map.json" "$W/unit-map.json"
  [ -f "$W/lid-items.json" ] || echo '[]' > "$W/lid-items.json"
  node cli/demo-setup.js --routes "$W/routes.csv" --map "$W/unit-map.json" --pairs "$arg" --lid-items "$W/lid-items.json"
fi
unset DEMO_ADMIN_PASSWORD
