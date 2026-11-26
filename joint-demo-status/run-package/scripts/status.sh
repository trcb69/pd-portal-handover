#!/usr/bin/env bash
# One screen of health for the whole demo. Read-only. Prints no secret.
# Prepared by Abdul Hadhee | IT Executive
set -u
. "$(dirname "$0")/lib.sh"
echo "== PM2 =="; pm2 jlist 2>/dev/null | jq -r '.[] | select(.name|startswith("demo-")) | "\(.name)  \(.pm2_env.status)  restarts=\(.pm2_env.restart_time)  up_since=\(.pm2_env.pm_uptime/1000|floor|strftime("%d %b %H:%M"))"'
echo "== gateway :4850 =="; curl -s -m 5 http://127.0.0.1:4850/health | jq -c . || echo "NO ANSWER"
echo "== dashboard :4300 =="; curl -s -m 5 http://127.0.0.1:4300/api/health | jq -c . || echo "NO ANSWER"
echo "== portal :4800 =="; curl -s -m 5 http://127.0.0.1:4800/api/health | jq -c '{ok,mode,db,sps,sh,budget,writesEnabled,restorePending,draftsAwaitingConfirm}' || echo "NO ANSWER"
