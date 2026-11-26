# db-migration-guard — Production Dashboard migration 007 (`cf_portal_ref`)

Reviewed 2026-10-25, read-only. Repo `/root/dev/production-dashboard-v01`, branch `feature/joint-demo-v0.1`, commit `e8af351`.
Spec: `wiki/specs/2026-10-21-joint-demo-v0-1.md` §2 (lines 84-90), J-AC8 (219-221), §11 rollback (264-267).

## Migration under review

`server/db/migrations/007-portal-ref.sql:2`: `ALTER TABLE zoho_so_headers ADD COLUMN cf_portal_ref TEXT;` (one statement, nullable,
no default, no backfill). Plus the `MANIFEST.json` entry, the `config/zoho-columns.json:122` mapping `cf_portal_ref ← ["cf_portal_ref"]` (text),
and the AC48 edit in `test/release-migrations.test.js:34,40,71,74`.

How it runs: `server/db/migrate.js` `runMigrations` skips every file with `n <= user_version` (line 54), runs each new file plus
`user_version = n` plus its hash row in one transaction (61-69), and before that re-checks the sha256 of every applied file against the
append-only `schema_migrations` (44-49; triggers in 004). The guard is `user_version`, not "does the column exist", so it is **not** the
always-satisfied-guard bug class: once 007 is applied, the body never runs again.

## Simulated runs

Run in a scratch DB (`/tmp/claude-0/.../scratchpad/sim.db`, WAL, foreign_keys ON). Not a live snapshot: `/root/production-dashboard/` does not exist yet, so there is no live DB to snapshot.

- **first run on empty DB:** 001→007 applied in seven transactions; `{from:0,to:7}`; seven hash rows; the column is in the fresh schema (also J-AC8 test "fresh database").
- **first run on populated DB (v6 with a `zoho_so_headers` row):** only 007 applied, `{from:6,to:7}`; existing row gets `cf_portal_ref = NULL`, no other column changes (J-AC8 test checks this row by row, and that only the `zoho_so_headers` definition changes in `sqlite_master`). SQLite `ADD COLUMN` with no default is a metadata-only change: no rewrite of rows, no lock beyond the single write transaction.
- **second and subsequent runs:** runs 2–10 returned `{from:7,to:7}`, logged no "migration applied", and a value set between runs (`'keep'`) survived all ten. Hash for 007 recorded once (`a9d95e80…`), verified on every later start. `integrity_check = ok`, `foreign_key_check = []`.
- **rollback start (code at 006 on a v7 DB):** `WARN database user_version 7 is newer than this code (6); starting anyway` → starts, column unused. **Forward again:** `{from:7,to:7}`, hashes verify, nothing applied.

Tests: `node --test test/joint-demo-migration-007.test.js test/release-migrations.test.js test/migrations.test.js` → 35/35 pass.

## Findings

