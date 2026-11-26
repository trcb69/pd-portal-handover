# Code review — demo gateway (`feature/demo-gateway`)

Reviewed 25 Oct 2026. Worktree `/root/dev/order-portal-gateway`, `git diff 9db7c02..HEAD` (b6899d6, f3cd2db, 86b5c2a, 975e016) plus the
tests in bdcb1b4. Spec: `wiki/specs/2026-10-24-joint-demo-v0-1-rev4-demo-first.md` Rev 4.7 §2, §6. `npm test` re-run by me: 235/235 pass.
Consumers read: dashboard `/root/dev/production-dashboard-v01` (`zoho-sync.js`, `zoho-queue.js`, `line-jobs.js`, `client.js`,
`config/zoho-columns.json`), portal `server/services/sps-sync.js`, OP spec §6.9 payload. Real data checked: `maps.json` built by the
script and `reports/2026-10-08-pd-zoho-study/pulls/details.json`.

## Verdict
**BLOCK**

## Critical (must fix before merge)

- **[C1] `tools/demo-gateway/server/create-gateway.js:261-262` (with `226-231`) and `scripts/build-maps.mjs:82-84` — on real data, the
  base-material field makes almost every DEMO approve fail.**
  The OP §6.9 payload always sends `cf_material_to_be_used` = a raw-material item id (`2026-10-18-order-portal-spec.md:381`), pre-filled from
  the last line (§6.1:302). Item-type custom fields go through `lookupItem()`, which needs **all six** line-item fields
  (`name, sku, unit, item_type, is_combo_product, combo_type`). But `build-maps.mjs` puts only *sold line items* into `maps.items`. Checked
  against `details.json`: 309 orders use 102 distinct material ids, and **only 2 of those are in `maps.items`**. The rest go to the portal
  mirror. That mirror is off by default (`main.js:32`, `PORTAL_DB_PATH` empty), and when it is on, its raw list row is the one the spec
  itself says "probably lacks `combo_type`" (§2.3). The result is a 400 "Item … cannot be resolved" and no order. The tests pass only because
  `fixtures/maps.fixture.json` puts both test materials (`…300003` paper, `…300004` film) into `items` with every flag filled. The real map
  does not look like that.
  **Fix:**
  (a) In `build-maps.mjs`, also record `custom_field_hash.cf_material_to_be_used_unformatted → cf_material_to_be_used` and the same for
  `cf_additional_other_material_t`. Put them in a `materials` id → name map.
  (b) For `def.lookup === 'item'`, resolve the **name only**, in this order: `maps.items[id].name`, then `maps.materials[id]`, then the mirror's
  `sps_items.name` column. Keep the six-field rule for `line_items` only (G-AC15 needs only the name).
  (c) Add a test with a material id that is absent from `maps.items`. Add a check that the real `maps.json` covers the materials.

## Warnings (fix now or file a ticket)

- **[W1] Spec gap, needs the spec owner: `create-gateway.js:323-332` (`advance`) and `:442` (`/bundles` passed through unmerged).**
  231 of the 234 mapped items are `is_combo_product: true, combo_type: assembly`. For those, the dashboard's Bundle step comes only from
  `zoho_bundles` (`line-jobs.js:224-239, 435-438`), so a DEMO job shows **Bundle "not seen yet"** permanently, next to Package/Shipment/Invoice
  "done". `packed` also leaves `quantity_picked` = 0, so a **Pick list** step on the route shows "not done" (`line-jobs.js:440`).
  Nothing crashes, and R4-AC3 only names Packed/Shipped/Invoiced, so the code meets the letter of the spec. But the walkthrough strip will
  look wrong for almost every item. Only the 3 BG paper cups (`4892105000023186001/014/034`) are non-combo, and they are unlikely to be the
  MacPro item R4-AC3 uses.
  **Fix (spec decision):** either (i) a `/demo` "Bundled" step that writes a sandbox bundle merged into `GET bundles` page 1 (same merge
  rule; row keys from a recorded bundle list row, `reference_number`/`composite_item_id` per `zoho-columns.json` `bundles`), plus `packed`
  setting `quantity_picked`; or (ii) record in §2.5 and the presenter notes that Bundle stays "not seen yet" in the demo.

