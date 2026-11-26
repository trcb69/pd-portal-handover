#!/usr/bin/env bash
# Shows the dashboard's history load (warm-up progress) from the admin status route. Asks for the dashboard ADMIN password (typed hidden, never on the command line).
# Usage: dashboard-sync-status.sh <admin username>
# Prepared by Abdul Hadhee | IT Executive
set -u
. "$(dirname "$0")/lib.sh"
user=${1:?usage: dashboard-sync-status.sh <admin username>}
base=http://127.0.0.1:4300/api; origin=http://localhost:4300
read -rsp "Dashboard admin password: " DASH_PW; echo; export DASH_PW DASH_USER=$user
resp=$(jq -n '{username: env.DASH_USER, password: env.DASH_PW}' | curl -s -m 15 -D - -o /dev/null -H "origin: $origin" -H 'content-type: application/json' -d @- "$base/auth/login")
unset DASH_PW DASH_USER
code=$(printf '%s' "$resp" | head -1 | awk '{print $2}')
[ "$code" = 200 ] || { echo "Sign-in failed (HTTP $code)."; exit 1; }
cookie=$(printf '%s' "$resp" | tr -d '\r' | grep -i '^set-cookie:' | sed 's/^[Ss]et-[Cc]ookie: *//; s/;.*//' | paste -sd';' | sed 's/;/; /g')
printf 'cookie: %s\n' "$cookie" | curl -s -m 20 -H @- "$base/admin/zoho-sync/status" | jq '{enabled, calls_today, cap, history_calls_today, in_scope_sos, loaded_sos, backlog, catching_up_orders, sync_problems, quarantined_sos, limit_reached_today, last_full_list}'
printf 'cookie: %s\n' "$cookie" | curl -s -m 15 -o /dev/null -X POST -H "origin: $origin" -H @- "$base/auth/logout"
