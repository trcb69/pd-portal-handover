# Plan-critic round 2: PD demo release Rev 2 (21 Oct 2026) — verdict BLOCK

Saved by the lead from the critic's hand-back (read-only tools; no git diff of V-D4, no npm check).

Round-1 findings: C1, C3, C4, C5, C6 resolved; C2 mostly (AC-D4 wrong for home OPD); C7 partly.

## Blocking
- **C1** Session types undefined: `sessions.via` CHECK only ('password','zoho') (`006:87`); new users have must_reset=1 (`admin-users.js:50`) and requireAuth 403s them except Zoho sessions (`middleware.js:74-79`); the enrol step looks like a tunnel admin session. Add `sessions.auth_method` (CHECK) in 007; new sign-in sessions skip must_reset; device-less sessions only on loopback; enrol step only reaches enrol routes; ACs.
- **C2** Tunnel break-glass dead: `requireOrigin` accepts only APP_ORIGIN (`middleware.js:24`, `create-app.js:36`); tunnel browsers send `http://localhost:4300`. Exact origin list, localhost only on loopback sockets without XFF; AC-D13 on the socket rule (`auth.js:28`); 403 vs 404 and admin-only are new behaviour; AC for first admin via tunnel.
- **C3** Synced passkeys break "approved devices"; UV not required. (Superseded: passkeys dropped in Rev 3.)
- **C4** No allow-list editor: `web/src/admin/Users.tsx` has no email field; the only API path setting `zoho_email` (`admin-users.js:15,107-119`) may be V-D4 work. Name the editor as in-scope; say what of V-D4 stays.
- **C5** AC-D4 false for home OPD: families [["OPD","PACKPRO"]] + home OPD → `[MACPRO, OPD, CPU]` (`line-jobs.js:69,75`).

## Notes
N1 007 breaks AC48 (`release-migrations.test.js:40,44-47`) + MANIFEST entry · N2 create MACPRO before `PUT /admin/division-rules` (`admin-config.js:531-534`); the PUT replaces 5 keys (`:539`) → undo saves all 5 · N3 `import-routes.js` is a CLI, no audit (`:78-89`); admin-edited lids become source='admin' and are skipped on re-import (`:81`) · N4 set-up script: 409 on re-create = success; undo list written once, appended before each change · N5 AC-D9 timing untestable → queue mail; same answer at the rate cap · N6 restate AC-D14 AC48-style · N7 WebAuthn storage (superseded) · N8 cookie lifetime claim false (`sessions.js:3-4`) · N9 admin one-time code not specified · N10 person block must block devices; self-approval rule; out-of-band confirmation · N11 first deploy: rollback = pm2 delete + Traefik route removal; anonymise `test/fixtures/zoho/sample-200.json` before push (`runbook-release-0.md:83`); runbook Part B steps 2–4 (`:89-126`); shared Traefik custom.yaml · N12 estimate +2–3 days; name a demo date and a cut list · N13 Windows Hello unverified (superseded) · N14 npm versions unchecked by the critic (the lead checked on 21 Oct).

## Simpler alternatives offered
Admin one-time enrolment link instead of email codes; or Sign in with Zoho as the first-time check. (The owner chose email login + admin approval on 21 Oct; see Rev 3 §2.)