- **[D1] LOW — "a detail never blanks a stored Portal Ref" holds only when the key is *absent*.** `server/services/zoho-sync.js:288` puts a field in the UPDATE when its key is present in the payload (`k in obj`); `cli/import/columns.js:10,15` turns `""`/`null` into NULL; `cli/import/upsert.js:20-21` writes it. So a detail that carries `cf_portal_ref: ""` (or `null`) **clears** the stored value. That is the same mirror rule every other `cf_*` field follows (P-AC43), and Zoho is the source of truth, so the value is recoverable and this is the right behaviour if someone really cleared the field in Zoho. The risk is if Zoho sends the key empty for reasons other than a real clear. The J-AC8 test (`test/joint-demo-migration-007.test.js:149-153`) only covers the key-absent case, because the fake drops null keys (`test/helpers/fake-zoho.js:109`). **Change:** when OP G1 step 6 records the real API name, record too what the detail payload holds for an *unset* custom field (absent / `""` / `null`). If it can be `""` without a real clear, add a test and decide whether to keep the stored value. Not blocking for v0.1 (demo DBs are disposable).
- **[D2] LOW — the mapping key is still a placeholder.** `config/zoho-columns.json:122` maps from `cf_portal_ref`, which is assumed until OP G1 step 6 (spec §2 line 89; the test message at `test/joint-demo-migration-007.test.js:133` says so). If the real API name is different, nothing fails: the column just stays NULL and portal orders are not "always shown" (`server/services/job-queries.js:99`). The fix is a config change only, and the column name never has to change. **Change:** keep this on the v0.1 gate list (spec line 195, "P2 … + Portal Ref API name"), and add a one-line check to the demo-morning G3 TEST order: the TEST order's header row has a non-NULL `cf_portal_ref`.
- **[D3] INFO — the AC48 edit does not weaken the guard; it differs from the spec's wording.** Before the edit, AC48 ran a v5 DB on the real directory and pinned `user_version === 6`, which fails as soon as 007 exists. Now it runs on a 001–006 copy (`migrationsUpTo(6)`), so its exact-objects, NULL-on-existing-rows, hash-equals-MANIFEST and second-start-changes-nothing checks still test 006 alone, and they will not break again when 008 lands. The v5→latest-on-the-real-directory path a deploy takes is still tested by AC44 (`release-migrations.test.js:108`) and AC50 (`:126`). 007 has its own exact-objects test, as the spec requires. Two things are out of date: (a) the spec says the pin "is updated to read the expected version from the migrations folder" (spec line 85-86), and the code took a different, equally valid approach; (b) the file header `release-migrations.test.js:4` still says every DB "is then started on the real directory", which is no longer true for AC48. **Change:** amend spec §2 to describe the 001–006-copy approach, and fix the header comment. Neither is a migration change.
- **[D4] INFO — the pull/xlsx import paths do not carry the column.** `cli/import/upsert.js:25-33` (`HEADER_FIELDS_PULL`/`_XLSX`) leave out `cf_portal_ref`. They therefore never write it and never blank it; only the sync's detail write and list write (`upsert.js:45`, `ctx.fields` = keys present) do. That is fine for v0.1. Note it if CLI imports ever need to restore the Portal Ref.

Checked and clean, no finding:
- **Data loss:** none. The change is additive, there is no DML, nothing is dropped or renamed, and the linter passes.
- **Idempotency:** proven, see above.
- **Hash/MANIFEST:** `sha256sum` of all seven files equals `MANIFEST.json`, and the hash recorded in `schema_migrations` for n=7 equals the MANIFEST value. Editing an applied 007 is refused (J-AC8 test at line 106).
- **Numbering:** 001–007 are contiguous and unique (AC90 real-dir test). 008 stays free for the sign-in migration and matches the `/root/CLAUDE.md` reservation (line 128).
- **NULL/uniqueness:** the column is not in any key, index or conflict target, and the upsert keys are `(org, salesorder_number)`.
- **Backfill:** none needed, because the column is nullable and the spec says no backfill on purpose (only post-G3 orders carry a ref).
- **Transaction:** a single statement, applied inside the runner's per-migration transaction together with the `user_version` and hash row. There is no external call.
- **Ordering:** 007 depends only on `zoho_so_headers` (001), and `user_version` order enforces that.

## Schema-file drift

There is no separate declarative schema file: the schema is the migration chain, and a fresh DB is built from 001–007 (J-AC8 fresh-DB test).
`cf_portal_ref` exists in exactly these places: migration 007, the `config/zoho-columns.json` mapping, the reads at `server/services/line-jobs.js:134`
and `server/services/job-queries.js:99`, and the test fake. No code reads or writes a table that is missing from the chain. Not drift, but
note it: `HEADER_FIELDS_PULL`/`_XLSX` do not list the column (D4).

## Rollback procedure

There is no backup restore. 007 is additive, and the code below it ignores the column.
1. `shdeploy rollback production-dashboard` (or deploy the pre-`e8af351` commit). The older code starts on the v7 DB with the warning `user_version 7 is newer than this code (6); starting anyway` (`migrate.js:39-42`). That was verified in simulation.
2. Leave the column and the `schema_migrations` row for n=7 in place. Do **not** drop the column or lower `user_version`: the linter forbids DROP COLUMN, and `schema_migrations` is append-only (004).
3. Roll forward again by redeploying the same 007 file: the hash verifies and nothing is applied.
4. Never re-use number 007 for a different file. On a DB that already has 007, the hash guard refuses to start ("edited after it was applied"). It fails safe, but it fails.
5. Demo DBs: disposable by design (spec §11).

VERDICT: APPROVE

D1 and D2 are follow-ups tied to OP G1 step 6 (record the real API name and what an unset field looks like). D3 is a spec and comment wording fix. None of them changes the migration file, so 007 can be frozen as is.
