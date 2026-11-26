#!/usr/bin/env bash
# Gives the pinned gateway checkout its data/maps.json and its .env. Never prints a value from .env.
#  - maps.json is rebuilt from the recorded details (ids, names, item flags only) and compared with the dev copy by checksum.
#  - .env is COPIED from the dev gateway folder (where set-read-key.sh wrote it) with mode 600. It is gitignored, so the new checkout does not have it.
#  - one non-secret line is appended: PORTAL_DB_PATH (so the gateway can look up items missing from the map, read-only).
# Prepared by Abdul Hadhee | IT Executive
set -euo pipefail
umask 077
. "$(dirname "$0")/lib.sh"
SRC_ENV=$GW_DEV/tools/demo-gateway/.env
[ -f "$SRC_ENV" ] || { echo "STOP: $SRC_ENV missing. Run /root/tools/demo-key/set-read-key.sh first."; exit 1; }
cd "$GW_DIR"
node tools/demo-gateway/scripts/build-maps.mjs "/root/Project Management/reports/2026-10-08-pd-zoho-study/pulls/details.json"
a=$(sha256sum "$GW_DIR/tools/demo-gateway/data/maps.json" | cut -c1-16); b=$(sha256sum "$GW_DEV/tools/demo-gateway/data/maps.json" 2>/dev/null | cut -c1-16 || echo none)
[ "$a" = "$b" ] && echo "maps.json: identical to the dev copy ($a)" || echo "maps.json: differs from the dev copy ($a vs $b). Fine if the recording changed; tell the lead if unexpected."
if [ -f "$GW_ENV" ]; then echo "kept   $GW_ENV (already there)"; else install -m 600 "$SRC_ENV" "$GW_ENV"; echo "copied gateway .env (mode $(stat -c %a "$GW_ENV"))"; fi
chmod 600 "$GW_ENV"
if hask "$GW_ENV" PORTAL_DB_PATH; then echo "kept   PORTAL_DB_PATH line"; else printf 'PORTAL_DB_PATH=%s\n' "$PT_DB" >> "$GW_ENV"; echo "added  PORTAL_DB_PATH=$PT_DB"; fi
echo "names present:"; for k in ZOHO_CLIENT_ID ZOHO_CLIENT_SECRET ZOHO_READ_REFRESH_TOKEN DEMO_CLIENT_ID DEMO_CLIENT_SECRET DEMO_READ_REFRESH DEMO_WRITE_REFRESH DEMO_PAGE_TOKEN PORTAL_DB_PATH; do
  hask "$GW_ENV" "$k" && echo "  $k  (length $(getv "$GW_ENV" "$k" | wc -c | awk '{print $1-1}'))" || echo "  $k  MISSING"; done
echo "DONE gateway setup"
