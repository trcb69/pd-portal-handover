# Production Dashboard — Release 0 (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A running, tested `production-dashboard` service with logins, admin configuration, the Zoho import CLI (with capture-time freshness and per-SO facts), the post-import sweep, backups, a health endpoint and an admin web UI. No job screens yet; those are Release 1.

**Architecture:** One Node 24 process (Express 5 + better-sqlite3) listening on 127.0.0.1:4300 and 172.17.0.1:4300, serving a JSON API, an SSE stream and a prebuilt React app from `web/dist`. The database schema for **all** releases is created by migration 001 (so later releases never need DROP/RENAME); Release 0 code only uses part of it. Zoho data enters only through `cli/import-zoho.js`, which writes mirror tables and never core tables; the server's sweep does the core-table follow-up.

**Tech Stack:** Node 24.18 (ESM), Express 5, better-sqlite3, exceljs, zod, dotenv, multer (installed now, used in Release 1); React 19 + Vite + TypeScript + Tailwind 4 + shadcn/ui source; node:test + supertest; Playwright + @axe-core/playwright.

**Spec:** `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (Rev 7.2, plan-critic PASS on Rev 7).

**Plan revision:** 3 — plan-critic review 1 (BLOCK: 3/7/13) and review 2 (BLOCK: 2 new blocking, 6 minor) addressed; see the tables at the end. Section references below (§n, ACn) are to that spec. Read §4, §5.2, §6, §8, §11, §12, §13 (Release 0), §14 before starting.

## Global Constraints

- Develop **only** in `/root/dev/production-dashboard`. Never write in `/root/production-dashboard` (live). Never deploy, restart PM2, push or run migrations against live data — produce the commands for the human.
- Port **4300**. Listen on `127.0.0.1` and `BRIDGE_HOST` (default `172.17.0.1`) only; never `0.0.0.0` / `::` / an undefined host (§4).
- `trust proxy` = only the addresses in `TRUSTED_PROXY_IPS` (default `172.18.0.3`) (§4).
- SQLite: WAL, `foreign_keys=ON`, `busy_timeout=10000` on every connection. Times stored as UTC ISO strings ending in `Z`. Colombo dates only via `shared/time.js` (fixed +05:30). Money in LKR cents.
- Migrations: numbered `.sql` files, `user_version`, forbidden `DROP TABLE`, `DROP COLUMN`, `RENAME`; `DROP VIEW|TRIGGER|INDEX IF EXISTS` only when the same file re-creates it. Seed = migration 002. `PD_MIGRATIONS_DIR` override. Migrations run at startup; the human never runs `migrate.js` by hand.
- Passwords: `crypto.scrypt` async, N=2^15, r=8, p=1, maxmem 64 MiB, 16-byte salt, min length 10. Session id 256-bit random, stored as SHA-256 only; cookie `pd_sid` `HttpOnly; Secure; SameSite=Strict; Path=/`; 12 h idle, 7 days absolute. No `SESSION_SECRET`.
- Rate limits: 10 login failures per username / 15 min → 429; 100 per IP / 15 min → 429.
- Every non-GET/HEAD request needs `Origin` equal to `APP_ORIGIN`; a missing `Origin` → 403.
- `/api/health` always 200 while the process is up; body `{ok, db, employeeMaster, lastImport, lastSync}`; never secrets.
- Zoho is **read-only** (D15). Nothing in this repo sends a non-GET request to Zoho.
- Upsert batches: 2,000 rows, each `BEGIN IMMEDIATE`. Capture guard on every mirror table (§6.2).
- Error bodies carry a request id only. Logs are JSON lines with user ids only.
- **Dependencies:** only those listed in Task 1. `@tailwindcss/vite`, `@types/react`, `@types/react-dom` and `@types/node` are **awaiting the user's OK** (Tailwind 4's official Vite plugin and TypeScript type packages; dev/build only). Do not start Task 17 until the main session confirms they are approved.
- Commit after every task in `/root/dev/production-dashboard` with a message ending in the attribution line the main session gives you.

## Verified data facts (2026-09-17) the code relies on

- `Sales_Order.xlsx`: one row per SO line; headers include `SalesOrder ID`, `Order Date`, `Expected Shipment Date`, `SalesOrder Number`, `Status`, `Item Name`, `SKU`, `QuantityOrdered`, `QuantityInvoiced`, `QuantityPacked`, `QuantityCancelled`, `Usage unit`, `Item Price`, `Item Total`, `Total`, `CF.Order Received from`, `CF.Base Material to be Used`, `CF.SH Sales Order Ref`, `CF.Job No`, `CF.Order Type`, `CF.Manufacturing Division`, `CF.Clickup Link`, `CF.Job Nature`, and **two** spellings each of the availability fields (`CF.Artwork Availability` / `CF.Artwork Availablility`, `CF.Dye Cutter Availability` / `CF.Dye Cutter Availablity`, `CF.Screen / Plate Available` / `CF.Screen / Plate Availability`). **No line number, no shipped quantity, no created/modified time.** Line number = 1-based order of the row within its SO in the file.
- `Package_ALL.xlsx` (and daily `Package.xlsx`): one row per package line; `PackageItemID` (unique line id), `Packing Date`, `Packing Number`, `SO Number`, `Status`, `Item Name`, `SKU`, `Quantity Packed`. No created time. Line key = `PackageItemID`.
- `Shipment_ALL.xlsx`: one row per (shipment, package); `Shipment ID`, `Packing Number`, `Shipment Date`, `Shipment Number`, `Status`, `Delivery Date`, `Created Time`, `Last Modified Time`, `SO Number`. No quantity. Line key = `Packing Number`.
- `Invoice.xlsx`: one row per invoice line; `Invoice Date`, `Invoice ID`, `Invoice Number`, `Invoice Status`, `Sales Order Number`, `Template Name`. No created time. Collapse to one row per invoice.
- `Picklist.xlsx`: `picklist_id`, `picklist_number`, `date`, `status`, `created_time` (`+0530`), `last_modified_time`, `salesorder_numbers` (comma list or empty).
- `Item.xlsx`: `Item ID`, `Item Name`, `SKU`, `Unit`, `Status`, `Is Combo Product`, `Last Modified Time`.
- Header-pull JSON (plain arrays): SO headers keys `salesorder_id, salesorder_number, reference_number, date, shipment_date, status, shipped_status, invoiced_status, quantity, quantity_packed, quantity_shipped, quantity_invoiced, total, created_time, last_modified_time, cf_*`; bundles keys `bundle_id, date, composite_item_name, quantity_to_bundle, reference_number, status, created_time, last_modified_time`; invoice headers keys `invoice_id, invoice_number, reference_number (= JOBORDER no), date, status, created_time, last_modified_time`. Times look like `2026-09-17T12:43:05+0530`.
- Naive xlsx timestamps (`2025-06-15 20:08:26`, or exceljs `Date` objects whose UTC fields hold the wall time) are **Colombo local time**.
- 12 distinct `cf_manufacturing_division` values (§6.5). `cf_order_type` values: `Customized Order`, `Ex Stock`, `Internal SH Order`, `Make to Order (MTO)`.

## File Structure

```
/root/dev/production-dashboard/
  package.json, package-lock.json, .gitignore, .env.example, README.md
  server/
    config.js              env → frozen config object
    app.js                 entry: open DB, migrate, rebuild facts if needed, start listeners, start sweep timer
    create-app.js          express app factory (injected db, clock, config, sse)
    listen.js              dual listeners with bridge retry
    log.js                 JSON-line logger
    db/
      open.js              openDb(path) with pragmas
      migrate.js           runMigrations(db, dir) + CLI guard message
      lint-migrations.js   lintMigration(sql) → string[] problems
      migrations/001-schema.sql, 002-seed.sql
    auth/
      password.js          hashPassword, verifyPassword
      sessions.js          createSession, loadSession, revokeUserSessions
      rate-limit.js        makeLimiter
      middleware.js        requireOrigin, loadUser, requireAuth, requireRole
    routes/
      auth.js, health.js, admin-users.js, admin-config.js, admin-imports.js, events.js
    services/
      audit.js             audit(db, actor, action, entity, id, detail)
      sse.js               createSseHub()
      forms.js             loadForms(db, dir)
      facts.js             FACTS_RULES_VERSION, recomputeFacts, rebuildAllFacts, ensureFactsVersion
      freshness.js         shippedFresh, bundlesDataAge
      sweep.js             runSweep, resolvePendingLink, startSweepTimer
      employee-master.js   status() → 'not_configured' (Release 5 fills it in)
  shared/
    time.js, text.js, schemas.js, labels.js
  cli/
    import-zoho.js         CLI entry
    import/columns.js      loads config/zoho-columns.json
    import/readers.js      readXlsxRows, readJsonArray
    import/files.js        classifyFolder, loadCaptured
    import/upsert.js       upsert functions per module (capture guard)
    import/run.js          importFolder(db, opts)
    captured.js            helper to write/merge captured.json
    create-admin.js, backup.js, restore-check.js
  config/
    zoho-columns.json
    forms/.gitkeep
  tools/zoho-pull-snippet.js
  scripts/build-stamp.mjs
  web/  index.html, vite.config.ts, tsconfig.json, src/…, dist/ (committed)
  test/
    helpers/db.js, helpers/app.js, helpers/xlsx.js
    fixtures/zoho/…        small hand-made files with real headers
    *.test.js
    e2e/admin.spec.js, e2e/pull-snippet.spec.js, playwright.config.js
  docs/runbook-release-0.md
```

---
### Task 1: Repository scaffold

**Files:**
- Create: `package.json`, `.gitignore`, `.env.example`, `README.md`, `server/config.js`, `server/log.js`, `test/helpers/db.js` (stub filled in Task 3), `test/config.test.js`

**Interfaces:**
- Produces: `loadConfig(env = process.env) → Readonly<{port, bridgeHost, appOrigin, trustedProxyIps: string[], dbPath, filesDir, backupsDir, migrationsDir, sweepIntervalMs, employeeMasterUrl, employeeMasterToken, nodeEnv}>`; `log.info(msg, fields)`, `log.warn`, `log.error` writing one JSON line to stdout/stderr.

- [ ] **Step 1: Create the repo and install dependencies**

```bash
mkdir -p /root/dev/production-dashboard && cd /root/dev/production-dashboard && git init -b main
npm init -y
npm pkg set type=module name=production-dashboard private=true engines.node=">=24"
npm install express better-sqlite3 dotenv multer exceljs zod
npm install --save-dev supertest @playwright/test @axe-core/playwright jsqr
```

Expected: `package-lock.json` created. (Front-end packages are installed in Task 15.)

- [ ] **Step 2: Scripts and ignore file**

```bash
npm pkg set scripts.start="node server/app.js" \
  scripts.test="node --test --test-concurrency=1 test/*.test.js" \
  scripts.test:e2e="playwright test -c test/e2e/playwright.config.js" \
  scripts.build="vite build web && node scripts/build-stamp.mjs"
```

`.gitignore`:
```
node_modules/
data/
.env
test-results/
playwright-report/
```

`.env.example`:
```
PORT=4300
BRIDGE_HOST=172.17.0.1
APP_ORIGIN=https://production.standard-holdings.lk
TRUSTED_PROXY_IPS=172.18.0.3
DB_PATH=data/production.db
# EMPLOYEE_MASTER_URL= (Release 5)
# EMPLOYEE_MASTER_TOKEN= (Release 5, read-only token)
```

- [ ] **Step 3: Write the failing config test** — `test/config.test.js`

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadConfig } from '../server/config.js';

test('defaults', () => {
  const c = loadConfig({});
  assert.equal(c.port, 4300);
  assert.equal(c.bridgeHost, '172.17.0.1');
  assert.deepEqual(c.trustedProxyIps, ['172.18.0.3']);
  assert.equal(c.migrationsDir.endsWith('server/db/migrations'), true);
  assert.equal(c.sweepIntervalMs, 30000);
});

test('overrides and lists', () => {
  const c = loadConfig({ PORT: '4400', BRIDGE_HOST: '', TRUSTED_PROXY_IPS: '10.0.0.1, 10.0.0.2', PD_MIGRATIONS_DIR: '/tmp/m' });
  assert.equal(c.port, 4400);
  assert.equal(c.bridgeHost, '');
  assert.deepEqual(c.trustedProxyIps, ['10.0.0.1', '10.0.0.2']);
  assert.equal(c.migrationsDir, '/tmp/m');
  assert.throws(() => { c.port = 1; });
});

test('rejects wildcard bridge host', () => {
  assert.throws(() => loadConfig({ BRIDGE_HOST: '0.0.0.0' }), /BRIDGE_HOST/);
  assert.throws(() => loadConfig({ BRIDGE_HOST: '::' }), /BRIDGE_HOST/);
});
```

- [ ] **Step 4: Run it — expect FAIL** (`Cannot find module '../server/config.js'`)

Run: `npm test`

- [ ] **Step 5: Implement** — `server/config.js`

```js
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const list = (v, d) => (v ?? d).split(',').map((s) => s.trim()).filter(Boolean);

export function loadConfig(env = process.env) {
  const bridgeHost = env.BRIDGE_HOST ?? '172.17.0.1';
  if (['0.0.0.0', '::', '*'].includes(bridgeHost)) throw new Error('BRIDGE_HOST must be a specific address');
  const dbPath = path.resolve(ROOT, env.DB_PATH ?? 'data/production.db');
  return Object.freeze({
    root: ROOT,
    port: Number(env.PORT ?? 4300),
    bridgeHost,
    appOrigin: env.APP_ORIGIN ?? 'https://production.standard-holdings.lk',
    trustedProxyIps: Object.freeze(list(env.TRUSTED_PROXY_IPS, '172.18.0.3')),
    dbPath,
    filesDir: path.resolve(path.dirname(dbPath), 'files'),
    backupsDir: path.resolve(path.dirname(dbPath), 'backups'),
    migrationsDir: env.PD_MIGRATIONS_DIR ?? path.join(ROOT, 'server/db/migrations'),
    formsDir: path.join(ROOT, 'config/forms'),
    webDist: path.join(ROOT, 'web/dist'),
    sweepIntervalMs: Number(env.SWEEP_INTERVAL_MS ?? 30000),
    employeeMasterUrl: env.EMPLOYEE_MASTER_URL ?? '',
    employeeMasterToken: env.EMPLOYEE_MASTER_TOKEN ?? '',
    nodeEnv: env.NODE_ENV ?? 'production',
  });
}
```

`server/log.js`:
```js
const write = (stream, level, msg, fields = {}) =>
  stream.write(JSON.stringify({ t: new Date().toISOString(), level, msg, ...fields }) + '\n');
export const log = {
  info: (m, f) => write(process.stdout, 'info', m, f),
  warn: (m, f) => write(process.stderr, 'warn', m, f),
  error: (m, f) => write(process.stderr, 'error', m, f),
};
```

- [ ] **Step 6: Run — expect PASS.** `npm test`

- [ ] **Step 7: README stub and commit**

`README.md` — service name, port, the dev/live doctrine (§4b of the VPS doctrine), "migrations run at startup; do not run migrate.js by hand", and "shdeploy installs dev dependencies into the live tree (`npm ci --no-audit --no-fund`); that is expected".

```bash
git add -A && git commit -m "chore: scaffold production-dashboard"
```

---

### Task 2: Shared time and text helpers

**Files:**
- Create: `shared/time.js`, `shared/text.js`, `test/time.test.js`, `test/text.test.js`

**Interfaces:**
- Produces (`shared/time.js`):
  - `colomboDate(utcIso: string) → 'YYYY-MM-DD'`
  - `colomboToday(now: Date) → 'YYYY-MM-DD'`
  - `parseZohoTime(value, kind: 'time'|'date') → { iso: string, precision: 'time'|'date' } | null` — accepts ISO with offset (`+0530`, `+05:30`, `Z`), epoch ms (number or 13-digit string), exceljs `Date` (UTC fields = Colombo wall time), `'YYYY-MM-DD HH:MM:SS'` (Colombo wall time), `'YYYY-MM-DD'` (00:00 Colombo, precision `date`). With `kind='date'` the result always has precision `date`.
  - `previousWorkingDay(date: 'YYYY-MM-DD', cal: { weekdays: number[], holidays: Set<string> }) → 'YYYY-MM-DD'` (weekdays: 0=Sun…6=Sat)
  - `isRecentCapture(capturedIso, now: Date, cal) → boolean` = `colomboDate(capturedIso) >= previousWorkingDay(colomboToday(now), cal)`
- Produces (`shared/text.js`):
  - `cleanText(v) → string|null` (trim, collapse internal whitespace, '' → null)
  - `cmpKey(v) → string|null` (cleanText + lower-case)
  - `soKey(reference) → string|null` (§6.2)
  - `isShBlocked(ref) → boolean` (§6.4)
  - `toCents(v) → number|null`, `toNumber(v) → number|null`

- [ ] **Step 1: Failing tests** — `test/time.test.js`

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { colomboDate, parseZohoTime, previousWorkingDay, isRecentCapture } from '../shared/time.js';

const cal = { weekdays: [1, 2, 3, 4, 5], holidays: new Set(['2026-09-21']) }; // Mon 21 Sep = holiday

test('colomboDate boundaries (AC0.10)', () => {
  assert.equal(colomboDate('2026-09-16T19:00:00Z'), '2026-09-17');
  assert.equal(colomboDate('2026-09-16T18:29:59Z'), '2026-09-16');
});

test('parseZohoTime formats (AC0.10)', () => {
  assert.deepEqual(parseZohoTime('2026-09-17T12:43:05+0530', 'time'), { iso: '2026-09-17T07:13:05.000Z', precision: 'time' });
  assert.deepEqual(parseZohoTime('2026-09-17T12:43:05+05:30', 'time'), { iso: '2026-09-17T07:13:05.000Z', precision: 'time' });
  assert.deepEqual(parseZohoTime(1718461706000, 'time'), { iso: '2024-06-15T14:28:26.000Z', precision: 'time' });
  assert.deepEqual(parseZohoTime('1718461706000', 'time'), { iso: '2024-06-15T14:28:26.000Z', precision: 'time' });
  assert.deepEqual(parseZohoTime('2025-06-15 20:08:26', 'time'), { iso: '2025-06-15T14:38:26.000Z', precision: 'time' });
  assert.deepEqual(parseZohoTime(new Date(Date.UTC(2025, 5, 15, 20, 8, 26)), 'time'), { iso: '2025-06-15T14:38:26.000Z', precision: 'time' });
  assert.deepEqual(parseZohoTime('2026-09-14', 'time'), { iso: '2026-09-13T18:30:00.000Z', precision: 'date' });
  assert.deepEqual(parseZohoTime('2024-04-02 00:00:00', 'date'), { iso: '2024-04-01T18:30:00.000Z', precision: 'date' });
  assert.equal(parseZohoTime('', 'time'), null);
  assert.equal(parseZohoTime(null, 'date'), null);
  assert.throws(() => parseZohoTime('17/09/2026', 'time'), /Unrecognised time/);
  assert.throws(() => parseZohoTime(45000, 'date'), /Excel serial/);
});

test('previousWorkingDay skips weekends and holidays', () => {
  assert.equal(previousWorkingDay('2026-09-22', cal), '2026-09-18'); // Tue → Fri (Mon is a holiday)
  assert.equal(previousWorkingDay('2026-09-14', cal), '2026-09-11'); // Mon → Fri
});

test('isRecentCapture (AC0.20b l)', () => {
  const fri = '2026-09-11T03:00:00Z', sat = '2026-09-12T03:00:00Z', sun = '2026-09-20T03:00:00Z';
  assert.equal(isRecentCapture(fri, new Date('2026-09-14T03:00:00Z'), cal), true);   // Mon morning
  assert.equal(isRecentCapture(fri, new Date('2026-09-15T03:00:00Z'), cal), false);  // Tue
  assert.equal(isRecentCapture(sat, new Date('2026-09-14T03:00:00Z'), cal), true);   // Sat capture on Mon
  assert.equal(isRecentCapture(sun, new Date('2026-09-22T03:00:00Z'), cal), true);   // Sun before holiday Mon, on Tue
});
```

`test/text.test.js`:
```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cleanText, cmpKey, soKey, isShBlocked, toCents } from '../shared/text.js';

test('cleanText trims and collapses (AC0.10)', () => {
  assert.equal(cleanText('Reorder '), 'Reorder');
  assert.equal(cleanText('  Folding  Box   Board '), 'Folding Box Board');
  assert.equal(cleanText('   '), null);
  assert.equal(cmpKey(' Not Avaialble '), 'not avaialble');
});

test('soKey (AC1.20 rule, used by facts)', () => {
  assert.equal(soKey('JOBORDER-08338 - C'), 'JOBORDER-08338');
  assert.equal(soKey('joborder-08338'), 'JOBORDER-08338');
  assert.equal(soKey('JOBORDER-083381'), 'JOBORDER-083381');
  assert.equal(soKey('hello world'), null);
  assert.equal(soKey(''), null);
});

test('isShBlocked covers the real variants (AC0.20b j)', () => {
  for (const v of ['To be received', 'to receive', 'TO BE RECEIVDE', 'to b received', 'to be receives',
    'TO BE RECEVIED', 'to be recevide', 'TO BE RECIVED', 'to be recevived']) assert.equal(isShBlocked(v), true, v);
  for (const v of ['HTXSO260702836', '', null, 'received']) assert.equal(isShBlocked(v), false, String(v));
});

test('toCents', () => {
  assert.equal(toCents('134617.5'), 13461750);
  assert.equal(toCents(''), null);
});
```

- [ ] **Step 2: Run — expect FAIL** (modules missing). `npm test`

- [ ] **Step 3: Implement** — `shared/time.js`

```js
const OFFSET_MS = 5.5 * 3600 * 1000;
const pad = (n) => String(n).padStart(2, '0');
const ymd = (d) => `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;

export const colomboDate = (utcIso) => ymd(new Date(Date.parse(utcIso) + OFFSET_MS));
export const colomboToday = (now) => colomboDate(now.toISOString());

// Wall-clock fields in Colombo → UTC instant
const fromColomboWall = (y, mo, d, h = 0, mi = 0, s = 0) =>
  new Date(Date.UTC(y, mo - 1, d, h, mi, s) - OFFSET_MS);

export function parseZohoTime(value, kind) {
  if (value === null || value === undefined || value === '') return null;
  let date; let precision = 'time';
  if (value instanceof Date) {
    date = fromColomboWall(value.getUTCFullYear(), value.getUTCMonth() + 1, value.getUTCDate(),
      value.getUTCHours(), value.getUTCMinutes(), value.getUTCSeconds());
  } else if (typeof value === 'number' || /^\d{13}$/.test(String(value).trim())) {
    // Only epoch milliseconds are accepted. An Excel serial day number (≈45,000) means the
    // cell's date style was not read; refuse it rather than store a 1970 date.
    if (Number(value) < 1e11) throw new Error(`Unrecognised time value: ${value} (looks like an Excel serial date)`);
    date = new Date(Number(value));
  } else {
    const s = String(value).trim();
    let m;
    if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})$/))) {
      date = new Date(s.replace(/([+-]\d{2})(\d{2})$/, '$1:$2'));
    } else if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/))) {
      date = fromColomboWall(+m[1], +m[2], +m[3], +m[4], +m[5], +m[6]);
    } else if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/))) {
      date = fromColomboWall(+m[1], +m[2], +m[3]);
      precision = 'date';
    } else {
      throw new Error(`Unrecognised time value: ${s}`);
    }
  }
  if (Number.isNaN(date.getTime())) throw new Error(`Unrecognised time value: ${value}`);
  if (kind === 'date') {
    const day = colomboDate(date.toISOString()).split('-').map(Number);
    return { iso: fromColomboWall(day[0], day[1], day[2]).toISOString(), precision: 'date' };
  }
  return { iso: date.toISOString(), precision };
}

export function previousWorkingDay(dateStr, cal) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  do { d.setUTCDate(d.getUTCDate() - 1); }
  while (!cal.weekdays.includes(d.getUTCDay()) || cal.holidays.has(ymd(d)));
  return ymd(d);
}

export const isRecentCapture = (capturedIso, now, cal) =>
  colomboDate(capturedIso) >= previousWorkingDay(colomboToday(now), cal);
```

`shared/text.js`:
```js
export function cleanText(v) {
  if (v === null || v === undefined) return null;
  const s = String(v).replace(/\s+/g, ' ').trim();
  return s === '' ? null : s;
}
export const cmpKey = (v) => cleanText(v)?.toLowerCase() ?? null;
export function soKey(reference) {
  const s = cleanText(reference)?.toUpperCase();
  const m = s?.match(/^([A-Z]+-\d+)(\s*-.*)?$/);
  return m ? m[1] : null;
}
export const isShBlocked = (ref) => /^to\s+(b|be)?\s*rec/.test(cmpKey(ref) ?? '');
export function toNumber(v) {
  if (v === null || v === undefined || String(v).trim() === '') return null;
  const n = Number(String(v).replace(/,/g, ''));
  if (Number.isNaN(n)) throw new Error(`Not a number: ${v}`);
  return n;
}
export const toCents = (v) => { const n = toNumber(v); return n === null ? null : Math.round(n * 100); };
```

- [ ] **Step 4: Run — expect PASS.** `npm test`
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: shared Colombo time and text helpers"`

---

### Task 3: Database open, migrations, linter and full schema

**Files:**
- Create: `server/db/open.js`, `server/db/migrate.js`, `server/db/lint-migrations.js`, `server/db/migrations/001-schema.sql`, `test/helpers/db.js`, `test/migrations.test.js`, `test/schema.test.js`

**Interfaces:**
- Produces: `openDb(file: string) → Database` (pragmas set); `runMigrations(db, dir, logger?) → { from, to }` (throws on a lint problem; warns when `user_version` > highest file); `lintMigration(sql: string) → string[]`; test helper `makeDb({ migrationsDir? }) → { db, file, dir, close() }` (temp dir, migrations applied).

- [ ] **Step 1: Failing tests** — `test/migrations.test.js` (AC0.2, AC0.15)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { lintMigration, lintAll } from '../server/db/lint-migrations.js';
import { runMigrations } from '../server/db/migrate.js';
import { openDb } from '../server/db/open.js';
import { makeDb, MIGRATIONS } from './helpers/db.js';

test('linter rejects forbidden statements', () => {
  assert.ok(lintMigration('DROP TABLE jobs;').length);
  assert.ok(lintMigration('ALTER TABLE jobs DROP COLUMN job_no;').length);
  assert.ok(lintMigration('ALTER TABLE jobs RENAME TO x;').length);
  assert.ok(lintMigration('ALTER TABLE jobs RENAME COLUMN a TO b;').length);
  assert.ok(lintMigration('DROP INDEX IF EXISTS ix_a;').length);
  assert.deepEqual(lintMigration('DROP INDEX IF EXISTS ix_a; CREATE INDEX ix_a ON jobs(id);'), []);
  assert.deepEqual(lintMigration('DROP TRIGGER IF EXISTS t1;\nCREATE TRIGGER t1 BEFORE DELETE ON jobs BEGIN SELECT 1; END;'), []);
  assert.ok(lintMigration('DROP VIEW v1;').length, 'DROP VIEW without IF EXISTS');
});

test('every shipped migration passes the linter', () => {
  assert.deepEqual(lintAll(MIGRATIONS), []);
});

test('pragmas', () => {
  const { db, close } = makeDb();
  assert.equal(db.pragma('journal_mode', { simple: true }), 'wal');
  assert.equal(db.pragma('foreign_keys', { simple: true }), 1);
  assert.equal(db.pragma('busy_timeout', { simple: true }), 10000);
  close();
});

test('startup twice changes nothing (AC0.2)', () => {
  const { db, file, dir, close } = makeDb();
  const counts = () => db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").all()
    .map(({ name }) => [name, db.prepare(`SELECT count(*) c FROM "${name}"`).get().c]);
  const before = { v: db.pragma('user_version', { simple: true }), c: counts() };
  runMigrations(db, dir);
  assert.deepEqual({ v: db.pragma('user_version', { simple: true }), c: counts() }, before);
  close();
});

test('an extra migration in a custom dir is applied; newer schema warns (AC0.15)', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pdmig-'));
  for (const f of fs.readdirSync(MIGRATIONS)) fs.copyFileSync(path.join(MIGRATIONS, f), path.join(tmp, f));
  fs.writeFileSync(path.join(tmp, '900-extra.sql'), 'CREATE TABLE extra_test (id INTEGER PRIMARY KEY);');
  const { db, dir, close } = makeDb({ migrationsDir: tmp });
  assert.ok(db.prepare("SELECT 1 FROM sqlite_master WHERE name='extra_test'").get());
  const warnings = [];
  runMigrations(db, MIGRATIONS, { warn: (m) => warnings.push(m), info() {} });
  assert.match(warnings.join(' '), /newer than this code/);
  close();
});
```

`test/schema.test.js` (AC0.3, AC0.18):
```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeDb } from './helpers/db.js';

const APPEND_ONLY = ['job_so_links', 'job_status_events', 'job_assignment_events', 'manual_stage_events',
  'stage_overrides', 'handovers', 'form_submissions', 'submission_reviews', 'output_entries',
  'reference_entries', 'reference_matches', 'reference_approvals', 'qc_ticks', 'order_events',
  'order_messages', 'order_message_hides', 'audit_log', 'orders', 'order_lines'];

test('every append-only table has abort triggers for UPDATE and DELETE (AC0.3)', () => {
  const { db, close } = makeDb();
  for (const t of APPEND_ONLY) {
    const trig = db.prepare("SELECT sql FROM sqlite_master WHERE type='trigger' AND tbl_name=?").all(t).map((r) => r.sql).join('\n');
    assert.match(trig, /BEFORE UPDATE/i, `${t} update trigger`);
    assert.match(trig, /BEFORE DELETE/i, `${t} delete trigger`);
  }
  db.prepare("INSERT INTO audit_log(at, actor, action, entity, entity_id, detail_json) VALUES ('2026-01-01T00:00:00Z','t','x','e','1','{}')").run();
  assert.throws(() => db.prepare('UPDATE audit_log SET action = ?').run('y'), /append-only/);
  assert.throws(() => db.prepare('DELETE FROM audit_log').run(), /append-only/);
  // exercise a job-side table and the order tables too
  db.prepare("INSERT OR IGNORE INTO divisions(code, name) VALUES ('OPD','OPD')").run();
  db.prepare("INSERT INTO users(username, display_name, password_hash, created_at) VALUES ('z','Z','x','x')").run();
  db.prepare("INSERT INTO teams(name) VALUES ('T')").run();
  const jobId = db.prepare("INSERT INTO jobs(division_code, order_type, created_by, created_at) VALUES ('OPD','customised',1,'x')").run().lastInsertRowid;
  db.prepare("INSERT INTO job_so_links(job_id, action, salesorder_number, actor_type, at) VALUES (?, 'link', 'J', 'user', 'x')").run(jobId);
  assert.throws(() => db.prepare("UPDATE job_so_links SET salesorder_number='K'").run(), /append-only/);
  assert.throws(() => db.prepare('DELETE FROM job_so_links').run(), /append-only/);
  const o = db.prepare("INSERT INTO orders(requester_id, team_id, customer, required_date, order_type, submitted_at, entered_at, created_via, entered_by) VALUES (1,1,'C','2026-10-01','customised','x','x','portal',1)").run().lastInsertRowid;
  db.prepare("INSERT INTO order_lines(order_id, line_no, item_description, qty, unit) VALUES (?, 1, 'Box', 10, 'pcs')").run(o);
  assert.throws(() => db.prepare("UPDATE orders SET customer='D'").run(), /append-only/);
  assert.throws(() => db.prepare('UPDATE order_lines SET qty=11').run(), /append-only/);
  assert.throws(() => db.prepare('DELETE FROM order_lines').run(), /append-only/);
  close();
});

function seedJob(db) {
  // Task 3 runs before the seed migration exists, so create the rows the FKs need.
  db.prepare("INSERT OR IGNORE INTO divisions(code, name) VALUES ('OPD','OPD')").run();
  db.prepare("INSERT OR IGNORE INTO reason_codes(code, label, default_owner_label) VALUES ('artwork','A','Coordinator'), ('rework','R','Manager')").run();
  db.prepare("INSERT INTO users(username, display_name, password_hash, roles, created_at) VALUES ('u','U','x','[\"admin\"]','2026-01-01T00:00:00Z')").run();
  const job = db.prepare("INSERT INTO jobs(division_code, org, order_type, created_by, created_at) VALUES ('OPD','SPS','customised',1,'2026-01-01T00:00:00Z')").run();
  return Number(job.lastInsertRowid);
}

test('blockers: one close only (AC0.3)', () => {
  const { db, close } = makeDb();
  const jobId = seedJob(db);
  const b = db.prepare("INSERT INTO blockers(job_id, reason_code, owner_label, opened_by, opened_at) VALUES (?, 'artwork', 'Design', 1, '2026-01-01T00:00:00Z')").run(jobId);
  db.prepare("UPDATE blockers SET closed_by=1, closed_at='2026-01-02T00:00:00Z' WHERE id=?").run(b.lastInsertRowid);
  assert.throws(() => db.prepare("UPDATE blockers SET closed_at='2026-01-03T00:00:00Z' WHERE id=?").run(b.lastInsertRowid), /blockers/);
  const b2 = db.prepare("INSERT INTO blockers(job_id, reason_code, owner_label, opened_by, opened_at) VALUES (?, 'rework', 'Manager', 1, 'x')").run(jobId).lastInsertRowid;
  assert.throws(() => db.prepare("UPDATE blockers SET owner_label='y' WHERE id=?").run(b2), /blockers/);
  close();
});

test('attachments: one soft delete; portal_visible only on job files (AC0.3)', () => {
  const { db, close } = makeDb();
  const jobId = seedJob(db);
  const a = db.prepare("INSERT INTO attachments(job_id, kind, portal_visible, original_name, stored_name, mime, size_bytes, sha256, uploaded_by, uploaded_at) VALUES (?, 'artwork', 0, 'a.pdf', 's1', 'application/pdf', 1, 'h', 1, 'x')").run(jobId).lastInsertRowid;
  db.prepare('UPDATE attachments SET portal_visible=1 WHERE id=?').run(a);
  db.prepare("UPDATE attachments SET deleted_by=1, deleted_at='x', delete_reason='wrong' WHERE id=?").run(a);
  assert.throws(() => db.prepare("UPDATE attachments SET deleted_at='y' WHERE id=?").run(a), /attachments/);
  assert.throws(() => db.prepare('UPDATE attachments SET portal_visible=0 WHERE id=?').run(a), /attachments/);
  assert.throws(() => db.prepare("UPDATE attachments SET original_name='b' WHERE id=?").run(a), /attachments/);
  close();
});

test('generated numbers read back right after insert (AC0.18)', () => {
  const { db, close } = makeDb();
  const jobId = seedJob(db);
  assert.equal(db.prepare('SELECT file_no FROM jobs WHERE id=?').get(jobId).file_no, `PD-${String(jobId).padStart(6, '0')}`);
  db.prepare("INSERT INTO teams(name) VALUES ('Sales')").run();
  const o = db.prepare("INSERT INTO orders(requester_id, team_id, customer, required_date, order_type, submitted_at, entered_at, created_via, entered_by) VALUES (1, 1, 'C', '2026-10-01', 'customised', 'x', 'x', 'portal', 1)").run().lastInsertRowid;
  assert.equal(db.prepare('SELECT order_no FROM orders WHERE id=?').get(o).order_no, `OR-${String(o).padStart(6, '0')}`);
  close();
});

test('one job per order (partial unique)', () => {
  const { db, close } = makeDb();
  seedJob(db);
  db.prepare("INSERT INTO teams(name) VALUES ('Sales')").run();
  db.prepare("INSERT INTO orders(requester_id, team_id, customer, required_date, order_type, submitted_at, entered_at, created_via, entered_by) VALUES (1, 1, 'C', '2026-10-01', 'customised', 'x', 'x', 'portal', 1)").run();
  const ins = db.prepare("INSERT INTO jobs(division_code, org, order_type, order_id, created_by, created_at) VALUES ('OPD','SPS','customised',1,1,'x')");
  ins.run();
  assert.throws(() => ins.run(), /UNIQUE/);
  close();
});
```


- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement** — `server/db/open.js`

```js
import Database from 'better-sqlite3';
import fs from 'node:fs';
import path from 'node:path';

export function openDb(file, { readonly = false } = {}) {
  if (!readonly) fs.mkdirSync(path.dirname(file), { recursive: true });
  const db = new Database(file, { readonly, fileMustExist: readonly });
  if (!readonly) db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  db.pragma('busy_timeout = 10000');
  return db;
}
```

`server/db/lint-migrations.js`:
```js
import fs from 'node:fs';
import path from 'node:path';

const strip = (sql) => sql.replace(/--.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');

export function lintMigration(sqlText) {
  const sql = strip(sqlText);
  const problems = [];
  if (/\bDROP\s+TABLE\b/i.test(sql)) problems.push('DROP TABLE is forbidden');
  if (/\bDROP\s+COLUMN\b/i.test(sql)) problems.push('DROP COLUMN is forbidden');
  if (/\bRENAME\b/i.test(sql)) problems.push('RENAME is forbidden');
  for (const m of sql.matchAll(/\bDROP\s+(VIEW|TRIGGER|INDEX)\s+(IF\s+EXISTS\s+)?("?[\w]+"?)/gi)) {
    const [, kind, ifExists, rawName] = m;
    const name = rawName.replace(/"/g, '');
    if (!ifExists) problems.push(`DROP ${kind} ${name} must use IF EXISTS`);
    const recreate = new RegExp(`\\bCREATE\\s+(UNIQUE\\s+)?${kind}\\s+(IF\\s+NOT\\s+EXISTS\\s+)?"?${name}"?\\b`, 'i');
    if (!recreate.test(sql)) problems.push(`DROP ${kind} ${name} without re-creating it in the same file`);
  }
  return problems;
}

export const migrationFiles = (dir) =>
  fs.readdirSync(dir).filter((f) => /^\d{3}-[\w-]+\.sql$/.test(f)).sort();

export const lintAll = (dir) =>
  migrationFiles(dir).flatMap((f) => lintMigration(fs.readFileSync(path.join(dir, f), 'utf8')).map((p) => `${f}: ${p}`));
```

`server/db/migrate.js`:
```js
import fs from 'node:fs';
import path from 'node:path';
import { lintMigration, migrationFiles } from './lint-migrations.js';
import { log } from '../log.js';

export function runMigrations(db, dir, logger = log) {
  const files = migrationFiles(dir);
  const highest = files.length ? Number(files.at(-1).slice(0, 3)) : 0;
  const from = db.pragma('user_version', { simple: true });
  if (from > highest) {
    logger.warn(`database user_version ${from} is newer than this code (${highest}); starting anyway`);
    return { from, to: from };
  }
  for (const f of files) {
    const n = Number(f.slice(0, 3));
    if (n <= from) continue;
    const sql = fs.readFileSync(path.join(dir, f), 'utf8');
    const problems = lintMigration(sql);
    if (problems.length) throw new Error(`${f}: ${problems.join('; ')}`);
    db.transaction(() => { db.exec(sql); db.pragma(`user_version = ${n}`); })();
    logger.info(`migration applied: ${f}`);
  }
  return { from, to: db.pragma('user_version', { simple: true }) };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  console.error('Do not run migrate.js by hand. Migrations run when the service starts (spec §6.1).');
  process.exit(1);
}
```

`test/helpers/db.js`:
```js
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { openDb } from '../../server/db/open.js';
import { runMigrations } from '../../server/db/migrate.js';

const quiet = { info() {}, warn() {}, error() {} };
// The Release 1+ compatibility check runs this suite with PD_MIGRATIONS_DIR pointing at newer migrations.
export const MIGRATIONS = process.env.PD_MIGRATIONS_DIR ?? path.resolve('server/db/migrations');
export function makeDb({ migrationsDir = MIGRATIONS } = {}) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pdtest-'));
  const file = path.join(tmp, 'test.db');
  const db = openDb(file);
  runMigrations(db, migrationsDir, quiet);
  return { db, file, dir: migrationsDir, tmp, close: () => { db.close(); fs.rmSync(tmp, { recursive: true, force: true }); } };
}
```

`server/db/migrations/001-schema.sql` — the complete schema below. Rules: every column the spec lists (§6.2, §6.3) exists now so later releases add no destructive changes; (A) tables get the two abort triggers; times are TEXT.

```sql
-- 001: full schema for all releases (spec Rev 7.1 §6.2, §6.3)

-- ===== mirror (written only by cli/import) =====
CREATE TABLE zoho_so_headers (
  org TEXT NOT NULL, salesorder_number TEXT NOT NULL, zoho_id TEXT, order_date TEXT,
  expected_shipment_date TEXT, reference_number TEXT, status TEXT, shipped_status TEXT, invoiced_status TEXT,
  quantity REAL, quantity_packed REAL, quantity_shipped REAL, quantity_invoiced REAL, total_cents INTEGER,
  cf_job_no TEXT, cf_order_received_from TEXT, cf_order_type TEXT, cf_manufacturing_division TEXT,
  cf_job_nature TEXT, cf_material_to_be_used TEXT, cf_sh_sales_order_ref TEXT, cf_clickup_link TEXT,
  cf_artwork_availablility TEXT, cf_dye_cutter_availablity TEXT, cf_screen_plate_availability_2 TEXT,
  created_at TEXT, modified_at TEXT, source TEXT NOT NULL CHECK (source IN ('xlsx','pull','sync')),
  source_file TEXT, last_synced_at TEXT NOT NULL, sync_state TEXT, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, salesorder_number)
);
CREATE TABLE zoho_so_lines (
  org TEXT NOT NULL, salesorder_number TEXT NOT NULL, line_no INTEGER NOT NULL,
  item_name TEXT, sku TEXT, quantity_ordered REAL, quantity_packed REAL, quantity_invoiced REAL,
  quantity_cancelled REAL, usage_unit TEXT, rate_cents INTEGER, amount_cents INTEGER,
  source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, salesorder_number, line_no)
);
-- One row per SO: the capture that last wrote its line set from Sales_Order.xlsx (plan rev 2, M5).
CREATE TABLE zoho_so_line_sets (
  org TEXT NOT NULL, salesorder_number TEXT NOT NULL, captured_at TEXT NOT NULL, line_count INTEGER NOT NULL,
  PRIMARY KEY (org, salesorder_number)
);
CREATE TABLE zoho_bundles (
  org TEXT NOT NULL, zoho_id TEXT NOT NULL, reference_number TEXT, so_key TEXT, date TEXT,
  composite_item_name TEXT, quantity REAL, status TEXT, created_at TEXT, modified_at TEXT,
  source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, zoho_id)
);
CREATE INDEX ix_bundles_so ON zoho_bundles(org, so_key);
CREATE TABLE zoho_package_lines (
  org TEXT NOT NULL, package_number TEXT NOT NULL, line_no TEXT NOT NULL, -- line_no = Zoho PackageItemID
  so_number TEXT, packing_date TEXT, status TEXT, item_name TEXT, sku TEXT, quantity_packed REAL,
  source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, package_number, line_no)
);
CREATE UNIQUE INDEX ux_package_line_id ON zoho_package_lines(org, line_no);
CREATE INDEX ix_packages_so ON zoho_package_lines(org, so_number);
CREATE TABLE zoho_shipment_lines (
  org TEXT NOT NULL, shipment_number TEXT NOT NULL, line_no TEXT NOT NULL, -- line_no = Packing Number
  so_number TEXT, packing_number TEXT, shipment_date TEXT, delivery_date TEXT, status TEXT,
  created_at TEXT, modified_at TEXT, source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, shipment_number, line_no)
);
CREATE INDEX ix_shipments_so ON zoho_shipment_lines(org, so_number);
CREATE TABLE zoho_invoices (
  org TEXT NOT NULL, invoice_number TEXT NOT NULL, so_number TEXT, invoice_date TEXT,
  invoice_date_precision TEXT, status TEXT, created_at TEXT, modified_at TEXT,
  source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, invoice_number)
);
CREATE INDEX ix_invoices_so ON zoho_invoices(org, so_number);
CREATE TABLE zoho_picklists (
  org TEXT NOT NULL, zoho_id TEXT NOT NULL, picklist_number TEXT, date TEXT, status TEXT,
  salesorder_numbers TEXT, created_at TEXT, modified_at TEXT,
  source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, zoho_id)
);
CREATE TABLE zoho_picklist_sos (
  org TEXT NOT NULL, picklist_id TEXT NOT NULL, so_number TEXT NOT NULL,
  PRIMARY KEY (org, picklist_id, so_number)
);
CREATE INDEX ix_picklist_sos_so ON zoho_picklist_sos(org, so_number);
CREATE TABLE zoho_items (
  org TEXT NOT NULL, zoho_id TEXT NOT NULL, name TEXT, sku TEXT, unit TEXT, status TEXT,
  is_composite INTEGER, modified_at TEXT, source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, zoho_id)
);
CREATE TABLE zoho_so_facts (
  org TEXT NOT NULL, so_number TEXT NOT NULL, stage_id INTEGER NOT NULL,
  done_at TEXT NOT NULL, at_precision TEXT NOT NULL CHECK (at_precision IN ('time','date')), source_ref TEXT,
  PRIMARY KEY (org, so_number, stage_id)
);
CREATE TABLE zoho_import_runs (
  id INTEGER PRIMARY KEY, org TEXT NOT NULL, module TEXT NOT NULL, source TEXT NOT NULL, file TEXT,
  captured_at TEXT NOT NULL, full_list INTEGER NOT NULL DEFAULT 0,
  status TEXT CHECK (status IS NULL OR status IN ('ok','warning','failed')),
  started_at TEXT NOT NULL, finished_at TEXT, processed_at TEXT,
  rows_read INTEGER NOT NULL DEFAULT 0, rows_upserted INTEGER NOT NULL DEFAULT 0, rows_skipped INTEGER NOT NULL DEFAULT 0,
  changed_so_numbers TEXT NOT NULL DEFAULT '[]', warnings TEXT NOT NULL DEFAULT '[]', error TEXT,
  CHECK ((status IS NULL) = (finished_at IS NULL))
);
CREATE INDEX ix_runs_module ON zoho_import_runs(org, module, captured_at);
CREATE INDEX ix_runs_unprocessed ON zoho_import_runs(processed_at) WHERE processed_at IS NULL;

-- ===== people and config =====
CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE users (
  id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE, display_name TEXT NOT NULL,
  password_hash TEXT NOT NULL, roles TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(roles)),
  team_id INTEGER REFERENCES teams(id), can_create_files INTEGER NOT NULL DEFAULT 0,
  can_receive_files INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  must_reset INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE sessions (
  id_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
  created_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, expires_at TEXT NOT NULL, ip TEXT, user_agent TEXT
);
CREATE INDEX ix_sessions_user ON sessions(user_id);
CREATE TABLE divisions (
  code TEXT PRIMARY KEY, name TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
  provisional INTEGER NOT NULL DEFAULT 0, floor_live INTEGER NOT NULL DEFAULT 0,
  counting_process TEXT, quantity_form_id TEXT NOT NULL DEFAULT 'inline_inspection_run',
  FOREIGN KEY (code, counting_process) REFERENCES processes(division_code, code)
);
CREATE TABLE processes (
  division_code TEXT NOT NULL REFERENCES divisions(code), code TEXT NOT NULL, label TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1, counts_in_production INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (division_code, code)
);
CREATE TABLE division_aliases (zoho_value TEXT PRIMARY KEY, zoho_key TEXT NOT NULL UNIQUE, division_code TEXT NOT NULL REFERENCES divisions(code));
CREATE TABLE division_pairs (
  id INTEGER PRIMARY KEY, division_code TEXT NOT NULL REFERENCES divisions(code),
  manager_user_id INTEGER NOT NULL REFERENCES users(id), coordinator_user_id INTEGER NOT NULL REFERENCES users(id),
  active INTEGER NOT NULL DEFAULT 1, UNIQUE (division_code, manager_user_id, coordinator_user_id)
);
CREATE TABLE stage_catalog (id INTEGER PRIMARY KEY CHECK (id BETWEEN 1 AND 11), name TEXT NOT NULL, detected INTEGER NOT NULL, detector_key TEXT);
CREATE TABLE division_stages (
  division_code TEXT NOT NULL REFERENCES divisions(code), stage_id INTEGER NOT NULL REFERENCES stage_catalog(id),
  sort_order INTEGER NOT NULL, PRIMARY KEY (division_code, stage_id), UNIQUE (division_code, sort_order)
);
CREATE TABLE order_type_aliases (zoho_value TEXT PRIMARY KEY, zoho_key TEXT NOT NULL UNIQUE, order_type TEXT NOT NULL CHECK (order_type IN ('customised','ex_stock','internal')), provisional INTEGER NOT NULL DEFAULT 0);
CREATE TABLE reason_codes (code TEXT PRIMARY KEY, label TEXT NOT NULL, default_owner_label TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE reject_reasons (code TEXT PRIMARY KEY, label TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE holidays (date TEXT PRIMARY KEY, label TEXT NOT NULL);
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);

-- ===== jobs =====
CREATE TABLE orders (
  id INTEGER PRIMARY KEY, order_no TEXT GENERATED ALWAYS AS ('OR-' || printf('%06d', id)) VIRTUAL,
  requester_id INTEGER NOT NULL REFERENCES users(id), team_id INTEGER NOT NULL REFERENCES teams(id),
  customer TEXT NOT NULL, required_date TEXT NOT NULL,
  order_type TEXT NOT NULL CHECK (order_type IN ('customised','ex_stock','internal')),
  division_hint TEXT REFERENCES divisions(code), notes TEXT,
  submitted_at TEXT NOT NULL, entered_at TEXT NOT NULL,
  created_via TEXT NOT NULL CHECK (created_via IN ('portal','on_behalf')), entered_by INTEGER NOT NULL REFERENCES users(id)
);
CREATE TABLE order_lines (
  order_id INTEGER NOT NULL REFERENCES orders(id), line_no INTEGER NOT NULL,
  item_description TEXT NOT NULL, qty REAL NOT NULL, unit TEXT NOT NULL, notes TEXT,
  PRIMARY KEY (order_id, line_no)
);
CREATE TABLE jobs (
  id INTEGER PRIMARY KEY, file_no TEXT GENERATED ALWAYS AS ('PD-' || printf('%06d', id)) VIRTUAL,
  job_no TEXT, division_code TEXT NOT NULL REFERENCES divisions(code), org TEXT NOT NULL DEFAULT 'SPS',
  order_id INTEGER REFERENCES orders(id),
  entered_product TEXT, entered_customer TEXT, entered_ordered_qty REAL, entered_unit TEXT, entered_delivery_date TEXT,
  order_type TEXT NOT NULL CHECK (order_type IN ('customised','ex_stock','internal')),
  job_nature TEXT, order_received_at TEXT, created_by INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
  UNIQUE (division_code, job_no)
);
CREATE UNIQUE INDEX ux_jobs_order ON jobs(order_id) WHERE order_id IS NOT NULL;
CREATE TABLE job_so_links (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id),
  action TEXT NOT NULL CHECK (action IN ('link_pending','link','unlink')), salesorder_number TEXT,
  actor_type TEXT NOT NULL CHECK (actor_type IN ('user','system')), actor_id INTEGER, at TEXT NOT NULL, note TEXT
);
CREATE INDEX ix_links_job ON job_so_links(job_id, id);
CREATE TABLE job_status_events (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id),
  status TEXT NOT NULL CHECK (status IN ('open','closed','cancelled')), actor_id INTEGER NOT NULL, at TEXT NOT NULL, reason TEXT
);
CREATE INDEX ix_status_job ON job_status_events(job_id, id);
CREATE TABLE job_assignment_events (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), pair_id INTEGER NOT NULL REFERENCES division_pairs(id),
  actor_id INTEGER NOT NULL, at TEXT NOT NULL, reason TEXT
);
CREATE INDEX ix_assign_job ON job_assignment_events(job_id, id);
CREATE TABLE manual_stage_events (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), stage_id INTEGER NOT NULL CHECK (stage_id IN (1,2,3,9,11)),
  action TEXT NOT NULL CHECK (action IN ('tick','untick')), actor_type TEXT NOT NULL, actor_id INTEGER, actor_label TEXT,
  at TEXT NOT NULL, note TEXT, CHECK (action = 'tick' OR note IS NOT NULL)
);
CREATE INDEX ix_manual_job ON manual_stage_events(job_id, stage_id, id);
CREATE TABLE stage_overrides (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), stage_id INTEGER NOT NULL CHECK (stage_id IN (4,5,6,7,8,10)),
  action TEXT NOT NULL CHECK (action IN ('force_done','force_not_done','clear')), salesorder_number TEXT,
  actor_id INTEGER NOT NULL, at TEXT NOT NULL, note TEXT NOT NULL
);
CREATE INDEX ix_overrides_job ON stage_overrides(job_id, stage_id, id);
CREATE TABLE handovers (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), kind TEXT NOT NULL,
  from_state TEXT NOT NULL, to_state TEXT NOT NULL, actor_type TEXT NOT NULL CHECK (actor_type IN ('user','worker')),
  actor_id INTEGER, actor_label TEXT, device_id INTEGER, at TEXT NOT NULL, note TEXT
);
CREATE INDEX ix_handovers_job ON handovers(job_id, id);
CREATE TABLE blockers (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), reason_code TEXT NOT NULL REFERENCES reason_codes(code),
  note TEXT, owner_label TEXT NOT NULL, opened_by INTEGER NOT NULL, opened_at TEXT NOT NULL,
  closed_by INTEGER, closed_at TEXT
);
CREATE UNIQUE INDEX ux_blockers_open ON blockers(job_id, reason_code) WHERE closed_at IS NULL;
CREATE TABLE day_plans (
  job_id INTEGER NOT NULL REFERENCES jobs(id), plan_date TEXT NOT NULL, process TEXT NOT NULL,
  planned_qty REAL NOT NULL, set_by INTEGER NOT NULL, set_at TEXT NOT NULL, PRIMARY KEY (job_id, plan_date, process)
);
CREATE TABLE order_messages (
  id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id), author_id INTEGER NOT NULL REFERENCES users(id),
  body TEXT NOT NULL CHECK (length(body) <= 4000), at TEXT NOT NULL, internal INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE order_message_hides (
  id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL UNIQUE REFERENCES order_messages(id),
  actor_id INTEGER NOT NULL, at TEXT NOT NULL, reason TEXT NOT NULL
);
CREATE TABLE attachments (
  id INTEGER PRIMARY KEY, job_id INTEGER REFERENCES jobs(id), order_id INTEGER REFERENCES orders(id),
  message_id INTEGER REFERENCES order_messages(id), kind TEXT NOT NULL, portal_visible INTEGER NOT NULL DEFAULT 0,
  original_name TEXT NOT NULL, stored_name TEXT NOT NULL UNIQUE, mime TEXT NOT NULL, size_bytes INTEGER NOT NULL,
  sha256 TEXT NOT NULL, uploaded_by INTEGER NOT NULL, uploaded_at TEXT NOT NULL,
  deleted_by INTEGER, deleted_at TEXT, delete_reason TEXT,
  CHECK ((job_id IS NULL) <> (order_id IS NULL))
);
CREATE TABLE form_definitions (
  id TEXT NOT NULL, version INTEGER NOT NULL, division_code TEXT, title TEXT NOT NULL,
  schema_json TEXT NOT NULL, output_map_json TEXT NOT NULL, content_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL, PRIMARY KEY (id, version)
);
CREATE TABLE floor_devices (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, division_code TEXT NOT NULL REFERENCES divisions(code),
  token_hash TEXT NOT NULL UNIQUE, enrolled_by INTEGER NOT NULL, enrolled_at TEXT NOT NULL, revoked_at TEXT, last_seen_at TEXT
);
CREATE TABLE floor_sessions (
  id_hash TEXT PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES floor_devices(id), worker_epf TEXT NOT NULL,
  worker_name TEXT NOT NULL, started_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, ended_at TEXT, pin_verified_at TEXT
);
CREATE TABLE enrollment_codes (
  code_hash TEXT PRIMARY KEY, division_code TEXT NOT NULL REFERENCES divisions(code), device_name TEXT NOT NULL,
  created_by INTEGER NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL, used_at TEXT, invalidated_at TEXT
);
CREATE TABLE enroll_failures (ip TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE floor_drafts (
  id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES floor_devices(id), worker_epf TEXT NOT NULL,
  job_id INTEGER NOT NULL REFERENCES jobs(id), form_id TEXT NOT NULL, form_version INTEGER NOT NULL,
  payload_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  UNIQUE (device_id, worker_epf, job_id, form_id)
);
CREATE TABLE form_submissions (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), form_id TEXT NOT NULL, form_version INTEGER NOT NULL,
  payload_json TEXT NOT NULL, actor_type TEXT NOT NULL, actor_id INTEGER, actor_label TEXT,
  device_id INTEGER REFERENCES floor_devices(id), dept_mismatch INTEGER NOT NULL DEFAULT 0, submitted_at TEXT NOT NULL,
  supersedes_id INTEGER UNIQUE REFERENCES form_submissions(id),
  FOREIGN KEY (form_id, form_version) REFERENCES form_definitions(id, version)
);
CREATE TABLE submission_reviews (
  id INTEGER PRIMARY KEY, submission_id INTEGER NOT NULL REFERENCES form_submissions(id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','queried')), note TEXT, actor_id INTEGER NOT NULL, at TEXT NOT NULL
);
CREATE TABLE output_entries (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), division_code TEXT NOT NULL,
  entry_date TEXT NOT NULL, checkpoint TEXT, process TEXT NOT NULL, line_no INTEGER NOT NULL,
  quantity REAL, minutes REAL, source_form_id TEXT, worker_epf TEXT, worker_label TEXT, missed_reason_code TEXT,
  source TEXT NOT NULL CHECK (source IN ('manager','submission')), source_submission_id INTEGER REFERENCES form_submissions(id),
  entered_by_type TEXT NOT NULL, entered_by_id INTEGER, entered_at TEXT NOT NULL, device_id INTEGER,
  supersedes_id INTEGER UNIQUE REFERENCES output_entries(id),
  FOREIGN KEY (division_code, process) REFERENCES processes(division_code, code),
  CHECK (source <> 'submission' OR (source_submission_id IS NOT NULL AND worker_epf IS NOT NULL AND source_form_id IS NOT NULL))
);
CREATE UNIQUE INDEX ux_output_submission_line ON output_entries(source_submission_id, line_no) WHERE source = 'submission';
CREATE TABLE reference_entries (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), section TEXT NOT NULL,
  reference_no TEXT NOT NULL, qty REAL, entered_by INTEGER NOT NULL, entered_at TEXT NOT NULL,
  supersedes_id INTEGER UNIQUE REFERENCES reference_entries(id), voided INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE reference_matches (
  id INTEGER PRIMARY KEY, reference_entry_id INTEGER NOT NULL REFERENCES reference_entries(id),
  zoho_ref TEXT NOT NULL, actor_type TEXT NOT NULL CHECK (actor_type IN ('user','system')), at TEXT NOT NULL
);
CREATE INDEX ix_reference_matches_entry ON reference_matches(reference_entry_id);
CREATE TABLE reference_approvals (
  id INTEGER PRIMARY KEY, reference_entry_id INTEGER NOT NULL REFERENCES reference_entries(id),
  decision TEXT NOT NULL, actor_id INTEGER NOT NULL, at TEXT NOT NULL, note TEXT
);
CREATE TABLE qc_ticks (
  id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id), kind TEXT NOT NULL,
  paper_doc_ref TEXT, actor_id INTEGER NOT NULL, at TEXT NOT NULL
);
CREATE TABLE order_events (
  id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
  event TEXT NOT NULL CHECK (event IN ('submitted','asked','answered','accepted','rejected','cancel_requested','cancel_declined','cancel_resolved','cancelled')),
  reject_reason_code TEXT REFERENCES reject_reasons(code), actor_id INTEGER NOT NULL, at TEXT NOT NULL, note TEXT,
  job_id INTEGER REFERENCES jobs(id)
);
CREATE INDEX ix_order_events ON order_events(order_id, id);
CREATE TABLE upload_quota (
  user_id INTEGER NOT NULL REFERENCES users(id), colombo_date TEXT NOT NULL,
  files INTEGER NOT NULL DEFAULT 0, bytes INTEGER NOT NULL DEFAULT 0, messages INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, colombo_date)
);
CREATE TABLE outbox (
  id INTEGER PRIMARY KEY, job_id INTEGER REFERENCES jobs(id), target TEXT NOT NULL, payload_json TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'held' CHECK (state = 'held'), created_at TEXT NOT NULL
);
CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
  entity TEXT NOT NULL, entity_id TEXT, detail_json TEXT NOT NULL DEFAULT '{}'
);

-- ===== append-only guards =====
-- One pair per table; the message contains "append-only".
CREATE TRIGGER ao_u_job_so_links BEFORE UPDATE ON job_so_links BEGIN SELECT RAISE(ABORT, 'job_so_links is append-only'); END;
CREATE TRIGGER ao_d_job_so_links BEFORE DELETE ON job_so_links BEGIN SELECT RAISE(ABORT, 'job_so_links is append-only'); END;
CREATE TRIGGER ao_u_job_status_events BEFORE UPDATE ON job_status_events BEGIN SELECT RAISE(ABORT, 'job_status_events is append-only'); END;
CREATE TRIGGER ao_d_job_status_events BEFORE DELETE ON job_status_events BEGIN SELECT RAISE(ABORT, 'job_status_events is append-only'); END;
CREATE TRIGGER ao_u_job_assignment_events BEFORE UPDATE ON job_assignment_events BEGIN SELECT RAISE(ABORT, 'job_assignment_events is append-only'); END;
CREATE TRIGGER ao_d_job_assignment_events BEFORE DELETE ON job_assignment_events BEGIN SELECT RAISE(ABORT, 'job_assignment_events is append-only'); END;
CREATE TRIGGER ao_u_manual_stage_events BEFORE UPDATE ON manual_stage_events BEGIN SELECT RAISE(ABORT, 'manual_stage_events is append-only'); END;
CREATE TRIGGER ao_d_manual_stage_events BEFORE DELETE ON manual_stage_events BEGIN SELECT RAISE(ABORT, 'manual_stage_events is append-only'); END;
CREATE TRIGGER ao_u_stage_overrides BEFORE UPDATE ON stage_overrides BEGIN SELECT RAISE(ABORT, 'stage_overrides is append-only'); END;
CREATE TRIGGER ao_d_stage_overrides BEFORE DELETE ON stage_overrides BEGIN SELECT RAISE(ABORT, 'stage_overrides is append-only'); END;
CREATE TRIGGER ao_u_handovers BEFORE UPDATE ON handovers BEGIN SELECT RAISE(ABORT, 'handovers is append-only'); END;
CREATE TRIGGER ao_d_handovers BEFORE DELETE ON handovers BEGIN SELECT RAISE(ABORT, 'handovers is append-only'); END;
CREATE TRIGGER ao_u_form_submissions BEFORE UPDATE ON form_submissions BEGIN SELECT RAISE(ABORT, 'form_submissions is append-only'); END;
CREATE TRIGGER ao_d_form_submissions BEFORE DELETE ON form_submissions BEGIN SELECT RAISE(ABORT, 'form_submissions is append-only'); END;
CREATE TRIGGER ao_u_submission_reviews BEFORE UPDATE ON submission_reviews BEGIN SELECT RAISE(ABORT, 'submission_reviews is append-only'); END;
CREATE TRIGGER ao_d_submission_reviews BEFORE DELETE ON submission_reviews BEGIN SELECT RAISE(ABORT, 'submission_reviews is append-only'); END;
CREATE TRIGGER ao_u_output_entries BEFORE UPDATE ON output_entries BEGIN SELECT RAISE(ABORT, 'output_entries is append-only'); END;
CREATE TRIGGER ao_d_output_entries BEFORE DELETE ON output_entries BEGIN SELECT RAISE(ABORT, 'output_entries is append-only'); END;
CREATE TRIGGER ao_u_reference_entries BEFORE UPDATE ON reference_entries BEGIN SELECT RAISE(ABORT, 'reference_entries is append-only'); END;
CREATE TRIGGER ao_d_reference_entries BEFORE DELETE ON reference_entries BEGIN SELECT RAISE(ABORT, 'reference_entries is append-only'); END;
CREATE TRIGGER ao_u_reference_matches BEFORE UPDATE ON reference_matches BEGIN SELECT RAISE(ABORT, 'reference_matches is append-only'); END;
CREATE TRIGGER ao_d_reference_matches BEFORE DELETE ON reference_matches BEGIN SELECT RAISE(ABORT, 'reference_matches is append-only'); END;
CREATE TRIGGER ao_u_reference_approvals BEFORE UPDATE ON reference_approvals BEGIN SELECT RAISE(ABORT, 'reference_approvals is append-only'); END;
CREATE TRIGGER ao_d_reference_approvals BEFORE DELETE ON reference_approvals BEGIN SELECT RAISE(ABORT, 'reference_approvals is append-only'); END;
CREATE TRIGGER ao_u_qc_ticks BEFORE UPDATE ON qc_ticks BEGIN SELECT RAISE(ABORT, 'qc_ticks is append-only'); END;
CREATE TRIGGER ao_d_qc_ticks BEFORE DELETE ON qc_ticks BEGIN SELECT RAISE(ABORT, 'qc_ticks is append-only'); END;
CREATE TRIGGER ao_u_order_events BEFORE UPDATE ON order_events BEGIN SELECT RAISE(ABORT, 'order_events is append-only'); END;
CREATE TRIGGER ao_d_order_events BEFORE DELETE ON order_events BEGIN SELECT RAISE(ABORT, 'order_events is append-only'); END;
CREATE TRIGGER ao_u_order_messages BEFORE UPDATE ON order_messages BEGIN SELECT RAISE(ABORT, 'order_messages is append-only'); END;
CREATE TRIGGER ao_d_order_messages BEFORE DELETE ON order_messages BEGIN SELECT RAISE(ABORT, 'order_messages is append-only'); END;
CREATE TRIGGER ao_u_order_message_hides BEFORE UPDATE ON order_message_hides BEGIN SELECT RAISE(ABORT, 'order_message_hides is append-only'); END;
CREATE TRIGGER ao_d_order_message_hides BEFORE DELETE ON order_message_hides BEGIN SELECT RAISE(ABORT, 'order_message_hides is append-only'); END;
CREATE TRIGGER ao_u_audit_log BEFORE UPDATE ON audit_log BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER ao_d_audit_log BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER ao_u_orders BEFORE UPDATE ON orders BEGIN SELECT RAISE(ABORT, 'orders is append-only'); END;
CREATE TRIGGER ao_d_orders BEFORE DELETE ON orders BEGIN SELECT RAISE(ABORT, 'orders is append-only'); END;
CREATE TRIGGER ao_u_order_lines BEFORE UPDATE ON order_lines BEGIN SELECT RAISE(ABORT, 'order_lines is append-only'); END;
CREATE TRIGGER ao_d_order_lines BEFORE DELETE ON order_lines BEGIN SELECT RAISE(ABORT, 'order_lines is append-only'); END;

CREATE TRIGGER blockers_update_guard BEFORE UPDATE ON blockers
WHEN OLD.closed_at IS NOT NULL OR NEW.closed_at IS NULL OR NEW.closed_by IS NULL
  OR NEW.id IS NOT OLD.id OR NEW.job_id IS NOT OLD.job_id OR NEW.reason_code IS NOT OLD.reason_code
  OR NEW.note IS NOT OLD.note OR NEW.owner_label IS NOT OLD.owner_label
  OR NEW.opened_by IS NOT OLD.opened_by OR NEW.opened_at IS NOT OLD.opened_at
BEGIN SELECT RAISE(ABORT, 'blockers: only a single close is allowed'); END;
CREATE TRIGGER blockers_no_delete BEFORE DELETE ON blockers BEGIN SELECT RAISE(ABORT, 'blockers: rows are never deleted'); END;

CREATE TRIGGER attachments_update_guard BEFORE UPDATE ON attachments
WHEN NEW.id IS NOT OLD.id OR NEW.job_id IS NOT OLD.job_id OR NEW.order_id IS NOT OLD.order_id
  OR NEW.message_id IS NOT OLD.message_id OR NEW.kind IS NOT OLD.kind OR NEW.original_name IS NOT OLD.original_name
  OR NEW.stored_name IS NOT OLD.stored_name OR NEW.mime IS NOT OLD.mime OR NEW.size_bytes IS NOT OLD.size_bytes
  OR NEW.sha256 IS NOT OLD.sha256 OR NEW.uploaded_by IS NOT OLD.uploaded_by OR NEW.uploaded_at IS NOT OLD.uploaded_at
  OR OLD.deleted_at IS NOT NULL
  OR NOT (
    -- (a) one-time soft delete, nothing else changes
    (NEW.deleted_at IS NOT NULL AND NEW.deleted_by IS NOT NULL AND NEW.delete_reason IS NOT NULL
      AND NEW.portal_visible IS OLD.portal_visible)
    OR
    -- (b) portal_visible toggle on a job file
    (NEW.deleted_at IS NULL AND NEW.deleted_by IS NULL AND NEW.delete_reason IS NULL
      AND OLD.job_id IS NOT NULL AND NEW.portal_visible IS NOT OLD.portal_visible)
  )
BEGIN SELECT RAISE(ABORT, 'attachments: only one soft delete, or portal_visible on job files'); END;
CREATE TRIGGER attachments_no_delete BEFORE DELETE ON attachments BEGIN SELECT RAISE(ABORT, 'attachments: rows are never deleted'); END;
```

- [ ] **Step 4: Run — expect PASS.** `npm test`
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: database open, migrations, linter and full schema"`

---

### Task 4: Seed migration 002

**Files:**
- Create: `server/db/migrations/002-seed.sql`, `test/seed.test.js`

**Interfaces:**
- Produces: seeded `divisions` (14 codes), `processes`, `stage_catalog`, `division_stages`, `division_aliases`, `order_type_aliases`, `reason_codes`, `reject_reasons`, `settings('working_weekdays','[1,2,3,4,5]')`. No users, no pairs.

- [ ] **Step 1: Failing test** — `test/seed.test.js` (AC0.24, AC0.17 first half, AC1.26 data)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { makeDb, MIGRATIONS } from './helpers/db.js';
import { runMigrations } from '../server/db/migrate.js';

const quiet = { info() {}, warn() {} };

test('002 applies on an empty DB with foreign keys on (AC0.24)', () => {
  const { db, close } = makeDb();
  assert.deepEqual(db.pragma('foreign_key_check'), []);
  assert.equal(db.prepare('SELECT count(*) c FROM divisions').get().c, 14);
  assert.equal(db.prepare('SELECT count(*) c FROM division_pairs').get().c, 0);
  assert.equal(db.prepare("SELECT counting_process FROM divisions WHERE code='RWU'").get().counting_process, 'rewinding');
  assert.equal(db.prepare("SELECT quantity_form_id FROM divisions WHERE code='RWU'").get().quantity_form_id, 'rwu_internal_job_card');
  close();
});

test('stage orders match §6.5', () => {
  const { db, close } = makeDb();
  const order = (d) => db.prepare('SELECT stage_id FROM division_stages WHERE division_code=? ORDER BY sort_order').all(d).map((r) => r.stage_id).join(',');
  assert.equal(order('OPD'), '1,2,3,4,6,5,7,8,9,10,11');
  assert.equal(order('SHPS'), '1,2,3,4,5,6,7,8,9,10,11');
  assert.equal(order('PSU'), '1,2,3,4,5,7,8,9,10,11');
  assert.equal(order('RWU'), '2,3,4,5,7,8,9,10,11');
  for (const d of ['MOBA', 'MOBA_P', 'FPP', 'CPU', 'PACKPRO', 'PCU', 'PCLU', 'DPU', 'PPU', 'CWU']) assert.equal(order(d), order('OPD'), d);
  close();
});

test('all 12 Zoho division values are mapped', () => {
  const { db, close } = makeDb();
  const values = ['Offset Printing Division (OPD)', 'Screen Printing Division (SHPS)', 'Paper Straw Unit (PSU)',
    'Rewinding Unit (RWU)', 'Paper Cup Unit (PCU)', 'Customized Packing Unit (CPU)', 'MOBA Punching Unit',
    'Paper Cup Lid Unit', 'Food Product Processing (FPP)', 'Digital Printing Unit (DPU)', 'Paper Plate Unit', 'Cake Wrapper Unit'];
  for (const v of values) assert.ok(db.prepare('SELECT 1 FROM division_aliases WHERE zoho_value=?').get(v), v);
  close();
});

test('an output row with another division\'s process is refused (AC0.24)', () => {
  const { db, close } = makeDb();
  db.prepare("INSERT INTO users(username, display_name, password_hash, created_at) VALUES ('u','U','x','x')").run();
  db.prepare("INSERT INTO jobs(division_code, order_type, created_by, created_at) VALUES ('SHPS','customised',1,'x')").run();
  assert.throws(() => db.prepare("INSERT INTO output_entries(job_id, division_code, entry_date, process, line_no, source, entered_by_type, entered_at) VALUES (1,'SHPS','2026-09-17','rewinding',1,'manager','user','x')").run(), /FOREIGN KEY/);
  close();
});

test('deleted seed rows stay deleted; later migrations converge (AC0.17)', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pdseed-'));
  for (const f of fs.readdirSync(MIGRATIONS)) fs.copyFileSync(path.join(MIGRATIONS, f), path.join(tmp, f));
  const { db, close } = makeDb({ migrationsDir: tmp });
  db.prepare("DELETE FROM division_aliases WHERE zoho_value='Cake Wrapper Unit'").run();
  db.prepare("UPDATE divisions SET counting_process='curing' WHERE code='SHPS'").run(); // admin edit (seed value is 'print')
  fs.writeFileSync(path.join(tmp, '901-psu-count.sql'), "UPDATE divisions SET counting_process='forming' WHERE code='PSU';");
  runMigrations(db, tmp, quiet);
  assert.equal(db.prepare("SELECT 1 FROM division_aliases WHERE zoho_value='Cake Wrapper Unit'").get(), undefined);
  assert.equal(db.prepare("SELECT counting_process FROM divisions WHERE code='PSU'").get().counting_process, 'forming');
  assert.equal(db.prepare("SELECT counting_process FROM divisions WHERE code='SHPS'").get().counting_process, 'curing', 'admin edit survives');
  const fresh = makeDb({ migrationsDir: tmp });
  assert.equal(fresh.db.prepare("SELECT counting_process FROM divisions WHERE code='PSU'").get().counting_process, 'forming');
  fresh.close(); close();
});
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement** — `server/db/migrations/002-seed.sql`, in the §6.5 insert order:

```sql
-- 002: seed configuration (spec §6.5). Pairs are NOT seeded (created by the admin at go-live).
INSERT INTO divisions(code, name, provisional) VALUES
 ('OPD','Offset Printing Division',0), ('SHPS','Screen Printing Division',0), ('PSU','Paper Straw Unit',0),
 ('RWU','Rewinding Unit',0), ('MOBA','MOBA Punching Unit',1), ('MOBA_P','MOBA Punching (P)',1),
 ('FPP','Food Product Processing',1), ('CPU','Customized Packing Unit',1), ('PACKPRO','Packpro',1),
 ('PCU','Paper Cup Unit',1), ('PCLU','Paper Cup Lid Unit',1), ('DPU','Digital Printing Unit',1),
 ('PPU','Paper Plate Unit',1), ('CWU','Cake Wrapper Unit',1);
```


```sql
INSERT INTO processes(division_code, code, label, counts_in_production) VALUES
 ('SHPS','print','Print',1), ('SHPS','curing','Curing',1), ('SHPS','packing','Packing',1),
 ('RWU','rewinding','Rewinding',1), ('RWU','cutting','Cutting',1), ('RWU','packing','Packing',1), ('RWU','personal','Personal / break',0),
 ('PSU','forming','Forming',1), ('PSU','cutting','Cutting',1), ('PSU','packing','Packing',1);
-- OPD-style process list for OPD, MOBA, MOBA_P, FPP, CPU, PACKPRO, PCU, PCLU, DPU, PPU, CWU:
INSERT INTO processes(division_code, code, label)
  SELECT d.code, p.code, p.label FROM divisions d,
    (SELECT 'print' code, 'Print' label UNION ALL SELECT 'die_cut','Die cut' UNION ALL SELECT 'pasting','Pasting' UNION ALL SELECT 'packing','Packing') p
  WHERE d.code NOT IN ('SHPS','RWU','PSU');

UPDATE divisions SET counting_process = CASE code WHEN 'SHPS' THEN 'print' WHEN 'RWU' THEN 'rewinding' ELSE 'packing' END;
UPDATE divisions SET quantity_form_id = 'rwu_internal_job_card' WHERE code = 'RWU';

INSERT INTO stage_catalog(id, name, detected, detector_key) VALUES
 (1,'Artwork image',0,NULL), (2,'Item photo (in system)',0,NULL), (3,'Job card',0,NULL),
 (4,'Sales order',1,'so'), (5,'Bundle',1,'bundle'), (6,'Pick list',1,'picklist'), (7,'Package',1,'package'),
 (8,'Shipment',1,'shipment'), (9,'Inventory adjustment',0,NULL), (10,'Sales invoice to SH',1,'invoice'),
 (11,'Purchase bill from SPS',0,NULL);
```

(Names from J§1.2. Stages 9 and 11 are Zoho or cross-org documents in J§1.2 but are **manual ticks** in this build, per spec §6.3 `manual_stage_events`.)

```sql
-- Stage orders (§6.5)
INSERT INTO division_stages(division_code, stage_id, sort_order)
  SELECT 'SHPS', value, key + 1 FROM json_each('[1,2,3,4,5,6,7,8,9,10,11]');
INSERT INTO division_stages(division_code, stage_id, sort_order)
  SELECT 'PSU', value, key + 1 FROM json_each('[1,2,3,4,5,7,8,9,10,11]');
INSERT INTO division_stages(division_code, stage_id, sort_order)
  SELECT 'RWU', value, key + 1 FROM json_each('[2,3,4,5,7,8,9,10,11]');
INSERT INTO division_stages(division_code, stage_id, sort_order)
  SELECT d.code, j.value, j.key + 1 FROM divisions d, json_each('[1,2,3,4,6,5,7,8,9,10,11]') j
  WHERE d.code NOT IN ('SHPS','PSU','RWU');

INSERT INTO division_aliases(zoho_value, zoho_key, division_code) VALUES
 ('Offset Printing Division (OPD)','offset printing division (opd)','OPD'),
 ('Screen Printing Division (SHPS)','screen printing division (shps)','SHPS'),
 ('Paper Straw Unit (PSU)','paper straw unit (psu)','PSU'),
 ('Rewinding Unit (RWU)','rewinding unit (rwu)','RWU'),
 ('Paper Cup Unit (PCU)','paper cup unit (pcu)','PCU'),
 ('Customized Packing Unit (CPU)','customized packing unit (cpu)','CPU'),
 ('MOBA Punching Unit','moba punching unit','MOBA'),
 ('Paper Cup Lid Unit','paper cup lid unit','PCLU'),
 ('Food Product Processing (FPP)','food product processing (fpp)','FPP'),
 ('Digital Printing Unit (DPU)','digital printing unit (dpu)','DPU'),
 ('Paper Plate Unit','paper plate unit','PPU'),
 ('Cake Wrapper Unit','cake wrapper unit','CWU');

INSERT INTO order_type_aliases(zoho_value, zoho_key, order_type, provisional) VALUES
 ('Customized Order','customized order','customised',0), ('Ex Stock','ex stock','ex_stock',0),
 ('Internal SH Order','internal sh order','internal',0), ('Make to Order (MTO)','make to order (mto)','customised',1);

INSERT INTO reject_reasons(code, label) VALUES
 ('not_feasible','Not feasible'), ('duplicate','Duplicate order'), ('missing_info','Missing information'),
 ('needs_approval','Needs approval / price'), ('other','Other');

INSERT INTO settings(key, value) VALUES ('working_weekdays','[1,2,3,4,5]');
```

```sql
-- Reason codes: the fixed list in brief B§9. Default owners are provisional (admin-editable).
INSERT INTO reason_codes(code, label, default_owner_label) VALUES
 ('raw_material','Raw material not available','Stores'),
 ('dye_cutter','Dye cutter not available','Coordinator'),
 ('artwork','Artwork not available','Coordinator'),
 ('waiting_sh_so','Waiting on SH sales order','SH sales'),
 ('machine_down','Machine down','Maintenance'),
 ('staff_absent','Staff absent','Manager'),
 ('rework','Rework','Manager'),
 ('customer_hold','Customer hold','SH sales'),
 ('other','Other','Manager');
```

- [ ] **Step 4: Run — expect PASS.** Fix the division count assertion to 14 if not done.
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: seed migration 002"`

---
### Task 5: Form definition loader (hash-versioned)

**Files:**
- Create: `server/services/forms.js`, `config/forms/.gitkeep`, `test/forms.test.js`

**Interfaces:**
- Produces: `loadForms(db, dir, now: Date) → { inserted: string[] }` — for each `*.json` (`{id, division_code, title, schema, output_map}`), SHA-256 of the file bytes; if it differs from the `content_hash` of the highest version of that id, insert `version = max + 1`. Never updates or deletes. `formExists(db, id) → boolean` (used by the admin divisions route for `quantity_form_id`).

- [ ] **Step 1: Failing test** — `test/forms.test.js` (AC0.17 second half)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { makeDb } from './helpers/db.js';
import { loadForms, formExists } from '../server/services/forms.js';

test('changed form JSON creates a new version; old stays', () => {
  const { db, close } = makeDb();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'forms-'));
  const f = path.join(dir, 'inline_inspection_run.json');
  const def = { id: 'inline_inspection_run', division_code: null, title: 'Inline inspection', schema: { fields: [] }, output_map: { lines: [] } };
  fs.writeFileSync(f, JSON.stringify(def));
  const now = new Date('2026-09-17T00:00:00Z');
  assert.deepEqual(loadForms(db, dir, now).inserted, ['inline_inspection_run@1']);
  assert.deepEqual(loadForms(db, dir, now).inserted, []);
  fs.writeFileSync(f, JSON.stringify({ ...def, title: 'Inline inspection run' }));
  assert.deepEqual(loadForms(db, dir, now).inserted, ['inline_inspection_run@2']);
  assert.equal(db.prepare('SELECT count(*) c FROM form_definitions').get().c, 2);
  assert.equal(formExists(db, 'inline_inspection_run'), true);
  assert.equal(formExists(db, 'nope'), false);
  close();
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement** — `server/services/forms.js`

```js
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export function loadForms(db, dir, now) {
  const inserted = [];
  if (!fs.existsSync(dir)) return { inserted };
  const latest = db.prepare('SELECT version, content_hash FROM form_definitions WHERE id = ? ORDER BY version DESC LIMIT 1');
  const insert = db.prepare(`INSERT INTO form_definitions(id, version, division_code, title, schema_json, output_map_json, content_hash, created_at)
    VALUES (@id, @version, @division_code, @title, @schema_json, @output_map_json, @content_hash, @created_at)`);
  for (const file of fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()) {
    const bytes = fs.readFileSync(path.join(dir, file));
    const hash = crypto.createHash('sha256').update(bytes).digest('hex');
    const def = JSON.parse(bytes.toString('utf8'));
    if (!def.id || !def.title || !def.schema || !def.output_map) throw new Error(`${file}: id, title, schema and output_map are required`);
    const cur = latest.get(def.id);
    if (cur?.content_hash === hash) continue;
    const version = (cur?.version ?? 0) + 1;
    insert.run({ id: def.id, version, division_code: def.division_code ?? null, title: def.title,
      schema_json: JSON.stringify(def.schema), output_map_json: JSON.stringify(def.output_map),
      content_hash: hash, created_at: now.toISOString() });
    inserted.push(`${def.id}@${version}`);
  }
  return { inserted };
}

export const formExists = (db, id) => Boolean(db.prepare('SELECT 1 FROM form_definitions WHERE id = ?').get(id));
```

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** — `git commit -am "feat: hash-versioned form loader"` (add new files first with `git add -A`).

---

### Task 6: Auth primitives and the create-admin CLI

**Files:**
- Create: `server/auth/password.js`, `server/auth/sessions.js`, `server/auth/rate-limit.js`, `server/services/audit.js`, `cli/create-admin.js`, `test/auth-primitives.test.js`

**Interfaces:**
- Produces:
  - `hashPassword(plain) → Promise<string>` (format `scrypt$32768$8$1$<salt b64>$<hash b64>`; throws `PasswordTooShort` when `< 10` chars); `verifyPassword(plain, stored) → Promise<boolean>` (timing-safe)
  - `createSession(db, userId, { now, ip, userAgent }) → { token, idHash }` (token = 32 random bytes base64url; stores SHA-256 hex; expires_at = now + 7 d)
  - `loadSession(db, token, now) → { user, idHash } | null` (null if unknown, expired, idle > 12 h, or user inactive; on success updates `last_seen_at`)
  - `deleteSession(db, idHash)`; `revokeUserSessions(db, userId) → number`
  - `makeLimiter({ max, windowMs }) → { fail(key, now), blocked(key, now) → boolean, reset(key) }` (in memory; single process)
  - `audit(db, { actor, action, entity, entityId, detail, now })`
  - `SESSION_IDLE_MS = 12 * 3600e3`, `SESSION_MAX_MS = 7 * 86400e3`

- [ ] **Step 1: Failing test** — `test/auth-primitives.test.js`

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeDb } from './helpers/db.js';
import { hashPassword, verifyPassword } from '../server/auth/password.js';
import { createSession, loadSession, revokeUserSessions } from '../server/auth/sessions.js';
import { makeLimiter } from '../server/auth/rate-limit.js';

test('password hashing', async () => {
  const h = await hashPassword('correct horse 1');
  assert.match(h, /^scrypt\$32768\$8\$1\$/);
  assert.equal(await verifyPassword('correct horse 1', h), true);
  assert.equal(await verifyPassword('wrong horse 12', h), false);
  await assert.rejects(hashPassword('short'), /at least 10/);
});

test('sessions: stored hashed, idle and absolute expiry, revoke', () => {
  const { db, close } = makeDb();
  db.prepare("INSERT INTO users(username, display_name, password_hash, roles, created_at) VALUES ('a','A','x','[\"admin\"]','x')").run();
  const t0 = new Date('2026-09-17T00:00:00Z');
  const { token, idHash } = createSession(db, 1, { now: t0 });
  assert.notEqual(token, idHash);
  assert.equal(db.prepare('SELECT count(*) c FROM sessions WHERE id_hash = ?').get(token).c, 0);
  const lastSeen = () => db.prepare('SELECT last_seen_at FROM sessions').get()?.last_seen_at;
  assert.equal(loadSession(db, token, new Date(t0.getTime() + 60e3)).user.username, 'a');
  assert.equal(lastSeen(), t0.toISOString(), 'no write within 5 minutes');
  assert.equal(loadSession(db, token, new Date(t0.getTime() + 11 * 3600e3)).user.username, 'a');
  assert.equal(loadSession(db, token, new Date(t0.getTime() + 11 * 3600e3 + 13 * 3600e3)), null, 'idle > 12 h');
  const s2 = createSession(db, 1, { now: t0 });
  let t = t0.getTime();
  for (let i = 0; i < 16; i++) { t += 11 * 3600e3; if (t < t0.getTime() + 7 * 86400e3) assert.ok(loadSession(db, s2.token, new Date(t))); }
  assert.equal(loadSession(db, s2.token, new Date(t0.getTime() + 7 * 86400e3 + 1)), null, 'absolute 7 d');
  const s3 = createSession(db, 1, { now: t0 });
  assert.equal(revokeUserSessions(db, 1) >= 1, true);
  assert.equal(loadSession(db, s3.token, t0), null);
  db.prepare('UPDATE users SET active = 0').run();
  const s4 = createSession(db, 1, { now: t0 });
  assert.equal(loadSession(db, s4.token, t0), null, 'inactive user');
  close();
});

test('limiter', () => {
  const l = makeLimiter({ max: 2, windowMs: 1000 });
  const now = new Date(0);
  l.fail('k', now); assert.equal(l.blocked('k', now), false);
  l.fail('k', now); assert.equal(l.blocked('k', now), true);
  assert.equal(l.blocked('k', new Date(1001)), false);
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement**

`server/auth/password.js`:
```js
import crypto from 'node:crypto';
import { promisify } from 'node:util';

const scrypt = promisify(crypto.scrypt);
const N = 32768, r = 8, p = 1, KEYLEN = 64, MAXMEM = 64 * 1024 * 1024;

export async function hashPassword(plain) {
  if (typeof plain !== 'string' || plain.length < 10) throw new Error('Password must be at least 10 characters');
  const salt = crypto.randomBytes(16);
  const hash = await scrypt(plain, salt, KEYLEN, { N, r, p, maxmem: MAXMEM });
  return `scrypt$${N}$${r}$${p}$${salt.toString('base64')}$${hash.toString('base64')}`;
}

export async function verifyPassword(plain, stored) {
  const [alg, n, rr, pp, saltB64, hashB64] = String(stored).split('$');
  if (alg !== 'scrypt' || !hashB64) return false;
  const expected = Buffer.from(hashB64, 'base64');
  const got = await scrypt(String(plain), Buffer.from(saltB64, 'base64'), expected.length,
    { N: Number(n), r: Number(rr), p: Number(pp), maxmem: MAXMEM });
  return crypto.timingSafeEqual(expected, got);
}
```

`server/auth/sessions.js`:
```js
import crypto from 'node:crypto';

export const SESSION_IDLE_MS = 12 * 3600e3;
export const SESSION_MAX_MS = 7 * 86400e3;
const sha = (t) => crypto.createHash('sha256').update(t).digest('hex');

export function createSession(db, userId, { now, ip = null, userAgent = null }) {
  const token = crypto.randomBytes(32).toString('base64url');
  const idHash = sha(token);
  db.prepare(`INSERT INTO sessions(id_hash, user_id, created_at, last_seen_at, expires_at, ip, user_agent)
    VALUES (?, ?, ?, ?, ?, ?, ?)`).run(idHash, userId, now.toISOString(), now.toISOString(),
    new Date(now.getTime() + SESSION_MAX_MS).toISOString(), ip, userAgent?.slice(0, 200) ?? null);
  return { token, idHash };
}

export function loadSession(db, token, now) {
  if (!token) return null;
  const idHash = sha(token);
  const row = db.prepare(`SELECT s.id_hash, s.last_seen_at, s.expires_at, u.* FROM sessions s
    JOIN users u ON u.id = s.user_id WHERE s.id_hash = ?`).get(idHash);
  if (!row) return null;
  const t = now.getTime();
  if (!row.active || t > Date.parse(row.expires_at) || t - Date.parse(row.last_seen_at) > SESSION_IDLE_MS) {
    db.prepare('DELETE FROM sessions WHERE id_hash = ?').run(idHash);
    return null;
  }
  // Keep ordinary reads read-only: refresh last_seen_at at most every 5 minutes (imports hold the write lock).
  if (t - Date.parse(row.last_seen_at) > 5 * 60e3) {
    db.prepare('UPDATE sessions SET last_seen_at = ? WHERE id_hash = ?').run(now.toISOString(), idHash);
  }
  const { id_hash, last_seen_at, expires_at, password_hash, ...user } = row;
  return { idHash, user: { ...user, roles: JSON.parse(user.roles) } };
}

export const deleteSession = (db, idHash) => db.prepare('DELETE FROM sessions WHERE id_hash = ?').run(idHash);
export const revokeUserSessions = (db, userId) => db.prepare('DELETE FROM sessions WHERE user_id = ?').run(userId).changes;
```

`server/auth/rate-limit.js`:
```js
export function makeLimiter({ max, windowMs }) {
  const hits = new Map();
  const recent = (key, now) => (hits.get(key) ?? []).filter((t) => now.getTime() - t < windowMs);
  return {
    fail(key, now) { const r = recent(key, now); r.push(now.getTime()); hits.set(key, r); },
    undo(key) { const r = hits.get(key); if (r?.length) r.pop(); },
    blocked(key, now) { const r = recent(key, now); hits.set(key, r); return r.length >= max; },
    reset(key) { hits.delete(key); },
  };
}
```

`server/services/audit.js`:
```js
export function audit(db, { actor, action, entity, entityId = null, detail = {}, now }) {
  db.prepare('INSERT INTO audit_log(at, actor, action, entity, entity_id, detail_json) VALUES (?, ?, ?, ?, ?, ?)')
    .run(now.toISOString(), String(actor), action, entity, entityId === null ? null : String(entityId), JSON.stringify(detail));
}
```

`cli/create-admin.js` — prompts for username, display name and password twice (hidden input via `readline` with muted output), refuses if the username exists, inserts with roles `["admin"]` and `must_reset = 0`, writes an audit row with actor `cli`. Opens the DB with `openDb(loadConfig().dbPath)` and runs migrations first (so it works on a fresh live DB).

```js
import readline from 'node:readline';
import 'dotenv/config';
import { loadConfig } from '../server/config.js';
import { openDb } from '../server/db/open.js';
import { runMigrations } from '../server/db/migrate.js';
import { hashPassword } from '../server/auth/password.js';
import { audit } from '../server/services/audit.js';

function ask(q, hidden = false) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
    if (hidden) rl._writeToOutput = (s) => { if (s.includes(q)) process.stdout.write(s); };
    rl.question(q, (a) => { rl.close(); if (hidden) process.stdout.write('\n'); resolve(a.trim()); });
  });
}

const config = loadConfig();
const db = openDb(config.dbPath);
runMigrations(db, config.migrationsDir);
const username = await ask('Username: ');
if (db.prepare('SELECT 1 FROM users WHERE username = ?').get(username)) { console.error('That username exists.'); process.exit(1); }
const display = await ask('Display name: ');
const p1 = await ask('Password (min 10): ', true);
const p2 = await ask('Again: ', true);
if (p1 !== p2) { console.error('Passwords differ.'); process.exit(1); }
const hash = await hashPassword(p1);
const now = new Date();
const id = db.prepare(`INSERT INTO users(username, display_name, password_hash, roles, created_at)
  VALUES (?, ?, ?, '["admin"]', ?)`).run(username, display, hash, now.toISOString()).lastInsertRowid;
audit(db, { actor: 'cli', action: 'user.create_admin', entity: 'user', entityId: id, now });
console.log(`Admin ${username} created.`);
db.close();
```

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: password hashing, sessions, limiter, create-admin"`

---

### Task 7: App factory, listeners, proxy trust, headers, health, login

**Files:**
- Create: `server/startup.js`, `server/create-app.js`, `server/listen.js`, `server/auth/middleware.js`, `server/routes/auth.js`, `server/routes/health.js`, `server/services/employee-master.js`, `server/services/sse.js`, `server/app.js`, `test/helpers/app.js`, `test/app-security.test.js`, `test/listen.test.js`

**Interfaces:**
- Consumes: Task 3 `openDb`, `runMigrations`; Task 5 `loadForms`; Task 6 auth primitives; Task 12 `ensureFactsVersion` (call site added in Task 12); Task 14 `startSweepTimer` (call site added in Task 14).
- Produces:
  - `prepareDatabase(db, config, logger) → void` (in `server/startup.js`): `runMigrations` → `loadForms` → `ensureFactsVersion` (the last call is added in Task 12). `server/app.js` and the AC0.2 test both use it.
  - `createApp({ db, config, clock = { now: () => new Date() }, sse = createSseHub() }) → express app` with `app.locals.{db, config, clock, sse, stats}`; `stats.untrustedForwarded` counter.
  - `startListeners({ app, port, hosts: string[], listen = defaultListen, retryMs = 5000, logger }) → { servers, stop() }` — refuses any host in `['', '0.0.0.0', '::', undefined]`; retries a host that fails with `EADDRNOTAVAIL` every `retryMs`.
  - middleware `requireOrigin(config)`, `loadUser` (sets `req.user` from cookie `pd_sid`), `requireAuth` (401), `requireRole(...roles)` (403), `setSessionCookie(res, token)`, `clearSessionCookie(res)`
  - `createSseHub() → { add(res, { userId, kind }), closeUser(userId), closeAll(), size() }`
  - `employeeMaster.status(config) → 'not_configured' | 'ok' | 'down'` (Release 0: `'not_configured'` when URL or token empty, otherwise `'ok'`; Release 5 adds the real probe)
  - Routes: `POST /api/auth/login {username, password}`, `POST /api/auth/logout`, `GET /api/me`, `POST /api/auth/password {current, next}` (clears `must_reset`), `GET /api/health`.
  - Test helper `makeApp({ now?, env? }) → { app, db, clock, agent(), login(username, password?) → supertest agent, origin, close() }` — `clock.set(date)` to move time; creates user `admin1` (roles admin) with password `admin-password-1`.

- [ ] **Step 1: Failing tests** — `test/app-security.test.js` (AC0.4, 0.5, 0.6, 0.12, 0.13 headers, 0.22)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import { makeApp } from './helpers/app.js';

test('login sets a secure cookie; wrong password 401 (AC0.4)', async () => {
  const t = makeApp();
  const res = await request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: 'admin1', password: 'admin-password-1' });
  assert.equal(res.status, 200);
  const cookie = res.headers['set-cookie'][0];
  assert.match(cookie, /^pd_sid=/);
  for (const flag of ['HttpOnly', 'Secure', 'SameSite=Strict', 'Path=/']) assert.match(cookie, new RegExp(flag));
  assert.equal((await request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: 'admin1', password: 'nope-nope-nope' })).status, 401);
  t.close();
});

test('11th failure for a username → 429; 101st from one IP → 429 (AC0.4)', async () => {
  const t = makeApp();
  for (let i = 0; i < 10; i++) await request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: 'admin1', password: 'bad-password-x' });
  assert.equal((await request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: 'admin1', password: 'admin-password-1' })).status, 429);
  for (let i = 0; i < 90; i++) await request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: `ghost${i}`, password: 'bad-password-x' });
  assert.equal((await request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: 'ghost-new', password: 'bad-password-x' })).status, 429);
  t.clock.set(new Date(t.clock.now().getTime() + 16 * 60e3));
  assert.equal((await request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: 'admin1', password: 'admin-password-1' })).status, 200);
  t.close();
});

test('parallel wrong guesses are capped at 10 per username (AC0.4)', async () => {
  const t = makeApp();
  const results = await Promise.all(Array.from({ length: 15 }, () =>
    request(t.app).post('/api/auth/login').set('Origin', t.origin).send({ username: 'admin1', password: 'bad-password-x' })));
  const codes = results.map((r) => r.status);
  assert.equal(codes.filter((c) => c === 401).length, 10);
  assert.equal(codes.filter((c) => c === 429).length, 5);
  t.close();
});

test('foreign or missing Origin → 403 (AC0.5)', async () => {
  const t = makeApp();
  assert.equal((await request(t.app).post('/api/auth/login').set('Origin', 'https://evil.example').send({})).status, 403);
  assert.equal((await request(t.app).post('/api/auth/login').send({})).status, 403);
  t.close();
});

test('unauthenticated walk → 401 except public routes (AC0.6)', async () => {
  const t = makeApp();
  for (const [m, p] of [['get', '/api/me'], ['get', '/api/admin/users'], ['post', '/api/admin/users'], ['get', '/api/admin/imports'],
    ['get', '/api/events'], ['get', '/api/jobs'], ['get', '/api/anything/else'], ['get', '/files/1'], ['post', '/api/auth/logout']]) {
    const r = await request(t.app)[m](p).set('Origin', t.origin);
    assert.equal(r.status, 401, `${m} ${p}`);
  }
  assert.equal((await request(t.app).get('/api/health')).status, 200);
  const shell = await request(t.app).get('/admin/users');
  assert.ok([200, 404].includes(shell.status)); // 200 once web/dist exists (Task 17)
  t.close();
});

test('health: always 200, no secrets (AC0.12)', async () => {
  const t = makeApp({ env: { EMPLOYEE_MASTER_URL: '', EMPLOYEE_MASTER_TOKEN: '' } });
  const r = await request(t.app).get('/api/health');
  assert.equal(r.status, 200);
  assert.deepEqual(Object.keys(r.body).sort(), ['db', 'employeeMaster', 'lastImport', 'lastSync', 'ok']);
  assert.equal(r.body.employeeMaster, 'not_configured');
  const t2 = makeApp({ env: { EMPLOYEE_MASTER_URL: 'http://127.0.0.1:1', EMPLOYEE_MASTER_TOKEN: 'secret-token-value' } });
  const r2 = await request(t2.app).get('/api/health');
  assert.equal(r2.status, 200);
  assert.doesNotMatch(JSON.stringify(r2.body), /secret-token-value/);
  t.close(); t2.close();
});

test('security headers (AC0.13)', async () => {
  const t = makeApp();
  const r = await request(t.app).get('/api/health');
  assert.match(r.headers['content-security-policy'], /default-src 'self'/);
  assert.match(r.headers['content-security-policy'], /frame-ancestors 'none'/);
  assert.equal(r.headers['x-content-type-options'], 'nosniff');
  assert.equal(r.headers['referrer-policy'], 'same-origin');
  assert.match(r.headers['strict-transport-security'], /max-age=/);
  assert.equal(r.headers['x-powered-by'], undefined);
  t.close();
});

test('proxy trust: only TRUSTED_PROXY_IPS (AC0.13, AC0.22)', async () => {
  const trusted = makeApp({ env: { TRUSTED_PROXY_IPS: '127.0.0.1' } });
  const a = await trusted.login('admin1');
  const me = await a.get('/api/me').set('X-Forwarded-For', '203.0.113.9');
  assert.equal(me.body.ip, '203.0.113.9');
  const untrusted = makeApp({ env: { TRUSTED_PROXY_IPS: '172.18.0.3' } });
  const b = await untrusted.login('admin1');
  const me2 = await b.get('/api/me').set('X-Forwarded-For', '203.0.113.9');
  assert.notEqual(me2.body.ip, '203.0.113.9');
  assert.equal(untrusted.app.locals.stats.untrustedForwarded >= 1, true);
  trusted.close(); untrusted.close();
});

test('password change clears must_reset; logout ends the session', async () => {
  const t = makeApp();
  t.db.prepare('UPDATE users SET must_reset = 1').run();
  const a = await t.login('admin1');
  assert.equal((await a.get('/api/me')).body.user.must_reset, 1);
  assert.equal((await a.get('/api/admin/users')).status, 403, 'nothing else until the password is changed');
  assert.equal((await a.post('/api/auth/password').set('Origin', t.origin).send({ current: 'admin-password-1', next: 'new-password-22' })).status, 200);
  assert.equal((await a.get('/api/me')).body.user.must_reset, 0);
  await a.post('/api/auth/logout').set('Origin', t.origin);
  assert.equal((await a.get('/api/me')).status, 401);
  t.close();
});
```

`/api/me` returns `{ user: {id, username, display_name, roles, team_id, must_reset, can_create_files, can_receive_files}, ip: req.ip }`. (`ip` is included only so the proxy check can be observed; it is the caller's own address.)

`test/listen.test.js` (AC0.13 bind rule):
```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { startListeners } from '../server/listen.js';

const quiet = { info() {}, warn() {}, error() {} };

test('never binds a wildcard; retries the bridge', async () => {
  const calls = [];
  let bridgeFails = 1;
  const listen = (app, port, host) => new Promise((resolve, reject) => {
    calls.push(host);
    if (host === '172.17.0.1' && bridgeFails-- > 0) return reject(Object.assign(new Error('x'), { code: 'EADDRNOTAVAIL' }));
    resolve({ close: (cb) => cb?.() });
  });
  const h = await startListeners({ app: {}, port: 4300, hosts: ['127.0.0.1', '172.17.0.1'], listen, retryMs: 10, logger: quiet });
  await new Promise((r) => setTimeout(r, 50));
  assert.deepEqual(calls, ['127.0.0.1', '172.17.0.1', '172.17.0.1']);
  h.stop();
  await assert.rejects(startListeners({ app: {}, port: 1, hosts: ['0.0.0.0'], listen, logger: quiet }), /wildcard/);
  await assert.rejects(startListeners({ app: {}, port: 1, hosts: ['::'], listen, logger: quiet }), /wildcard/);
});
```

- [ ] **Step 2: Run — expect FAIL.**

- [ ] **Step 3: Implement**

`server/listen.js`:
```js
import http from 'node:http';

const WILDCARD = new Set(['', '0.0.0.0', '::', undefined, null]);
export const defaultListen = (app, port, host) => new Promise((resolve, reject) => {
  const server = http.createServer(app);
  server.once('error', reject);
  server.listen(port, host, () => { server.off('error', reject); resolve(server); });
});

export async function startListeners({ app, port, hosts, listen = defaultListen, retryMs = 5000, logger }) {
  if (hosts.some((h) => WILDCARD.has(h))) throw new Error('Refusing to bind a wildcard address');
  const servers = []; const timers = [];
  const attempt = async (host, first) => {
    try {
      servers.push(await listen(app, port, host));
      logger.info('listening', { host, port });
    } catch (err) {
      if (err.code !== 'EADDRNOTAVAIL' || host === '127.0.0.1') throw err;
      if (first) logger.warn('bridge address not available yet; retrying', { host, retryMs });
      timers.push(setTimeout(() => attempt(host, false).catch((e) => logger.error('listen failed', { host, error: e.message })), retryMs));
    }
  };
  for (const h of hosts) await attempt(h, true);
  return { servers, stop: () => { timers.forEach(clearTimeout); servers.forEach((s) => s.close()); } };
}
```

`server/services/sse.js`:
```js
export function createSseHub() {
  const conns = new Set();
  return {
    add(res, meta) {
      const c = { res, ...meta };
      conns.add(c);
      res.on('close', () => conns.delete(c));
      return c;
    },
    send(filter, event) {
      for (const c of conns) if (filter(c)) c.res.write(`data: ${JSON.stringify(event)}\n\n`);
    },
    closeUser(userId) { for (const c of conns) if (c.userId === userId) { c.res.end(); conns.delete(c); } },
    closeAll() { for (const c of conns) c.res.end(); conns.clear(); },
    size: () => conns.size,
  };
}
```

`server/auth/middleware.js`:
```js
import { loadSession } from './sessions.js';

const COOKIE = 'pd_sid';
export const setSessionCookie = (res, token) =>
  res.cookie(COOKIE, token, { httpOnly: true, secure: true, sameSite: 'strict', path: '/' });
export const clearSessionCookie = (res) =>
  res.clearCookie(COOKIE, { httpOnly: true, secure: true, sameSite: 'strict', path: '/' });

const readCookie = (req) => {
  const raw = req.headers.cookie ?? '';
  for (const part of raw.split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k === COOKIE) return decodeURIComponent(v.join('='));
  }
  return null;
};

export const requireOrigin = (config) => (req, res, next) => {
  if (req.method === 'GET' || req.method === 'HEAD') return next();
  if (req.headers.origin !== config.appOrigin) return res.status(403).json({ error: 'origin', requestId: req.id });
  next();
};

export const loadUser = (req, res, next) => {
  const { db, clock } = req.app.locals;
  const s = loadSession(db, readCookie(req), clock.now());
  if (s) { req.user = s.user; req.sessionHash = s.idHash; }
  next();
};

const RESET_ALLOWED = new Set(['/api/me', '/api/auth/password', '/api/auth/logout']);
export const requireAuth = (req, res, next) => {
  if (!req.user) return res.status(401).json({ error: 'auth', requestId: req.id });
  if (req.user.must_reset && !RESET_ALLOWED.has(req.originalUrl.split('?')[0])) {
    return res.status(403).json({ error: 'must_reset', requestId: req.id });
  }
  next();
};

export const requireRole = (...roles) => (req, res, next) =>
  req.user?.roles.some((r) => roles.includes(r)) ? next() : res.status(403).json({ error: 'forbidden', requestId: req.id });
```

`server/routes/auth.js`:
```js
import { Router } from 'express';
import { z } from 'zod';
import { verifyPassword, hashPassword } from '../auth/password.js';
import { createSession, deleteSession, revokeUserSessions } from '../auth/sessions.js';
import { makeLimiter } from '../auth/rate-limit.js';
import { setSessionCookie, clearSessionCookie, requireAuth } from '../auth/middleware.js';
import { audit } from '../services/audit.js';

const Login = z.object({ username: z.string().min(1).max(64), password: z.string().min(1).max(200) });
const Change = z.object({ current: z.string().min(1).max(200), next: z.string().min(10).max(200) });
const DUMMY = 'scrypt$32768$8$1$AAAAAAAAAAAAAAAAAAAAAA==$' + 'A'.repeat(88);

export function authRoutes() {
  const r = Router();
  const byUser = makeLimiter({ max: 10, windowMs: 15 * 60e3 });
  const byIp = makeLimiter({ max: 100, windowMs: 15 * 60e3 });

  r.post('/auth/login', async (req, res) => {
    const { db, clock } = req.app.locals;
    const now = clock.now();
    const parsed = Login.safeParse(req.body);
    if (!parsed.success) return res.status(400).json({ error: 'invalid', fields: parsed.error.flatten().fieldErrors });
    const key = parsed.data.username.toLowerCase();
    if (byUser.blocked(key, now) || byIp.blocked(req.ip, now)) return res.status(429).json({ error: 'too_many_attempts' });
    // Count the attempt before the slow scrypt check, so parallel guesses cannot all slip past the limit.
    byUser.fail(key, now); byIp.fail(req.ip, now);
    const user = db.prepare('SELECT * FROM users WHERE username = ?').get(parsed.data.username);
    const ok = await verifyPassword(parsed.data.password, user?.password_hash ?? DUMMY);
    if (!user || !ok || !user.active) return res.status(401).json({ error: 'bad_credentials' });
    byUser.reset(key); byIp.undo(req.ip);
    const { token } = createSession(db, user.id, { now, ip: req.ip, userAgent: req.headers['user-agent'] });
    audit(db, { actor: user.id, action: 'auth.login', entity: 'user', entityId: user.id, now });
    setSessionCookie(res, token);
    res.json({ ok: true, must_reset: Boolean(user.must_reset) });
  });

  r.use(requireAuth);

  r.post('/auth/logout', (req, res) => {
    deleteSession(req.app.locals.db, req.sessionHash);
    req.app.locals.sse.closeUser(req.user.id);
    clearSessionCookie(res);
    res.json({ ok: true });
  });

  r.get('/me', (req, res) => {
    const { id, username, display_name, roles, team_id, must_reset, can_create_files, can_receive_files } = req.user;
    res.json({ user: { id, username, display_name, roles, team_id, must_reset, can_create_files, can_receive_files }, ip: req.ip });
  });

  r.post('/auth/password', async (req, res) => {
    const { db, clock } = req.app.locals;
    const parsed = Change.safeParse(req.body);
    if (!parsed.success) return res.status(400).json({ error: 'invalid', fields: parsed.error.flatten().fieldErrors });
    const row = db.prepare('SELECT password_hash FROM users WHERE id = ?').get(req.user.id);
    if (!(await verifyPassword(parsed.data.current, row.password_hash))) return res.status(401).json({ error: 'bad_credentials' });
    const hash = await hashPassword(parsed.data.next);
    const now = clock.now();
    db.transaction(() => {
      db.prepare('UPDATE users SET password_hash = ?, must_reset = 0 WHERE id = ?').run(hash, req.user.id);
      revokeUserSessions(db, req.user.id);
      audit(db, { actor: req.user.id, action: 'auth.password_change', entity: 'user', entityId: req.user.id, now });
    })();
    const { token } = createSession(db, req.user.id, { now, ip: req.ip, userAgent: req.headers['user-agent'] });
    setSessionCookie(res, token);
    res.json({ ok: true });
  });
  return r;
}
```

`server/services/employee-master.js`:
```js
export const employeeMasterStatus = (config) =>
  config.employeeMasterUrl && config.employeeMasterToken ? 'ok' : 'not_configured';
```

`server/routes/health.js`:
```js
import { Router } from 'express';
import { employeeMasterStatus } from '../services/employee-master.js';

export function healthRoutes() {
  const r = Router();
  r.get('/health', (req, res) => {
    const { db, config } = req.app.locals;
    let dbOk = false, lastImport = null, lastSync = null;
    try {
      db.prepare('SELECT 1').get();
      dbOk = true;
      lastImport = db.prepare("SELECT max(finished_at) t FROM zoho_import_runs WHERE source <> 'sync' AND status IN ('ok','warning')").get().t;
      lastSync = db.prepare("SELECT max(finished_at) t FROM zoho_import_runs WHERE source = 'sync' AND status IN ('ok','warning')").get().t;
    } catch { dbOk = false; }
    res.status(200).json({ ok: true, db: dbOk ? 'ok' : 'down', employeeMaster: employeeMasterStatus(config), lastImport, lastSync });
  });
  return r;
}
```

`server/create-app.js`:
```js
import express from 'express';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { requireOrigin, loadUser, requireAuth } from './auth/middleware.js';
import { authRoutes } from './routes/auth.js';
import { healthRoutes } from './routes/health.js';
import { createSseHub } from './services/sse.js';
import { log } from './log.js';

const norm = (a) => String(a ?? '').replace(/^::ffff:/, '');

export function createApp({ db, config, clock = { now: () => new Date() }, sse = createSseHub(), extraRoutes = [] }) {
  const app = express();
  const trusted = new Set(config.trustedProxyIps);
  app.disable('x-powered-by');
  app.set('trust proxy', (addr) => trusted.has(norm(addr)));
  Object.assign(app.locals, { db, config, clock, sse, stats: { untrustedForwarded: 0 } });

  app.use((req, res, next) => {
    req.id = crypto.randomUUID();
    if (req.headers['x-forwarded-for'] && !trusted.has(norm(req.socket.remoteAddress))) {
      app.locals.stats.untrustedForwarded += 1;
      log.warn('forwarded header from untrusted address', { remote: norm(req.socket.remoteAddress), requestId: req.id });
    }
    res.set({
      'Content-Security-Policy': "default-src 'self'; img-src 'self' data: blob:; frame-src 'self'; frame-ancestors 'none'",
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'same-origin',
      'Strict-Transport-Security': 'max-age=31536000',
    });
    next();
  });
  app.use(express.json({ limit: '1mb' }));
  app.use(requireOrigin(config));

  app.use('/api', healthRoutes());
  app.use(loadUser);
  app.use('/api', authRoutes());           // login is public; the router applies requireAuth after it
  app.use(['/api', '/files'], requireAuth);
  for (const [mount, router] of extraRoutes) app.use(mount, router);
  app.use(['/api', '/files'], (req, res) => res.status(404).json({ error: 'not_found', requestId: req.id }));

  if (fs.existsSync(path.join(config.webDist, 'index.html'))) {
    app.use(express.static(config.webDist, { index: false }));
    app.get(/^\/(?!api\/|files\/).*/, (req, res) => res.sendFile(path.join(config.webDist, 'index.html')));
  }

  app.use((err, req, res, _next) => {
    log.error('request failed', { requestId: req.id, error: err.message, userId: req.user?.id });
    res.status(err.status ?? 500).json({ error: 'server_error', requestId: req.id });
  });
  return app;
}
```

Later tasks add routers by passing them in `extraRoutes` from `server/app.js` **and** from `test/helpers/app.js`; keep one function `buildRoutes()` in `server/routes/index.js` (create it now, returning `[]`) that both call, so tests and production mount the same routers.

`server/routes/index.js`:
```js
export function buildRoutes() {
  return [];
}
```

`test/helpers/app.js`:
```js
import request from 'supertest';
import { makeDb } from './db.js';
import { loadConfig } from '../../server/config.js';
import { createApp } from '../../server/create-app.js';
import { buildRoutes } from '../../server/routes/index.js';
import { hashPassword } from '../../server/auth/password.js';
import { createSseHub } from '../../server/services/sse.js';

const ORIGIN = 'https://production.standard-holdings.lk';
const PASSWORDS = new Map();
const cachedHash = async (pw) => { if (!PASSWORDS.has(pw)) PASSWORDS.set(pw, await hashPassword(pw)); return PASSWORDS.get(pw); };
// scrypt is slow; precompute the admin hash once per test file
const ADMIN_HASH = await cachedHash('admin-password-1');

export function makeApp({ now = new Date('2026-09-17T03:00:00Z'), env = {} } = {}) {
  const { db, close } = makeDb();
  let t = now.getTime();
  const clock = { now: () => new Date(t), set: (d) => { t = d.getTime(); } };
  const config = loadConfig({ APP_ORIGIN: ORIGIN, BRIDGE_HOST: '', PD_MIGRATIONS_DIR: process.env.PD_MIGRATIONS_DIR, ...env });
  const sse = createSseHub();
  const app = createApp({ db, config, clock, sse, extraRoutes: buildRoutes() });
  db.prepare(`INSERT INTO users(username, display_name, password_hash, roles, created_at) VALUES ('admin1','Admin One',?, '["admin"]', ?)`)
    .run(ADMIN_HASH, now.toISOString());
  const addUser = async ({ username, roles = [], password = 'user-password-1', team_id = null }) =>
    Number(db.prepare(`INSERT INTO users(username, display_name, password_hash, roles, team_id, created_at) VALUES (?,?,?,?,?,?)`)
      .run(username, username, await cachedHash(password), JSON.stringify(roles), team_id, now.toISOString()).lastInsertRowid);
  // supertest's cookie jar will not send a Secure cookie over plain HTTP, so carry the
  // session cookie by hand and pick up any replacement the server sets.
  const login = async (username, password = username === 'admin1' ? 'admin-password-1' : 'user-password-1') => {
    const res = await request(app).post('/api/auth/login').set('Origin', ORIGIN).send({ username, password });
    if (res.status !== 200) throw new Error(`login ${username} → ${res.status}`);
    const state = { cookie: res.headers['set-cookie'][0].split(';')[0] };
    const call = (method) => (url) => {
      const req = request(app)[method](url).set('Cookie', state.cookie);
      req.on('response', (r) => { const sc = r.headers['set-cookie']; if (sc) state.cookie = sc[0].split(';')[0]; });
      return req;
    };
    return { get: call('get'), post: call('post'), put: call('put'), patch: call('patch'), delete: call('delete'), cookie: () => state.cookie };
  };
  return { app, db, clock, sse, config, origin: ORIGIN, login, addUser, close: () => { sse.closeAll(); close(); } };
}
```


`server/startup.js`:
```js
import { runMigrations } from './db/migrate.js';
import { loadForms } from './services/forms.js';

export function prepareDatabase(db, config, logger) {
  runMigrations(db, config.migrationsDir, logger);
  loadForms(db, config.formsDir, new Date());
}
```

Add to `test/migrations.test.js` (AC0.2, whole startup):
```js
import { prepareDatabase } from '../server/startup.js';
import { loadConfig } from '../server/config.js';

test('the whole startup twice changes nothing (AC0.2)', () => {
  const { db, close } = makeDb();
  const config = loadConfig({ PD_MIGRATIONS_DIR: MIGRATIONS });
  const quiet = { info() {}, warn() {}, error() {} };
  prepareDatabase(db, config, quiet);
  const snap = () => db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").all()
    .map(({ name }) => [name, db.prepare(`SELECT count(*) c FROM "${name}"`).get().c, db.pragma('user_version', { simple: true })]);
  const before = snap();
  prepareDatabase(db, config, quiet);
  assert.deepEqual(snap(), before);
  close();
});

test('the service honours PD_MIGRATIONS_DIR at startup (AC0.15)', async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pdmigenv-'));
  const migs = path.join(tmp, 'migs');
  fs.mkdirSync(migs);
  for (const f of fs.readdirSync(MIGRATIONS)) fs.copyFileSync(path.join(MIGRATIONS, f), path.join(migs, f));
  fs.writeFileSync(path.join(migs, '900-extra.sql'), 'CREATE TABLE extra_env_test (id INTEGER PRIMARY KEY);');
  const dbFile = path.join(tmp, 'svc.db');
  const child = spawn(process.execPath, ['server/app.js'], {
    env: { ...process.env, PD_MIGRATIONS_DIR: migs, DB_PATH: dbFile, PORT: '0', BRIDGE_HOST: '' }, stdio: ['ignore', 'pipe', 'pipe'],
  });
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('service did not start')), 20000);
    child.stdout.on('data', (d) => { if (String(d).includes('"msg":"listening"')) { clearTimeout(timer); resolve(); } });
    child.on('exit', (code) => reject(new Error(`service exited ${code}`)));
  });
  child.kill('SIGTERM');
  await new Promise((r) => child.on('exit', r));
  const check = openDb(dbFile);
  assert.ok(check.prepare("SELECT 1 FROM sqlite_master WHERE name='extra_env_test'").get());
  check.close();
  fs.rmSync(tmp, { recursive: true, force: true });
});
```

(These two tests also need `import { spawn } from 'node:child_process';` at the top of `test/migrations.test.js`.)

`server/app.js` (entry):
```js
import 'dotenv/config';
import { loadConfig } from './config.js';
import { openDb } from './db/open.js';
import { prepareDatabase } from './startup.js';
import { createApp } from './create-app.js';
import { buildRoutes } from './routes/index.js';
import { startListeners } from './listen.js';
import { createSseHub } from './services/sse.js';
import { employeeMasterStatus } from './services/employee-master.js';
import { log } from './log.js';

const config = loadConfig();
const db = openDb(config.dbPath);
prepareDatabase(db, config, log);
if (employeeMasterStatus(config) === 'not_configured') log.warn('Employee Master is not configured (needed only for Release 5 floor stations)');
const sse = createSseHub();
const app = createApp({ db, config, sse, extraRoutes: buildRoutes() });
const hosts = ['127.0.0.1', ...(config.bridgeHost ? [config.bridgeHost] : [])];
const listeners = await startListeners({ app, port: config.port, hosts, logger: log });
const heartbeat = setInterval(() => sse.send(() => true, { type: 'ping' }), 25_000);
const shutdown = () => { clearInterval(heartbeat); sse.closeAll(); listeners.stop(); db.close(); process.exit(0); };
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
```

- [ ] **Step 4: Run — expect PASS.** `npm test`
- [ ] **Step 5: Smoke run** — `PORT=4399 BRIDGE_HOST= DB_PATH=/tmp/pd-smoke/production.db node server/app.js &` then `curl -s http://127.0.0.1:4399/api/health` → `{"ok":true,...}`; stop it with `kill <pid>` (use the PID printed by `$!`, never `pkill`).
- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: app factory, dual listeners, proxy trust, login, health"`

---

### Task 8: Admin users and teams, SSE endpoint

**Files:**
- Create: `server/routes/admin-users.js`, `server/routes/events.js`, `test/admin-users.test.js`
- Modify: `server/routes/index.js` (mount both)

**Interfaces:**
- Consumes: Task 6 `hashPassword`, `revokeUserSessions`, `audit`; Task 7 `requireRole`, `sse`.
- Produces:
  - `GET /api/admin/users` → `[{id, username, display_name, roles, team_id, can_create_files, can_receive_files, active, must_reset}]`
  - `POST /api/admin/users {username, display_name, roles, team_id?, can_create_files?, can_receive_files?}` → `{id, temporary_password}` (16-char random; `must_reset = 1`)
  - `POST /api/admin/users/bulk-requesters` (JSON `{rows: [{display_name, username, team}]}`; the web page parses the CSV) → `[{username, temporary_password}]`
  - `PATCH /api/admin/users/:id {display_name?, roles?, team_id?, can_create_files?, can_receive_files?, active?}` — a change to `roles`, `team_id` or `active` revokes sessions and closes SSE streams
  - `POST /api/admin/users/:id/reset-password` → `{temporary_password}`; revokes sessions
  - `GET/POST /api/admin/teams`, `PATCH /api/admin/teams/:id {name?, active?}`
  - `GET /api/events` — SSE for any signed-in user; `retry: 5000`, `: hello`, then events; no compression.
  - `ROLES` constant in `shared/schemas.js`: `['requester','triage','coordinator','manager','stores','invoicing','approver_stores','approver_invoicing','gm','coo','analyst','admin']`

- [ ] **Step 1: Failing test** — `test/admin-users.test.js` (AC0.14)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { makeApp } from './helpers/app.js';

test('admin creates desk and requester users; non-admin 403 (AC0.14)', async () => {
  const t = makeApp();
  const a = await t.login('admin1');
  const team = (await a.post('/api/admin/teams').set('Origin', t.origin).send({ name: 'Sales' })).body;
  const desk = await a.post('/api/admin/users').set('Origin', t.origin).send({ username: 'nimesha', display_name: 'Nimesha', roles: ['coordinator'], can_create_files: true });
  assert.equal(desk.status, 201);
  assert.equal(desk.body.temporary_password.length, 16);
  const noTeam = await a.post('/api/admin/users').set('Origin', t.origin).send({ username: 'req1', display_name: 'R', roles: ['requester'] });
  assert.equal(noTeam.status, 400, 'requester needs a team');
  const req = await a.post('/api/admin/users').set('Origin', t.origin).send({ username: 'req1', display_name: 'R', roles: ['requester'], team_id: team.id });
  assert.equal(req.status, 201);
  const badRole = await a.post('/api/admin/users').set('Origin', t.origin).send({ username: 'valid.name', display_name: 'X', roles: ['wizard'] });
  assert.equal(badRole.status, 400);
  assert.ok(badRole.body.fields.roles, 'rejected for the role, not the username');
  await t.addUser({ username: 'mgr', roles: ['manager'] });
  const m = await t.login('mgr');
  assert.equal((await m.get('/api/admin/users')).status, 403);
  t.close();
});

test('role/team change ends sessions and SSE streams (AC0.14)', async () => {
  const t = makeApp();
  const id = await t.addUser({ username: 'mgr', roles: ['manager'] });
  const m = await t.login('mgr');
  assert.equal((await m.get('/api/me')).status, 200);

  const server = http.createServer(t.app).listen(0);
  const port = server.address().port;
  const cookie = (await t.login('mgr')).cookie();
  const closed = new Promise((resolve) => {
    http.get({ port, path: '/api/events', headers: { cookie } }, (res) => {
      res.on('data', () => {});
      res.on('end', resolve);
    });
  });
  await new Promise((r) => setTimeout(r, 50));
  assert.equal(t.sse.size(), 1);

  const a = await t.login('admin1');
  assert.equal((await a.patch(`/api/admin/users/${id}`).set('Origin', t.origin).send({ roles: ['coordinator'] })).status, 200);
  await closed;
  assert.equal(t.sse.size(), 0);
  assert.equal((await m.get('/api/me')).status, 401);
  server.close();
  t.close();
});

test('team change and deactivation end sessions (AC0.14)', async () => {
  const t = makeApp();
  const a = await t.login('admin1');
  const t1 = (await a.post('/api/admin/teams').set('Origin', t.origin).send({ name: 'T1' })).body.id;
  const t2 = (await a.post('/api/admin/teams').set('Origin', t.origin).send({ name: 'T2' })).body.id;
  const id = await t.addUser({ username: 'req', roles: ['requester'], team_id: t1 });
  const r1 = await t.login('req');
  await a.patch(`/api/admin/users/${id}`).set('Origin', t.origin).send({ team_id: t2 });
  assert.equal((await r1.get('/api/me')).status, 401);
  const r2 = await t.login('req');
  await a.patch(`/api/admin/users/${id}`).set('Origin', t.origin).send({ display_name: 'Renamed' });
  assert.equal((await r2.get('/api/me')).status, 200, 'a name change keeps the session');
  await a.patch(`/api/admin/users/${id}`).set('Origin', t.origin).send({ active: false });
  assert.equal((await r2.get('/api/me')).status, 401);
  t.close();
});

test('bulk requesters and password reset', async () => {
  const t = makeApp();
  const a = await t.login('admin1');
  await a.post('/api/admin/teams').set('Origin', t.origin).send({ name: 'Sales' });
  const r = await a.post('/api/admin/users/bulk-requesters').set('Origin', t.origin)
    .send({ rows: [{ display_name: 'A', username: 'ra', team: 'Sales' }, { display_name: 'B', username: 'rb', team: 'Sales' }] });
  assert.equal(r.status, 201);
  assert.equal(r.body.length, 2);
  const bad = await a.post('/api/admin/users/bulk-requesters').set('Origin', t.origin).send({ rows: [{ display_name: 'C', username: 'rc', team: 'Nope' }] });
  assert.equal(bad.status, 400);
  assert.equal(t.db.prepare("SELECT count(*) c FROM users WHERE username='rc'").get().c, 0, 'all-or-nothing');
  const id = t.db.prepare("SELECT id FROM users WHERE username='ra'").get().id;
  const reset = await a.post(`/api/admin/users/${id}/reset-password`).set('Origin', t.origin);
  assert.equal(reset.body.temporary_password.length, 16);
  assert.equal(t.db.prepare('SELECT must_reset FROM users WHERE id=?').get(id).must_reset, 1);
  assert.ok(t.db.prepare("SELECT 1 FROM audit_log WHERE action='user.reset_password'").get());
  t.close();
});
```


- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement**

`shared/schemas.js`:
```js
import { z } from 'zod';
export const ROLES = ['requester', 'triage', 'coordinator', 'manager', 'stores', 'invoicing',
  'approver_stores', 'approver_invoicing', 'gm', 'coo', 'analyst', 'admin'];
export const Role = z.enum(ROLES);
export const Username = z.string().trim().min(2).max(64).regex(/^[a-z0-9._-]+$/i);
```

`server/routes/admin-users.js`:
```js
import { Router } from 'express';
import crypto from 'node:crypto';
import { z } from 'zod';
import { requireRole } from '../auth/middleware.js';
import { hashPassword } from '../auth/password.js';
import { revokeUserSessions } from '../auth/sessions.js';
import { audit } from '../services/audit.js';
import { Role, Username } from '../../shared/schemas.js';

const tempPassword = () => crypto.randomBytes(12).toString('base64url').slice(0, 16);
const NewUser = z.object({
  username: Username, display_name: z.string().trim().min(1).max(100), roles: z.array(Role).min(1),
  team_id: z.number().int().nullable().optional(), can_create_files: z.boolean().optional(), can_receive_files: z.boolean().optional(),
});
const EditUser = NewUser.omit({ username: true }).partial().extend({ active: z.boolean().optional() });
const TeamBody = z.object({ name: z.string().trim().min(1).max(100), active: z.boolean().optional() });
const bad = (res, error) => res.status(400).json({ error: 'invalid', fields: error.flatten?.().fieldErrors ?? error });
const publicUser = (u) => ({ id: u.id, username: u.username, display_name: u.display_name, roles: JSON.parse(u.roles),
  team_id: u.team_id, can_create_files: u.can_create_files, can_receive_files: u.can_receive_files, active: u.active, must_reset: u.must_reset });

function checkRequesterTeam(db, roles, teamId) {
  if (!roles.includes('requester')) return null;
  if (!teamId) return { team_id: ['A requester must have a team'] };
  if (!db.prepare('SELECT 1 FROM teams WHERE id = ? AND active = 1').get(teamId)) return { team_id: ['Unknown team'] };
  return null;
}

export function adminUserRoutes() {
  const r = Router();
  r.use('/admin', requireRole('admin'));

  r.get('/admin/users', (req, res) => res.json(req.app.locals.db.prepare('SELECT * FROM users ORDER BY username').all().map(publicUser)));

  r.post('/admin/users', async (req, res) => {
    const { db, clock } = req.app.locals;
    const p = NewUser.safeParse(req.body);
    if (!p.success) return bad(res, p.error);
    const teamProblem = checkRequesterTeam(db, p.data.roles, p.data.team_id);
    if (teamProblem) return bad(res, teamProblem);
    if (db.prepare('SELECT 1 FROM users WHERE username = ?').get(p.data.username)) return res.status(409).json({ error: 'username_taken' });
    const temp = tempPassword();
    const now = clock.now();
    const id = db.prepare(`INSERT INTO users(username, display_name, password_hash, roles, team_id, can_create_files, can_receive_files, must_reset, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)`).run(p.data.username, p.data.display_name, await hashPassword(temp), JSON.stringify(p.data.roles),
      p.data.team_id ?? null, p.data.can_create_files ? 1 : 0, p.data.can_receive_files ? 1 : 0, now.toISOString()).lastInsertRowid;
    audit(db, { actor: req.user.id, action: 'user.create', entity: 'user', entityId: id, detail: { roles: p.data.roles }, now });
    res.status(201).json({ id: Number(id), temporary_password: temp });
  });

  r.post('/admin/users/bulk-requesters', async (req, res) => {
    const { db, clock } = req.app.locals;
    const Rows = z.object({ rows: z.array(z.object({ display_name: z.string().trim().min(1), username: Username, team: z.string().trim().min(1) })).min(1).max(500) });
    const p = Rows.safeParse(req.body);
    if (!p.success) return bad(res, p.error);
    const problems = [];
    const prepared = [];
    for (const [i, row] of p.data.rows.entries()) {
      const team = db.prepare('SELECT id FROM teams WHERE name = ? AND active = 1').get(row.team);
      if (!team) problems.push(`row ${i + 1}: unknown team ${row.team}`);
      if (db.prepare('SELECT 1 FROM users WHERE username = ?').get(row.username)) problems.push(`row ${i + 1}: username taken`);
      const temp = tempPassword();
      prepared.push({ ...row, team_id: team?.id, temp, hash: await hashPassword(temp) });
    }
    if (problems.length) return bad(res, { rows: problems });
    const now = clock.now();
    db.transaction(() => {
      for (const u of prepared) {
        const id = db.prepare(`INSERT INTO users(username, display_name, password_hash, roles, team_id, must_reset, created_at)
          VALUES (?, ?, ?, '["requester"]', ?, 1, ?)`).run(u.username, u.display_name, u.hash, u.team_id, now.toISOString()).lastInsertRowid;
        audit(db, { actor: req.user.id, action: 'user.create', entity: 'user', entityId: id, detail: { roles: ['requester'], bulk: true }, now });
      }
    })();
    res.status(201).json(prepared.map((u) => ({ username: u.username, temporary_password: u.temp })));
  });

  r.patch('/admin/users/:id', (req, res) => {
    const { db, clock, sse } = req.app.locals;
    const id = Number(req.params.id);
    const cur = db.prepare('SELECT * FROM users WHERE id = ?').get(id);
    if (!cur) return res.status(404).json({ error: 'not_found' });
    const p = EditUser.safeParse(req.body);
    if (!p.success) return bad(res, p.error);
    const next = { ...publicUser(cur), ...p.data };
    const teamProblem = checkRequesterTeam(db, next.roles, next.team_id);
    if (teamProblem) return bad(res, teamProblem);
    const revoke = ('roles' in p.data && JSON.stringify(p.data.roles) !== cur.roles)
      || ('team_id' in p.data && p.data.team_id !== cur.team_id) || ('active' in p.data && Number(p.data.active) !== cur.active);
    const now = clock.now();
    db.transaction(() => {
      db.prepare(`UPDATE users SET display_name = ?, roles = ?, team_id = ?, can_create_files = ?, can_receive_files = ?, active = ? WHERE id = ?`)
        .run(next.display_name, JSON.stringify(next.roles), next.team_id ?? null, next.can_create_files ? 1 : 0,
          next.can_receive_files ? 1 : 0, next.active ? 1 : 0, id);
      if (revoke) revokeUserSessions(db, id);
      audit(db, { actor: req.user.id, action: 'user.update', entity: 'user', entityId: id, detail: p.data, now });
    })();
    if (revoke) sse.closeUser(id);
    res.json(publicUser(db.prepare('SELECT * FROM users WHERE id = ?').get(id)));
  });

  r.post('/admin/users/:id/reset-password', async (req, res) => {
    const { db, clock, sse } = req.app.locals;
    const id = Number(req.params.id);
    if (!db.prepare('SELECT 1 FROM users WHERE id = ?').get(id)) return res.status(404).json({ error: 'not_found' });
    const temp = tempPassword();
    const hash = await hashPassword(temp);
    const now = clock.now();
    db.transaction(() => {
      db.prepare('UPDATE users SET password_hash = ?, must_reset = 1 WHERE id = ?').run(hash, id);
      revokeUserSessions(db, id);
      audit(db, { actor: req.user.id, action: 'user.reset_password', entity: 'user', entityId: id, now });
    })();
    sse.closeUser(id);
    res.json({ temporary_password: temp });
  });

  r.get('/admin/teams', (req, res) => res.json(req.app.locals.db.prepare('SELECT * FROM teams ORDER BY name').all()));
  r.post('/admin/teams', (req, res) => {
    const { db, clock } = req.app.locals;
    const p = TeamBody.safeParse(req.body);
    if (!p.success) return bad(res, p.error);
    try {
      const id = db.prepare('INSERT INTO teams(name) VALUES (?)').run(p.data.name).lastInsertRowid;
      audit(db, { actor: req.user.id, action: 'team.create', entity: 'team', entityId: id, now: clock.now() });
      res.status(201).json({ id: Number(id), name: p.data.name, active: 1 });
    } catch (e) {
      if (/UNIQUE/.test(e.message)) return res.status(409).json({ error: 'name_taken' });
      throw e;
    }
  });
  r.patch('/admin/teams/:id', (req, res) => {
    const { db, clock, sse } = req.app.locals;
    const p = TeamBody.partial().safeParse(req.body);
    if (!p.success) return bad(res, p.error);
    const cur = db.prepare('SELECT * FROM teams WHERE id = ?').get(req.params.id);
    if (!cur) return res.status(404).json({ error: 'not_found' });
    db.prepare('UPDATE teams SET name = ?, active = ? WHERE id = ?').run(p.data.name ?? cur.name, p.data.active === undefined ? cur.active : Number(p.data.active), cur.id);
    audit(db, { actor: req.user.id, action: 'team.update', entity: 'team', entityId: cur.id, detail: p.data, now: clock.now() });
    if (p.data.active === false) {
      for (const u of db.prepare('SELECT id FROM users WHERE team_id = ?').all(cur.id)) { revokeUserSessions(db, u.id); sse.closeUser(u.id); }
    }
    res.json(db.prepare('SELECT * FROM teams WHERE id = ?').get(cur.id));
  });
  return r;
}
```

`server/routes/events.js`:
```js
import { Router } from 'express';

export function eventRoutes() {
  const r = Router();
  r.get('/events', (req, res) => {
    res.set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache, no-transform', Connection: 'keep-alive', 'X-Accel-Buffering': 'no' });
    res.flushHeaders();
    res.write('retry: 5000\n: hello\n\n');
    req.app.locals.sse.add(res, { userId: req.user.id, roles: req.user.roles, teamId: req.user.team_id, kind: 'user' });
  });
  return r;
}
```

`server/routes/index.js`:
```js
import { adminUserRoutes } from './admin-users.js';
import { eventRoutes } from './events.js';

export function buildRoutes() {
  return [['/api', adminUserRoutes()], ['/api', eventRoutes()]];
}
```

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: admin users, teams and SSE stream"`

---

### Task 9: Admin configuration API

**Files:**
- Create: `server/routes/admin-config.js`, `server/services/calendar.js`, `test/admin-config.test.js`
- Modify: `server/routes/index.js`

**Interfaces:**
- Consumes: Task 5 `formExists`; Task 7 `employeeMasterStatus`.
- Produces:
  - `loadCalendar(db) → { weekdays: number[], holidays: Set<string> }` (from `settings.working_weekdays` and `holidays`)
  - Routes (all `admin`):
    - `GET /api/admin/divisions` (with processes, stage order, aliases and pairs nested)
    - `PATCH /api/admin/divisions/:code {name?, active?, provisional?, counting_process?, quantity_form_id?, floor_live?}` — `counting_process` must be an active process of that division (400); `quantity_form_id` must exist in `form_definitions` (400); `floor_live: true` → **409 `employee_master_not_configured`** unless `employeeMasterStatus(config) === 'ok'`
    - `POST /api/admin/divisions {code, name}` (new division, provisional, OPD stage order and OPD process list copied, `counting_process = 'packing'`)
    - `PUT /api/admin/divisions/:code/stages {stage_ids: number[]}` (replaces the order; each id 1–11 once)
    - `POST /api/admin/divisions/:code/processes {code, label, counts_in_production?}`, `PATCH /api/admin/divisions/:code/processes/:process {label?, active?}` (deactivating the counting process → 409)
    - `POST /api/admin/aliases {zoho_value, division_code}`, `DELETE /api/admin/aliases/:zoho_value` (config table, not append-only; audited)
    - `POST /api/admin/pairs {division_code, manager_user_id, coordinator_user_id}` (users must hold `manager` / `coordinator`; 400 otherwise), `PATCH /api/admin/pairs/:id {active}`
    - `GET/POST /api/admin/reason-codes` + `PATCH /api/admin/reason-codes/:code {label?, default_owner_label?, active?}`; `GET/POST /api/admin/reject-reasons` + `PATCH /api/admin/reject-reasons/:code {label?, active?}`; `GET/POST /api/admin/order-type-aliases` (`{zoho_value, order_type}`, `zoho_key` computed) + `PATCH /api/admin/order-type-aliases/:zoho_value {order_type?, provisional?}`
    - `GET /api/admin/calendar`, `PUT /api/admin/calendar {weekdays: number[]}`, `POST /api/admin/holidays {date, label}`, `DELETE /api/admin/holidays/:date`
    - `GET /api/admin/audit?limit=&before_id=` (newest first, max 200)
  - Every write is audited.

- [ ] **Step 1: Failing test** — `test/admin-config.test.js` (AC5.13 second half is in Release 5; the 409 rule is built now)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeApp } from './helpers/app.js';
import { loadCalendar } from '../server/services/calendar.js';

test('division edits validated; floor_live refused without Employee Master', async () => {
  const t = makeApp();
  const a = await t.login('admin1');
  const o = { Origin: t.origin };
  assert.equal((await a.patch('/api/admin/divisions/SHPS').set(o).send({ counting_process: 'rewinding' })).status, 400);
  assert.equal((await a.patch('/api/admin/divisions/SHPS').set(o).send({ counting_process: 'packing' })).status, 200);
  assert.equal((await a.patch('/api/admin/divisions/SHPS').set(o).send({ quantity_form_id: 'nope' })).status, 400);
  const fl = await a.patch('/api/admin/divisions/SHPS').set(o).send({ floor_live: true });
  assert.equal(fl.status, 409);
  assert.equal(fl.body.error, 'employee_master_not_configured');
  assert.equal((await a.patch('/api/admin/divisions/SHPS/processes/packing').set(o).send({ active: false })).status, 409);
  assert.ok(t.db.prepare("SELECT 1 FROM audit_log WHERE action='division.update'").get());
  t.close();
});

test('stage order replace and new division', async () => {
  const t = makeApp();
  const a = await t.login('admin1');
  const o = { Origin: t.origin };
  assert.equal((await a.put('/api/admin/divisions/PCU/stages').set(o).send({ stage_ids: [1, 2, 3, 4, 5, 7, 8, 9, 10, 11] })).status, 200);
  assert.equal(t.db.prepare("SELECT count(*) c FROM division_stages WHERE division_code='PCU'").get().c, 10);
  assert.equal((await a.put('/api/admin/divisions/PCU/stages').set(o).send({ stage_ids: [1, 1] })).status, 400);
  assert.equal((await a.post('/api/admin/divisions').set(o).send({ code: 'NEWU', name: 'New unit' })).status, 201);
  assert.equal(t.db.prepare("SELECT provisional, counting_process FROM divisions WHERE code='NEWU'").get().counting_process, 'packing');
  t.close();
});

test('pairs require the right roles; aliases and calendar', async () => {
  const t = makeApp();
  const a = await t.login('admin1');
  const o = { Origin: t.origin };
  const mgr = await t.addUser({ username: 'ranga', roles: ['manager'] });
  const coord = await t.addUser({ username: 'nirmani', roles: ['coordinator'] });
  assert.equal((await a.post('/api/admin/pairs').set(o).send({ division_code: 'PCU', manager_user_id: coord, coordinator_user_id: mgr })).status, 400);
  assert.equal((await a.post('/api/admin/pairs').set(o).send({ division_code: 'PCU', manager_user_id: mgr, coordinator_user_id: coord })).status, 201);
  assert.equal((await a.post('/api/admin/aliases').set(o).send({ zoho_value: 'Packpro Unit', division_code: 'PACKPRO' })).status, 201);
  assert.equal(t.db.prepare("SELECT zoho_key FROM division_aliases WHERE zoho_value='Packpro Unit'").get().zoho_key, 'packpro unit');
  assert.equal((await a.put('/api/admin/calendar').set(o).send({ weekdays: [1, 2, 3, 4, 5, 6] })).status, 200);
  assert.equal((await a.post('/api/admin/holidays').set(o).send({ date: '2026-09-21', label: 'Poya' })).status, 201);
  const cal = loadCalendar(t.db);
  assert.deepEqual(cal.weekdays, [1, 2, 3, 4, 5, 6]);
  assert.equal(cal.holidays.has('2026-09-21'), true);
  assert.equal((await a.put('/api/admin/calendar').set(o).send({ weekdays: [] })).status, 400);
  const audit = await a.get('/api/admin/audit?limit=5');
  assert.equal(audit.body.length, 5);
  t.close();
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement**

`server/services/calendar.js`:
```js
export function loadCalendar(db) {
  const row = db.prepare("SELECT value FROM settings WHERE key = 'working_weekdays'").get();
  return {
    weekdays: row ? JSON.parse(row.value) : [1, 2, 3, 4, 5],
    holidays: new Set(db.prepare('SELECT date FROM holidays').all().map((r) => r.date)),
  };
}
```

`server/routes/admin-config.js` — implement every route listed under **Produces** with the same pattern as Task 8: zod body schema → 400 with `fields`; existence check → 404; business rule → 409/400; `db.transaction` for multi-row writes; `audit(db, { actor: req.user.id, action: '<entity>.<verb>', entity, entityId, detail: body, now })`. The rules that need care:

```js
// PATCH /admin/divisions/:code
if (body.counting_process !== undefined) {
  const ok = db.prepare('SELECT 1 FROM processes WHERE division_code = ? AND code = ? AND active = 1').get(code, body.counting_process);
  if (!ok) return bad(res, { counting_process: ['Not an active process of this division'] });
}
if (body.quantity_form_id !== undefined && !formExists(db, body.quantity_form_id)) {
  return bad(res, { quantity_form_id: ['Unknown form'] });
}
if (body.floor_live === true && employeeMasterStatus(config) !== 'ok') {
  return res.status(409).json({ error: 'employee_master_not_configured' });
}

// PUT /admin/divisions/:code/stages
const Stages = z.object({ stage_ids: z.array(z.number().int().min(1).max(11)).min(1).max(11)
  .refine((a) => new Set(a).size === a.length, 'Each stage once') });
db.transaction(() => {
  db.prepare('DELETE FROM division_stages WHERE division_code = ?').run(code);
  const ins = db.prepare('INSERT INTO division_stages(division_code, stage_id, sort_order) VALUES (?, ?, ?)');
  body.stage_ids.forEach((id, i) => ins.run(code, id, i + 1));
})();

// POST /admin/divisions  {code: /^[A-Z][A-Z0-9_]{1,11}$/, name}
db.transaction(() => {
  db.prepare('INSERT INTO divisions(code, name, provisional) VALUES (?, ?, 1)').run(code, name);
  db.prepare(`INSERT INTO processes(division_code, code, label, counts_in_production)
    SELECT ?, code, label, counts_in_production FROM processes WHERE division_code = 'OPD'`).run(code);
  db.prepare("UPDATE divisions SET counting_process = 'packing' WHERE code = ?").run(code);
  db.prepare(`INSERT INTO division_stages(division_code, stage_id, sort_order)
    SELECT ?, stage_id, sort_order FROM division_stages WHERE division_code = 'OPD'`).run(code);
})();

// PATCH /admin/divisions/:code/processes/:process with active:false
const isCounting = db.prepare('SELECT 1 FROM divisions WHERE code = ? AND counting_process = ?').get(code, proc);
if (body.active === false && isCounting) return res.status(409).json({ error: 'is_counting_process' });

// POST /admin/pairs
const hasRole = (id, role) => {
  const u = db.prepare('SELECT roles, active FROM users WHERE id = ?').get(id);
  return u && u.active && JSON.parse(u.roles).includes(role);
};
if (!hasRole(body.manager_user_id, 'manager') || !hasRole(body.coordinator_user_id, 'coordinator')) {
  return bad(res, { pair: ['The manager must have the manager role and the coordinator the coordinator role'] });
}

// POST /admin/aliases and /admin/order-type-aliases: zoho_key = cmpKey(zoho_value) (shared/text.js); UNIQUE → 409

// PUT /admin/calendar
const Cal = z.object({ weekdays: z.array(z.number().int().min(0).max(6)).min(1).max(7) });
db.prepare("INSERT INTO settings(key, value) VALUES ('working_weekdays', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value")
  .run(JSON.stringify([...new Set(body.weekdays)].sort()));

// POST /admin/holidays {date: /^\d{4}-\d{2}-\d{2}$/, label}
// GET /admin/audit: SELECT * FROM audit_log WHERE (? IS NULL OR id < ?) ORDER BY id DESC LIMIT min(limit, 200)
```

Mount in `server/routes/index.js`: `['/api', adminConfigRoutes()]` (after `adminUserRoutes`).

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: admin configuration API"`

---
### Task 10: Import inputs — folder classification, `captured.json`, column map, readers

**Files:**
- Create: `config/zoho-columns.json`, `cli/import/columns.js`, `cli/import/readers.js`, `cli/import/files.js`, `test/helpers/xlsx.js`, `test/fixtures/zoho/README.md`, `test/import-inputs.test.js`

**Interfaces:**
- Produces:
  - `FILE_MODULES` (in `files.js`): exact file name → `{ module, source, format }`:

    | File name | module | source | format |
    |---|---|---|---|
    | `Sales_Order.xlsx` | `so_xlsx` | `xlsx` | xlsx |
    | `Package.xlsx`, `Package_ALL.xlsx` | `packages` | `xlsx` | xlsx |
    | `Shipment.xlsx`, `Shipment_ALL.xlsx` | `shipments` | `xlsx` | xlsx |
    | `Invoice.xlsx` | `invoices_xlsx` | `xlsx` | xlsx |
    | `Picklist.xlsx` | `picklists` | `xlsx` | xlsx |
    | `Item.xlsx` | `items` | `xlsx` | xlsx |
    | `zoho-pull-so-headers.json` | `so_headers` | `pull` | json |
    | `zoho-pull-bundles.json` | `bundles` | `pull` | json |
    | `zoho-pull-invoice-headers.json` | `invoices_pull` | `pull` | json |

    Ignored names: `captured.json`, `captured-pull.json`, `README.md`, `MANIFEST.txt`, `*.py`, sub-directories. Anything else → unrecognised (that file fails).
  - `classifyFolder(dir) → { files: [{ name, path, module, source, format }], unrecognised: string[] }`
  - `loadCaptured(dir, { capturedAtFlag?: string, now: Date, files }) → Map<name, { capturedAt: iso, fullListClaim: boolean, rowsClaim: number|null } | { error: string }>` — rules (§6.2): entry from `captured.json` wins; `--captured-at` fills only missing **xlsx** entries; a missing `pull` entry is an error even with the flag; a time more than 5 min in the future is an error; `full_list` may only be true for `pull` files.
  - `loadColumns() → spec` from `config/zoho-columns.json`; `mapRow(moduleSpec, raw) → record` (applies `from` lists, first non-empty wins; types `text` (cleanText), `raw` (trimmed, no collapsing), `number`, `cents`, `time`, `date`, `bool`; `time`/`date` produce `{field, field_precision?}`); `missingHeaders(moduleSpec, headerNames) → string[]`.
  - `readXlsx(file) → { headers: string[], rows: AsyncIterable<object> }` (exceljs streaming reader; first worksheet; cell values normalised: `Date` kept, rich text joined, hyperlink → text, formula → result)
  - `readJsonArray(file) → object[]` (throws if not an array)
  - Test helper `writeXlsx(file, headers, rows)`.

- [ ] **Step 1: Write `config/zoho-columns.json`** (the real headers, from the verified facts at the top of this plan)

```json
{
  "so_xlsx": {
    "required": ["SalesOrder Number", "Order Date", "Item Name", "QuantityOrdered", "CF.Manufacturing Division"],
    "fields": {
      "salesorder_number": { "from": ["SalesOrder Number"], "type": "raw" },
      "zoho_id": { "from": ["SalesOrder ID"], "type": "raw" },
      "order_date": { "from": ["Order Date"], "type": "date" },
      "expected_shipment_date": { "from": ["Expected Shipment Date"], "type": "date" },
      "reference_number": { "from": ["PurchaseOrder"], "type": "text" },
      "status": { "from": ["Status"], "type": "text" },
      "total_cents": { "from": ["Total"], "type": "cents" },
      "cf_job_no": { "from": ["CF.Job No"], "type": "text" },
      "cf_order_received_from": { "from": ["CF.Order Received from"], "type": "text" },
      "cf_order_type": { "from": ["CF.Order Type"], "type": "text" },
      "cf_manufacturing_division": { "from": ["CF.Manufacturing Division"], "type": "text" },
      "cf_job_nature": { "from": ["CF.Job Nature"], "type": "text" },
      "cf_material_to_be_used": { "from": ["CF.Base Material to be Used"], "type": "text" },
      "cf_sh_sales_order_ref": { "from": ["CF.SH Sales Order Ref"], "type": "text" },
      "cf_clickup_link": { "from": ["CF.Clickup Link"], "type": "raw" },
      "cf_artwork_availablility": { "from": ["CF.Artwork Availablility", "CF.Artwork Availability"], "type": "text" },
      "cf_dye_cutter_availablity": { "from": ["CF.Dye Cutter Availablity", "CF.Dye Cutter Availability"], "type": "text" },
      "cf_screen_plate_availability_2": { "from": ["CF.Screen / Plate Availability", "CF.Screen / Plate Available"], "type": "text" },
      "item_name": { "from": ["Item Name"], "type": "text" },
      "sku": { "from": ["SKU"], "type": "text" },
      "quantity_ordered": { "from": ["QuantityOrdered"], "type": "number" },
      "quantity_packed": { "from": ["QuantityPacked"], "type": "number" },
      "quantity_invoiced": { "from": ["QuantityInvoiced"], "type": "number" },
      "quantity_cancelled": { "from": ["QuantityCancelled"], "type": "number" },
      "usage_unit": { "from": ["Usage unit"], "type": "text" },
      "rate_cents": { "from": ["Item Price"], "type": "cents" },
      "amount_cents": { "from": ["Item Total"], "type": "cents" }
    }
  },
  "packages": {
    "required": ["PackageItemID", "Packing Number", "SO Number", "Packing Date", "Quantity Packed"],
    "fields": {
      "line_no": { "from": ["PackageItemID"], "type": "raw" },
      "package_number": { "from": ["Packing Number"], "type": "raw" },
      "so_number": { "from": ["SO Number"], "type": "raw" },
      "packing_date": { "from": ["Packing Date"], "type": "date" },
      "status": { "from": ["Status"], "type": "text" },
      "item_name": { "from": ["Item Name"], "type": "text" },
      "sku": { "from": ["SKU"], "type": "text" },
      "quantity_packed": { "from": ["Quantity Packed"], "type": "number" }
    }
  },
  "shipments": {
    "required": ["Shipment Number", "Packing Number", "SO Number", "Created Time"],
    "fields": {
      "shipment_number": { "from": ["Shipment Number"], "type": "raw" },
      "line_no": { "from": ["Packing Number"], "type": "raw" },
      "packing_number": { "from": ["Packing Number"], "type": "raw" },
      "so_number": { "from": ["SO Number"], "type": "raw" },
      "shipment_date": { "from": ["Shipment Date"], "type": "date" },
      "delivery_date": { "from": ["Delivery Date"], "type": "date" },
      "status": { "from": ["Status"], "type": "text" },
      "created_at": { "from": ["Created Time"], "type": "time" },
      "modified_at": { "from": ["Last Modified Time"], "type": "time" }
    }
  },
  "invoices_xlsx": {
    "required": ["Invoice Number", "Invoice Date", "Sales Order Number"],
    "fields": {
      "invoice_number": { "from": ["Invoice Number"], "type": "raw" },
      "so_number": { "from": ["Sales Order Number"], "type": "raw" },
      "invoice_date": { "from": ["Invoice Date"], "type": "date" },
      "status": { "from": ["Invoice Status"], "type": "text" }
    }
  },
  "picklists": {
    "required": ["picklist_id", "picklist_number", "salesorder_numbers"],
    "fields": {
      "zoho_id": { "from": ["picklist_id"], "type": "raw" },
      "picklist_number": { "from": ["picklist_number"], "type": "raw" },
      "date": { "from": ["date"], "type": "date" },
      "status": { "from": ["status"], "type": "text" },
      "salesorder_numbers": { "from": ["salesorder_numbers"], "type": "raw" },
      "created_at": { "from": ["created_time"], "type": "time" },
      "modified_at": { "from": ["last_modified_time"], "type": "time" }
    }
  },
  "items": {
    "required": ["Item ID", "Item Name"],
    "fields": {
      "zoho_id": { "from": ["Item ID"], "type": "raw" },
      "name": { "from": ["Item Name"], "type": "text" },
      "sku": { "from": ["SKU"], "type": "text" },
      "unit": { "from": ["Unit"], "type": "text" },
      "status": { "from": ["Status"], "type": "text" },
      "is_composite": { "from": ["Is Combo Product"], "type": "bool" },
      "modified_at": { "from": ["Last Modified Time"], "type": "time" }
    }
  },
  "so_headers": {
    "id": "salesorder_id",
    "required": ["salesorder_id", "salesorder_number", "quantity_shipped", "last_modified_time"],
    "fields": {
      "zoho_id": { "from": ["salesorder_id"], "type": "raw" },
      "salesorder_number": { "from": ["salesorder_number"], "type": "raw" },
      "order_date": { "from": ["date"], "type": "date" },
      "expected_shipment_date": { "from": ["shipment_date"], "type": "date" },
      "reference_number": { "from": ["reference_number"], "type": "text" },
      "status": { "from": ["status"], "type": "text" },
      "shipped_status": { "from": ["shipped_status"], "type": "text" },
      "invoiced_status": { "from": ["invoiced_status"], "type": "text" },
      "quantity": { "from": ["quantity"], "type": "number" },
      "quantity_packed": { "from": ["quantity_packed"], "type": "number" },
      "quantity_shipped": { "from": ["quantity_shipped"], "type": "number" },
      "quantity_invoiced": { "from": ["quantity_invoiced"], "type": "number" },
      "total_cents": { "from": ["total"], "type": "cents" },
      "cf_job_no": { "from": ["cf_job_no"], "type": "text" },
      "cf_order_received_from": { "from": ["cf_order_received_from"], "type": "text" },
      "cf_order_type": { "from": ["cf_order_type"], "type": "text" },
      "cf_manufacturing_division": { "from": ["cf_manufacturing_division"], "type": "text" },
      "cf_job_nature": { "from": ["cf_job_nature"], "type": "text" },
      "cf_material_to_be_used": { "from": ["cf_material_to_be_used"], "type": "text" },
      "cf_sh_sales_order_ref": { "from": ["cf_sh_sales_order_ref"], "type": "text" },
      "cf_clickup_link": { "from": ["cf_clickup_link"], "type": "raw" },
      "cf_artwork_availablility": { "from": ["cf_artwork_availablility"], "type": "text" },
      "cf_dye_cutter_availablity": { "from": ["cf_dye_cutter_availablity"], "type": "text" },
      "cf_screen_plate_availability_2": { "from": ["cf_screen_plate_availability_2"], "type": "text" },
      "created_at": { "from": ["created_time"], "type": "time" },
      "modified_at": { "from": ["last_modified_time"], "type": "time" }
    }
  },
  "bundles": {
    "id": "bundle_id",
    "required": ["bundle_id", "reference_number", "status", "created_time"],
    "fields": {
      "zoho_id": { "from": ["bundle_id"], "type": "raw" },
      "reference_number": { "from": ["reference_number"], "type": "text" },
      "date": { "from": ["date"], "type": "date" },
      "composite_item_name": { "from": ["composite_item_name"], "type": "text" },
      "quantity": { "from": ["quantity_to_bundle"], "type": "number" },
      "status": { "from": ["status"], "type": "text" },
      "created_at": { "from": ["created_time"], "type": "time" },
      "modified_at": { "from": ["last_modified_time"], "type": "time" }
    }
  },
  "invoices_pull": {
    "id": "invoice_id",
    "required": ["invoice_id", "invoice_number", "reference_number", "created_time"],
    "fields": {
      "invoice_number": { "from": ["invoice_number"], "type": "raw" },
      "so_number": { "from": ["reference_number"], "type": "raw" },
      "invoice_date": { "from": ["date"], "type": "date" },
      "status": { "from": ["status"], "type": "text" },
      "created_at": { "from": ["created_time"], "type": "time" },
      "modified_at": { "from": ["last_modified_time"], "type": "time" }
    }
  }
}
```

- [ ] **Step 2: Failing test** — `test/import-inputs.test.js` (AC0.8, AC0.20b f/k)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { classifyFolder, loadCaptured } from '../cli/import/files.js';
import { loadColumns, mapRow, missingHeaders } from '../cli/import/columns.js';
import { readXlsx } from '../cli/import/readers.js';
import { writeXlsx } from './helpers/xlsx.js';

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'pdimp-'));
const now = new Date('2026-09-18T04:00:00Z'); // 09:30 Colombo (was 03:00Z, which put the 09:00 capture 30 min in the future)

test('classify: exact names only', () => {
  const d = tmp();
  for (const f of ['Sales_Order.xlsx', 'zoho-pull-so-headers.json', 'zoho-pull-so-headers (1).json', 'captured.json', 'README.md', 'Package (1).xlsx']) fs.writeFileSync(path.join(d, f), '[]');
  fs.mkdirSync(path.join(d, 'parts'));
  const c = classifyFolder(d);
  assert.deepEqual(c.files.map((f) => f.module).sort(), ['so_headers', 'so_xlsx']);
  assert.deepEqual(c.unrecognised.sort(), ['Package (1).xlsx', 'zoho-pull-so-headers (1).json']);
});

test('captured.json rules (AC0.20b f, k)', () => {
  const d = tmp();
  const files = [{ name: 'Sales_Order.xlsx', source: 'xlsx' }, { name: 'zoho-pull-so-headers.json', source: 'pull' }];
  let m = loadCaptured(d, { now, files });
  assert.match(m.get('Sales_Order.xlsx').error, /no capture time/);
  m = loadCaptured(d, { now, files, capturedAtFlag: '2026-09-18T08:00:00+05:30' });
  assert.equal(m.get('Sales_Order.xlsx').capturedAt, '2026-09-18T02:30:00.000Z');
  assert.match(m.get('zoho-pull-so-headers.json').error, /header pull/);
  fs.writeFileSync(path.join(d, 'captured.json'), JSON.stringify({
    'zoho-pull-so-headers.json': { captured_at: '2026-09-18T09:00:00+05:30', full_list: true, rows: 3 },
    'Sales_Order.xlsx': { captured_at: '2026-09-19T09:00:00+05:30', full_list: false },
  }));
  m = loadCaptured(d, { now, files });
  assert.equal(m.get('zoho-pull-so-headers.json').fullListClaim, true);
  assert.equal(m.get('zoho-pull-so-headers.json').rowsClaim, 3);
  assert.match(m.get('Sales_Order.xlsx').error, /future/);
  fs.writeFileSync(path.join(d, 'captured.json'), JSON.stringify({ 'Sales_Order.xlsx': { captured_at: '2026-09-18T08:00:00+05:30', full_list: true } }));
  assert.match(loadCaptured(d, { now, files }).get('Sales_Order.xlsx').error, /full_list/);
});

test('column map: shuffled columns map identically; missing required header reported (AC0.8)', async () => {
  const spec = loadColumns().packages;
  const d = tmp();
  const a = path.join(d, 'a.xlsx'), b = path.join(d, 'b.xlsx');
  const headers = ['PackageItemID', 'Packing Date', 'Packing Number', 'SO Number', 'Status', 'Item Name', 'Quantity Packed', 'SKU'];
  const row = ['4892105000000519569', new Date(Date.UTC(2024, 3, 1)), 'SPSPKG-00082', 'JOBORDER-00106', 'delivered', 'Box', '3200.000000', 'OPS501'];
  await writeXlsx(a, headers, [row]);
  const order = [7, 3, 0, 6, 1, 5, 2, 4];
  await writeXlsx(b, order.map((i) => headers[i]), [order.map((i) => row[i])]);
  const read = async (f) => { const x = await readXlsx(f); const out = []; for await (const r of x.rows) out.push(mapRow(spec, r)); return out; };
  assert.deepEqual(await read(a), await read(b));
  const [rec] = await read(a);
  assert.equal(rec.packing_date, '2024-03-31T18:30:00.000Z');
  assert.equal(rec.quantity_packed, 3200);
  assert.deepEqual(missingHeaders(spec, headers.filter((h) => h !== 'SO Number')), ['SO Number']);
});

test('an ID stored as a huge number is refused, not rounded', () => {
  const spec = loadColumns().packages;
  assert.throws(() => mapRow(spec, { PackageItemID: 4892105000000519569, 'Packing Number': 'P', 'SO Number': 'S' }), /too large/);
});

test('duplicate CF spellings: first non-empty wins', () => {
  const spec = loadColumns().so_xlsx;
  const rec = mapRow(spec, { 'SalesOrder Number': 'JOBORDER-1', 'CF.Artwork Availablility': '', 'CF.Artwork Availability': 'true ' });
  assert.equal(rec.cf_artwork_availablility, 'true');
});
```

- [ ] **Step 3: Run — expect FAIL.**
- [ ] **Step 4: Implement**

`test/helpers/xlsx.js`:
```js
import ExcelJS from 'exceljs';
export async function writeXlsx(file, headers, rows) {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet('Sheet1');
  ws.addRow(headers);
  for (const r of rows) ws.addRow(r);
  await wb.xlsx.writeFile(file);
}
```

`cli/import/readers.js`:
```js
import fs from 'node:fs';
import ExcelJS from 'exceljs';

const cellValue = (v) => {
  if (v === null || v === undefined) return null;
  if (v instanceof Date) return v;
  if (typeof v === 'object') {
    if (Array.isArray(v.richText)) return v.richText.map((p) => p.text).join('');
    if ('text' in v) return v.text;
    if ('result' in v) return v.result;
    if ('error' in v) return null;
  }
  return v;
};

export async function readXlsx(file) {
  const reader = new ExcelJS.stream.xlsx.WorkbookReader(file, { worksheets: 'emit', sharedStrings: 'cache', styles: 'cache' });
  const iter = reader[Symbol.asyncIterator]();
  const { value: sheet } = await iter.next();
  if (!sheet) throw new Error(`${file}: no worksheet`);
  const rowIter = sheet[Symbol.asyncIterator]();
  const first = await rowIter.next();
  const headers = first.done ? [] : first.value.values.slice(1).map((h) => String(cellValue(h) ?? '').trim());
  async function* rows() {
    for await (const row of { [Symbol.asyncIterator]: () => rowIter }) {
      const vals = row.values;
      const obj = {};
      headers.forEach((h, i) => { if (h) obj[h] = cellValue(vals[i + 1]); });
      if (Object.values(obj).some((v) => v !== null && v !== '')) yield obj;
    }
    // Reached only when the sheet was read to the end: drain the rest of the workbook so exceljs
    // finishes and removes its temp files. After an early exit (a bad cell threw) we must NOT await
    // the reader — with sheet-before-sharedStrings files it would never settle. That path may leave
    // one temp file behind; the file is recorded as failed and the import moves on.
    for (let n = await iter.next(); !n.done; n = await iter.next()) {
      for await (const _row of n.value) { /* skip other sheets */ }
    }
  }
  return { headers, rows: rows() };
}

export function readJsonArray(file) {
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!Array.isArray(data)) throw new Error(`${file}: expected a JSON array`);
  return data;
}
```

`cli/import/columns.js`:
```js
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { cleanText, toNumber, toCents } from '../../shared/text.js';
import { parseZohoTime } from '../../shared/time.js';

const FILE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../config/zoho-columns.json');
export const loadColumns = () => JSON.parse(fs.readFileSync(FILE, 'utf8'));

const empty = (v) => v === null || v === undefined || (typeof v === 'string' && v.trim() === '');

export function mapRow(spec, raw) {
  const out = {};
  for (const [field, { from, type }] of Object.entries(spec.fields)) {
    const v = from.map((h) => raw[h]).find((x) => !empty(x)) ?? null;
    switch (type) {
      case 'raw':
        if (typeof v === 'number' && !Number.isSafeInteger(v) && Number.isInteger(v)) {
          throw new Error(`${field}: number ${v} is too large to keep exactly; the export must store it as text`);
        }
        out[field] = empty(v) ? null : String(v).trim();
        break;
      case 'text': out[field] = cleanText(v); break;
      case 'number': out[field] = toNumber(v); break;
      case 'cents': out[field] = toCents(v); break;
      case 'bool': out[field] = empty(v) ? null : (String(v).trim().toLowerCase() === 'true' ? 1 : 0); break;
      case 'time':
      case 'date': {
        const t = parseZohoTime(v, type);
        out[field] = t?.iso ?? null;
        out[`${field}_precision`] = t?.precision ?? null;
        break;
      }
      default: throw new Error(`Unknown column type ${type}`);
    }
  }
  return out;
}

export const missingHeaders = (spec, headers) => spec.required.filter((h) => !headers.includes(h));
```

`cli/import/files.js`:
```js
import fs from 'node:fs';
import path from 'node:path';
import { parseZohoTime } from '../../shared/time.js';

export const FILE_MODULES = {
  'Sales_Order.xlsx': { module: 'so_xlsx', source: 'xlsx', format: 'xlsx' },
  'Package.xlsx': { module: 'packages', source: 'xlsx', format: 'xlsx' },
  'Package_ALL.xlsx': { module: 'packages', source: 'xlsx', format: 'xlsx' },
  'Shipment.xlsx': { module: 'shipments', source: 'xlsx', format: 'xlsx' },
  'Shipment_ALL.xlsx': { module: 'shipments', source: 'xlsx', format: 'xlsx' },
  'Invoice.xlsx': { module: 'invoices_xlsx', source: 'xlsx', format: 'xlsx' },
  'Picklist.xlsx': { module: 'picklists', source: 'xlsx', format: 'xlsx' },
  'Item.xlsx': { module: 'items', source: 'xlsx', format: 'xlsx' },
  'zoho-pull-so-headers.json': { module: 'so_headers', source: 'pull', format: 'json' },
  'zoho-pull-bundles.json': { module: 'bundles', source: 'pull', format: 'json' },
  'zoho-pull-invoice-headers.json': { module: 'invoices_pull', source: 'pull', format: 'json' },
};
const IGNORED = new Set(['captured.json', 'captured-pull.json', 'README.md', 'MANIFEST.txt']);

export function classifyFolder(dir) {
  const files = []; const unrecognised = [];
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ent.isDirectory() || IGNORED.has(ent.name) || ent.name.endsWith('.py')) continue;
    const m = FILE_MODULES[ent.name];
    if (m) files.push({ name: ent.name, path: path.join(dir, ent.name), ...m });
    else unrecognised.push(ent.name);
  }
  return { files, unrecognised };
}

export function loadCaptured(dir, { capturedAtFlag, now, files }) {
  const file = path.join(dir, 'captured.json');
  const entries = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {};
  const out = new Map();
  for (const f of files) {
    const e = entries[f.name];
    let rawTime = e?.captured_at;
    if (!e) {
      if (f.source === 'pull') { out.set(f.name, { error: 'a header pull file needs its own captured.json entry' }); continue; }
      if (!capturedAtFlag) { out.set(f.name, { error: 'no capture time (captured.json or --captured-at)' }); continue; }
      rawTime = capturedAtFlag;
    }
    let t;
    try { t = parseZohoTime(rawTime, 'time'); } catch { t = null; }
    if (!t || t.precision !== 'time') { out.set(f.name, { error: `invalid captured_at: ${rawTime}` }); continue; }
    if (Date.parse(t.iso) > now.getTime() + 5 * 60e3) { out.set(f.name, { error: 'captured_at is in the future' }); continue; }
    if (e?.full_list && f.source !== 'pull') { out.set(f.name, { error: 'full_list may only be set for header pull files' }); continue; }
    out.set(f.name, { capturedAt: t.iso, fullListClaim: Boolean(e?.full_list), rowsClaim: Number.isInteger(e?.rows) ? e.rows : null });
  }
  return out;
}
```

`test/fixtures/zoho/README.md`: "Fixture files are generated inside each test with `writeXlsx` and plain JSON, using the real header names from `config/zoho-columns.json`. The 200-SO sample (Task 12) is built by `test/fixtures/zoho/make-sample.js` from `/root/exports/zoho/native/2026-09-16` and committed as JSON so tests stay offline."

- [ ] **Step 5: Run — expect PASS.**
- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: import inputs (files, captured.json, columns, readers)"`

---

### Task 11: Guarded upserts, import runs and the CLI

**Files:**
- Create: `cli/import/upsert.js`, `cli/import/run.js`, `cli/import-zoho.js`, `test/import-run.test.js`

**Interfaces:**
- Consumes: Task 10 everything; Task 2 `soKey`.
- Produces:
  - `upsertGuarded(db, { table, keys: string[], fields: string[], rec, capturedAt, sourceFile, now, fullList = true, alwaysTakeOver = () => false }) → { changed: boolean, before: object|null }` — the §6.2 rule: insert if absent; skip if `before.captured_at > capturedAt`; skip if `!fullList && before.modified_at > rec.modified_at`; update when any of `fields` differs (or `alwaysTakeOver(before)`), writing `fields` + `source_file`, `last_synced_at = now`, `captured_at`; otherwise no write.
  - `MODULE_HANDLERS[module] = { table, keys, fields, soOf(rec) → string[], prepare?(rec) }` for every module in Task 10's table (so_xlsx writes two tables; see code).
  - `importFolder(db, { dir, org, capturedAtFlag, now, dryRun, afterBatch = () => {}, logger }) → { files: [{ name, runId, status, error?, warnings }], exitCode: 0|1|2 }`
  - Run lifecycle: `startRun`, `finishRun` (status + finished_at set together; §6.2).
  - CLI: `node cli/import-zoho.js --org SPS --dir <d> [--dir <d2>] [--captured-at <iso>] [--dry-run] [--rebuild-facts]`; exit 0 ok, 2 warnings only, 1 any failure or refusal. Refuses when the DB `user_version` is below the code's highest migration ("start the service first").

- [ ] **Step 1: Failing test** — `test/import-run.test.js` (AC0.7, 0.9, 0.20b c/i/i2 mirror part, 0.20c)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { makeDb } from './helpers/db.js';
import { writeXlsx } from './helpers/xlsx.js';
import { importFolder } from '../cli/import/run.js';

const quiet = { info() {}, warn() {}, error() {} };
const now = new Date('2026-09-18T06:00:00Z');
const PKG_H = ['PackageItemID', 'Packing Date', 'Packing Number', 'SO Number', 'Status', 'Item Name', 'Quantity Packed', 'SKU'];
const SO_H = ['SalesOrder ID', 'SalesOrder Number', 'Order Date', 'Expected Shipment Date', 'Status', 'Item Name', 'SKU',
  'QuantityOrdered', 'QuantityPacked', 'QuantityInvoiced', 'QuantityCancelled', 'Usage unit', 'Item Price', 'Item Total', 'Total',
  'CF.Manufacturing Division', 'CF.Order Type', 'CF.Job No'];
const soRow = (no, item, qty, div = 'Offset Printing Division (OPD)') =>
  ['1', no, '2026-09-01 00:00:00', '2026-09-20 00:00:00', 'confirmed', item, '', qty, '0', '0', '0', 'pcs', '10', String(qty * 10), '1000', div, 'Customized Order', 'OPD1'];
const header = (no, over = {}) => ({ salesorder_id: `id-${no}`, salesorder_number: no, date: '2026-09-01', shipment_date: '2026-09-20',
  status: 'confirmed', quantity: '100', quantity_packed: '0', quantity_shipped: '0', quantity_invoiced: '0', total: '1000',
  cf_manufacturing_division: 'Paper Cup Unit (PCU)', created_time: '2026-09-01T10:00:00+0530', last_modified_time: '2026-09-01T10:00:00+0530', ...over });

async function folder(spec) {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pdrun-'));
  const captured = {};
  if (spec.so) { await writeXlsx(path.join(d, 'Sales_Order.xlsx'), SO_H, spec.so); captured['Sales_Order.xlsx'] = { captured_at: spec.at, full_list: false }; }
  if (spec.packages) { await writeXlsx(path.join(d, 'Package.xlsx'), PKG_H, spec.packages); captured['Package.xlsx'] = { captured_at: spec.at, full_list: false }; }
  if (spec.shipments) { await writeXlsx(path.join(d, 'Shipment.xlsx'), SHP_H, spec.shipments); captured['Shipment.xlsx'] = { captured_at: spec.at, full_list: false }; }
  if (spec.bundles) {
    fs.writeFileSync(path.join(d, 'zoho-pull-bundles.json'), JSON.stringify(spec.bundles));
    captured['zoho-pull-bundles.json'] = { captured_at: spec.headersAt ?? spec.at, full_list: true, rows: spec.bundles.length };
  }
  if (spec.headers) {
    fs.writeFileSync(path.join(d, 'zoho-pull-so-headers.json'), JSON.stringify(spec.headers));
    captured['zoho-pull-so-headers.json'] = { captured_at: spec.headersAt ?? spec.at, full_list: spec.full ?? true, rows: spec.rows ?? new Set(spec.headers.map((h) => h.salesorder_id)).size };
  }
  fs.writeFileSync(path.join(d, 'captured.json'), JSON.stringify(captured));
  return d;
}
const run = (db, dir) => importFolder(db, { dir, org: 'SPS', now, logger: quiet });  // facts recompute is the default from Task 12
const MIRROR = ['zoho_so_headers', 'zoho_so_lines', 'zoho_so_line_sets', 'zoho_bundles', 'zoho_package_lines',
  'zoho_shipment_lines', 'zoho_invoices', 'zoho_picklists', 'zoho_picklist_sos', 'zoho_items', 'zoho_so_facts'];
const snapshot = (db) => MIRROR.map((t) =>
  db.prepare(`SELECT * FROM ${t} ORDER BY 1,2,3`).all().map(({ source_file, last_synced_at, ...r }) => r));
const SHP_H = ['Shipment ID', 'Packing Number', 'Shipment Date', 'Shipment Number', 'Status', 'Delivery Date', 'Created Time', 'Last Modified Time', 'SO Number'];

test('fixture import counts; re-run changes nothing; duplicates collapse; changed SOs listed (AC0.7)', async () => {
  const { db, close } = makeDb();
  const d = await folder({
    at: '2026-09-18T08:00:00+05:30',
    so: [soRow('JOBORDER-1', 'Box A', 100), soRow('JOBORDER-1', 'Box B', 50), soRow('JOBORDER-2', 'Cup', 10), soRow('JOBORDER-0', 'Old', 1)],
    packages: [['p1', '2026-09-05 00:00:00', 'PKG-1', 'JOBORDER-1', 'shipped', 'Box A', '100', ''],
      ['p1', '2026-09-05 00:00:00', 'PKG-1', 'JOBORDER-1', 'shipped', 'Box A', '100', '']],
    headers: [header('JOBORDER-1'), header('JOBORDER-1'), header('JOBORDER-9')],
  });
  const r1 = await run(db, d);
  assert.equal(r1.exitCode, 0);
  assert.equal(db.prepare('SELECT count(*) c FROM zoho_so_lines').get().c, 4);
  assert.equal(db.prepare('SELECT count(*) c FROM zoho_package_lines').get().c, 1);
  assert.equal(db.prepare('SELECT count(*) c FROM zoho_so_headers').get().c, 4);
  const pkgRun = db.prepare("SELECT * FROM zoho_import_runs WHERE module='packages'").get();
  assert.deepEqual(JSON.parse(pkgRun.changed_so_numbers), ['JOBORDER-1']);
  const before = snapshot(db);
  const r2 = await run(db, d);
  assert.deepEqual(snapshot(db), before);
  for (const f of r2.files) assert.deepEqual(JSON.parse(db.prepare('SELECT changed_so_numbers c FROM zoho_import_runs WHERE id=?').get(f.runId).c), []);
  close();
});

test('rows before 2024-01-01 are skipped and counted', async () => {
  const { db, close } = makeDb();
  const old = soRow('JOBORDER-OLD', 'x', 1); old[2] = '2023-12-31 00:00:00';
  const d = await folder({ at: '2026-09-18T08:00:00+05:30', so: [old, soRow('JOBORDER-NEW', 'y', 1)] });
  const r = await run(db, d);
  assert.equal(db.prepare("SELECT count(*) c FROM zoho_so_lines WHERE salesorder_number='JOBORDER-OLD'").get().c, 0);
  assert.equal(db.prepare('SELECT rows_skipped FROM zoho_import_runs WHERE id=?').get(r.files[0].runId).rows_skipped, 1);
  close();
});

test('unmapped division values import and keep status ok (AC0.9)', async () => {
  const { db, close } = makeDb();
  const d = await folder({ at: '2026-09-18T08:00:00+05:30', so: [soRow('JOBORDER-5', 'x', 1, 'Mystery Unit')] });
  const r = await run(db, d);
  assert.equal(r.exitCode, 0);
  assert.equal(db.prepare("SELECT cf_manufacturing_division d FROM zoho_so_headers WHERE salesorder_number='JOBORDER-5'").get().d, 'Mystery Unit');
  close();
});

test('a bad cell mid-file fails that file, and the next file still imports (no hang)', { timeout: 20000 }, async () => {
  const { db, close } = makeDb();
  const d = await folder({ at: '2026-09-18T08:00:00+05:30',
    packages: [['p1', '2026-09-05 00:00:00', 'PKG-1', 'JOBORDER-1', 'shipped', 'Box', '10', ''],
      ['p2', '2026-09-05 00:00:00', 'PKG-2', 'JOBORDER-1', 'shipped', 'Box', 'ten', ''],   // "Not a number"
      ['p3', '2026-09-05 00:00:00', 'PKG-3', 'JOBORDER-1', 'shipped', 'Box', '10', '']],
    headers: [header('JOBORDER-1')] });
  const r = await run(db, d);
  assert.equal(r.exitCode, 1);
  const pkg = db.prepare("SELECT status, finished_at, error FROM zoho_import_runs WHERE module='packages'").get();
  assert.equal(pkg.status, 'failed');
  assert.ok(pkg.finished_at);
  assert.match(pkg.error, /Not a number/);
  assert.equal(db.prepare("SELECT status FROM zoho_import_runs WHERE module='so_headers'").get().status, 'ok');
  close();
});

test('missing required header fails that file only', async () => {
  const { db, close } = makeDb();
  const d = await folder({ at: '2026-09-18T08:00:00+05:30', packages: [] });
  await writeXlsx(path.join(d, 'Package.xlsx'), PKG_H.filter((h) => h !== 'SO Number'), []);
  fs.writeFileSync(path.join(d, 'zoho-pull-so-headers.json'), JSON.stringify([header('JOBORDER-1')]));
  fs.writeFileSync(path.join(d, 'captured.json'), JSON.stringify({ 'Package.xlsx': { captured_at: '2026-09-18T08:00:00+05:30' }, 'zoho-pull-so-headers.json': { captured_at: '2026-09-18T08:00:00+05:30', full_list: true, rows: 1 } }));
  const r = await run(db, d);
  assert.equal(r.exitCode, 1);
  const pkg = db.prepare("SELECT status, error FROM zoho_import_runs WHERE module='packages'").get();
  assert.equal(pkg.status, 'failed');
  assert.match(pkg.error, /SO Number/);
  assert.equal(db.prepare("SELECT status FROM zoho_import_runs WHERE module='so_headers'").get().status, 'ok');
  close();
});

test('full_list verified: rows mismatch or < 98% of previous → false with a warning', async () => {
  const { db, close } = makeDb();
  const many = Array.from({ length: 100 }, (_, i) => header(`JOBORDER-${i}`));
  await run(db, await folder({ at: '2026-09-17T08:00:00+05:30', headers: many }));
  await run(db, await folder({ at: '2026-09-18T08:00:00+05:30', headers: many.slice(0, 90) }));
  const last = db.prepare("SELECT full_list, status, warnings FROM zoho_import_runs WHERE module='so_headers' ORDER BY id DESC").get();
  assert.equal(last.full_list, 0);
  assert.equal(last.status, 'warning');
  await run(db, await folder({ at: '2026-09-18T09:00:00+05:30', headers: many, rows: 99 }));
  assert.equal(db.prepare("SELECT full_list FROM zoho_import_runs WHERE module='so_headers' ORDER BY id DESC").get().full_list, 0);
  close();
});

test('pull takes over xlsx-created header; same modified_at, new quantity_shipped updates (AC0.20c)', async () => {
  const { db, close } = makeDb();
  await run(db, await folder({ at: '2026-09-18T07:00:00+05:30', so: [soRow('JOBORDER-1', 'Box', 100)] }));
  assert.equal(db.prepare('SELECT source FROM zoho_so_headers').get().source, 'xlsx');
  await run(db, await folder({ at: '2026-09-18T08:00:00+05:30', headers: [header('JOBORDER-1')] }));
  assert.equal(db.prepare('SELECT source FROM zoho_so_headers').get().source, 'pull');
  await run(db, await folder({ at: '2026-09-18T09:00:00+05:30', headers: [header('JOBORDER-1', { quantity_shipped: '60' })] }));
  assert.equal(db.prepare('SELECT quantity_shipped q FROM zoho_so_headers').get().q, 60);
  // a later xlsx never overwrites a pulled header
  await run(db, await folder({ at: '2026-09-18T10:00:00+05:30', so: [soRow('JOBORDER-1', 'Box', 100)] }));
  assert.equal(db.prepare('SELECT source, quantity_shipped q FROM zoho_so_headers').get().q, 60);
  close();
});

test('out-of-order folders end in the same mirror, every table; A→B→A; H and M are maxima (AC0.20b i)', async () => {
  const bundle = (ref, status, mod) => ({ bundle_id: 'b1', reference_number: ref, status, date: '2026-09-15',
    quantity_to_bundle: '10', composite_item_name: 'Box', created_time: '2026-09-15T09:00:00+0530', last_modified_time: mod });
  const ship = (so, status, mod) => [['s1', 'PKG-1', '2026-09-15 00:00:00', 'SHP-1', status, '', '2026-09-15 10:00:00', mod, so]];
  const mk = async () => [
    await folder({ at: '2026-09-16T08:00:00+05:30', headers: [header('JOBORDER-1', { quantity_shipped: '0', last_modified_time: '2026-09-16T07:00:00+0530' })],
      packages: [['p1', '2026-09-15 00:00:00', 'PKG-1', 'JOBORDER-1', 'not_shipped', 'Box', '10', '']],
      shipments: ship('JOBORDER-1', 'shipped', '2026-09-16 07:00:00'),
      bundles: [bundle('JOBORDER-1', 'bundled', '2026-09-16T07:00:00+0530')] }),
    await folder({ at: '2026-09-17T08:00:00+05:30', headers: [header('JOBORDER-1', { quantity_shipped: '10', last_modified_time: '2026-09-17T07:00:00+0530' })],
      packages: [['p1', '2026-09-15 00:00:00', 'PKG-1', 'JOBORDER-2', 'shipped', 'Box', '10', '']],
      shipments: ship('JOBORDER-2', 'delivered', '2026-09-17 07:00:00'),
      bundles: [bundle('JOBORDER-2 - B', 'draft', '2026-09-17T07:00:00+0530')] }),
    await folder({ at: '2026-09-18T08:00:00+05:30', headers: [header('JOBORDER-1', { quantity_shipped: '0', last_modified_time: '2026-09-18T07:00:00+0530' })],
      packages: [['p1', '2026-09-15 00:00:00', 'PKG-1', 'JOBORDER-1', 'shipped', 'Box', '10', '']],
      shipments: ship('JOBORDER-1', 'delivered', '2026-09-18 07:00:00'),
      bundles: [bundle('JOBORDER-1', 'bundled', '2026-09-18T07:00:00+0530')] }),
  ];
  const a = makeDb(); const [f1, f2, f3] = await mk();
  for (const f of [f1, f2, f3]) await run(a.db, f);
  const b = makeDb();
  for (const f of [f1, f3, f2]) await run(b.db, f);
  assert.deepEqual(snapshot(b.db), snapshot(a.db));
  assert.equal(b.db.prepare('SELECT quantity_shipped q FROM zoho_so_headers').get().q, 0);
  assert.equal(b.db.prepare('SELECT so_number FROM zoho_package_lines').get().so_number, 'JOBORDER-1');
  assert.deepEqual(b.db.prepare('SELECT so_key, status FROM zoho_bundles').get(), { so_key: 'JOBORDER-1', status: 'bundled' });
  assert.equal(b.db.prepare('SELECT so_number FROM zoho_shipment_lines').get().so_number, 'JOBORDER-1');
  const maxCap = (db, where) => db.prepare(`SELECT max(captured_at) m FROM zoho_import_runs WHERE ${where}`).get().m;
  for (const db of [a.db, b.db]) {
    assert.equal(maxCap(db, "module='so_headers' AND full_list=1 AND finished_at IS NOT NULL"), '2026-09-18T02:30:00.000Z');
    assert.equal(maxCap(db, "module IN ('packages','shipments') AND rows_upserted > 0"), '2026-09-18T02:30:00.000Z');
  }
  a.close(); b.close();
});

test('SO line sets: removed lines disappear; an older file cannot bring them back', async () => {
  const { db, close } = makeDb();
  const two = await folder({ at: '2026-09-16T08:00:00+05:30', so: [soRow('JOBORDER-1', 'A', 1), soRow('JOBORDER-1', 'B', 2)] });
  const one = await folder({ at: '2026-09-17T08:00:00+05:30', so: [soRow('JOBORDER-1', 'A', 1)] });
  await run(db, one);
  await run(db, two);   // older capture imported later
  assert.equal(db.prepare('SELECT count(*) c FROM zoho_so_lines').get().c, 1);
  const fresh = makeDb();
  await run(fresh.db, two);
  await run(fresh.db, one);
  assert.equal(fresh.db.prepare('SELECT count(*) c FROM zoho_so_lines').get().c, 1);
  fresh.close(); close();
});

test('run rows: status NULL until finished; failure sets both (AC0.20b i2 support)', async () => {
  const { db, close } = makeDb();
  const d = await folder({ at: '2026-09-18T08:00:00+05:30', headers: [header('JOBORDER-1')] });
  let seen;
  await importFolder(db, { dir: d, org: 'SPS', now, logger: quiet, afterBatch: () => { seen = db.prepare('SELECT status, finished_at FROM zoho_import_runs').get(); } });
  assert.deepEqual(seen, { status: null, finished_at: null });
  assert.equal(db.prepare('SELECT status FROM zoho_import_runs').get().status, 'ok');
  close();
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement**

`cli/import/upsert.js`:
```js
import { soKey } from '../../shared/text.js';

const same = (a, b) => (a ?? null) === (b ?? null);

export function upsertGuarded(db, { table, keys, fields, rec, capturedAt, sourceFile, now, fullList = true, alwaysTakeOver = () => false }) {
  const where = keys.map((k) => `${k} = ?`).join(' AND ');
  const before = db.prepare(`SELECT * FROM ${table} WHERE ${where}`).get(...keys.map((k) => rec[k]));
  const meta = { source_file: sourceFile, last_synced_at: now.toISOString(), captured_at: capturedAt };
  if (!before) {
    const cols = [...keys, ...fields, ...Object.keys(meta)];
    db.prepare(`INSERT INTO ${table}(${cols.join(',')}) VALUES (${cols.map(() => '?').join(',')})`)
      .run(...cols.map((c) => (c in meta ? meta[c] : rec[c] ?? null)));
    return { changed: true, before: null };
  }
  const takeOver = alwaysTakeOver(before);
  if (!takeOver && before.captured_at > capturedAt) return { changed: false, before };
  if (!takeOver && !fullList && before.modified_at && rec.modified_at && before.modified_at > rec.modified_at) return { changed: false, before };
  if (!takeOver && fields.every((f) => same(before[f], rec[f]))) return { changed: false, before };
  const cols = [...fields, ...Object.keys(meta)];
  db.prepare(`UPDATE ${table} SET ${cols.map((c) => `${c} = ?`).join(', ')} WHERE ${where}`)
    .run(...cols.map((c) => (c in meta ? meta[c] : rec[c] ?? null)), ...keys.map((k) => rec[k]));
  return { changed: true, before };
}

const HEADER_FIELDS_PULL = ['zoho_id', 'order_date', 'expected_shipment_date', 'reference_number', 'status', 'shipped_status',
  'invoiced_status', 'quantity', 'quantity_packed', 'quantity_shipped', 'quantity_invoiced', 'total_cents', 'cf_job_no',
  'cf_order_received_from', 'cf_order_type', 'cf_manufacturing_division', 'cf_job_nature', 'cf_material_to_be_used',
  'cf_sh_sales_order_ref', 'cf_clickup_link', 'cf_artwork_availablility', 'cf_dye_cutter_availablity',
  'cf_screen_plate_availability_2', 'created_at', 'modified_at', 'source'];
const HEADER_FIELDS_XLSX = ['zoho_id', 'order_date', 'expected_shipment_date', 'reference_number', 'status', 'total_cents',
  'cf_job_no', 'cf_order_received_from', 'cf_order_type', 'cf_manufacturing_division', 'cf_job_nature', 'cf_material_to_be_used',
  'cf_sh_sales_order_ref', 'cf_clickup_link', 'cf_artwork_availablility', 'cf_dye_cutter_availablity',
  'cf_screen_plate_availability_2', 'source'];
const LINE_FIELDS = ['item_name', 'sku', 'quantity_ordered', 'quantity_packed', 'quantity_invoiced', 'quantity_cancelled', 'usage_unit', 'rate_cents', 'amount_cents'];

// Each handler: write(db, rec, ctx) → Set of SO numbers touched (before and after).
export const MODULE_HANDLERS = {
  so_headers: {
    idField: 'zoho_id',
    dateField: 'order_date',
    write(db, rec, ctx) {
      const r = upsertGuarded(db, { table: 'zoho_so_headers', keys: ['org', 'salesorder_number'], fields: HEADER_FIELDS_PULL,
        rec: { ...rec, org: ctx.org, source: 'pull' }, ...ctx.guard, alwaysTakeOver: (b) => b.source === 'xlsx' });
      return r.changed ? [rec.salesorder_number] : [];
    },
  },
  so_xlsx: {
    dateField: 'order_date',
    write(db, rec, ctx) {
      const touched = [];
      // header fields only while no pulled/synced header exists
      const existing = db.prepare('SELECT source FROM zoho_so_headers WHERE org = ? AND salesorder_number = ?').get(ctx.org, rec.salesorder_number);
      if (!existing || existing.source === 'xlsx') {
        if (ctx.headerSeen.has(rec.salesorder_number) === false) {
          ctx.headerSeen.add(rec.salesorder_number);
          const h = upsertGuarded(db, { table: 'zoho_so_headers', keys: ['org', 'salesorder_number'], fields: HEADER_FIELDS_XLSX,
            rec: { ...rec, org: ctx.org, source: 'xlsx' }, ...ctx.guard });
          if (h.changed) touched.push(rec.salesorder_number);
        }
      }
      // Line set rule: a file's lines for an SO are used only if this capture is at least as new as the
      // capture that last wrote that SO's lines; lines beyond the new count are removed in finish().
      const so = rec.salesorder_number;
      if (!ctx.lineSetAllowed.has(so)) {
        const set = db.prepare('SELECT captured_at FROM zoho_so_line_sets WHERE org = ? AND salesorder_number = ?').get(ctx.org, so);
        ctx.lineSetAllowed.set(so, !set || set.captured_at <= ctx.guard.capturedAt);
      }
      if (!ctx.lineSetAllowed.get(so)) return touched;
      const lineNo = (ctx.lineCounters.get(so) ?? 0) + 1;
      ctx.lineCounters.set(so, lineNo);
      const l = upsertGuarded(db, { table: 'zoho_so_lines', keys: ['org', 'salesorder_number', 'line_no'], fields: LINE_FIELDS,
        rec: { ...rec, org: ctx.org, line_no: lineNo }, ...ctx.guard });
      if (l.changed) touched.push(so);
      return touched;
    },
    // Runs once after the last batch, in its own IMMEDIATE transaction.
    finish(db, ctx) {
      const touched = [];
      const upsertSet = db.prepare(`INSERT INTO zoho_so_line_sets(org, salesorder_number, captured_at, line_count) VALUES (?, ?, ?, ?)
        ON CONFLICT(org, salesorder_number) DO UPDATE SET captured_at = excluded.captured_at, line_count = excluded.line_count`);
      const trim = db.prepare('DELETE FROM zoho_so_lines WHERE org = ? AND salesorder_number = ? AND line_no > ?');
      for (const [so, count] of ctx.lineCounters) {
        upsertSet.run(ctx.org, so, ctx.guard.capturedAt, count);
        if (trim.run(ctx.org, so, count).changes) touched.push(so);
      }
      return touched;
    },
  },
  packages: {
    idField: 'line_no',
    dateField: 'packing_date',
    write(db, rec, ctx) {
      const r = upsertGuarded(db, { table: 'zoho_package_lines', keys: ['org', 'package_number', 'line_no'],
        fields: ['so_number', 'packing_date', 'status', 'item_name', 'sku', 'quantity_packed'], rec: { ...rec, org: ctx.org }, ...ctx.guard });
      return r.changed ? [rec.so_number, r.before?.so_number].filter(Boolean) : [];
    },
  },
  shipments: {
    idField: (rec) => `${rec.shipment_number}|${rec.line_no}`,
    dateField: 'shipment_date',
    write(db, rec, ctx) {
      const r = upsertGuarded(db, { table: 'zoho_shipment_lines', keys: ['org', 'shipment_number', 'line_no'],
        fields: ['so_number', 'packing_number', 'shipment_date', 'delivery_date', 'status', 'created_at', 'modified_at'],
        rec: { ...rec, org: ctx.org }, ...ctx.guard });
      return r.changed ? [rec.so_number, r.before?.so_number].filter(Boolean) : [];
    },
  },
  invoices_xlsx: {
    idField: 'invoice_number',     // Invoice.xlsx has one row per line; keep the first row per invoice
    dateField: 'invoice_date',
    write(db, rec, ctx) {
      const r = upsertGuarded(db, { table: 'zoho_invoices', keys: ['org', 'invoice_number'],
        fields: ['so_number', 'invoice_date', 'invoice_date_precision', 'status'], rec: { ...rec, org: ctx.org }, ...ctx.guard });
      return r.changed ? [rec.so_number, r.before?.so_number].filter(Boolean) : [];
    },
  },
  invoices_pull: {
    idField: 'invoice_number',
    dateField: 'invoice_date',
    write(db, rec, ctx) {
      const r = upsertGuarded(db, { table: 'zoho_invoices', keys: ['org', 'invoice_number'],
        fields: ['so_number', 'invoice_date', 'invoice_date_precision', 'status', 'created_at', 'modified_at'],
        rec: { ...rec, org: ctx.org }, ...ctx.guard });
      return r.changed ? [rec.so_number, r.before?.so_number].filter(Boolean) : [];
    },
  },
  bundles: {
    idField: 'zoho_id',
    dateField: 'date',
    write(db, rec, ctx) {
      const r = upsertGuarded(db, { table: 'zoho_bundles', keys: ['org', 'zoho_id'],
        fields: ['reference_number', 'so_key', 'date', 'composite_item_name', 'quantity', 'status', 'created_at', 'modified_at'],
        rec: { ...rec, org: ctx.org, so_key: soKey(rec.reference_number) }, ...ctx.guard });
      return r.changed ? [soKey(rec.reference_number), r.before?.so_key].filter(Boolean) : [];
    },
  },
  picklists: {
    idField: 'zoho_id',
    dateField: 'date',
    write(db, rec, ctx) {
      const r = upsertGuarded(db, { table: 'zoho_picklists', keys: ['org', 'zoho_id'],
        fields: ['picklist_number', 'date', 'status', 'salesorder_numbers', 'created_at', 'modified_at'], rec: { ...rec, org: ctx.org }, ...ctx.guard });
      if (!r.changed) return [];
      const oldSos = db.prepare('SELECT so_number FROM zoho_picklist_sos WHERE org = ? AND picklist_id = ?').all(ctx.org, rec.zoho_id).map((x) => x.so_number);
      db.prepare('DELETE FROM zoho_picklist_sos WHERE org = ? AND picklist_id = ?').run(ctx.org, rec.zoho_id);
      const sos = [...new Set(String(rec.salesorder_numbers ?? '').split(',').map((s) => s.trim()).filter(Boolean))];
      const ins = db.prepare('INSERT INTO zoho_picklist_sos(org, picklist_id, so_number) VALUES (?, ?, ?)');
      for (const so of sos) ins.run(ctx.org, rec.zoho_id, so);
      return [...sos, ...oldSos];
    },
  },
  items: {
    idField: 'zoho_id',
    dateField: null,
    write(db, rec, ctx) {
      upsertGuarded(db, { table: 'zoho_items', keys: ['org', 'zoho_id'], fields: ['name', 'sku', 'unit', 'status', 'is_composite', 'modified_at'],
        rec: { ...rec, org: ctx.org }, ...ctx.guard });
      return [];
    },
  },
};
```

`cli/import/run.js`:
```js
import { classifyFolder, loadCaptured } from './files.js';
import { loadColumns, mapRow, missingHeaders } from './columns.js';
import { readXlsx, readJsonArray } from './readers.js';
import { MODULE_HANDLERS } from './upsert.js';

const BATCH = 2000;
const CUTOFF = '2023-12-31T18:30:00.000Z'; // 2024-01-01 00:00 Colombo
const MOVEMENT = new Set(['packages', 'shipments']);

export function startRun(db, { org, module, source, file, capturedAt, fullList, now }) {
  return Number(db.prepare(`INSERT INTO zoho_import_runs(org, module, source, file, captured_at, full_list, started_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`).run(org, module, source, file, capturedAt, fullList ? 1 : 0, now.toISOString()).lastInsertRowid);
}

export function finishRun(db, id, { status, error = null, warnings = [], now }) {
  db.prepare('UPDATE zoho_import_runs SET status = ?, error = ?, warnings = ?, finished_at = ? WHERE id = ?')
    .run(status, error, JSON.stringify(warnings), now.toISOString(), id);
}

const previousFullCount = (db, org, module) => db.prepare(`SELECT rows_read FROM zoho_import_runs
  WHERE org = ? AND module = ? AND full_list = 1 AND finished_at IS NOT NULL AND status IN ('ok','warning')
  ORDER BY captured_at DESC LIMIT 1`).get(org, module)?.rows_read ?? null;

async function* recordsOf(file, spec) {
  if (file.format === 'json') {
    for (const raw of readJsonArray(file.path)) yield raw;
    return;
  }
  const { headers, rows } = await readXlsx(file.path);
  const missing = missingHeaders(spec, headers);
  if (missing.length) throw new Error(`missing required headers: ${missing.join(', ')}`);
  yield* rows;
}

export async function importFolder(db, { dir, org, capturedAtFlag, now, dryRun = false, afterBatch = () => {}, logger }) {
  const columns = loadColumns();
  const { files, unrecognised } = classifyFolder(dir);
  const captured = loadCaptured(dir, { capturedAtFlag, now, files });
  const results = unrecognised.map((name) => ({ name, status: 'failed', error: 'unrecognised file name' }));
  const movementMax = Math.max(0, ...files.filter((f) => MOVEMENT.has(f.module)).map((f) => Date.parse(captured.get(f.name)?.capturedAt ?? 0)));

  for (const file of files) {
    const cap = captured.get(file.name);
    if (cap.error) { results.push({ name: file.name, status: 'failed', error: cap.error }); continue; }
    const spec = columns[file.module];
    const handler = MODULE_HANDLERS[file.module];
    const warnings = [];

    // JSON pulls: de-duplicate first, then verify the full-list claim
    let fullList = false;
    let preloaded = null;
    if (file.format === 'json') {
      const seen = new Map();
      for (const raw of readJsonArray(file.path)) seen.set(raw[spec.id], raw);
      preloaded = [...seen.values()];
      if (cap.fullListClaim) {
        const prev = previousFullCount(db, org, file.module);
        if (cap.rowsClaim !== preloaded.length) warnings.push(`rows in captured.json (${cap.rowsClaim}) ≠ file (${preloaded.length}); not treated as a full list`);
        else if (prev !== null && preloaded.length < 0.98 * prev) warnings.push(`only ${preloaded.length} rows vs ${prev} last time; not treated as a full list`);
        else fullList = true;
      }
      if (file.module === 'so_headers' && Date.parse(cap.capturedAt) < movementMax) {
        warnings.push('header pull was captured before a package/shipment export in this folder; shipped figures will show as unknown');
      }
    }
    if (dryRun) { results.push({ name: file.name, status: 'dry-run', warnings }); continue; }

    const runId = startRun(db, { org, module: file.module, source: file.source, file: file.name, capturedAt: cap.capturedAt, fullList, now });
    const ctx = { org, guard: { capturedAt: cap.capturedAt, sourceFile: file.name, now, fullList: file.source === 'xlsx' ? true : fullList },
      headerSeen: new Set(), lineCounters: new Map(), lineSetAllowed: new Map() };
    const changed = new Set();
    let read = 0, skipped = 0, upserted = 0;
    let batch = [];
    const seenIds = new Set();
    const flush = db.transaction((rows) => {
      const touched = new Set();
      for (const rec of rows) for (const so of handler.write(db, rec, ctx)) touched.add(so);
      touched.forEach((so) => changed.add(so));
      upserted += rows.length;
      db.prepare('UPDATE zoho_import_runs SET rows_read = ?, rows_upserted = ?, rows_skipped = ?, changed_so_numbers = ? WHERE id = ?')
        .run(read, upserted, skipped, JSON.stringify([...changed].sort()), runId);
      afterBatch(db, org, touched);
    });
    try {
      if (preloaded?.length) {
        const miss = missingHeaders(spec, Object.keys(preloaded[0]));
        if (miss.length) throw new Error(`missing required keys: ${miss.join(', ')}`);
      }
      const source = preloaded ?? recordsOf(file, spec);
      for await (const raw of source) {
        read += 1;
        const rec = mapRow(spec, raw);
        const idf = typeof handler.idField === 'function' ? handler.idField(rec) : rec[handler.idField];
        if (handler.idField && file.format === 'xlsx' && file.module !== 'so_xlsx') {
          if (seenIds.has(idf)) { skipped += 1; continue; }
          seenIds.add(idf);
        }
        if (handler.dateField && rec[handler.dateField] && rec[handler.dateField] < CUTOFF) { skipped += 1; continue; }
        batch.push(rec);
        if (batch.length >= BATCH) { flush.immediate(batch); batch = []; }
      }
      if (batch.length || read === 0) flush.immediate(batch);
      if (handler.finish) {
        db.transaction(() => {
          const touched = new Set(handler.finish(db, ctx));
          touched.forEach((so) => changed.add(so));
          db.prepare('UPDATE zoho_import_runs SET changed_so_numbers = ? WHERE id = ?').run(JSON.stringify([...changed].sort()), runId);
          afterBatch(db, org, touched);
        }).immediate();
      }
      const status = warnings.length ? 'warning' : 'ok';
      finishRun(db, runId, { status, warnings, now });
      results.push({ name: file.name, runId, status, warnings });
    } catch (err) {
      finishRun(db, runId, { status: 'failed', error: err.message, warnings, now });
      results.push({ name: file.name, runId, status: 'failed', error: err.message, warnings });
      logger.error('import file failed', { file: file.name, error: err.message });
    }
  }
  const exitCode = results.some((r) => r.status === 'failed') ? 1 : results.some((r) => r.status === 'warning') ? 2 : 0;
  return { files: results, exitCode };
}
```

The "rows before 2024-01-01" skip applies to the xlsx SO rows too: for `so_xlsx` the date field is `order_date`, so a skipped line also skips its header (the header is only written from a kept line). In the counting test the `JOBORDER-0` row has a 2026 date, so four lines are kept.

`cli/import-zoho.js`:
```js
import 'dotenv/config';
import { parseArgs } from 'node:util';
import { loadConfig } from '../server/config.js';
import { openDb } from '../server/db/open.js';
import { migrationFiles } from '../server/db/lint-migrations.js';
import { importFolder } from './import/run.js';
import { log } from '../server/log.js';

const { values } = parseArgs({ options: {
  org: { type: 'string', default: 'SPS' }, dir: { type: 'string', multiple: true, default: [] },
  'captured-at': { type: 'string' }, 'dry-run': { type: 'boolean', default: false }, 'rebuild-facts': { type: 'boolean', default: false },
} });
if (!['SPS', 'SH'].includes(values.org)) { console.error('--org must be SPS or SH'); process.exit(1); }
const config = loadConfig();
const db = openDb(config.dbPath);
const highest = Number(migrationFiles(config.migrationsDir).at(-1).slice(0, 3));
if (db.pragma('user_version', { simple: true }) < highest) {
  console.error('The database is older than this code. Start the service once (it migrates), then import.');
  process.exit(1);
}
// Task 12 adds: assertFactsVersion(db) and the --rebuild-facts branch; Task 12 also passes afterBatch.
let code = 0;
for (const dir of values.dir) {
  const r = await importFolder(db, { dir, org: values.org, capturedAtFlag: values['captured-at'], now: new Date(), dryRun: values['dry-run'], logger: log });
  for (const f of r.files) console.log(`${dir}  ${f.name}: ${f.status}${f.error ? ` — ${f.error}` : ''}${f.warnings?.length ? ` — ${f.warnings.join('; ')}` : ''}`);
  code = code === 1 || r.exitCode === 1 ? 1 : Math.max(code, r.exitCode);
}
db.close();
process.exit(code);
```

- [ ] **Step 4: Run — expect PASS.** If the out-of-order test fails because the header row's `modified_at` is unchanged between folders, check the fixture gives each folder a different `last_modified_time` (it does); the rule is §6.2 "modified_at counts as a mapped value".
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: guarded upserts, import runs and import CLI"`

---

### Task 12: Per-SO facts, rules version and startup rebuild

**Files:**
- Create: `server/services/facts.js`, `test/facts.test.js`, `test/fixtures/zoho/make-sample.js`, `test/fixtures/zoho/sample-200.json` (generated, committed)
- Modify: `cli/import/run.js` (**facts recompute becomes the default `afterBatch`**), `cli/import-zoho.js` (version check, `--rebuild-facts`), `server/startup.js` (startup rebuild)

**Interfaces:**
- Produces:
  - `FACTS_RULES_VERSION = 1`
  - `recomputeFacts(db, org, soNumbers: Iterable<string>)` — deletes and re-inserts `zoho_so_facts` rows for those SOs using the §8.2 rules
  - `allSoNumbers(db, org) → string[]` (union over headers, lines, packages, shipments, invoices, bundles.so_key, picklist_sos)
  - `rebuildAllFacts(db) → { sos: number, ms: number }` (one `BEGIN IMMEDIATE` transaction; both orgs)
  - `ensureFactsVersion(db, logger) → boolean` (server: rebuild when `settings.facts_rules_version` ≠ constant; returns whether it rebuilt)
  - `assertFactsVersion(db)` (CLI: throws when they differ)

§8.2 rules (org = the job's org; X = SO number):

| stage | done when | done_at / precision | source_ref |
|---|---|---|---|
| 4 | header row exists | `created_at`/time, else `order_date`/date | `X` |
| 5 | a bundle with `so_key = X` and `lower(status) = 'bundled'` | earliest `created_at`/time | bundle `zoho_id` |
| 6 | a `zoho_picklist_sos` row for X | earliest picklist `created_at`/time, else its `date`/date | picklist number |
| 7 | a package line with `so_number = X` | earliest `packing_date`/**date** | package number |
| 8 | a shipment line with `so_number = X` | earliest `created_at`/time | shipment number |
| 10 | an invoice with `so_number = X` | earliest of `created_at`/time or `invoice_date`/date (compare instants; keep that row's precision) | invoice number |

- [ ] **Step 1: Failing test** — `test/facts.test.js` (AC0.20, AC0.23, and the detection rules later ACs rely on: 1.19, 1.20)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { makeDb } from './helpers/db.js';
import { importFolder } from '../cli/import/run.js';
import { recomputeFacts, rebuildAllFacts, ensureFactsVersion, assertFactsVersion, FACTS_RULES_VERSION } from '../server/services/facts.js';

const T = '2026-09-18T00:00:00.000Z';
const base = { last_synced_at: T, captured_at: T };
const ins = (db, table, row) => {
  const r = { ...base, ...row };
  db.prepare(`INSERT INTO ${table}(${Object.keys(r).join(',')}) VALUES (${Object.keys(r).map(() => '?').join(',')})`).run(...Object.values(r));
};
const facts = (db, so, org = 'SPS') => Object.fromEntries(db.prepare('SELECT stage_id, done_at, at_precision, source_ref FROM zoho_so_facts WHERE org = ? AND so_number = ?')
  .all(org, so).map((f) => [f.stage_id, f]));

test('rules per stage', () => {
  const { db, close } = makeDb();
  ins(db, 'zoho_so_headers', { org: 'SPS', salesorder_number: 'JOBORDER-08338', created_at: '2026-09-01T04:00:00.000Z', source: 'pull' });
  ins(db, 'zoho_bundles', { org: 'SPS', zoho_id: 'b1', reference_number: 'JOBORDER-08338 - C', so_key: 'JOBORDER-08338', status: 'bundled', created_at: '2026-09-03T04:00:00.000Z' });
  ins(db, 'zoho_bundles', { org: 'SPS', zoho_id: 'b2', reference_number: 'JOBORDER-083381', so_key: 'JOBORDER-083381', status: 'bundled', created_at: '2026-09-02T04:00:00.000Z' });
  ins(db, 'zoho_package_lines', { org: 'SPS', package_number: 'PKG-2', line_no: 'l2', so_number: 'JOBORDER-08338', packing_date: '2026-09-05T18:30:00.000Z' });
  ins(db, 'zoho_package_lines', { org: 'SPS', package_number: 'PKG-1', line_no: 'l1', so_number: 'JOBORDER-08338', packing_date: '2026-09-04T18:30:00.000Z' });
  ins(db, 'zoho_shipment_lines', { org: 'SPS', shipment_number: 'SHP-1', line_no: 'PKG-1', so_number: 'JOBORDER-08338', created_at: '2026-09-06T04:00:00.000Z' });
  ins(db, 'zoho_invoices', { org: 'SPS', invoice_number: 'INTRANS-1', so_number: 'JOBORDER-08338', invoice_date: '2026-09-06T18:30:00.000Z', invoice_date_precision: 'date' });
  ins(db, 'zoho_shipment_lines', { org: 'SH', shipment_number: 'SH-SHP', line_no: 'x', so_number: 'JOBORDER-09999', created_at: '2026-09-06T04:00:00.000Z' });
  recomputeFacts(db, 'SPS', ['JOBORDER-08338', 'JOBORDER-09999']);
  const f = facts(db, 'JOBORDER-08338');
  assert.deepEqual(Object.keys(f).map(Number).sort((a, b) => a - b), [4, 5, 7, 8, 10]);
  assert.equal(f[5].source_ref, 'b1');
  assert.deepEqual([f[7].done_at, f[7].at_precision, f[7].source_ref], ['2026-09-04T18:30:00.000Z', 'date', 'PKG-1']);
  assert.equal(f[10].at_precision, 'date');
  assert.deepEqual(facts(db, 'JOBORDER-09999'), {}, 'SH rows never tick SPS');
  close();
});

test('moving a bundle between SOs through the importer recomputes both (AC0.20)', async () => {
  const { db, close } = makeDb();
  const quiet = { info() {}, warn() {}, error() {} };
  const pull = (ref, at) => {
    const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pdbundle-'));
    fs.writeFileSync(path.join(d, 'zoho-pull-bundles.json'), JSON.stringify([{ bundle_id: 'b1', reference_number: ref, status: 'bundled',
      date: '2026-09-15', created_time: '2026-09-15T09:00:00+0530', last_modified_time: at.replace('+05:30', '+0530') }]));
    fs.writeFileSync(path.join(d, 'captured.json'), JSON.stringify({ 'zoho-pull-bundles.json': { captured_at: at, full_list: true, rows: 1 } }));
    return d;
  };
  const now = new Date('2026-09-18T00:00:00Z');
  await importFolder(db, { dir: pull('JOBORDER-1', '2026-09-16T08:00:00+05:30'), org: 'SPS', now, logger: quiet });  // default afterBatch
  assert.ok(facts(db, 'JOBORDER-1')[5]);
  await importFolder(db, { dir: pull('JOBORDER-2 - B', '2026-09-17T08:00:00+05:30'), org: 'SPS', now, logger: quiet });
  assert.equal(facts(db, 'JOBORDER-1')[5], undefined, 'old SO recomputed');
  assert.ok(facts(db, 'JOBORDER-2')[5], 'new SO recomputed');
  close();
});

test('incremental equals full rebuild; version rebuild runs once (AC0.20, AC0.23)', () => {
  const { db, close } = makeDb();
  for (let i = 0; i < 50; i++) {
    ins(db, 'zoho_so_headers', { org: 'SPS', salesorder_number: `JOBORDER-${i}`, order_date: T, source: 'xlsx' });
    if (i % 2) ins(db, 'zoho_package_lines', { org: 'SPS', package_number: `P${i}`, line_no: `l${i}`, so_number: `JOBORDER-${i}`, packing_date: T });
  }
  const quiet = { info() {}, warn() {} };
  // fresh DB: no stored version yet
  assert.throws(() => assertFactsVersion(db), /facts rules/);
  recomputeFacts(db, 'SPS', Array.from({ length: 50 }, (_, i) => `JOBORDER-${i}`));
  const inc = db.prepare('SELECT * FROM zoho_so_facts ORDER BY 1,2,3').all();
  assert.equal(ensureFactsVersion(db, quiet), true, 'first start rebuilds');
  assert.deepEqual(db.prepare('SELECT * FROM zoho_so_facts ORDER BY 1,2,3').all(), inc, 'rebuild equals incremental');
  assert.equal(ensureFactsVersion(db, quiet), false, 'second start does nothing');
  assert.doesNotThrow(() => assertFactsVersion(db));
  db.prepare("UPDATE settings SET value = '0' WHERE key = 'facts_rules_version'").run();
  assert.equal(ensureFactsVersion(db, quiet), true);
  assert.equal(db.prepare("SELECT value FROM settings WHERE key='facts_rules_version'").get().value, String(FACTS_RULES_VERSION));
  close();
});

test('rebuild budget on a full-size mirror: < 15 s (AC0.23)', () => {
  const { db, close } = makeDb();
  db.transaction(() => {
    for (let i = 0; i < 8500; i++) {
      const so = `JOBORDER-${i}`;
      ins(db, 'zoho_so_headers', { org: 'SPS', salesorder_number: so, created_at: T, source: 'pull' });
      ins(db, 'zoho_package_lines', { org: 'SPS', package_number: `P${i}`, line_no: `a${i}`, so_number: so, packing_date: T });
      ins(db, 'zoho_package_lines', { org: 'SPS', package_number: `P${i}`, line_no: `b${i}`, so_number: so, packing_date: T });
      ins(db, 'zoho_shipment_lines', { org: 'SPS', shipment_number: `S${i}`, line_no: `P${i}`, so_number: so, created_at: T });
      ins(db, 'zoho_invoices', { org: 'SPS', invoice_number: `I${i}`, so_number: so, created_at: T });
      ins(db, 'zoho_bundles', { org: 'SPS', zoho_id: `B${i}`, reference_number: so, so_key: so, status: 'bundled', created_at: T });
    }
  })();
  const { ms, sos } = rebuildAllFacts(db);
  assert.equal(sos, 8500);
  assert.ok(ms < 15000, `rebuild took ${ms} ms`);
  close();
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement** — `server/services/facts.js`

```js
export const FACTS_RULES_VERSION = 1;

const RULES = [
  { stage: 4, sql: `SELECT coalesce(created_at, order_date) AS at, CASE WHEN created_at IS NOT NULL THEN 'time' ELSE 'date' END AS p, salesorder_number AS ref
      FROM zoho_so_headers WHERE org = ? AND salesorder_number = ? AND coalesce(created_at, order_date) IS NOT NULL` },
  { stage: 5, sql: `SELECT created_at AS at, 'time' AS p, zoho_id AS ref FROM zoho_bundles
      WHERE org = ? AND so_key = ? AND lower(status) = 'bundled' AND created_at IS NOT NULL ORDER BY created_at LIMIT 1` },
  { stage: 6, sql: `SELECT coalesce(p.created_at, p.date) AS at, CASE WHEN p.created_at IS NOT NULL THEN 'time' ELSE 'date' END AS p, p.picklist_number AS ref
      FROM zoho_picklist_sos s JOIN zoho_picklists p ON p.org = s.org AND p.zoho_id = s.picklist_id
      WHERE s.org = ? AND s.so_number = ? AND coalesce(p.created_at, p.date) IS NOT NULL ORDER BY 1 LIMIT 1` },
  { stage: 7, sql: `SELECT packing_date AS at, 'date' AS p, package_number AS ref FROM zoho_package_lines
      WHERE org = ? AND so_number = ? AND packing_date IS NOT NULL ORDER BY packing_date, package_number LIMIT 1` },
  { stage: 8, sql: `SELECT created_at AS at, 'time' AS p, shipment_number AS ref FROM zoho_shipment_lines
      WHERE org = ? AND so_number = ? AND created_at IS NOT NULL ORDER BY created_at LIMIT 1` },
  { stage: 10, sql: `SELECT coalesce(created_at, invoice_date) AS at, CASE WHEN created_at IS NOT NULL THEN 'time' ELSE 'date' END AS p, invoice_number AS ref
      FROM zoho_invoices WHERE org = ? AND so_number = ? AND coalesce(created_at, invoice_date) IS NOT NULL ORDER BY 1 LIMIT 1` },
];

const prepared = new WeakMap();
function stmts(db) {
  if (!prepared.has(db)) {
    prepared.set(db, {
      rules: RULES.map((r) => ({ stage: r.stage, st: db.prepare(r.sql) })),
      del: db.prepare('DELETE FROM zoho_so_facts WHERE org = ? AND so_number = ?'),
      ins: db.prepare('INSERT INTO zoho_so_facts(org, so_number, stage_id, done_at, at_precision, source_ref) VALUES (?, ?, ?, ?, ?, ?)'),
    });
  }
  return prepared.get(db);
}

export function recomputeFacts(db, org, soNumbers) {
  const s = stmts(db);
  for (const so of new Set(soNumbers)) {
    if (!so) continue;
    s.del.run(org, so);
    for (const { stage, st } of s.rules) {
      const row = st.get(org, so);
      if (row) s.ins.run(org, so, stage, row.at, row.p, row.ref);
    }
  }
}

export const allSoNumbers = (db, org) => db.prepare(`
  SELECT salesorder_number AS so FROM zoho_so_headers WHERE org = ?1
  UNION SELECT salesorder_number FROM zoho_so_lines WHERE org = ?1
  UNION SELECT so_number FROM zoho_package_lines WHERE org = ?1 AND so_number IS NOT NULL
  UNION SELECT so_number FROM zoho_shipment_lines WHERE org = ?1 AND so_number IS NOT NULL
  UNION SELECT so_number FROM zoho_invoices WHERE org = ?1 AND so_number IS NOT NULL
  UNION SELECT so_key FROM zoho_bundles WHERE org = ?1 AND so_key IS NOT NULL
  UNION SELECT so_number FROM zoho_picklist_sos WHERE org = ?1`).all(org).map((r) => r.so);

export function rebuildAllFacts(db) {
  const t0 = Date.now();
  let sos = 0;
  db.transaction(() => {
    db.prepare('DELETE FROM zoho_so_facts').run();
    for (const org of ['SPS', 'SH']) {
      const list = allSoNumbers(db, org);
      sos += list.length;
      recomputeFacts(db, org, list);
    }
    db.prepare("INSERT INTO settings(key, value) VALUES ('facts_rules_version', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value")
      .run(String(FACTS_RULES_VERSION));
  }).immediate();
  return { sos, ms: Date.now() - t0 };
}

const storedVersion = (db) => db.prepare("SELECT value FROM settings WHERE key = 'facts_rules_version'").get()?.value;

export function ensureFactsVersion(db, logger) {
  if (storedVersion(db) === String(FACTS_RULES_VERSION)) return false;
  const r = rebuildAllFacts(db);
  logger.info('facts rebuilt for rules version', { version: FACTS_RULES_VERSION, ...r });
  return true;
}

export function assertFactsVersion(db) {
  if (storedVersion(db) !== String(FACTS_RULES_VERSION)) {
    throw new Error(`facts rules version differs (db ${storedVersion(db) ?? 'none'}, code ${FACTS_RULES_VERSION}); restart the service first`);
  }
}
```

Wire-up:
- `server/startup.js`: add `ensureFactsVersion(db, logger);` as the last line of `prepareDatabase` (so it runs before `startListeners`).
- `cli/import/run.js`: `import { recomputeFacts } from '../../server/services/facts.js';` and change the default parameter to `afterBatch = recomputeFacts`. Facts are then recomputed inside every upsert transaction unless a caller deliberately passes something else (spec §6.2, §8.1).
- `cli/import-zoho.js`: replace the Task 11 comment line with:

```js
import { assertFactsVersion, rebuildAllFacts } from '../server/services/facts.js';
// …
if (values['rebuild-facts']) { console.log(rebuildAllFacts(db)); db.close(); process.exit(0); }
try { assertFactsVersion(db); } catch (e) { console.error(e.message); process.exit(1); }
```

Add `test/import-cli.test.js` — the real CLI, end to end (B2):

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { makeDb } from './helpers/db.js';
import { prepareDatabase } from '../server/startup.js';
import { loadConfig } from '../server/config.js';
import { openDb } from '../server/db/open.js';

test('cli/import-zoho.js fills zoho_so_facts; refuses when the rules version differs', () => {
  const { db, file, tmp, close } = makeDb();
  prepareDatabase(db, loadConfig({ PD_MIGRATIONS_DIR: process.env.PD_MIGRATIONS_DIR }), { info() {}, warn() {}, error() {} });
  db.close();
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pdcli-'));
  fs.writeFileSync(path.join(d, 'zoho-pull-so-headers.json'), JSON.stringify([{ salesorder_id: '1', salesorder_number: 'JOBORDER-1',
    quantity_shipped: '0', created_time: '2026-09-01T10:00:00+0530', last_modified_time: '2026-09-01T10:00:00+0530', date: '2026-09-01' }]));
  fs.writeFileSync(path.join(d, 'captured.json'), JSON.stringify({ 'zoho-pull-so-headers.json': { captured_at: '2026-09-10T08:00:00+05:30', full_list: true, rows: 1 } }));
  const env = { ...process.env, DB_PATH: file };
  const ok = spawnSync(process.execPath, ['cli/import-zoho.js', '--org', 'SPS', '--dir', d], { env, encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stderr);
  const check = openDb(file);
  assert.equal(check.prepare("SELECT count(*) c FROM zoho_so_facts WHERE so_number='JOBORDER-1' AND stage_id=4").get().c, 1);
  check.prepare("UPDATE settings SET value='0' WHERE key='facts_rules_version'").run();
  check.close();
  const refused = spawnSync(process.execPath, ['cli/import-zoho.js', '--org', 'SPS', '--dir', d], { env, encoding: 'utf8' });
  assert.equal(refused.status, 1);
  assert.match(refused.stderr, /facts rules version/);
  fs.rmSync(tmp, { recursive: true, force: true });
});
```

`test/fixtures/zoho/make-sample.js` — run once by the implementer; its output `sample-200.json` is committed so tests stay offline:

```js
// node test/fixtures/zoho/make-sample.js  → test/fixtures/zoho/sample-200.json
import fs from 'node:fs';
import { readXlsx } from '../../../cli/import/readers.js';
import { soKey } from '../../../shared/text.js';

const A = '/root/exports/zoho/native/2026-09-16';
const B = '/root/exports/zoho/native/2026-09-17/sps';
const all = async (file) => { const x = await readXlsx(file); const out = []; for await (const r of x.rows) out.push(r); return out; };
import { loadColumns } from '../../../cli/import/columns.js';

const COLS = loadColumns();
const keysOf = (module) => new Set([
  ...Object.values(COLS[module].fields).flatMap((f) => f.from),
  ...COLS[module].required,
  ...(COLS[module].id ? [COLS[module].id] : []),
]);
// Keep only the mapped columns (no addresses, prices beyond the mapped ones, or free text we do not import).
const pick = (module) => (r) => Object.fromEntries(Object.entries(r).filter(([k]) => keysOf(module).has(k)));
const plain = (r) => Object.fromEntries(Object.entries(r).map(([k, v]) => {
  if (typeof v === 'number' && /ID|Date|Time/i.test(k)) throw new Error(`${k} arrived as a number (${v}); the importer expects text or a date cell`);
  return [k, v instanceof Date ? v.toISOString().slice(0, 19).replace('T', ' ') : v];
}));

const packages = await all(`${A}/Package_ALL.xlsx`);
const withPkg = new Set(packages.map((p) => p['SO Number']));
const headers = JSON.parse(fs.readFileSync(`${B}/salesorders_headers.json`, 'utf8'))
  .filter((h) => withPkg.has(h.salesorder_number) && h.date >= '2026-06-01' && h.date <= '2026-09-10')
  .sort((a, b) => b.date.localeCompare(a.date)).slice(0, 200);
const sos = new Set(headers.map((h) => h.salesorder_number));
const out = {
  so_xlsx: (await all(`${A}/Sales_Order.xlsx`)).filter((r) => sos.has(r['SalesOrder Number'])).map(plain).map(pick('so_xlsx')),
  packages: packages.filter((r) => sos.has(r['SO Number'])).map(plain).map(pick('packages')),
  shipments: (await all(`${A}/Shipment_ALL.xlsx`)).filter((r) => sos.has(r['SO Number'])).map(plain).map(pick('shipments')),
  invoices_xlsx: (await all(`${A}/Invoice.xlsx`)).filter((r) => sos.has(r['Sales Order Number'])).map(plain).map(pick('invoices_xlsx')),
  so_headers: headers.map(pick('so_headers')),
  bundles: JSON.parse(fs.readFileSync(`${B}/bundles.json`, 'utf8')).filter((b) => sos.has(soKey(b.reference_number))).map(pick('bundles')),
  invoices_pull: JSON.parse(fs.readFileSync(`${B}/invoices_headers.json`, 'utf8')).filter((i) => sos.has(i.reference_number)).map(pick('invoices_pull')),
};
fs.writeFileSync(new URL('./sample-200.json', import.meta.url), JSON.stringify(out));
console.log(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])));
```

The sample keeps only the columns the importer maps (it still contains `cf_order_received_from` customer names, which are internal company data; the repo is private). Do not copy the sample anywhere else.

Add to `test/facts.test.js` (AC0.20, "two different file orders, and one run versus split runs"):

```js
import { writeXlsx } from './helpers/xlsx.js';

const sample = JSON.parse(fs.readFileSync(new URL('./fixtures/zoho/sample-200.json', import.meta.url), 'utf8'));
const NAMES = { so_xlsx: 'Sales_Order.xlsx', packages: 'Package.xlsx', shipments: 'Shipment.xlsx', invoices_xlsx: 'Invoice.xlsx',
  so_headers: 'zoho-pull-so-headers.json', bundles: 'zoho-pull-bundles.json', invoices_pull: 'zoho-pull-invoice-headers.json' };
const IDS = { so_headers: 'salesorder_id', bundles: 'bundle_id', invoices_pull: 'invoice_id' };

async function writeFolder(modules) {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pdsample-'));
  const captured = {};
  for (const m of modules) {
    const rows = sample[m];
    if (NAMES[m].endsWith('.json')) {
      fs.writeFileSync(path.join(d, NAMES[m]), JSON.stringify(rows));
      captured[NAMES[m]] = { captured_at: '2026-09-17T12:00:00+05:30', full_list: false, rows: new Set(rows.map((r) => r[IDS[m]])).size };
    } else {
      const headers = Object.keys(rows[0]);
      await writeXlsx(path.join(d, NAMES[m]), headers, rows.map((r) => headers.map((h) => r[h] ?? null)));
      captured[NAMES[m]] = { captured_at: '2026-09-16T12:00:00+05:30' };
    }
  }
  fs.writeFileSync(path.join(d, 'captured.json'), JSON.stringify(captured));
  return d;
}

test('real 200-SO sample: one run vs split runs in reverse order give identical facts (AC0.20)', async () => {
  const quiet = { info() {}, warn() {}, error() {} };
  const now = new Date('2026-09-18T00:00:00Z');
  const opts = (dir) => ({ dir, org: 'SPS', now, logger: quiet });   // default afterBatch = recomputeFacts
  const one = makeDb();
  const noFailures = (res) => assert.deepEqual(res.files.filter((f) => f.status === 'failed'), [], JSON.stringify(res.files));
  noFailures(await importFolder(one.db, opts(await writeFolder(Object.keys(NAMES)))));
  const two = makeDb();
  noFailures(await importFolder(two.db, opts(await writeFolder(['so_headers', 'bundles', 'invoices_pull']))));
  noFailures(await importFolder(two.db, opts(await writeFolder(['invoices_xlsx', 'shipments', 'packages', 'so_xlsx']))));
  assert.ok(one.db.prepare('SELECT count(*) c FROM zoho_invoices WHERE created_at IS NOT NULL').get().c > 0, 'invoice header pull imported');
  const q = 'SELECT * FROM zoho_so_facts ORDER BY 1,2,3';
  assert.ok(one.db.prepare(q).all().length > 400);
  assert.deepEqual(two.db.prepare(q).all(), one.db.prepare(q).all());
  const before = one.db.prepare(q).all();
  rebuildAllFacts(one.db);
  assert.deepEqual(one.db.prepare(q).all(), before, '--rebuild-facts gives the same again');
  one.close(); two.close();
});
```

(The pull files here use `full_list: false`, so the full-list checks don't depend on the sample size; freshness is covered in Task 13.)

- [ ] **Step 4: Run — expect PASS.** Run `node test/fixtures/zoho/make-sample.js` once before the sample test.
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: per-SO facts with rules-version rebuild"`

---

### Task 13: Freshness, bundle data age, imports admin page API

**Files:**
- Create: `server/services/freshness.js`, `server/services/mirror-report.js`, `server/routes/admin-imports.js`, `test/freshness.test.js`
- Modify: `server/routes/index.js`

**Interfaces:**
- Consumes: Task 2 `isRecentCapture`; Task 9 `loadCalendar`.
- Produces:
  - `shippedFresh(db, org, now, cal) → { fresh: boolean, H: string|null, M: string|null, reason: 'ok'|'no_full_header'|'header_older_than_movements'|'header_too_old' }` — exactly §6.4:
    - H = `max(captured_at)` over runs with `module='so_headers'`, `full_list=1`, `finished_at IS NOT NULL`, `status IN ('ok','warning')`, same org.
    - M = `max(captured_at)` over runs with `module IN ('packages','shipments')`, same org, `rows_upserted > 0` (any status, including unfinished).
    - fresh = H not null and (M null or H ≥ M) and `isRecentCapture(H, now, cal)`.
  - `shippedState(db, org, soNumber, freshness) → 'fresh'|'stale'|'no_header'` (`no_header` when the header row is missing or `source='xlsx'`)
  - `bundlesDataAge(db, org, now, cal) → { recent: boolean, capturedAt: string|null }` (same filters as H but `module='bundles'`)
  - `crashedRuns(db, now) → runs` (`finished_at IS NULL AND started_at < now − 30 min`)
  - `unmappedDivisions(db) → [{ value, so_count }]` (in `mirror-report.js`; informational, §8.1)
  - `GET /api/admin/imports` (admin; analyst gets it in Release 4) → `{ runs: last 100, orgs: { SPS: { shipped: shippedFresh, bundles: bundlesDataAge, staleJobs: 0 } }, unmapped: unmappedDivisions, crashed, untrustedForwarded }` (`staleJobs` is filled in Release 1 when jobs exist; return the count of open jobs with a linked SO whose `shippedState` ≠ fresh — with no jobs it is 0).

- [ ] **Step 1: Failing test** — `test/freshness.test.js` (AC0.20b a, b, d, e, g, h, i2, l; AC0.9 listing)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeDb } from './helpers/db.js';
import { makeApp } from './helpers/app.js';
import { shippedFresh, shippedState, bundlesDataAge, crashedRuns } from '../server/services/freshness.js';

const cal = { weekdays: [1, 2, 3, 4, 5], holidays: new Set() };
const now = new Date('2026-09-18T06:00:00Z'); // Fri 11:30 Colombo
function runRow(db, { module, at, full = 0, status = 'ok', finished = true, rows = 1, org = 'SPS', started = at }) {
  db.prepare(`INSERT INTO zoho_import_runs(org, module, source, captured_at, full_list, status, started_at, finished_at, rows_upserted)
    VALUES (?, ?, 'x', ?, ?, ?, ?, ?, ?)`).run(org, module, at, full, finished ? status : null, started, finished ? at : null, rows);
}

test('(a) re-observed unchanged header after a shipment change → fresh', () => {
  const { db, close } = makeDb();
  runRow(db, { module: 'shipments', at: '2026-09-18T02:00:00Z' });
  runRow(db, { module: 'so_headers', at: '2026-09-18T03:00:00Z', full: 1, rows: 0 });
  assert.equal(shippedFresh(db, 'SPS', now, cal).fresh, true);
  close();
});

test('(b) header captured before a shipments capture → not fresh, whatever the import order', () => {
  for (const order of [['h', 's'], ['s', 'h']]) {
    const { db, close } = makeDb();
    for (const k of order) {
      if (k === 'h') runRow(db, { module: 'so_headers', at: '2026-09-18T02:00:00Z', full: 1 });
      else runRow(db, { module: 'shipments', at: '2026-09-18T03:00:00Z' });
    }
    const f = shippedFresh(db, 'SPS', now, cal);
    assert.equal(f.fresh, false);
    assert.equal(f.reason, 'header_older_than_movements');
    close();
  }
});

test('(d) header older than the previous working day → not fresh', () => {
  const { db, close } = makeDb();
  runRow(db, { module: 'so_headers', at: '2026-09-16T03:00:00Z', full: 1 }); // Wed; now is Fri
  assert.equal(shippedFresh(db, 'SPS', now, cal).reason, 'header_too_old');
  close();
});

test('(e) SO known only from Sales_Order.xlsx → no_header', () => {
  const { db, close } = makeDb();
  runRow(db, { module: 'so_headers', at: '2026-09-18T03:00:00Z', full: 1 });
  db.prepare("INSERT INTO zoho_so_headers(org, salesorder_number, source, last_synced_at, captured_at) VALUES ('SPS','JOBORDER-1','xlsx','x','x')").run();
  db.prepare("INSERT INTO zoho_so_headers(org, salesorder_number, source, last_synced_at, captured_at) VALUES ('SPS','JOBORDER-2','pull','x','x')").run();
  const f = shippedFresh(db, 'SPS', now, cal);
  assert.equal(shippedState(db, 'SPS', 'JOBORDER-1', f), 'no_header');
  assert.equal(shippedState(db, 'SPS', 'JOBORDER-2', f), 'fresh');
  assert.equal(shippedState(db, 'SPS', 'JOBORDER-3', f), 'no_header');
  close();
});

test('(g) warning header run counts; failed or non-full does not', () => {
  const { db, close } = makeDb();
  runRow(db, { module: 'so_headers', at: '2026-09-18T03:00:00Z', full: 1, status: 'warning' });
  assert.equal(shippedFresh(db, 'SPS', now, cal).fresh, true);
  runRow(db, { module: 'so_headers', at: '2026-09-18T04:00:00Z', full: 1, status: 'failed' });
  runRow(db, { module: 'so_headers', at: '2026-09-18T05:00:00Z', full: 0 });
  assert.equal(shippedFresh(db, 'SPS', now, cal).H, '2026-09-18T03:00:00Z');
  close();
});

test('(h) failed or unfinished shipments run that wrote rows counts for M; one that wrote none does not', () => {
  const { db, close } = makeDb();
  runRow(db, { module: 'so_headers', at: '2026-09-18T03:00:00Z', full: 1 });
  runRow(db, { module: 'shipments', at: '2026-09-18T04:00:00Z', finished: false, rows: 0 });
  assert.equal(shippedFresh(db, 'SPS', now, cal).fresh, true);
  runRow(db, { module: 'shipments', at: '2026-09-18T04:30:00Z', status: 'failed', rows: 5 });
  assert.equal(shippedFresh(db, 'SPS', now, cal).fresh, false);
  close();
});

test('(i2) unfinished full-list header run does not move H', () => {
  const { db, close } = makeDb();
  runRow(db, { module: 'so_headers', at: '2026-09-18T03:00:00Z', full: 1 });
  runRow(db, { module: 'shipments', at: '2026-09-18T04:00:00Z' });
  runRow(db, { module: 'so_headers', at: '2026-09-18T05:00:00Z', full: 1, finished: false });
  assert.equal(shippedFresh(db, 'SPS', now, cal).fresh, false);
  close();
});

test('(l) weekend and holiday captures', () => {
  const { db, close } = makeDb();
  const hol = { weekdays: [1, 2, 3, 4, 5], holidays: new Set(['2026-09-21']) };
  runRow(db, { module: 'so_headers', at: '2026-09-20T03:00:00Z', full: 1 }); // Sunday
  assert.equal(shippedFresh(db, 'SPS', new Date('2026-09-22T03:00:00Z'), hol).fresh, true); // Tue after holiday Mon
  close();
});

test('bundles data age and crashed runs', () => {
  const { db, close } = makeDb();
  assert.equal(bundlesDataAge(db, 'SPS', now, cal).recent, false);
  runRow(db, { module: 'bundles', at: '2026-09-17T03:00:00Z', full: 1 });
  assert.equal(bundlesDataAge(db, 'SPS', now, cal).recent, true);
  runRow(db, { module: 'packages', at: '2026-09-18T05:00:00Z', finished: false, started: '2026-09-18T05:00:00Z' });
  assert.equal(crashedRuns(db, now).length, 1);
  close();
});

test('GET /api/admin/imports lists unmapped values and freshness', async () => {
  const t = makeApp();
  t.db.prepare("INSERT INTO zoho_so_headers(org, salesorder_number, cf_manufacturing_division, source, last_synced_at, captured_at) VALUES ('SPS','J1','Mystery Unit','pull','x','x')").run();
  const a = await t.login('admin1');
  const r = await a.get('/api/admin/imports');
  assert.equal(r.status, 200);
  assert.deepEqual(r.body.unmapped, [{ value: 'Mystery Unit', so_count: 1 }]);
  assert.equal(r.body.orgs.SPS.shipped.fresh, false);
  t.close();
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement** — `server/services/freshness.js`

```js
import { isRecentCapture } from '../../shared/time.js';

const maxHeader = (db, org, module) => db.prepare(`SELECT max(captured_at) AS t FROM zoho_import_runs
  WHERE org = ? AND module = ? AND full_list = 1 AND finished_at IS NOT NULL AND status IN ('ok','warning')`).get(org, module).t;

export function shippedFresh(db, org, now, cal) {
  const H = maxHeader(db, org, 'so_headers');
  const M = db.prepare(`SELECT max(captured_at) AS t FROM zoho_import_runs
    WHERE org = ? AND module IN ('packages','shipments') AND rows_upserted > 0`).get(org).t;
  if (!H) return { fresh: false, H, M, reason: 'no_full_header' };
  if (M && Date.parse(H) < Date.parse(M)) return { fresh: false, H, M, reason: 'header_older_than_movements' };
  if (!isRecentCapture(H, now, cal)) return { fresh: false, H, M, reason: 'header_too_old' };
  return { fresh: true, H, M, reason: 'ok' };
}

export function shippedState(db, org, soNumber, freshness) {
  const row = db.prepare('SELECT source FROM zoho_so_headers WHERE org = ? AND salesorder_number = ?').get(org, soNumber);
  if (!row || row.source === 'xlsx') return 'no_header';
  return freshness.fresh ? 'fresh' : 'stale';
}

export function bundlesDataAge(db, org, now, cal) {
  const t = maxHeader(db, org, 'bundles');
  return { recent: Boolean(t) && isRecentCapture(t, now, cal), capturedAt: t };
}

export const crashedRuns = (db, now) => db.prepare(`SELECT * FROM zoho_import_runs
  WHERE finished_at IS NULL AND started_at < ? ORDER BY id`).all(new Date(now.getTime() - 30 * 60e3).toISOString());
```

`server/services/mirror-report.js`:
```js
// Division values in the mirror with no alias. Import already collapsed whitespace (cleanText),
// so SQL lower() gives the same key as shared/text.js cmpKey().
export const unmappedDivisions = (db) => db.prepare(`
  SELECT h.cf_manufacturing_division AS value, count(*) AS so_count FROM zoho_so_headers h
  WHERE h.cf_manufacturing_division IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM division_aliases a WHERE a.zoho_key = lower(h.cf_manufacturing_division))
  GROUP BY h.cf_manufacturing_division ORDER BY so_count DESC`).all();
```

`server/routes/admin-imports.js`:
```js
import { Router } from 'express';
import { requireRole } from '../auth/middleware.js';
import { shippedFresh, bundlesDataAge, crashedRuns } from '../services/freshness.js';
import { loadCalendar } from '../services/calendar.js';
import { unmappedDivisions } from '../services/mirror-report.js';

export function adminImportRoutes() {
  const r = Router();
  r.get('/admin/imports', requireRole('admin'), (req, res) => {
    const { db, clock, stats } = req.app.locals;
    const now = clock.now();
    const cal = loadCalendar(db);
    const orgs = {};
    for (const org of ['SPS', 'SH']) {
      orgs[org] = { shipped: shippedFresh(db, org, now, cal), bundles: bundlesDataAge(db, org, now, cal), staleJobs: 0 };
    }
    res.json({
      runs: db.prepare('SELECT * FROM zoho_import_runs ORDER BY id DESC LIMIT 100').all()
        .map((x) => ({ ...x, changed_so_numbers: undefined, changed_count: JSON.parse(x.changed_so_numbers).length, warnings: JSON.parse(x.warnings) })),
      orgs,
      unmapped: unmappedDivisions(db),
      crashed: crashedRuns(db, now),
      untrustedForwarded: stats.untrustedForwarded,
    });
  });
  return r;
}
```

Mount `['/api', adminImportRoutes()]` in `server/routes/index.js` **before** `adminUserRoutes()`, so Release 4 can open it to `analyst` without touching the admin-wide guard.

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: capture-time freshness and imports admin API"`

---

### Task 14: Post-import sweep

**Files:**
- Create: `server/services/sweep.js`, `test/sweep.test.js`
- Modify: `server/app.js` (start the timer after listening)

**Interfaces:**
- Consumes: jobs tables from Task 3; `sse` from Task 7.
- Produces:
  - `resolvePendingLink(db, jobId, now) → boolean` — inside `BEGIN IMMEDIATE`: the job's highest-id `job_so_links` row must be `link_pending`; if the SO exists in `zoho_so_headers` for `jobs.org`, insert a `link` row (`actor_type='system'`, `note='resolved by import'`) and return true.
  - `rematchReferences(db, now, changedByOrg: Map<org, Set<so>>) → number` — for every **current** (not superseded), non-voided `reference_entries` row in section `shipments` or `itn` with no `reference_matches` row, **on a job whose current linked SO is in the processed runs' changed SOs**: find the job's current `link` SO; `shipments` matches `zoho_shipment_lines(org, so_number, shipment_number = reference_no)`; `itn` matches `zoho_invoices(org, so_number, invoice_number = reference_no)` (compare with `upper(trim())`); insert `reference_matches(actor_type='system')` inside `BEGIN IMMEDIATE`, re-checking the row is still current.
  - `runSweep(db, { now, notify = () => {} }) → { runs, links, matches }` — the §4 steps in order; `notify({ type: 'job', job_id })` for every job whose linked or pending SO is in the processed runs' `changed_so_numbers`, and for every job whose link was resolved.
  - `startSweepTimer({ db, clock, intervalMs, notify, logger }) → stop()` — runs once immediately, then every `intervalMs`; errors are logged, never thrown.
  - `jobNotifier(sse) → notify` — Release 0 sends job events to connections of users with the `admin` role only (Release 1 replaces the filter with the job-scope rule).

- [ ] **Step 1: Failing test** — `test/sweep.test.js` (AC0.21)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeDb } from './helpers/db.js';
import { runSweep, resolvePendingLink } from '../server/services/sweep.js';

const now = new Date('2026-09-18T06:00:00Z');
function setup() {
  const t = makeDb();
  const { db } = t;
  db.prepare("INSERT INTO users(username, display_name, password_hash, created_at) VALUES ('c','C','x','x')").run();
  const job = (n) => Number(db.prepare("INSERT INTO jobs(job_no, division_code, order_type, created_by, created_at) VALUES (?, 'OPD', 'customised', 1, 'x')").run(n).lastInsertRowid);
  const link = (jobId, action, so) => db.prepare("INSERT INTO job_so_links(job_id, action, salesorder_number, actor_type, actor_id, at) VALUES (?, ?, ?, 'user', 1, 'x')").run(jobId, action, so);
  const header = (so) => db.prepare("INSERT INTO zoho_so_headers(org, salesorder_number, source, last_synced_at, captured_at) VALUES ('SPS', ?, 'pull', 'x', 'x')").run(so);
  const run = (id, finished, changed) => db.prepare(`INSERT INTO zoho_import_runs(id, org, module, source, captured_at, status, started_at, finished_at, changed_so_numbers)
    VALUES (?, 'SPS', 'so_headers', 'pull', 'x', ?, 'x', ?, ?)`).run(id, finished ? 'ok' : null, finished ? 'x' : null, JSON.stringify(changed));
  return { ...t, job, link, header, run };
}
const latest = (db, jobId) => db.prepare('SELECT action, actor_type FROM job_so_links WHERE job_id = ? ORDER BY id DESC LIMIT 1').get(jobId);

test('out-of-order and offline runs are all processed; pending links resolve (AC0.21)', () => {
  const s = setup();
  const j1 = s.job('A'); const j2 = s.job('B');
  s.link(j1, 'link_pending', 'JOBORDER-1'); s.link(j2, 'link_pending', 'JOBORDER-2');
  s.header('JOBORDER-1'); s.header('JOBORDER-2');
  s.run(5, true, ['JOBORDER-2']);   // higher id finished first
  s.run(4, false, []);              // still running
  const events = [];
  let r = runSweep(s.db, { now, notify: (e) => events.push(e) });
  assert.equal(r.runs, 1);
  assert.equal(latest(s.db, j1).action, 'link');
  assert.equal(latest(s.db, j2).actor_type, 'system');
  assert.ok(events.some((e) => e.job_id === j2));
  s.db.prepare("UPDATE zoho_import_runs SET status='failed', finished_at='y' WHERE id=4").run();  // lower id finishes later, failed
  r = runSweep(s.db, { now });
  assert.equal(r.runs, 1);
  assert.equal(s.db.prepare('SELECT count(*) c FROM zoho_import_runs WHERE processed_at IS NULL').get().c, 0);
  s.close();
});

test('an unlink written after the import is never overwritten', () => {
  const s = setup();
  const j = s.job('A');
  s.link(j, 'link_pending', 'JOBORDER-1');
  s.header('JOBORDER-1');
  s.link(j, 'unlink', null);
  s.run(1, true, ['JOBORDER-1']);
  runSweep(s.db, { now });
  assert.equal(latest(s.db, j).action, 'unlink');
  assert.equal(resolvePendingLink(s.db, j, now), false);
  s.close();
});

test('pending link for an SO not yet in the mirror stays pending; sweep is idempotent', () => {
  const s = setup();
  const j = s.job('A');
  s.link(j, 'link_pending', 'JOBORDER-404');
  s.run(1, true, []);
  runSweep(s.db, { now });
  runSweep(s.db, { now });
  assert.equal(latest(s.db, j).action, 'link_pending');
  assert.equal(s.db.prepare('SELECT count(*) c FROM job_so_links WHERE job_id = ?').get(j).c, 1);
  s.close();
});

test('a link resolved by the sweep gets its references matched in the same sweep', () => {
  const s = setup();
  const j = s.job('A');
  s.link(j, 'link_pending', 'JOBORDER-7');
  s.db.prepare("INSERT INTO reference_entries(job_id, section, reference_no, qty, entered_by, entered_at) VALUES (?, 'shipments', 'SPSSHP-7', 5, 1, 'x')").run(j);
  s.header('JOBORDER-7');
  s.db.prepare("INSERT INTO zoho_shipment_lines(org, shipment_number, line_no, so_number, last_synced_at, captured_at) VALUES ('SPS','SPSSHP-7','PKG-7','JOBORDER-7','x','x')").run();
  const r = runSweep(s.db, { now });   // no runs at all
  assert.equal(r.links, 1);
  assert.equal(r.matches, 1);
  s.close();
});

test('reference rows are matched by the sweep; entry and approvals untouched', () => {
  const s = setup();
  const j = s.job('A');
  s.link(j, 'link', 'JOBORDER-1');
  const ref = Number(s.db.prepare("INSERT INTO reference_entries(job_id, section, reference_no, qty, entered_by, entered_at) VALUES (?, 'shipments', 'spsshp-1', 10, 1, 'x')").run(j).lastInsertRowid);
  s.db.prepare("INSERT INTO reference_approvals(reference_entry_id, decision, actor_id, at) VALUES (?, 'approved', 1, 'x')").run(ref);
  runSweep(s.db, { now });
  assert.equal(s.db.prepare('SELECT count(*) c FROM reference_matches').get().c, 0);
  s.db.prepare("INSERT INTO zoho_shipment_lines(org, shipment_number, line_no, so_number, last_synced_at, captured_at) VALUES ('SPS','SPSSHP-1','PKG-1','JOBORDER-1','x','x')").run();
  s.run(1, true, ['JOBORDER-1']);
  const r = runSweep(s.db, { now });
  assert.equal(r.matches, 1);
  assert.deepEqual(s.db.prepare('SELECT zoho_ref, actor_type FROM reference_matches').get(), { zoho_ref: 'SPSSHP-1', actor_type: 'system' });
  assert.equal(s.db.prepare('SELECT count(*) c FROM reference_entries').get().c, 1);
  assert.equal(s.db.prepare('SELECT count(*) c FROM reference_approvals').get().c, 1);
  s.close();
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement** — `server/services/sweep.js`

```js
const nowIso = (now) => now.toISOString();

export function resolvePendingLink(db, jobId, now) {
  return db.transaction(() => {
    const last = db.prepare('SELECT * FROM job_so_links WHERE job_id = ? ORDER BY id DESC LIMIT 1').get(jobId);
    if (!last || last.action !== 'link_pending') return false;
    const job = db.prepare('SELECT org FROM jobs WHERE id = ?').get(jobId);
    const exists = db.prepare('SELECT 1 FROM zoho_so_headers WHERE org = ? AND salesorder_number = ?').get(job.org, last.salesorder_number);
    if (!exists) return false;
    db.prepare(`INSERT INTO job_so_links(job_id, action, salesorder_number, actor_type, actor_id, at, note)
      VALUES (?, 'link', ?, 'system', NULL, ?, 'resolved by import')`).run(jobId, last.salesorder_number, nowIso(now));
    return true;
  }).immediate();
}

const pendingJobIds = (db) => db.prepare(`SELECT l.job_id FROM job_so_links l
  WHERE l.id = (SELECT max(id) FROM job_so_links WHERE job_id = l.job_id) AND l.action = 'link_pending'`).all().map((r) => r.job_id);

const MATCHERS = {
  shipments: `SELECT shipment_number AS ref FROM zoho_shipment_lines WHERE org = ? AND so_number = ? AND upper(trim(shipment_number)) = upper(trim(?)) LIMIT 1`,
  itn: `SELECT invoice_number AS ref FROM zoho_invoices WHERE org = ? AND so_number = ? AND upper(trim(invoice_number)) = upper(trim(?)) LIMIT 1`,
};

// Only jobs whose current SO changed in the runs being processed can gain a match (entry-time
// matching in Release 3 covers the rest), so the sweep stays cheap however many rows stay unmatched.
export function rematchReferences(db, now, changedByOrg) {
  const pairs = [...changedByOrg].flatMap(([org, sos]) => [...sos].map((so) => ({ org, so })));
  if (!pairs.length) return 0;
  const candidates = db.prepare(`SELECT e.id, e.job_id, e.section, e.reference_no FROM reference_entries e
    JOIN jobs j ON j.id = e.job_id
    JOIN job_so_links l ON l.job_id = e.job_id AND l.id = (SELECT max(id) FROM job_so_links WHERE job_id = e.job_id)
    WHERE e.section IN ('shipments','itn') AND e.voided = 0 AND l.action = 'link'
      AND EXISTS (SELECT 1 FROM json_each(?) p WHERE json_extract(p.value, '$.org') = j.org AND json_extract(p.value, '$.so') = l.salesorder_number)
      AND NOT EXISTS (SELECT 1 FROM reference_entries n WHERE n.supersedes_id = e.id)
      AND NOT EXISTS (SELECT 1 FROM reference_matches m WHERE m.reference_entry_id = e.id)`).all(JSON.stringify(pairs));
  let n = 0;
  for (const c of candidates) {
    const done = db.transaction(() => {
      const stillCurrent = !db.prepare('SELECT 1 FROM reference_entries WHERE supersedes_id = ?').get(c.id)
        && !db.prepare('SELECT 1 FROM reference_matches WHERE reference_entry_id = ?').get(c.id);
      if (!stillCurrent) return false;
      const link = db.prepare('SELECT action, salesorder_number FROM job_so_links WHERE job_id = ? ORDER BY id DESC LIMIT 1').get(c.job_id);
      if (link?.action !== 'link') return false;
      const org = db.prepare('SELECT org FROM jobs WHERE id = ?').get(c.job_id).org;
      const hit = db.prepare(MATCHERS[c.section]).get(org, link.salesorder_number, c.reference_no);
      if (!hit) return false;
      db.prepare("INSERT INTO reference_matches(reference_entry_id, zoho_ref, actor_type, at) VALUES (?, ?, 'system', ?)").run(c.id, hit.ref, nowIso(now));
      return true;
    }).immediate();
    if (done) n += 1;
  }
  return n;
}

export function runSweep(db, { now, notify = () => {} }) {
  const runs = db.prepare('SELECT id, org, changed_so_numbers FROM zoho_import_runs WHERE finished_at IS NOT NULL AND processed_at IS NULL').all();
  let links = 0;
  const changedByOrg = new Map();
  const addSo = (org, so) => { const set = changedByOrg.get(org) ?? new Set(); set.add(so); changedByOrg.set(org, set); };
  for (const jobId of pendingJobIds(db)) {
    if (resolvePendingLink(db, jobId, now)) {
      links += 1;
      const j = db.prepare(`SELECT j.org, l.salesorder_number AS so FROM jobs j JOIN job_so_links l ON l.job_id = j.id
        WHERE j.id = ? ORDER BY l.id DESC LIMIT 1`).get(jobId);
      addSo(j.org, j.so);          // a just-resolved link can match references whose shipment already exists
      notify({ type: 'job', job_id: jobId });
    }
  }
  for (const run of runs) JSON.parse(run.changed_so_numbers).forEach((so) => addSo(run.org, so));
  const matches = rematchReferences(db, now, changedByOrg);
  for (const run of runs) {
    const changed = JSON.parse(run.changed_so_numbers);
    if (changed.length) {
      const jobs = db.prepare(`SELECT DISTINCT l.job_id FROM job_so_links l JOIN jobs j ON j.id = l.job_id
        WHERE j.org = ? AND l.id = (SELECT max(id) FROM job_so_links WHERE job_id = l.job_id)
          AND l.salesorder_number IN (SELECT value FROM json_each(?))`).all(run.org, run.changed_so_numbers);
      for (const { job_id } of jobs) notify({ type: 'job', job_id });
    }
    db.prepare('UPDATE zoho_import_runs SET processed_at = ? WHERE id = ?').run(nowIso(now), run.id);
  }
  return { runs: runs.length, links, matches };
}

export function jobNotifier(sse) {
  return (event) => sse.send((c) => c.roles?.includes('admin'), event);
}

export function startSweepTimer({ db, clock, intervalMs, notify, logger }) {
  const tick = () => {
    try { runSweep(db, { now: clock.now(), notify }); } catch (err) { logger.error('sweep failed', { error: err.message }); }
  };
  tick();
  const timer = setInterval(tick, intervalMs);
  return () => clearInterval(timer);
}
```

`server/app.js`: after `startListeners(...)`:
```js
import { startSweepTimer, jobNotifier } from './services/sweep.js';
const stopSweep = startSweepTimer({ db, clock: { now: () => new Date() }, intervalMs: config.sweepIntervalMs, notify: jobNotifier(sse), logger: log });
// and call stopSweep() first in shutdown()
```

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: server-owned post-import sweep"`

---
### Task 15: Backups and the monthly restore check

**Files:**
- Create: `cli/backup.js`, `cli/restore-check.js`, `cli/lib/backup.js`, `test/backup.test.js`

**Interfaces:**
- Produces (`cli/lib/backup.js`):
  - `tableCounts(db) → { [table]: number }` (all non-`sqlite_` tables)
  - `makeBackup({ db, backupsDir, filesDir, now, keep = 14 }) → Promise<{ file, counts }>` — `await db.backup(file)` to `production-YYYYMMDD-HHMMSS.db` (Colombo wall time in the name); opens the copy read-only, requires `PRAGMA integrity_check` = `ok`, writes `<file>.counts.json`; prunes to the newest `keep` backups (and their sidecars); copies every file in `filesDir` missing from `backupsDir/files/`.
  - `restoreCheck({ backupsDir, tmpDir }) → { file, ok, integrity, mismatches: [{table, expected, got}] }` — copies the newest backup to `tmpDir`, opens it, runs `integrity_check`, compares counts with the sidecar.
- CLI: `node cli/backup.js` (exit 1 on failure; prints the file), `node cli/restore-check.js` (prints a table; exit 1 on any mismatch).

- [ ] **Step 1: Failing test** — `test/backup.test.js` (AC0.11, 0.11b)

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { makeDb } from './helpers/db.js';
import { makeBackup, restoreCheck } from '../cli/lib/backup.js';

test('backup: integrity ok, sidecar counts, pruned to 14, files copied; restore check matches', async () => {
  const { db, tmp, close } = makeDb();
  const backupsDir = path.join(tmp, 'backups');
  const filesDir = path.join(tmp, 'files');
  fs.mkdirSync(filesDir, { recursive: true });
  fs.writeFileSync(path.join(filesDir, 'abc'), 'x');
  db.prepare("INSERT INTO teams(name) VALUES ('Sales')").run();
  let last;
  for (let i = 0; i < 16; i++) {
    last = await makeBackup({ db, backupsDir, filesDir, now: new Date(Date.UTC(2026, 8, 1 + i, 20)) });
  }
  const dbs = fs.readdirSync(backupsDir).filter((f) => f.endsWith('.db'));
  assert.equal(dbs.length, 14);
  assert.equal(fs.readdirSync(backupsDir).filter((f) => f.endsWith('.counts.json')).length, 14);
  assert.deepEqual(fs.readdirSync(backupsDir).filter((f) => /-(wal|shm)$/.test(f)), []);
  assert.equal(last.counts.teams, 1);
  assert.ok(fs.existsSync(path.join(backupsDir, 'files', 'abc')));
  const rc = restoreCheck({ backupsDir, tmpDir: path.join(tmp, 'rc') });
  assert.equal(rc.ok, true);
  assert.equal(rc.integrity, 'ok');
  assert.deepEqual(rc.mismatches, []);
  const counts = JSON.parse(fs.readFileSync(`${rc.file}.counts.json`, 'utf8'));
  counts.teams = 5;
  fs.writeFileSync(`${rc.file}.counts.json`, JSON.stringify(counts));
  assert.equal(restoreCheck({ backupsDir, tmpDir: path.join(tmp, 'rc2') }).ok, false);
  close();
});
```

- [ ] **Step 2: Run — expect FAIL.**
- [ ] **Step 3: Implement** — `cli/lib/backup.js`

```js
import fs from 'node:fs';
import path from 'node:path';
import Database from 'better-sqlite3';

const pad = (n) => String(n).padStart(2, '0');
const stamp = (now) => {
  const d = new Date(now.getTime() + 5.5 * 3600e3);
  return `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}-${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}${pad(d.getUTCSeconds())}`;
};

export const tableCounts = (db) => Object.fromEntries(
  db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name").all()
    .map(({ name }) => [name, db.prepare(`SELECT count(*) AS c FROM "${name}"`).get().c]));

export async function makeBackup({ db, backupsDir, filesDir, now, keep = 14 }) {
  fs.mkdirSync(backupsDir, { recursive: true });
  const file = path.join(backupsDir, `production-${stamp(now)}.db`);
  await db.backup(file);
  // The copy inherits WAL mode; switch it to a single self-contained file before checking it.
  const rw = new Database(file);
  rw.pragma('journal_mode = DELETE');
  rw.close();
  const copy = new Database(file, { readonly: true });
  try {
    const integrity = copy.pragma('integrity_check', { simple: true });
    if (integrity !== 'ok') throw new Error(`backup integrity_check: ${integrity}`);
    const counts = tableCounts(copy);
    fs.writeFileSync(`${file}.counts.json`, JSON.stringify(counts, null, 2));
    const all = fs.readdirSync(backupsDir).filter((f) => /^production-\d{8}-\d{6}\.db$/.test(f)).sort();
    for (const old of all.slice(0, Math.max(0, all.length - keep))) {
      fs.rmSync(path.join(backupsDir, old), { force: true });
      for (const ext of ['.counts.json', '-wal', '-shm']) fs.rmSync(path.join(backupsDir, `${old}${ext}`), { force: true });
    }
    if (fs.existsSync(filesDir)) {
      const target = path.join(backupsDir, 'files');
      fs.mkdirSync(target, { recursive: true });
      for (const f of fs.readdirSync(filesDir)) {
        const dest = path.join(target, f);
        if (!fs.existsSync(dest)) fs.copyFileSync(path.join(filesDir, f), dest, fs.constants.COPYFILE_EXCL);
      }
    }
    return { file, counts };
  } finally {
    copy.close();
  }
}

export function restoreCheck({ backupsDir, tmpDir }) {
  const all = fs.readdirSync(backupsDir).filter((f) => /^production-\d{8}-\d{6}\.db$/.test(f)).sort();
  if (!all.length) throw new Error('no backups found');
  const file = path.join(backupsDir, all.at(-1));
  fs.mkdirSync(tmpDir, { recursive: true });
  const restored = path.join(tmpDir, 'restore-check.db');
  fs.copyFileSync(file, restored);
  const db = new Database(restored, { readonly: true });
  try {
    const integrity = db.pragma('integrity_check', { simple: true });
    const expected = JSON.parse(fs.readFileSync(`${file}.counts.json`, 'utf8'));
    const got = tableCounts(db);
    const mismatches = Object.keys({ ...expected, ...got })
      .filter((t) => expected[t] !== got[t]).map((t) => ({ table: t, expected: expected[t], got: got[t] }));
    return { file, ok: integrity === 'ok' && mismatches.length === 0, integrity, mismatches };
  } finally {
    db.close();
    fs.rmSync(restored, { force: true });
  }
}
```

`cli/backup.js`:
```js
import 'dotenv/config';
import { loadConfig } from '../server/config.js';
import { openDb } from '../server/db/open.js';
import { makeBackup } from './lib/backup.js';

const config = loadConfig();
const db = openDb(config.dbPath);
try {
  const { file } = await makeBackup({ db, backupsDir: config.backupsDir, filesDir: config.filesDir, now: new Date() });
  console.log(`backup ok: ${file}`);
} catch (err) {
  console.error(`backup FAILED: ${err.message}`);
  process.exitCode = 1;
} finally {
  db.close();
}
```

`cli/restore-check.js`:
```js
import 'dotenv/config';
import os from 'node:os';
import path from 'node:path';
import { loadConfig } from '../server/config.js';
import { restoreCheck } from './lib/backup.js';

const config = loadConfig();
const r = restoreCheck({ backupsDir: config.backupsDir, tmpDir: path.join(os.tmpdir(), 'pd-restore-check') });
console.log(`${r.file}\nintegrity: ${r.integrity}`);
for (const m of r.mismatches) console.log(`MISMATCH ${m.table}: expected ${m.expected}, got ${m.got}`);
console.log(r.ok ? 'restore check OK' : 'restore check FAILED');
process.exitCode = r.ok ? 0 : 1;
```

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: nightly backup and restore check"`

---

### Task 16: Zoho header-pull snippet and `captured.json` helper

**Files:**
- Create: `tools/zoho-pull-snippet.js`, `cli/captured.js`, `test/captured-cli.test.js`, `test/e2e/playwright.config.js`, `test/e2e/pull-snippet.spec.js`

**Interfaces:**
- Produces:
  - Browser snippet defining `window.zohoPull({ orgId, apiBase = '', perPage = 200, download = true }) → Promise<{ files: {name, rows}[], captured }>`. It runs automatically when pasted (`zohoPull({ orgId: '843825512' })`) unless `window.__ZOHO_PULL_NO_AUTORUN` is set. For each module it GETs `${apiBase}/api/v1/<module>?organization_id=<orgId>&per_page=<perPage>&page=<n>` with header `X-ZCSRF-TOKEN: zomcsparam=<value of the zomcsr cookie>` and `credentials: 'include'`, until `page_context.has_more_page` is false; de-duplicates by id; any non-OK response or missing `page_context` stops that module and marks it `full_list: false`. Modules: `salesorders` (key `salesorders`, id `salesorder_id`) → `zoho-pull-so-headers.json`; `bundles` (key `bundles`, id `bundle_id`) → `zoho-pull-bundles.json`; `invoices` (key `invoices`, id `invoice_id`) → `zoho-pull-invoice-headers.json`. `captured_at` = the pull's **start** time as ISO with `+05:30`. Downloads the three files plus `captured-pull.json`.
  - `node cli/captured.js --dir <d> [--merge <file>] [--set <name>=<iso>]…` — writes/merges `<d>/captured.json`; `--set` entries get `full_list: false`; refuses a `--set` for a `zoho-pull-*` name; validates times with `parseZohoTime`.

- [ ] **Step 1: Failing tests**

`test/captured-cli.test.js`:
```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const cli = (...args) => execFileSync(process.execPath, ['cli/captured.js', ...args], { encoding: 'utf8' });

test('merge snippet entries and set UI export times', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pdcap-'));
  fs.writeFileSync(path.join(d, 'captured-pull.json'), JSON.stringify({ 'zoho-pull-so-headers.json': { captured_at: '2026-09-18T09:00:00+05:30', full_list: true, rows: 8325 } }));
  cli('--dir', d, '--merge', path.join(d, 'captured-pull.json'), '--set', 'Sales_Order.xlsx=2026-09-18T08:30:00+05:30', '--set', 'Package.xlsx=2026-09-18T08:35:00+05:30');
  const c = JSON.parse(fs.readFileSync(path.join(d, 'captured.json'), 'utf8'));
  assert.equal(c['zoho-pull-so-headers.json'].rows, 8325);
  assert.deepEqual(c['Package.xlsx'], { captured_at: '2026-09-18T08:35:00+05:30', full_list: false });
  assert.throws(() => cli('--dir', d, '--set', 'zoho-pull-bundles.json=2026-09-18T08:30:00+05:30'), /Command failed/);
  assert.throws(() => cli('--dir', d, '--set', 'Invoice.xlsx=yesterday'), /Command failed/);
});
```

`test/e2e/playwright.config.js`:
```js
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: '.',
  timeout: 30_000,
  use: { acceptDownloads: true },
  projects: [
    { name: 'desk', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
  ],
  webServer: {
    command: 'node test/e2e/serve.js',
    url: 'http://localhost:4391/api/health',
    reuseExistingServer: false,
    cwd: '../..',
  },
});
```

`test/e2e/pull-snippet.spec.js` (AC0.25):
```js
import { test, expect } from '@playwright/test';
import fs from 'node:fs';

const SNIPPET = fs.readFileSync(new URL('../../tools/zoho-pull-snippet.js', import.meta.url), 'utf8');
const BASE = 'http://zoho.test';

function stub(page, { failBundlesAt } = {}) {
  const methods = [];
  const pages = {
    salesorders: [[{ salesorder_id: '1' }, { salesorder_id: '2' }], [{ salesorder_id: '2' }, { salesorder_id: '3' }]], // '2' repeats
    bundles: [[{ bundle_id: 'b1' }], [{ bundle_id: 'b2' }]],
    invoices: [[{ invoice_id: 'i1' }]],
  };
  page.route(`${BASE}/**`, (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === '/') return route.fulfill({ contentType: 'text/html', body: '<html><body>zoho</body></html>' });
    methods.push(route.request().method());
    expect(route.request().headers()['x-zcsrf-token']).toBe('zomcsparam=tok123');
    const module = url.pathname.split('/').pop();
    const n = Number(url.searchParams.get('page'));
    if (module === 'bundles' && failBundlesAt === n) return route.fulfill({ status: 500, body: '{}' });
    const list = pages[module];
    return route.fulfill({ contentType: 'application/json',
      body: JSON.stringify({ [module]: list[n - 1], page_context: { page: n, has_more_page: n < list.length } }) });
  });
  return methods;
}

async function runSnippet(page) {
  await page.goto(`${BASE}/`);
  await page.evaluate(() => { document.cookie = 'zomcsr=tok123'; window.__ZOHO_PULL_NO_AUTORUN = true; });
  await page.addScriptTag({ content: SNIPPET });
  const downloads = [];
  const allFour = new Promise((resolve) => page.on('download', (d) => { downloads.push(d); if (downloads.length === 4) resolve(); }));
  const result = await page.evaluate((base) => window.zohoPull({ orgId: '843825512', apiBase: base }), BASE);
  await allFour;
  return { result, downloads };
}

test('GET only, pages to the end, de-duplicates, writes captured entries', async ({ page }) => {
  const methods = stub(page);
  const { result, downloads } = await runSnippet(page);
  expect(new Set(methods)).toEqual(new Set(['GET']));
  const cap = result.captured;
  expect(cap['zoho-pull-so-headers.json']).toMatchObject({ full_list: true, rows: 3 });
  expect(cap['zoho-pull-bundles.json']).toMatchObject({ full_list: true, rows: 2 });
  expect(cap['zoho-pull-so-headers.json'].captured_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+05:30$/);
  expect(downloads.map((d) => d.suggestedFilename()).sort()).toEqual(
    ['captured-pull.json', 'zoho-pull-bundles.json', 'zoho-pull-invoice-headers.json', 'zoho-pull-so-headers.json']);
});

test('an error mid-way gives full_list false', async ({ page }) => {
  stub(page, { failBundlesAt: 2 });
  const { result } = await runSnippet(page);
  expect(result.captured['zoho-pull-bundles.json'].full_list).toBe(false);
  expect(result.captured['zoho-pull-so-headers.json'].full_list).toBe(true);
});
```

`test/e2e/serve.js` (used by all E2E tests; Task 17 extends it):
```js
// Starts the app on localhost:4391 with a throwaway database and one admin (admin1 / admin-password-1).
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { loadConfig } from '../../server/config.js';
import { openDb } from '../../server/db/open.js';
import { prepareDatabase } from '../../server/startup.js';
import { createApp } from '../../server/create-app.js';
import { buildRoutes } from '../../server/routes/index.js';
import { hashPassword } from '../../server/auth/password.js';
import { startListeners } from '../../server/listen.js';
import { log } from '../../server/log.js';

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pde2e-'));
const config = loadConfig({ PORT: '4391', BRIDGE_HOST: '', APP_ORIGIN: 'http://localhost:4391', DB_PATH: path.join(tmp, 'e2e.db') });
const db = openDb(config.dbPath);
prepareDatabase(db, config, log);
db.prepare(`INSERT INTO users(username, display_name, password_hash, roles, created_at) VALUES ('admin1','Admin One',?, '["admin"]', ?)`)
  .run(await hashPassword('admin-password-1'), new Date().toISOString());
const app = createApp({ db, config, extraRoutes: buildRoutes() });
await startListeners({ app, port: config.port, hosts: ['127.0.0.1'], logger: log });
```

- [ ] **Step 2: Run — expect FAIL.** `npm test` and `npx playwright install chromium && npm run test:e2e`

- [ ] **Step 3: Implement**

`tools/zoho-pull-snippet.js`:
```js
/*
 * Zoho Inventory header pull (read-only). Paste into the browser console while logged in to
 * https://inventory.zoho.com as a Zoho user with a read-only role. It only sends GET requests.
 * It downloads zoho-pull-so-headers.json, zoho-pull-bundles.json, zoho-pull-invoice-headers.json
 * and captured-pull.json. Clear old downloads first (spec §14.2).
 */
(() => {
  const MODULES = [
    { module: 'salesorders', key: 'salesorders', id: 'salesorder_id', file: 'zoho-pull-so-headers.json' },
    { module: 'bundles', key: 'bundles', id: 'bundle_id', file: 'zoho-pull-bundles.json' },
    { module: 'invoices', key: 'invoices', id: 'invoice_id', file: 'zoho-pull-invoice-headers.json' },
  ];
  const colomboIso = (d) => {
    const t = new Date(d.getTime() + 5.5 * 3600e3).toISOString().slice(0, 19);
    return `${t}+05:30`;
  };
  const cookie = (name) => document.cookie.split('; ').find((c) => c.startsWith(`${name}=`))?.split('=')[1] ?? '';
  const save = (name, data) => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data)], { type: 'application/json' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: name });
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };

  async function pullModule(m, { orgId, apiBase, perPage }) {
    const rows = new Map();
    for (let page = 1; ; page += 1) {
      const url = `${apiBase}/api/v1/${m.module}?organization_id=${encodeURIComponent(orgId)}&per_page=${perPage}&page=${page}`;
      let body;
      try {
        const res = await fetch(url, { method: 'GET', credentials: 'include', headers: { 'X-ZCSRF-TOKEN': `zomcsparam=${cookie('zomcsr')}` } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        body = await res.json();
      } catch (err) {
        console.warn(`${m.module}: stopped at page ${page}: ${err.message}`);
        return { rows: [...rows.values()], complete: false };
      }
      if (!Array.isArray(body[m.key]) || !body.page_context) {
        console.warn(`${m.module}: unexpected response on page ${page}`);
        return { rows: [...rows.values()], complete: false };
      }
      for (const r of body[m.key]) rows.set(r[m.id], r);
      if (!body.page_context.has_more_page) return { rows: [...rows.values()], complete: true };
    }
  }

  window.zohoPull = async function zohoPull({ orgId, apiBase = '', perPage = 200, download = true }) {
    const startedAt = colomboIso(new Date());
    const captured = {};
    const files = [];
    for (const m of MODULES) {
      const { rows, complete } = await pullModule(m, { orgId, apiBase, perPage });
      captured[m.file] = { captured_at: startedAt, full_list: complete, rows: rows.length };
      files.push({ name: m.file, rows: rows.length });
      if (download) save(m.file, rows);
      console.log(`${m.file}: ${rows.length} rows${complete ? '' : ' (INCOMPLETE)'}`);
    }
    if (download) save('captured-pull.json', captured);
    return { files, captured };
  };

  if (!window.__ZOHO_PULL_NO_AUTORUN) window.zohoPull({ orgId: '843825512' });
})();
```

`cli/captured.js`:
```js
import fs from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';
import { parseZohoTime } from '../shared/time.js';

const { values } = parseArgs({ options: { dir: { type: 'string' }, merge: { type: 'string' }, set: { type: 'string', multiple: true, default: [] } } });
if (!values.dir) { console.error('--dir is required'); process.exit(1); }
const file = path.join(values.dir, 'captured.json');
const out = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {};
if (values.merge) Object.assign(out, JSON.parse(fs.readFileSync(values.merge, 'utf8')));
for (const pair of values.set) {
  const [name, ...rest] = pair.split('=');
  const time = rest.join('=');
  if (name.startsWith('zoho-pull-')) { console.error(`${name}: header pull times come only from the snippet`); process.exit(1); }
  let t; try { t = parseZohoTime(time, 'time'); } catch { t = null; }
  if (!t || t.precision !== 'time') { console.error(`${name}: not a time with a zone: ${time}`); process.exit(1); }
  out[name] = { captured_at: time, full_list: false };
}
fs.writeFileSync(file, JSON.stringify(out, null, 2));
console.log(`wrote ${file}`);
```

- [ ] **Step 4: Run — expect PASS** (`npm test`, `npm run test:e2e`).
- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: read-only Zoho header-pull snippet and captured.json helper"`

---

### Task 17: Admin web app, build stamp and E2E

> **Blocked until the main session confirms** `@tailwindcss/vite`, `@types/react`, `@types/react-dom`, `@types/node` are approved (Global Constraints).

**Files:**
- Create: `web/index.html`, `web/vite.config.ts`, `web/tsconfig.json`, `web/src/main.tsx`, `web/src/index.css`, `web/src/lib/api.ts`, `web/src/lib/cn.ts`, `web/src/components/ui/{button,input,card,table,tabs,dialog,badge}.tsx`, `web/src/App.tsx`, `web/src/pages/Login.tsx`, `web/src/pages/ChangePassword.tsx`, `web/src/admin/AdminLayout.tsx`, `web/src/admin/Users.tsx`, `web/src/admin/Teams.tsx`, `web/src/admin/Divisions.tsx`, `web/src/admin/ListEditor.tsx`, `web/src/admin/Calendar.tsx`, `web/src/admin/Imports.tsx`, `web/src/admin/Audit.tsx`, `scripts/build-stamp.mjs`, `test/build-stamp.test.js`, `test/e2e/admin.spec.js`
- Commit: `web/dist/**` (build output)

**Interfaces:**
- Consumes: every admin route from Tasks 7–9 and 13.
- Produces: `computeStamp(root) → string` (SHA-256 hex over sorted relative paths + contents of `web/src/**`, `web/vite.config.ts`, `web/index.html`, `package-lock.json`); `web/dist/.build-stamp` containing that hex.

- [ ] **Step 1: Install front-end packages**

```bash
npm install react react-dom react-router-dom @tanstack/react-query @tanstack/react-table clsx tailwind-merge class-variance-authority lucide-react @radix-ui/react-slot qrcode
npm install --save-dev vite @vitejs/plugin-react typescript tailwindcss @tailwindcss/vite @types/react @types/react-dom @types/node
```

- [ ] **Step 2: Failing tests**

`test/build-stamp.test.js` (AC0.16):
```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { computeStamp } from '../scripts/build-stamp.mjs';

test('committed build stamp matches the sources', () => {
  const committed = fs.readFileSync('web/dist/.build-stamp', 'utf8').trim();
  assert.equal(committed, computeStamp(process.cwd()), 'web/dist is stale: run npm run build and commit web/dist');
});
```

`test/e2e/admin.spec.js` (AC0.19):
```js
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const BASE = 'http://localhost:4391';
const PAGES = ['users', 'teams', 'divisions', 'calendar', 'reason-codes', 'reject-reasons', 'order-types', 'imports', 'audit'];

test('admin pages render with no console errors', async ({ page }) => {
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`${BASE}/login`);
  await page.getByLabel('Username').fill('admin1');
  await page.getByLabel('Password').fill('admin-password-1');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/admin\/users/);
  for (const p of PAGES) {
    await page.goto(`${BASE}/admin/${p}`);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    const axe = await new AxeBuilder({ page }).analyze();
    expect(axe.violations.filter((v) => ['serious', 'critical'].includes(v.impact)), p).toEqual([]);
  }
  expect(errors).toEqual([]);
});

test('create a user shows the temporary password once', async ({ page }) => {
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`${BASE}/login`);
  await page.getByLabel('Username').fill('admin1');
  await page.getByLabel('Password').fill('admin-password-1');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('button', { name: 'New user' }).click();
  await page.getByLabel('Username').fill('nimesha');
  await page.getByLabel('Display name').fill('Nimesha');
  await page.getByLabel('coordinator').check();
  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page.getByText(/^Temporary password for nimesha:/)).toBeVisible();
  await expect(page.getByRole('cell', { name: 'nimesha', exact: true })).toBeVisible();
  expect(errors, 'no console errors (CSP) while the dialog was open').toEqual([]);
});
```

- [ ] **Step 3: Run — expect FAIL.**

- [ ] **Step 4: Implement the build stamp** — `scripts/build-stamp.mjs`

```js
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true })
  .flatMap((e) => (e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]));

export function computeStamp(root) {
  const files = [...walk(path.join(root, 'web/src')), path.join(root, 'web/vite.config.ts'),
    path.join(root, 'web/index.html'), path.join(root, 'package-lock.json')]
    .map((f) => path.relative(root, f).split(path.sep).join('/')).sort();
  const h = crypto.createHash('sha256');
  for (const rel of files) { h.update(rel); h.update('\0'); h.update(fs.readFileSync(path.join(root, rel))); h.update('\0'); }
  return h.digest('hex');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  fs.writeFileSync(path.join(root, 'web/dist/.build-stamp'), `${computeStamp(root)}\n`);
  console.log('build stamp written');
}
```

- [ ] **Step 5: Implement the web app**

`web/vite.config.ts`:
```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  root: __dirname,
  plugins: [react(), tailwindcss()],
  build: { outDir: 'dist', emptyOutDir: true, sourcemap: false },
  server: { proxy: { '/api': 'http://127.0.0.1:4300' } },
});
```

`web/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Production Dashboard</title>
  </head>
  <body class="bg-slate-50 text-slate-900">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`web/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022", "module": "ESNext", "moduleResolution": "Bundler", "jsx": "react-jsx",
    "strict": true, "noEmit": true, "skipLibCheck": true, "types": ["node"], "lib": ["ES2022", "DOM", "DOM.Iterable"]
  },
  "include": ["src", "vite.config.ts"]
}
```

`web/src/index.css`:
```css
@import "tailwindcss";
```

`web/src/lib/cn.ts`:
```ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));
```

`web/src/lib/api.ts`:
```ts
export class ApiError extends Error {
  constructor(public status: number, public body: any) { super(body?.error ?? `HTTP ${status}`); }
}

export async function api<T = any>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: opts.method ?? 'GET',
    credentials: 'same-origin',
    headers: opts.body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
  });
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}

export type Me = { user: { id: number; username: string; display_name: string; roles: string[]; must_reset: number } };
```

(The browser sends `Origin` automatically on same-origin POST/PATCH/PUT/DELETE `fetch` calls, which satisfies §5.2.)

`web/src/components/ui/button.tsx`:
```tsx
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/cn';

const button = cva('inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:pointer-events-none', {
  variants: {
    variant: {
      default: 'bg-blue-700 text-white hover:bg-blue-800',
      outline: 'border border-slate-300 bg-white hover:bg-slate-100',
      ghost: 'hover:bg-slate-100',
      danger: 'bg-red-700 text-white hover:bg-red-800',
    },
    size: { default: 'h-9 px-4', sm: 'h-8 px-3', lg: 'h-11 px-6' },
  },
  defaultVariants: { variant: 'default', size: 'default' },
});

type Props = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof button> & { asChild?: boolean };
export const Button = forwardRef<HTMLButtonElement, Props>(({ className, variant, size, asChild, ...props }, ref) => {
  const Comp = asChild ? Slot : 'button';
  return <Comp ref={ref} className={cn(button({ variant, size }), className)} {...props} />;
});
Button.displayName = 'Button';
```

`web/src/components/ui/input.tsx`:
```tsx
import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '../../lib/cn';
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(({ className, ...props }, ref) => (
  <input ref={ref} className={cn('h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm focus-visible:outline-2 focus-visible:outline-blue-600', className)} {...props} />
));
Input.displayName = 'Input';

export function Field({ label, id, children }: { label: string; id: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">{label}</label>
      {children}
    </div>
  );
}
```

`web/src/components/ui/card.tsx`, `table.tsx`, `badge.tsx` — thin styled wrappers:
```tsx
// card.tsx
import { cn } from '../../lib/cn';
export const Card = ({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) =>
  <div className={cn('rounded-lg border border-slate-200 bg-white p-4 shadow-sm', className)} {...p} />;

// table.tsx
import { cn } from '../../lib/cn';
export const Table = ({ className, ...p }: React.TableHTMLAttributes<HTMLTableElement>) =>
  <div className="overflow-x-auto"><table className={cn('w-full text-sm', className)} {...p} /></div>;
export const Th = (p: React.ThHTMLAttributes<HTMLTableCellElement>) =>
  <th scope="col" className="border-b border-slate-200 px-3 py-2 text-left font-semibold text-slate-600" {...p} />;
export const Td = (p: React.TdHTMLAttributes<HTMLTableCellElement>) =>
  <td className="border-b border-slate-100 px-3 py-2 align-top" {...p} />;

// badge.tsx
import { cn } from '../../lib/cn';
const tones = { gray: 'bg-slate-100 text-slate-700', green: 'bg-green-100 text-green-800', amber: 'bg-amber-100 text-amber-900', red: 'bg-red-100 text-red-800' };
export const Badge = ({ tone = 'gray', className, ...p }: React.HTMLAttributes<HTMLSpanElement> & { tone?: keyof typeof tones }) =>
  <span className={cn('inline-flex rounded px-2 py-0.5 text-xs font-medium', tones[tone], className)} {...p} />;
```

`web/src/components/ui/dialog.tsx` — the native `<dialog>` element. (Radix Dialog's scroll lock injects an inline `<style>`, which the §11 CSP `default-src 'self'` blocks; the native element needs no inline styles.)
```tsx
import { useEffect, useId, useRef } from 'react';
export function Dialog({ open, onOpenChange, title, children }: { open: boolean; onOpenChange: (o: boolean) => void; title: string; children: React.ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} aria-labelledby={titleId} onClose={() => onOpenChange(false)}
      className="m-auto w-[min(32rem,calc(100vw-2rem))] rounded-lg bg-white p-6 shadow-xl backdrop:bg-black/40">
      <h2 id={titleId} className="mb-4 text-lg font-semibold">{title}</h2>
      {open && children}
    </dialog>
  );
}
```

The create-user E2E test opens this dialog and fails on any console error, so a CSP problem would fail AC0.19.

`web/src/main.tsx`:
```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const qc = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } });
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={qc}>
      <BrowserRouter><App /></BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
```

`web/src/App.tsx`:
```tsx
import { Navigate, Route, Routes } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api, type Me } from './lib/api';
import Login from './pages/Login';
import ChangePassword from './pages/ChangePassword';
import AdminLayout from './admin/AdminLayout';
import Users from './admin/Users';
import Teams from './admin/Teams';
import Divisions from './admin/Divisions';
import ListEditor from './admin/ListEditor';
import Calendar from './admin/Calendar';
import Imports from './admin/Imports';
import Audit from './admin/Audit';

export function useMe() {
  return useQuery({ queryKey: ['me'], queryFn: () => api<Me>('/me') });
}

function Home() {
  const me = useMe();
  if (me.isLoading) return <p className="p-8">Loading…</p>;
  if (me.isError) return <Navigate to="/login" replace />;
  if (me.data!.user.must_reset) return <Navigate to="/password" replace />;
  if (me.data!.user.roles.includes('admin')) return <Navigate to="/admin/users" replace />;
  return <main className="p-8"><h1 className="text-xl font-semibold">Welcome, {me.data!.user.display_name}</h1><p className="mt-2 text-slate-600">Your workspace arrives in the next release.</p></main>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/password" element={<ChangePassword />} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route path="users" element={<Users />} />
        <Route path="teams" element={<Teams />} />
        <Route path="divisions" element={<Divisions />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="reason-codes" element={<ListEditor title="Reason codes" path="/admin/reason-codes" columns={['code', 'label', 'default_owner_label']} />} />
        <Route path="reject-reasons" element={<ListEditor title="Reject reasons" path="/admin/reject-reasons" columns={['code', 'label']} />} />
        <Route path="order-types" element={<ListEditor title="Order types from Zoho" path="/admin/order-type-aliases" columns={['zoho_value', 'order_type']} />} />
        <Route path="imports" element={<Imports />} />
        <Route path="audit" element={<Audit />} />
      </Route>
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
```

`web/src/pages/Login.tsx`:
```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../lib/api';
import { Button } from '../components/ui/button';
import { Field, Input } from '../components/ui/input';
import { Card } from '../components/ui/card';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const nav = useNavigate();
  const qc = useQueryClient();
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      const r = await api<{ must_reset: boolean }>('/auth/login', { method: 'POST', body: { username, password } });
      await qc.invalidateQueries({ queryKey: ['me'] });
      nav(r.must_reset ? '/password' : '/', { replace: true });
    } catch (err) {
      setError(err instanceof ApiError && err.status === 429 ? 'Too many attempts. Wait 15 minutes.' : 'Wrong username or password.');
    }
  }
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-4 text-xl font-semibold">Production Dashboard</h1>
        <form onSubmit={submit} className="space-y-3">
          <Field label="Username" id="u"><Input id="u" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required /></Field>
          <Field label="Password" id="p"><Input id="p" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></Field>
          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          <Button type="submit" className="w-full">Sign in</Button>
        </form>
      </Card>
    </main>
  );
}
```

`web/src/pages/ChangePassword.tsx` — same layout; fields "Current password", "New password (at least 10 characters)", "New password again"; client-side check that the two match and length ≥ 10; `POST /auth/password`; on success invalidate `me` and navigate to `/`; heading level 1 "Change your password".

`web/src/admin/AdminLayout.tsx`:
```tsx
import { NavLink, Navigate, Outlet } from 'react-router-dom';
import { useMe } from '../App';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { cn } from '../lib/cn';

const TABS = [['users', 'Users'], ['teams', 'Teams'], ['divisions', 'Divisions & checklists'], ['calendar', 'Working days'],
  ['reason-codes', 'Reason codes'], ['reject-reasons', 'Reject reasons'], ['order-types', 'Order types'], ['imports', 'Imports'], ['audit', 'Audit']];

export default function AdminLayout() {
  const me = useMe();
  if (me.isLoading) return <p className="p-8">Loading…</p>;
  if (me.isError) return <Navigate to="/login" replace />;
  if (me.data!.user.must_reset) return <Navigate to="/password" replace />;
  if (!me.data!.user.roles.includes('admin')) return <Navigate to="/" replace />;
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <span className="font-semibold">Production Dashboard · Admin</span>
        <div className="flex items-center gap-3 text-sm">
          <span>{me.data!.user.display_name}</span>
          <Button variant="outline" size="sm" onClick={async () => { await api('/auth/logout', { method: 'POST' }); location.href = '/login'; }}>Sign out</Button>
        </div>
      </header>
      <nav aria-label="Admin sections" className="flex flex-wrap gap-1 border-b border-slate-200 bg-white px-4">
        {TABS.map(([to, label]) => (
          <NavLink key={to} to={to} className={({ isActive }) => cn('border-b-2 px-3 py-2 text-sm', isActive ? 'border-blue-700 font-medium text-blue-800' : 'border-transparent text-slate-600 hover:text-slate-900')}>
            {label}
          </NavLink>
        ))}
      </nav>
      <main className="mx-auto max-w-6xl p-6"><Outlet /></main>
    </div>
  );
}
```

`web/src/admin/Users.tsx`:
```tsx
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../lib/api';
import { Button } from '../components/ui/button';
import { Field, Input } from '../components/ui/input';
import { Dialog } from '../components/ui/dialog';
import { Table, Th, Td } from '../components/ui/table';
import { Badge } from '../components/ui/badge';

const ROLES = ['requester', 'triage', 'coordinator', 'manager', 'stores', 'invoicing', 'approver_stores', 'approver_invoicing', 'gm', 'coo', 'analyst', 'admin'];
type User = { id: number; username: string; display_name: string; roles: string[]; team_id: number | null; active: number; must_reset: number };
type Team = { id: number; name: string; active: number };

export default function Users() {
  const qc = useQueryClient();
  const users = useQuery({ queryKey: ['users'], queryFn: () => api<User[]>('/admin/users') });
  const teams = useQuery({ queryKey: ['teams'], queryFn: () => api<Team[]>('/admin/teams') });
  const [open, setOpen] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [secret, setSecret] = useState<string | null>(null);
  const [form, setForm] = useState({ username: '', display_name: '', roles: [] as string[], team_id: '' });
  const [error, setError] = useState('');
  const [csv, setCsv] = useState('');

  const create = useMutation({
    mutationFn: () => api<{ temporary_password: string }>('/admin/users', { method: 'POST', body: {
      username: form.username, display_name: form.display_name, roles: form.roles, team_id: form.team_id ? Number(form.team_id) : null } }),
    onSuccess: (r) => { setSecret(`Temporary password for ${form.username}: ${r.temporary_password}`); setOpen(false); qc.invalidateQueries({ queryKey: ['users'] }); },
    onError: (e) => setError(e instanceof ApiError ? JSON.stringify(e.body?.fields ?? e.body?.error) : 'Failed'),
  });
  const bulk = useMutation({
    mutationFn: () => api<{ username: string; temporary_password: string }[]>('/admin/users/bulk-requesters', { method: 'POST', body: {
      rows: csv.trim().split(/\r?\n/).slice(1).filter(Boolean).map((line) => {
        const [display_name, username, team] = line.split(',').map((s) => s.trim());
        return { display_name, username, team };
      }) } }),
    onSuccess: (r) => { setSecret(r.map((x) => `${x.username}: ${x.temporary_password}`).join('\n')); setBulkOpen(false); qc.invalidateQueries({ queryKey: ['users'] }); },
    onError: (e) => setError(e instanceof ApiError ? JSON.stringify(e.body?.fields ?? e.body?.error) : 'Failed'),
  });
  const patch = useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) => api(`/admin/users/${id}`, { method: 'PATCH', body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });
  const reset = useMutation({
    mutationFn: (u: User) => api<{ temporary_password: string }>(`/admin/users/${u.id}/reset-password`, { method: 'POST' }).then((r) => ({ u, r })),
    onSuccess: ({ u, r }) => setSecret(`Temporary password for ${u.username}: ${r.temporary_password}`),
  });
  const teamName = (id: number | null) => teams.data?.find((t) => t.id === id)?.name ?? '—';

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Users</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => { setError(''); setBulkOpen(true); }}>Add requesters from CSV</Button>
          <Button onClick={() => { setError(''); setForm({ username: '', display_name: '', roles: [], team_id: '' }); setOpen(true); }}>New user</Button>
        </div>
      </div>
      {secret && (
        <div role="status" className="mb-4 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm">
          <p className="font-medium">Temporary password — shown once. Hand it over in person.</p>
          <pre className="mt-1 whitespace-pre-wrap">{secret}</pre>
          <Button size="sm" variant="ghost" onClick={() => setSecret(null)}>Done</Button>
        </div>
      )}
      <Table>
        <thead><tr><Th>Username</Th><Th>Name</Th><Th>Roles</Th><Th>Team</Th><Th>Status</Th><Th>Actions</Th></tr></thead>
        <tbody>
          {users.data?.map((u) => (
            <tr key={u.id}>
              <Td>{u.username}</Td><Td>{u.display_name}</Td>
              <Td><div className="flex flex-wrap gap-1">{u.roles.map((r) => <Badge key={r}>{r}</Badge>)}</div></Td>
              <Td>{teamName(u.team_id)}</Td>
              <Td>{u.active ? <Badge tone="green">active</Badge> : <Badge tone="red">inactive</Badge>}{u.must_reset ? <Badge tone="amber" className="ml-1">must reset</Badge> : null}</Td>
              <Td className="space-x-2 whitespace-nowrap">
                <Button size="sm" variant="outline" onClick={() => reset.mutate(u)}>Reset password</Button>
                <Button size="sm" variant="outline" onClick={() => patch.mutate({ id: u.id, body: { active: !u.active } })}>{u.active ? 'Deactivate' : 'Activate'}</Button>
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Dialog open={open} onOpenChange={setOpen} title="New user">
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); create.mutate(); }}>
          <Field label="Username" id="nu-username"><Input id="nu-username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required /></Field>
          <Field label="Display name" id="nu-name"><Input id="nu-name" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} required /></Field>
          <fieldset>
            <legend className="text-sm font-medium text-slate-700">Roles</legend>
            <div className="mt-1 grid grid-cols-2 gap-1">
              {ROLES.map((r) => (
                <label key={r} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={form.roles.includes(r)}
                    onChange={(e) => setForm({ ...form, roles: e.target.checked ? [...form.roles, r] : form.roles.filter((x) => x !== r) })} />
                  {r}
                </label>
              ))}
            </div>
          </fieldset>
          <Field label="Team (required for requesters)" id="nu-team">
            <select id="nu-team" className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 text-sm" value={form.team_id} onChange={(e) => setForm({ ...form, team_id: e.target.value })}>
              <option value="">— none —</option>
              {teams.data?.filter((t) => t.active).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </Field>
          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button type="submit">Create</Button></div>
        </form>
      </Dialog>

      <Dialog open={bulkOpen} onOpenChange={setBulkOpen} title="Add requesters from CSV">
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); bulk.mutate(); }}>
          <p className="text-sm text-slate-600">First line is a header: <code>name,username,team</code>. Teams must already exist. All rows are added, or none.</p>
          <label htmlFor="csv" className="sr-only">CSV</label>
          <textarea id="csv" className="h-40 w-full rounded-md border border-slate-300 p-2 font-mono text-sm" value={csv} onChange={(e) => setCsv(e.target.value)} />
          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setBulkOpen(false)}>Cancel</Button><Button type="submit">Add</Button></div>
        </form>
      </Dialog>
    </section>
  );
}
```

In the E2E test, the role checkbox is found with `getByLabel('coordinator')`; the `<label>` wrapping the checkbox provides that name.

`web/src/admin/ListEditor.tsx` — a generic table + "Add" form + inline "Deactivate" for the simple lists (reason codes, reject reasons, order-type aliases):
```tsx
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Table, Th, Td } from '../components/ui/table';

type Row = Record<string, string | number | null>;
export default function ListEditor({ title, path, columns }: { title: string; path: string; columns: string[] }) {
  const qc = useQueryClient();
  const rows = useQuery({ queryKey: [path], queryFn: () => api<Row[]>(path) });
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const add = useMutation({
    mutationFn: () => api(path, { method: 'POST', body: draft }),
    onSuccess: () => { setDraft({}); setError(''); qc.invalidateQueries({ queryKey: [path] }); },
    onError: (e) => setError(e instanceof ApiError ? JSON.stringify(e.body?.fields ?? e.body?.error) : 'Failed'),
  });
  const toggle = useMutation({
    mutationFn: (r: Row) => api(`${path}/${encodeURIComponent(String(r[columns[0]]))}`, { method: 'PATCH', body: { active: !r.active } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: [path] }),
  });
  return (
    <section>
      <h1 className="mb-4 text-xl font-semibold">{title}</h1>
      <Table>
        <thead><tr>{columns.map((c) => <Th key={c}>{c}</Th>)}<Th>Active</Th><Th /></tr></thead>
        <tbody>
          {rows.data?.map((r) => (
            <tr key={String(r[columns[0]])}>
              {columns.map((c) => <Td key={c}>{r[c]}</Td>)}
              <Td>{'active' in r ? (r.active ? 'yes' : 'no') : '—'}</Td>
              <Td>{'active' in r && <Button size="sm" variant="outline" onClick={() => toggle.mutate(r)}>{r.active ? 'Deactivate' : 'Activate'}</Button>}</Td>
            </tr>
          ))}
          <tr>
            {columns.map((c) => (
              <Td key={c}><Input aria-label={`New ${c}`} value={draft[c] ?? ''} onChange={(e) => setDraft({ ...draft, [c]: e.target.value })} /></Td>
            ))}
            <Td /><Td><Button size="sm" onClick={() => add.mutate()}>Add</Button></Td>
          </tr>
        </tbody>
      </Table>
      {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
    </section>
  );
}
```

(For `order-type-aliases` the PATCH body field is `order_type` or `provisional`, not `active`; the table has no `active` column, so no toggle is shown — the `'active' in r` check handles it.)

`web/src/admin/Teams.tsx` — `ListEditor`-style page for `/admin/teams` with a single `name` column; PATCH uses the numeric `id` (`/admin/teams/${r.id}`), so write it as its own small component rather than reusing `ListEditor`. Heading "Teams".

`web/src/admin/Divisions.tsx` — heading "Divisions & checklists"; loads `GET /admin/divisions`; one card per division showing name, code, `provisional` / `floor_live` badges, counting process (select of that division's active processes → PATCH), quantity form id (text input → PATCH; show the API's 400 message), the stage order as a numbered list with up/down buttons that PUT the new order, processes (list + add form + deactivate), aliases (list + add + delete) and pairs (list + add with two selects of users filtered by role + deactivate). A "Switch floor live" button calls PATCH `{floor_live: true}` and shows the 409 message "Employee Master is not configured" when refused. A "New division" form at the top (code, name). All controls have visible labels.

`web/src/admin/Calendar.tsx` — heading "Working days"; seven checkboxes (Sun…Sat) → PUT `/admin/calendar`; holiday list with date + label inputs → POST `/admin/holidays`, delete buttons → DELETE.

`web/src/admin/Imports.tsx`:
```tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Table, Th, Td } from '../components/ui/table';

const REASON: Record<string, string> = {
  ok: 'Shipped figures are up to date',
  no_full_header: 'No complete sales order list imported yet',
  header_older_than_movements: 'The sales order list was taken before the latest package/shipment export — do the header pull again',
  header_too_old: 'The sales order list is more than one working day old',
};
const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleString('en-GB', { timeZone: 'Asia/Colombo' }) : '—');

export default function Imports() {
  const q = useQuery({ queryKey: ['imports'], queryFn: () => api<any>('/admin/imports'), refetchInterval: 30_000 });
  if (!q.data) return <h1 className="text-xl font-semibold">Imports</h1>;
  const { orgs, runs, unmapped, crashed, untrustedForwarded } = q.data;
  return (
    <section className="space-y-4">
      <h1 className="text-xl font-semibold">Imports</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {Object.entries(orgs).map(([org, o]: [string, any]) => (
          <Card key={org}>
            <h2 className="font-semibold">{org}</h2>
            <p className="mt-1 text-sm">{o.shipped.fresh ? <Badge tone="green">Fresh</Badge> : <Badge tone="amber">Shipped: unknown</Badge>} {REASON[o.shipped.reason]}</p>
            <p className="mt-1 text-xs text-slate-600">Sales order list taken {fmt(o.shipped.H)} · latest package/shipment export {fmt(o.shipped.M)}</p>
            <p className="mt-1 text-sm">Bundle data: {o.bundles.recent ? 'recent' : 'old or missing'} ({fmt(o.bundles.capturedAt)})</p>
          </Card>
        ))}
      </div>
      {crashed.length > 0 && <Card className="border-red-300"><h2 className="font-semibold text-red-800">Imports that never finished</h2><ul className="text-sm">{crashed.map((r: any) => <li key={r.id}>#{r.id} {r.module} {r.file} started {fmt(r.started_at)}</li>)}</ul></Card>}
      {untrustedForwarded > 0 && <Card className="border-amber-300"><p className="text-sm">Requests with a forwarded address came from an unexpected container ({untrustedForwarded}). Traefik's address may have changed — check TRUSTED_PROXY_IPS.</p></Card>}
      {unmapped.length > 0 && (
        <Card><h2 className="font-semibold">Division names from Zoho with no mapping</h2>
          <p className="text-sm text-slate-600">For information. Add them under Divisions; no re-import is needed.</p>
          <ul className="text-sm">{unmapped.map((u: any) => <li key={u.value}>{u.value} — {u.so_count} SOs</li>)}</ul></Card>
      )}
      <Table>
        <thead><tr><Th>#</Th><Th>Org</Th><Th>Module</Th><Th>File</Th><Th>Taken from Zoho</Th><Th>Full list</Th><Th>Status</Th><Th>Rows</Th><Th>Changed SOs</Th><Th>Notes</Th></tr></thead>
        <tbody>
          {runs.map((r: any) => (
            <tr key={r.id}>
              <Td>{r.id}</Td><Td>{r.org}</Td><Td>{r.module}</Td><Td>{r.file}</Td><Td>{fmt(r.captured_at)}</Td><Td>{r.full_list ? 'yes' : 'no'}</Td>
              <Td>{r.status === 'ok' ? <Badge tone="green">ok</Badge> : r.status === 'warning' ? <Badge tone="amber">warning</Badge> : r.status === 'failed' ? <Badge tone="red">failed</Badge> : <Badge>running</Badge>}</Td>
              <Td>{r.rows_upserted}/{r.rows_read}</Td><Td>{r.changed_count}</Td><Td className="text-xs">{[r.error, ...r.warnings].filter(Boolean).join('; ')}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </section>
  );
}
```

`web/src/admin/Audit.tsx` — heading "Audit"; table of `GET /admin/audit?limit=100` (time in Colombo, actor, action, entity, id, detail as compact JSON); "Older" button pages with `before_id`.

- [ ] **Step 6: Build and run all checks**

```bash
npx tsc -p web/tsconfig.json
npm run build
npm test
npm run test:e2e
```
Expected: type check clean; build writes `web/dist` and `.build-stamp`; all tests pass. If axe reports a serious violation, fix the markup (labels, contrast, landmark) — do not filter the rule.

- [ ] **Step 7: Commit (including `web/dist`)** — `git add -A && git commit -m "feat: admin web app with build stamp and E2E"`

---

### Task 18: Runbook, Traefik router, dependency audit and final verification

**Files:**
- Create: `docs/runbook-release-0.md`
- Modify: `README.md`; `/root/dev/traefik-custom/custom.yaml` (dev copy only — the human copies it into place)

- [ ] **Step 1: Traefik router** — add to `/root/dev/traefik-custom/custom.yaml`, following the existing entries:

Under `routers:`
```yaml
    sh-production:
      rule: "Host(`production.standard-holdings.lk`)"
      entryPoints: [https]
      service: sh-production
      tls: {certResolver: letsencrypt}
```
Under `services:`
```yaml
    sh-production:
      loadBalancer:
        servers: [{url: "http://172.17.0.1:4300"}]
```
Validate: `python3 -c "import yaml,sys; yaml.safe_load(open('/root/dev/traefik-custom/custom.yaml'))"` → no error.

- [ ] **Step 2: `docs/runbook-release-0.md`** — the human's steps, copied from spec §14.1 and made concrete. It must contain, in this order:
  0. **Protect the live tree before it exists (M7):** add `deny /root/production-dashboard` to `/root/.claude/scripts/protected-paths.conf` and add the row `production-dashboard | /root/production-dashboard | /root/dev/production-dashboard | 4300 | data/production.db` to the §4b table in `/root/.claude/CLAUDE.md`. Both files are protected; the human edits them.
  1. GitHub repo `trcb69/production-dashboard` (private); push `main` from `/root/dev/production-dashboard`.
  1b. DNS: `production.standard-holdings.lk` already resolves to 45.151.122.105 through the wildcard record (verified 2026-09-17); nothing to add.
  2. Firewall lines from §14.1 step 2 (only as part of X2, SSH first).
  3. `cp /root/dev/traefik-custom/custom.yaml /etc/easypanel/traefik/config/custom.yaml` (Traefik picks it up by itself); check `curl -sI https://production.standard-holdings.lk/api/health` after step 4.
  4. Live install:
     ```bash
     git clone git@github.com:trcb69/production-dashboard.git /root/production-dashboard
     cd /root/production-dashboard
     cp .env.example .env    # then edit: keep PORT=4300, APP_ORIGIN=https://production.standard-holdings.lk
     npm ci --no-audit --no-fund
     node cli/create-admin.js
     pm2 start server/app.js --name production-dashboard && pm2 save
     curl -s http://127.0.0.1:4300/api/health
     ```
     After the first browser visit: `pm2 logs production-dashboard --lines 50 --nostream | grep '"ip"'` shows the office public IP (proxy check, §4). If Traefik's container address is not `172.18.0.3`, the Admin → Imports page warns; find it with `docker inspect` on the Traefik container and set `TRUSTED_PROXY_IPS` in `.env`, then `pm2 restart production-dashboard --update-env`.
  5. shdeploy: add the registry line from §12 to the `SERVICES` block in `/root/ops/shdeploy`, keeping its column format:
     ```
     production-dashboard|/root/production-dashboard|production-dashboard|data/production.db|http://127.0.0.1:4300/api/health|docs/
     ```
     shdeploy prints "Migration, schema or seed files changed" when a migration changes: **do not run `migrate.js`**; the service migrates on restart.
  6. Cron (`crontab -e`):
     ```
     30 1 * * * cd /root/production-dashboard && /usr/bin/node cli/backup.js >> data/backups/backup.log 2>&1
     0 9 1 * * cd /root/production-dashboard && /usr/bin/node cli/restore-check.js >> data/backups/restore-check.log 2>&1
     ```
  7. First data load (backfill) — staging folder outside the live tree, prepared by Claude in `/root/exports/zoho/staging/2026-09-backfill/` with copies renamed to the importer's names and a `captured.json` (UI exports captured 2026-09-16, header pulls 2026-09-17 with `full_list: true` and their de-duplicated row counts), then:
     ```bash
     cd /root/production-dashboard
     node cli/import-zoho.js --org SPS --dir /root/exports/zoho/staging/2026-09-backfill
     ```
     Expected: exit 0 or 2; Admin → Imports shows every module; `shipped` shows "too old" (the backfill is days old — correct until the first daily pull).
  8. Daily interim routine (§14.2). The first time the snippet runs, Chrome asks "Download multiple files?" — choose Allow for inventory.zoho.com. The exact commands: UI exports → `node cli/captured.js --dir <d> --set Sales_Order.xlsx=<time> …` → header pull (paste `tools/zoho-pull-snippet.js` in the Zoho console; clear old downloads first) → move downloads into `<d>` → `node cli/captured.js --dir <d> --merge <d>/captured-pull.json` → import command → check Admin → Imports.
  9. Users: desk users; manager + coordinator pairs per division (§6.5 list); teams; requesters from CSV (Release 1 uses them).
  9b. If a `Sales_Order.xlsx` import fails part-way, **re-run that same folder before importing any older folder** (the SO line sets are only recorded when the file finishes).
  10. Rollback: `shdeploy rollback production-dashboard`; removal: `pm2 delete production-dashboard`, remove the two Traefik entries, delete the folder.

- [ ] **Step 3: Prepare the backfill staging folder** (not a live path)

```bash
S=/root/exports/zoho/staging/2026-09-backfill
mkdir -p "$S"
cp /root/exports/zoho/native/2026-09-16/Sales_Order.xlsx "$S/"
cp /root/exports/zoho/native/2026-09-16/Package_ALL.xlsx "$S/"
cp /root/exports/zoho/native/2026-09-16/Shipment_ALL.xlsx "$S/"
cp /root/exports/zoho/native/2026-09-16/Invoice.xlsx "$S/"
cp /root/exports/zoho/native/2026-09-16/Picklist.xlsx "$S/"
cp /root/exports/zoho/native/2026-09-16/Item.xlsx "$S/"
cp /root/exports/zoho/native/2026-09-17/sps/salesorders_headers.json "$S/zoho-pull-so-headers.json"
cp /root/exports/zoho/native/2026-09-17/sps/bundles.json "$S/zoho-pull-bundles.json"
cp /root/exports/zoho/native/2026-09-17/sps/invoices_headers.json "$S/zoho-pull-invoice-headers.json"
```
(If the guard hook blocks shell variables in paths, write the paths out in full.) Then write `$S/captured.json` with the Write tool. File modification times are when each export **finished**, not when it started; for the backfill that approximation is acceptable (it only affects whether the backfill counts as fresh, and a days-old backfill is stale anyway): xlsx files `captured_at` = the MANIFEST/README export time on 2026-09-16 (read `/root/exports/zoho/native/2026-09-16/` file mtimes with `stat` and use the latest, as `+05:30`), JSON files `captured_at` = the latest mtime of the 2026-09-17 `sps/` JSON files, `full_list: true`, `rows` = the de-duplicated count of each JSON file (`python3 -c "import json;print(len({r['salesorder_id'] for r in json.load(open('…'))}))"`). Dry-run it against a scratch DB:

```bash
cd /root/dev/production-dashboard
DB_PATH=/tmp/pd-backfill-test/production.db BRIDGE_HOST= PORT=4398 timeout 20 node server/app.js || true   # creates + migrates the scratch DB, then stops
DB_PATH=/tmp/pd-backfill-test/production.db node cli/import-zoho.js --org SPS --dir /root/exports/zoho/staging/2026-09-backfill
```
Expected: exit 0 or 2; record the per-file line output and the time taken in the release notes. Then run `sqlite3 -readonly /tmp/pd-backfill-test/production.db "SELECT stage_id, count(*) FROM zoho_so_facts GROUP BY 1"` and record the counts (stage 4 ≈ number of SPS SOs since 2024; 7, 8, 10 in the thousands). Check the Package_ALL import time; if the whole import takes more than 10 minutes, report it (do not change batch size silently).

- [ ] **Step 4: Dependency audit** — `npm audit --omit=dev` → no high or critical. If any, stop and report.

- [ ] **Step 5: Full verification** — `npm test && npm run test:e2e && npx tsc -p web/tsconfig.json` all pass; `git status` clean.

- [ ] **Step 6: Commit** — `git add -A && git commit -m "docs: release 0 runbook"`

- [ ] **Step 7: Reviews (main session dispatches, in parallel):** `code-reviewer`, `security-auditor` (Release 0: auth, sessions, proxy trust, uploads not yet, admin routes, import CLI, pull snippet), `db-migration-guard` (001, 002, migration runner, seed policy). Fix any BLOCK findings, re-run Step 5, re-review.

- [ ] **Step 8: Hand-off** — main session reports to the human: the runbook path, the commands to run, the Traefik copy command, and the AC table for Release 0 with each AC's test name.

---

## Acceptance criteria → tests (Release 0)

| AC | Where |
|---|---|
| 0.1 | Task 18 Step 5 (`npm test` offline) |
| 0.2 | `test/migrations.test.js` "startup twice" |
| 0.3 | `test/schema.test.js` |
| 0.4, 0.5, 0.6 | `test/app-security.test.js` |
| 0.7, 0.9, 0.20c | `test/import-run.test.js` |
| 0.8 | `test/import-inputs.test.js` |
| 0.10 | `test/time.test.js`, `test/text.test.js` |
| 0.11, 0.11b | `test/backup.test.js` |
| 0.12 | `test/app-security.test.js` "health" |
| 0.13 | `test/app-security.test.js` headers + proxy, `test/listen.test.js` |
| 0.14 | `test/admin-users.test.js` |
| 0.15 | `test/migrations.test.js` |
| 0.16 | `test/build-stamp.test.js` |
| 0.17 | `test/seed.test.js`, `test/forms.test.js` |
| 0.18 | `test/schema.test.js` |
| 0.19 | `test/e2e/admin.spec.js` |
| 0.20 | `test/facts.test.js` |
| 0.20b | `test/freshness.test.js` (a, b, d, e, g, h, i2, l), `test/import-inputs.test.js` (f, k), `test/import-run.test.js` (c, i), `test/text.test.js` (j) |
| 0.21 | `test/sweep.test.js` |
| 0.22 | `test/app-security.test.js` "proxy trust" |
| 0.23 | `test/facts.test.js` |
| 0.24 | `test/seed.test.js` |
| 0.25 | `test/e2e/pull-snippet.spec.js` |

## Not in Release 0 (later plans)

Admin → **Forms** (read-only form versions; no forms exist until Release 5, so it ships with Release 5) and Admin → **Divergence** (needs jobs; ships with Release 4). Job screens, the order portal, uploads and `/files` serving, derived job state, SSE job scoping (Release 1); manager workspace (2); stores/invoicing (3); GM/COO/analyst reports and export (4); floor stations and the Employee Master client (5); the Zoho read-only sync (1b addendum). The schema for all of them already exists (Task 3).

## Plan revision 2 — plan-critic review 1 → fixes

| # | Fix |
|---|---|
| B1 | `MIGRATIONS` in the test helper honours `PD_MIGRATIONS_DIR`; `makeApp` passes it through; a test starts `server/app.js` with the variable set |
| B2 | `importFolder` recomputes facts by default; `test/import-cli.test.js` runs the real CLI and checks `zoho_so_facts`, and the version refusal |
| B3 | Bundle move tested through the importer; out-of-order test snapshots every mirror table with bundles and shipments and asserts H and M; AC0.17 edit uses `curing` and is asserted; `--rebuild-facts` compared on the real sample; invalid-role test uses a valid username |
| M1 | Version assertions run before the first rebuild |
| M2 | Exact E2E locators |
| M3 | Login attempts are counted before the scrypt check; a parallel test |
| M4 | Numeric times below 1e11 and unsafe integer IDs are refused; the sample script asserts cell types |
| M5 | `zoho_so_line_sets` with capture-ordered line sets; removed lines are trimmed; a test for both import orders (spec note added in Rev 7.2) |
| M6 | `last_seen_at` written at most every 5 minutes |
| M7 | Runbook step 0: protect the live path (human edits the protected files) |
| N1–N12 | Task numbers; exceljs reader drained; sweep re-match limited to changed SOs + index; downloads awaited; native `<dialog>` (CSP); server-side `must_reset`; invoice references verified exact in 12,049 of 12,133 (no suffixes) so no normalising; runbook DNS and download prompt; whole-startup AC0.2, more AC0.3 tables, team-change AC0.14; deferred admin tabs listed; sample trimmed to mapped columns; backup journal mode and sidecar pruning |
| N13 | Deviations accepted by the review; the pull-over-xlsx takeover is written into the spec (Rev 7.2) |

## Plan revision 3 — plan-critic review 2 → fixes

| # | Fix |
|---|---|
| NB1 | `readXlsx` drains the workbook only after a complete read; an early exit never awaits the reader. New test: a bad cell mid-file fails that file and the next file imports (20 s timeout) |
| NB2 | The sample keeps `id` and `required` keys; the sample test asserts no failed file and that invoice headers were imported |
| NB3 | SOs of links resolved in the sweep join the re-match set; test added; spec §4 note (Rev 7.3) |
| NB4 | Runbook 9b: re-run a failed Sales_Order folder before any older folder |
| NB5 | Console listener in the dialog test; `m-auto` on the dialog |
| NB6 | CLI test uses a capture date in the past |
| NB7 | Spawned service uses port 0 and removes its temp folder |
| NB8 | E2E server uses `prepareDatabase` |
