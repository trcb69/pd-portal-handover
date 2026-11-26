#!/usr/bin/env bash
# Pre-start checks (spec section 2.7). Usage: check-demo-env.sh gateway|dashboard|portal   Exit 0 = safe to start, 1 = do not start.
# Prints names and OK/FAIL only; never a value. Run by hand before each `pm2 start`; the ecosystem file also runs it when pm2 loads it for a start.
# Prepared by Abdul Hadhee | IT Executive
set -u
. "$(dirname "$0")/lib.sh"
what=${1:-}
bad=0
fail() { echo "FAIL  $*"; bad=1; }
pass() { echo "OK    $*"; }
want() { # want <file> <NAME> <exact value>
  hask "$1" "$2" || { fail "$2 line missing"; return; }
  [ "$(getv "$1" "$2")" = "$3" ] && pass "$2 is as required" || fail "$2 is not the required value ($3)"
}
mode600() { [ "$(stat -c %a "$1" 2>/dev/null)" = 600 ] && pass "$1 mode 600" || fail "$1 missing or not mode 600"; }
pinned() { local d=$1 sha=$2; [ "$(git -C "$d" rev-parse --short=7 HEAD 2>/dev/null)" = "$sha" ] && pass "$d is at pinned $sha" || fail "$d is not at pinned $sha"; }
notlive() { case "$1" in /root/demo/*) pass "running from /root/demo (not a live dir)";; *) fail "$1 is not under /root/demo";; esac; }
shellvars() { local v; for v in $(compgen -e | grep -E '^(ZOHO_|DEMO_|SH_|PORTAL_|GATEWAY_|DASH_|PROJECT_MODE$|PORT$|DB_PATH$|APP_ORIGIN$|BRIDGE_HOST$|NODE_ENV$|TRUSTED_PROXY_IPS$|SPS_HISTORY_DAYS$)'); do fail "$v is set in the shell (PM2 would store it and it would override .env); run: unset $v"; done; }
shellvars
case "$what" in
  gateway)
    notlive "$GW_DIR"; pinned "$GW_DIR" "$GW_SHA"; mode600 "$GW_ENV"
    for k in ZOHO_CLIENT_ID ZOHO_CLIENT_SECRET ZOHO_READ_REFRESH_TOKEN DEMO_CLIENT_ID DEMO_CLIENT_SECRET DEMO_READ_REFRESH DEMO_WRITE_REFRESH DEMO_PAGE_TOKEN; do hask "$GW_ENV" "$k" && [ -n "$(getv "$GW_ENV" "$k")" ] || fail "$k missing or empty"; done
    [ -s "$GW_DIR/tools/demo-gateway/data/maps.json" ] && pass "maps.json present" || fail "maps.json missing (run 02-gateway-setup.sh)"
    ss -ltn | awk '{print $4}' | grep -q ':4850$' && echo "INFO  4850 already listening" || pass "4850 free"
    echo "INFO  the gateway's own start checks (length, equal values, group-readable) run when it starts and name any problem"
    ;;
  dashboard)
    notlive "$DB_DIR"; pinned "$DB_DIR" "$DB_SHA"; mode600 "$DB_ENV"
    want "$DB_ENV" NODE_ENV production; want "$DB_ENV" DEMO_GATEWAY 1; want "$DB_ENV" BRIDGE_HOST ""
    want "$DB_ENV" APP_ORIGIN http://localhost:4300; want "$DB_ENV" TRUSTED_PROXY_IPS 192.0.2.1; want "$DB_ENV" PORT 4300
    want "$DB_ENV" ZOHO_API_BASE http://127.0.0.1:4850/inventory/v1; want "$DB_ENV" ZOHO_TOKEN_URL http://127.0.0.1:4850/oauth/v2/token
    want "$DB_ENV" ZOHO_DAILY_CALL_CAP 4500; want "$DB_ENV" ZOHO_SYNC_INTERVAL_MIN 2; want "$DB_ENV" ZOHO_SYNC_ENABLED true
    same "$(getv "$DB_ENV" ZOHO_CLIENT_ID)" "$(getv "$GW_ENV" DEMO_CLIENT_ID)" && same "$(getv "$DB_ENV" ZOHO_REFRESH_TOKEN)" "$(getv "$GW_ENV" DEMO_READ_REFRESH)" && pass "dashboard uses the DEMO_* stand-ins" || fail "dashboard Zoho values are not the DEMO_* stand-ins"
    same "$(getv "$DB_ENV" ZOHO_CLIENT_SECRET)" "$(getv "$GW_ENV" ZOHO_CLIENT_SECRET)" && fail "dashboard holds the REAL Zoho client secret" || pass "dashboard does not hold the real client secret"
    same "$(getv "$DB_ENV" ZOHO_REFRESH_TOKEN)" "$(getv "$GW_ENV" ZOHO_READ_REFRESH_TOKEN)" && fail "dashboard holds the REAL refresh token" || pass "dashboard does not hold the real refresh token"
    [ -f "$DB_DIR/web/dist/index.html" ] && pass "web/dist present" || fail "web/dist missing"
    curl -s -m 3 http://127.0.0.1:4850/health | grep -q 'DEMO MODE (gateway)' && pass "gateway is up (DEMO MODE)" || fail "gateway is not answering on 4850: start it first"
    ;;
  portal)
    notlive "$PT_DIR"; pinned "$PT_DIR" "$PT_SHA"; mode600 "$PT_ENV"
    want "$PT_ENV" NODE_ENV production; want "$PT_ENV" DEMO_GATEWAY 1; want "$PT_ENV" BRIDGE_HOST ""
    want "$PT_ENV" APP_ORIGIN http://localhost:4800; want "$PT_ENV" TRUSTED_PROXY_IPS 192.0.2.1; want "$PT_ENV" PORT 4800; want "$PT_ENV" PORTAL_INSTANCE demo
    want "$PT_ENV" ZOHO_API_BASE http://127.0.0.1:4850/inventory/v1; want "$PT_ENV" ZOHO_TOKEN_URL http://127.0.0.1:4850/oauth/v2/token
    want "$PT_ENV" ZOHO_DAILY_CALL_CAP 2000; want "$PT_ENV" SPS_HISTORY_DAYS 30; want "$PT_ENV" SH_READER cdp; want "$PT_ENV" SH_CDP_URL http://127.0.0.1:9333
    want "$PT_ENV" ZOHO_SYNC_ENABLED true; want "$PT_ENV" ZOHO_WRITES_ENABLED true; want "$PT_ENV" PROJECT_MODE pick
    [ -f "$(getv "$PT_ENV" ZOHO_FIELD_MAP)" ] && pass "field map file present" || fail "ZOHO_FIELD_MAP file missing"
    same "$(getv "$PT_ENV" ZOHO_CLIENT_ID)" "$(getv "$GW_ENV" DEMO_CLIENT_ID)" && same "$(getv "$PT_ENV" ZOHO_READ_REFRESH_TOKEN)" "$(getv "$GW_ENV" DEMO_READ_REFRESH)" && same "$(getv "$PT_ENV" ZOHO_WRITE_REFRESH_TOKEN)" "$(getv "$GW_ENV" DEMO_WRITE_REFRESH)" && pass "portal uses the DEMO_* stand-ins" || fail "portal Zoho values are not the DEMO_* stand-ins"
    same "$(getv "$PT_ENV" ZOHO_CLIENT_SECRET)" "$(getv "$GW_ENV" ZOHO_CLIENT_SECRET)" && fail "portal holds the REAL Zoho client secret" || pass "portal does not hold the real client secret"
    same "$(getv "$PT_ENV" ZOHO_READ_REFRESH_TOKEN)" "$(getv "$GW_ENV" ZOHO_READ_REFRESH_TOKEN)" && fail "portal holds the REAL refresh token" || pass "portal does not hold the real refresh token"
    curl -s -m 3 http://127.0.0.1:4850/health | grep -q 'DEMO MODE (gateway)' && pass "gateway is up (DEMO MODE)" || fail "gateway is not answering on 4850: start it first"
    n=$(curl -s -m 5 http://127.0.0.1:9333/json/list | jq '[.[]|select(.url|startswith("https://inventory.zoho.com/robots.txt"))]|length' 2>/dev/null || echo 0)
    [ "${n:-0}" -ge 1 ] && pass "robots.txt tab open in the :9333 browser" || fail "no robots.txt tab in the :9333 browser (the SH reader would stop at login_required)"
    ;;
  *) echo "usage: check-demo-env.sh gateway|dashboard|portal"; exit 2;;
esac
[ $bad = 0 ] && { echo "CHECK PASSED: $what"; exit 0; } || { echo "CHECK FAILED: $what (do not start it)"; exit 1; }
