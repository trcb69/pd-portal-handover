#!/usr/bin/env bash
# Shared names for the demo run package. Sourced by the other scripts; not run by itself.
# Prepared by Abdul Hadhee | IT Executive
RP="/root/Project Management/reports/2026-10-24-joint-demo-status/run-package"
DEMO=/root/demo
GW_DEV=/root/dev/order-portal-gateway          # branch feature/demo-gateway
PT_DEV=/root/dev/order-portal-s1               # branch feature/s1-demo
DB_DEV=/root/dev/production-dashboard-v01      # branch feature/joint-demo-v0.1
GW_SHA=65c72b6
PT_SHA=ca7f9fa
DB_SHA=5e8bbb6
GW_DIR=$DEMO/order-portal-gateway
PT_DIR=$DEMO/order-portal
DB_DIR=$DEMO/production-dashboard
GW_ENV=$GW_DIR/tools/demo-gateway/.env
PT_ENV=$PT_DIR/.env
DB_ENV=$DB_DIR/.env
PT_DB=$PT_DIR/data/order-portal.db
DB_DB=$DB_DIR/data/production.db

# getv <file> <NAME>  -> prints the value of NAME (last one wins). Never call this in a way that prints a secret.
getv() { sed -n "s/^$2=//p" "$1" | tail -n 1 | tr -d '\r'; }
# hask <file> <NAME>  -> true when a line NAME=... exists (the value may be empty)
hask() { grep -q "^$2=" "$1"; }
# same <a> <b> -> true when equal; prints nothing
same() { [ "$1" = "$2" ]; }
