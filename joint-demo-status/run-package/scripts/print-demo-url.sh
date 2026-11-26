#!/usr/bin/env bash
# Prints the gateway /demo address WITH its page token, on this terminal only. Do not paste the output anywhere; run `clear` afterwards.
# Prepared by Abdul Hadhee | IT Executive
set -eu
. "$(dirname "$0")/lib.sh"
tok=$(getv "$GW_ENV" DEMO_PAGE_TOKEN)
[ -n "$tok" ] || { echo "no DEMO_PAGE_TOKEN in the gateway .env"; exit 1; }
echo "Open this in your PC browser (tunnel on port 4850 must be open). Then run: clear"
echo "http://127.0.0.1:4850/demo?token=$tok"
