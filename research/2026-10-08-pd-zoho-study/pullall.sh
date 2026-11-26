cd "/root/Project Management/reports/2026-10-08-pd-zoho-study"
C=2025-10-01
node pager.mjs salesorders created_time created_time $C pulls/so_created
node pager.mjs salesorders last_modified_time last_modified_time $C pulls/so_modified
node pager.mjs packages created_time created_time $C pulls/pkg
node pager.mjs shipmentorders created_time created_time $C pulls/ship
node pager.mjs invoices created_time created_time $C pulls/inv
node pager.mjs picklists created_time created_time $C pulls/pick
echo ALLDONE
