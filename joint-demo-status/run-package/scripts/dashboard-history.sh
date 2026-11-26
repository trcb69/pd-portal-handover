#!/usr/bin/env bash
# Quick history count straight from the dashboard database, no password needed (read-only). The exact "in scope" figure is in dashboard-sync-status.sh.
# Prepared by Abdul Hadhee | IT Executive
set -u
. "$(dirname "$0")/lib.sh"
[ -f "$DB_DB" ] || { echo "no dashboard database yet: $DB_DB"; exit 1; }
sqlite3 -readonly -header -column "$DB_DB" "SELECT count(*) AS so_headers, coalesce(sum(detail_fetched_at IS NOT NULL),0) AS details_loaded, coalesce(sum(detail_fail_count >= 3),0) AS failing FROM zoho_so_headers WHERE org = 'SPS';"
sqlite3 -readonly -header -column "$DB_DB" "SELECT module, status, api_calls, rows_read, started_at, finished_at FROM zoho_import_runs WHERE source = 'sync' ORDER BY id DESC LIMIT 6;"