- **[W2] `create-gateway.js:158-164, 191` — no timeout on either upstream fetch.**
  A hung `accounts.zoho.com` keeps the shared `refreshing` promise pending, so **every** pass-through read hangs until undici's 300 s
  default. A hung API read holds a socket long after the app's 30 s abort. The spec budgets ~20 s for Zoho's answer (§2.1).
  **Fix:** `signal: AbortSignal.timeout(20_000)` on both fetches. Map the abort to the existing 502 (or a 504) in Zoho's shape. Add a test
  with a never-resolving fake fetch.

- **[W3] `create-gateway.js:183-191` — the slot is reserved before the token refresh, which breaks G-AC3.**
  Example: request 1 gets slot t=0, refreshes the token (say 500 ms) and fetches at t=500. Request 2 gets slot t=667 and fetches at t=667.
  The two upstream calls are 167 ms apart. This happens on every hourly refresh. The pacing tests use an instant fake fetch, so they cannot
  catch it.
  **Fix:** `await upstreamToken()` first, then `reserveSlot()`/sleep, then fetch. Add a test where the token fake resolves only after the
  clock advances.

- **[W4] `create-gateway.js:319, 31` — `last_modified_time` has 1 s resolution, so a "bump" can be a no-op.**
  The portal sends `so_create` then `so_confirm` back to back, and presenters click `/demo` buttons quickly. Both can land in the same
  second. The portal skips an order whose modified time it already holds (`sps-sync.js:179`), so its mirror can stay on `draft` or the
  previous step. G-AC13 asks for a real bump. The tests always move the clock 60–90 s between steps, so they hide this.
  **Fix:** in `replaceOrder`, set `next.last_modified_time = zohoTime(max(now(), parseZoho(old.last_modified_time) + 1000))`. Add a test
  for confirm in the same millisecond.

- **[W5] `test/fixtures/list-filters.json` (`_note`) — this is not yet the "final review" §2.4 / round 4 N2 asks for.**
  The projects/contacts filter lists are *assumed*, not regenerated from S1-demo code; that code does not exist yet. The strict detail rule
  (`create-gateway.js:396`, only `organization_id`) is correct for what the apps send today: dashboard `zoho-sync.js:371` and portal
  `sps-sync.js:140, 361` all pass `{}`. OP L16 mentions an optional "live filter if V8 allows" (`order-portal-spec.md:274`), and that would
  be refused (`cf_portal_ref` is in `refused_probe_keys`).
  **Fix:** when S1-demo lands, regenerate the fixture from its code and re-run this review on that delta.

## Nits (optional)

- [N1] `create-gateway.js:442` — the raw `url.search` is forwarded after validating a *parsed* copy. Forward
  `new URLSearchParams(q).toString()` instead, so what Zoho gets is exactly what was checked.
- [N2] `create-gateway.js:371` — `sinceFilter` (400 on a bad `last_modified_time`) runs inside `mergeFn`, after the upstream call has been
  spent. Validate it in `checkFilters` for list paths.
- [N3] `create-gateway.js:424` — confirm on a shipped sandbox order sets `status` back to `confirmed`. Only change `status` when it is
  `draft`.
- [N4] `create-gateway.js:294` — `shipment_date` is stored unvalidated. Apply the same `YYYY-MM-DD` check as `date` (the dashboard maps it as
  a date, `zoho-columns.json` `expected_shipment_date`).
- [N5] `create-gateway.js:101-105` — `load()` does not check that `counter.id/number/line` ≥ the highest values in `sandbox.json`. A
  partly restored data folder could reuse ids. Refuse the start if they are lower.
- [N6] `create-gateway.js:75` — no fsync of the directory after `rename`, so the rename is not durable across a power cut. Open
  `config.dataDir` and `fsyncSync` it after the rename.
