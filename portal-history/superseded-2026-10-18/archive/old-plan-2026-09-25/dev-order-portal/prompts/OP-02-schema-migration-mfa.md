# OP-02 — Additive schema migration (portal half)

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** renamed from "Additive
schema migration + MFA" — MFA and the `recursive_triggers` pragma fix both moved to the December
dashboard track's own migration, `PD-03D`. This step now covers only the order-portal-specific
schema (`orders.company`/`.location`, the lookup-table conversion, `notifications`) — **do not
build MFA or the pragma fix here.**

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published
dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-02`):** build 28 Oct – 3 Nov 2026 (**FORCED**: later start; MFA schema and the `recursive_triggers` pragma fix removed — both now `PD-03D`). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

OP-01's spec delta is approved (`plan-critic: PASS`). This step turns it into code: a new,
strictly additive migration for the order-portal-specific schema only. Schema 001–004 is frozen —
never edit those files, never `DROP`/`RENAME` anything. MFA and the `recursive_triggers` pragma fix
are **not** built here — they're `PD-03D`, a separate step in the December dashboard track.

## Files to read first

1. The approved OP-01 spec delta (wherever it landed — the design spec or its companion file).
2. `server/db/migrations/001-schema.sql` through `004-migration-hashes-append-only.sql` — read in
   full for the existing pattern: how tables are declared, how append-only **(A)** tables get their
   triggers, how seed data is inserted in `002-seed.sql`.
3. `server/db/migrate.js`, `server/db/lint-migrations.js`, `server/db/migrations/MANIFEST.json`.
4. `/root/Production Dashboard/LATER.md` — item L31 (D3, D6, D7) in full (L35/D4, the
   `recursive_triggers` pragma fix, is `PD-03D`'s to apply, not this step's).
5. `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/02-process-steps.md`,
   step OP-02.

## Exact scope

- One or more new numbered migration files (`008-...sql`, `009-...sql` if needed; numbering decided 8 Oct, PD full-release spec §8.1) implementing
  OP-01's delta: `orders.company`/`.location` columns, the lookup tables replacing growing enums
  (with `NOT NULL` FKs and seed rows), the `notifications` table, `customer_portal` flag.
- Delete-protection triggers on every new lookup table (a referencing row must block deletion of
  the lookup row it references).
- Extend `MANIFEST.json` and the hash-guard coverage in `migrate.js` for the new files.
- Extend `lint-migrations.js` only if the new migration needs a check pattern it doesn't already
  enforce.

## What NOT to touch

- `001-schema.sql`, `002-seed.sql`, `003-migration-hashes.sql`, `004-migration-hashes-append-only.sql`
  — read-only, never edited.
- Any route or business logic — this step is schema only.
- **MFA tables/fields and the `recursive_triggers = ON` pragma** — both moved to `PD-03D`, the
  December dashboard track's own migration. Do not add either here.

## Pipeline gates to follow

`test-author` writes the migration + idempotency + trigger tests first → `implementer` writes the
migration → `test-runner` → `code-reviewer` → **`db-migration-guard` (required, this is a
schema-touching change)**. Do not merge without `db-migration-guard: PASS`.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. Never run a migration against a live database. Never run
`shdeploy`, `git push`, or restart any PM2 service — the human does that.

## Definition of done

- `npm test` green, including the migration-parsing test.
- A fresh `npm start` against an empty DB and against a copy of the current dev DB both apply the
  new migration(s) idempotently.
- Every new lookup table has a `foreign_key_check` test and a delete-protection trigger test.
- `db-migration-guard: PASS` recorded.

## Stop and ask conditions

- Any ambiguity in a seed value or column type not fully specified by OP-01's delta — stop and ask
  IT (the user); do not invent a plausible value.
- Anything that seems to require touching 001–004 — stop, you've scoped something wrong.
