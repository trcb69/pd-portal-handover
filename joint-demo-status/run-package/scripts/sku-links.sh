#!/usr/bin/env bash
# SH item links in the portal demo database, split by how they were matched (read-only). The owner checks the sku ones before the rehearsal.
# Prepared by Abdul Hadhee | IT Executive
set -u
. "$(dirname "$0")/lib.sh"
[ -f "$PT_DB" ] || { echo "no portal database yet: $PT_DB"; exit 1; }
echo "-- links by matched_by --"
sqlite3 -readonly -header -column "$PT_DB" "SELECT matched_by, count(*) AS links FROM item_links GROUP BY matched_by UNION ALL SELECT 'TOTAL', count(*) FROM item_links;"
echo "-- SH items loaded / SPS items synced --"
sqlite3 -readonly "$PT_DB" "SELECT 'sh_items='||(SELECT count(*) FROM sh_items)||'  sps_items='||(SELECT count(*) FROM sps_items);"
echo "-- first 15 SKU links (SPS item name | SH item name | sku) --"
sqlite3 -readonly -column "$PT_DB" "SELECT substr(i.name,1,38) AS sps_item, substr(h.name,1,38) AS sh_item, h.sku FROM item_links l JOIN sps_items i ON i.item_id = l.sps_item_id JOIN sh_items h ON h.item_id = l.sh_item_id WHERE l.matched_by = 'sku' LIMIT 15;"