- [N7] `create-gateway.js:530` — `handle()` is not `.catch`ed. A throw inside the catch path (e.g. headers already sent) would be an unhandled
  rejection, which kills the process on Node 24. Add `.catch(log)` and guard `send` with `res.headersSent`.
- [N8] `main.js:30-32` — `GATEWAY_DATA_DIR`, `GATEWAY_MAPS_PATH` and `PORTAL_DB_PATH` resolve against the current directory when given as
  relative paths. Use `path.resolve(root, value)`.
- [N9] `create-gateway.js:157-169` — a failing upstream refresh is retried on every read, with no back-off. Zoho rate-limits token
  generation. Hold a failure for ~60 s.
- [N10] `build-maps.mjs:72` — `recorded_at` is hard-coded to 8 Oct. Take it from an argument, or from the newest `last_modified_time` in the
  input.

## What I verified and found clean

- **Strict detail filter vs what the apps send:** checked. Both apps send only `organization_id` on detail reads
  (`zoho-sync.js:371`, `sps-sync.js:140,361`, `client.js:44`). The list keys match `zoho-sync.js:166-167` and `sps-sync.js:90-91`.
- **Path to My jobs (gateway side):** checked. The hydrated detail passes the dashboard shape check (`zoho-sync.js:251-265`: all seven
  `QTY_KEYS` present and numeric, `tags` are objects). `divisionTag` sees `tag_name: "Division"` from the real map. The list row carries
  `status`, the three `quantity_*` fields and `last_modified_time`, so `listSignature` (`zoho-queue.js:12`) changes on confirm and each `/demo`
  step and the dashboard re-fetches. Drafts stay hidden (`line-jobs.js:139`). `shipped|shipped|invoiced` matches real recorded orders
  (61 of 309). The not-started values `pending` / `not_invoiced` are confirmed from 126 recorded confirmed orders (V-G2).
- **`last_modified_time` as `>=`, page-1 newest-first merge, unparseable upstream page passed through unmerged:** checked. This is consistent
  with both apps' early stop (`zoho-sync.js:196`, `sps-sync.js:245`). The full-list `seenKeys` includes the sandbox rows, so they are not
  marked `missing_in_zoho`.
- **Counter written before sandbox; refuse the start when there are orders but no counter:** checked. A crash between the two writes only
  burns a number. Torn or empty files stop the start (R4-AC6).
- **Atomic writes:** temp file, fsync, close, rename, then the 2xx. Cleanup on failure. Synchronous hydrate+commit, so concurrent POSTs do
  not race (only N6 open).
- **`shipped` fills packed too; `invoiced` leaves status:** matches the recorded Zoho shapes.
- **Security:** tokens are compared timing-safe, and the in-memory tokens expire after 1 h. The write tag is required on POSTs. The org is
  checked before any network call, and the path regex refuses `%` and `..`. No non-GET is forwarded (G-AC2 test covers every method). Logs
  carry the path without the query, so no token or body leaks (G-AC9). `/demo` takes its token from its own URL, and `advance` needs the
  `x-demo-token` header, so a cross-site form cannot drive it without the token. HTML is escaped. Binds 127.0.0.1 only. No new dependency
  (`better-sqlite3` and `dotenv` are already in `package.json`). `.env` and `data/` are gitignored; `maps.json` is not tracked.
- **Plain `node:http` instead of express:** an acceptable deviation; fewer parts, no URL normalisation surprises.
- **Placeholder contact:** left out of the served list (110 served = 111 recorded − placeholder), and checked before the map lookup.

## Not covered by this review

- G-AC6(b) and R4-AC3 live in the dashboard repo. The dashboard still hard-codes the Zoho URLs (`client.js:3-4`; R4-AC1 not built). So
  "a DEMO order reaches My jobs" is verified only by reading the code, not by running it.
- `tools/demo-gateway/ecosystem.demo.config.cjs` (§2.7) is not in this diff.
