#!/usr/bin/env bash
# Read-only checks before anything is created. Changes nothing, starts nothing. Prints OK / FAIL lines and names only (never a secret).
# Prepared by Abdul Hadhee | IT Executive
set -u
. "$(dirname "$0")/lib.sh"
fail=0
ok()  { echo "OK    $*"; }
bad() { echo "FAIL  $*"; fail=1; }
warn(){ echo "WARN  $*"; }

# 1. dev commits are where the runbook says
for pair in "$GW_DEV:$GW_SHA" "$PT_DEV:$PT_SHA" "$DB_DEV:$DB_SHA"; do
  d=${pair%%:*}; sha=${pair##*:}
  head=$(git -C "$d" rev-parse --short=7 HEAD 2>/dev/null || echo none)
  if [ "$head" = "$sha" ]; then ok "$d is at $sha"; else warn "$d HEAD is $head, runbook pins $sha (the pin still works: it is a commit, not a branch)"; fi
  git -C "$d" cat-file -e "$sha^{commit}" 2>/dev/null && ok "$d has commit $sha" || bad "$d does not have commit $sha"
  [ -z "$(git -C "$d" status --porcelain --untracked-files=no)" ] && ok "$d has no uncommitted changes" || warn "$d has uncommitted changes (they are NOT in the pinned demo)"
done
# 2. tools
node -v | grep -q '^v2[4-9]' && ok "node $(node -v)" || bad "node 24 or newer needed (package.json engines)"
for t in git npm pm2 sqlite3 jq curl ssh; do command -v "$t" >/dev/null && ok "$t found" || bad "$t not found"; done
# 3. ports free, and not PM2-owned yet
for p in 4300 4800 4850; do
  if ss -ltn | awk '{print $4}' | grep -q ":$p\$"; then warn "port $p is already listening (fine only if the demo is already running)"; else ok "port $p is free"; fi
done
# 4. disk and memory
avail=$(df -BG --output=avail /root | tail -1 | tr -dc 0-9)
[ "$avail" -ge 5 ] && ok "disk: ${avail} GB free on /" || bad "disk: only ${avail} GB free on /, need 5"
echo "INFO  memory: $(free -m | awk 'NR==2{print $7" MB available"}')"
# 5. the three demo dirs must not exist yet (or must be the pinned ones)
for d in "$GW_DIR" "$PT_DIR" "$DB_DIR"; do [ -e "$d" ] && warn "$d already exists (01-make-worktrees.sh will only verify it)" || ok "$d does not exist yet"; done
# 6. gateway key file exists, locked, names present (values are not read out)
if [ -f "$GW_DEV/tools/demo-gateway/.env" ]; then
  mode=$(stat -c %a "$GW_DEV/tools/demo-gateway/.env"); [ "$mode" = 600 ] && ok "gateway .env (dev copy) mode 600" || bad "gateway .env mode is $mode, must be 600"
  for k in ZOHO_CLIENT_ID ZOHO_CLIENT_SECRET ZOHO_READ_REFRESH_TOKEN DEMO_CLIENT_ID DEMO_CLIENT_SECRET DEMO_READ_REFRESH DEMO_WRITE_REFRESH DEMO_PAGE_TOKEN; do
    hask "$GW_DEV/tools/demo-gateway/.env" "$k" || bad "gateway .env has no $k line"
  done
  ok "gateway .env name check done"
else bad "gateway .env missing: run /root/tools/demo-key/set-read-key.sh"; fi
# 7. the SH item file
[ -s "$RP/sh-items.json" ] && ok "sh-items.json present ($(jq length "$RP/sh-items.json") rows)" || bad "sh-items.json missing"
[ -f "/root/Project Management/reports/2026-10-08-pd-zoho-study/pulls/details.json" ] && ok "recorded details.json present (for maps)" || bad "details.json missing: maps cannot be rebuilt (copy the dev maps.json instead)"
[ -f "/root/Project Management/reports/2026-10-08-pd-zoho-study/routes.csv" ] && ok "routes.csv present (for the dashboard set-up)" || bad "routes.csv missing"
# 8. the rizwan@ browser (:9333): reachable, and the robots.txt tab the SH reader needs is open. Reads only the tab list (not Zoho).
n=$(curl -s -m 5 http://127.0.0.1:9333/json/list | jq '[.[]|select(.url|startswith("https://inventory.zoho.com/robots.txt"))]|length' 2>/dev/null || echo err)
case "$n" in err|"") bad "cannot reach the browser on 127.0.0.1:9333";; 0) bad "no https://inventory.zoho.com/robots.txt tab open in the :9333 browser (open one by hand; do not sign out)";; *) ok "robots.txt tab open ($n)";; esac
echo "INFO  other processes naming :9333 (SEC-9333: nothing else heavy while the demo runs):"
ps -eo pid,etime,args | grep -E '[9]333' | cut -c1-110 || true
# 9. the production services are online, because 'pm2 save' later saves the list as it is NOW
echo "INFO  pm2 now (all five production services should be online):"
pm2 jlist 2>/dev/null | jq -r '.[] | "      \(.name)  \(.pm2_env.status)"'
# 10. environment variables in this shell that would override the apps' .env files (dotenv does not override)
for v in $(compgen -e | grep -E '^(ZOHO_|DEMO_|SH_|PORTAL_|GATEWAY_|DASH_|PROJECT_MODE$|PORT$|DB_PATH$|APP_ORIGIN$|BRIDGE_HOST$|NODE_ENV$|TRUSTED_PROXY_IPS$|SPS_HISTORY_DAYS$)'); do
  bad "$v is set in this shell; PM2 would store it and pass it to the demo apps. Run: unset $v"
done
echo; [ $fail = 0 ] && echo "PREFLIGHT PASSED" || { echo "PREFLIGHT FAILED: fix the FAIL lines first"; exit 1; }
