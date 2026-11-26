#!/usr/bin/env bash
# Writes the portal's and the dashboard's .env (mode 600) from the DEMO_* stand-in values in the gateway's .env.
# Copies by name, prints only names and lengths. The real ZOHO_* values are NEVER copied to the apps.
# Usage: 03-make-app-env.sh            (refuses to overwrite an existing app .env)
#        03-make-app-env.sh --replace  (overwrites both; the databases are untouched)
# Prepared by Abdul Hadhee | IT Executive
set -euo pipefail
umask 077
. "$(dirname "$0")/lib.sh"
replace=0; [ "${1:-}" = "--replace" ] && replace=1
[ -f "$GW_ENV" ] || { echo "STOP: $GW_ENV missing (run 02-gateway-setup.sh)"; exit 1; }
[ "$(stat -c %a "$GW_ENV")" = 600 ] || { echo "STOP: $GW_ENV is not mode 600"; exit 1; }
for f in "$PT_ENV" "$DB_ENV"; do [ -e "$f" ] && [ $replace = 0 ] && { echo "STOP: $f exists. Use --replace to overwrite."; exit 1; }; done
[ -f "$PT_DIR/data/field-map.json" ] || { echo "STOP: $PT_DIR/data/field-map.json missing (run: node $RP/scripts/make-portal-field-map.mjs)"; exit 1; }

CID=$(getv "$GW_ENV" DEMO_CLIENT_ID); CSEC=$(getv "$GW_ENV" DEMO_CLIENT_SECRET)
RD=$(getv "$GW_ENV" DEMO_READ_REFRESH); WR=$(getv "$GW_ENV" DEMO_WRITE_REFRESH)
for n in CID CSEC RD WR; do [ -n "${!n}" ] || { echo "STOP: a DEMO_* value is empty in the gateway .env"; exit 1; }; done
for n in CID CSEC RD WR; do [[ "${!n}" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "STOP: a DEMO_* value ($n) has characters other than letters, digits, . _ - ; nothing written"; exit 1; }; done
tmp=; trap 'rm -f "${tmp:-}"' EXIT
echo "copying (names and lengths only):"
printf '  DEMO_CLIENT_ID      %s\n  DEMO_CLIENT_SECRET  %s\n  DEMO_READ_REFRESH   %s\n  DEMO_WRITE_REFRESH  %s\n' "${#CID}" "${#CSEC}" "${#RD}" "${#WR}"

GWURL=http://127.0.0.1:4850
tmp=$(mktemp "$PT_DIR/.env.new.XXXXXX")
cat > "$tmp" <<EOT
# Demo portal (joint demo v0.1). Written by 03-make-app-env.sh. Only DEMO_* stand-in values; no real Zoho secret.
NODE_ENV=production
PORT=4800
APP_ORIGIN=http://localhost:4800
BRIDGE_HOST=
TRUSTED_PROXY_IPS=192.0.2.1
PORTAL_INSTANCE=demo
DEMO_GATEWAY=1
ZOHO_API_BASE=$GWURL/inventory/v1
ZOHO_TOKEN_URL=$GWURL/oauth/v2/token
ZOHO_CLIENT_ID=$CID
ZOHO_CLIENT_SECRET=$CSEC
ZOHO_READ_REFRESH_TOKEN=$RD
ZOHO_WRITE_REFRESH_TOKEN=$WR
ZOHO_SYNC_ENABLED=true
ZOHO_WRITES_ENABLED=true
ZOHO_FIELD_MAP=$PT_DIR/data/field-map.json
ZOHO_DAILY_CALL_CAP=2000
SPS_HISTORY_DAYS=30
PROJECT_MODE=pick
SH_READER=cdp
SH_CDP_URL=http://127.0.0.1:9333
EOT
chmod 600 "$tmp"; mv -f "$tmp" "$PT_ENV"

tmp=$(mktemp "$DB_DIR/.env.new.XXXXXX")
cat > "$tmp" <<EOT
# Demo dashboard (joint demo v0.1). Written by 03-make-app-env.sh. Only DEMO_* stand-in values; no real Zoho secret.
NODE_ENV=production
PORT=4300
APP_ORIGIN=http://localhost:4300
BRIDGE_HOST=
TRUSTED_PROXY_IPS=192.0.2.1
DEMO_GATEWAY=1
ZOHO_API_BASE=$GWURL/inventory/v1
ZOHO_TOKEN_URL=$GWURL/oauth/v2/token
ZOHO_CLIENT_ID=$CID
ZOHO_CLIENT_SECRET=$CSEC
ZOHO_REFRESH_TOKEN=$RD
ZOHO_SYNC_ENABLED=true
ZOHO_SYNC_INTERVAL_MIN=2
ZOHO_DAILY_CALL_CAP=4500
EOT
chmod 600 "$tmp"; mv -f "$tmp" "$DB_ENV"
unset CID CSEC RD WR
echo "wrote $PT_ENV (mode $(stat -c %a "$PT_ENV")) and $DB_ENV (mode $(stat -c %a "$DB_ENV"))"
echo "DONE app env"
