# R4 - Login and hosting for the standalone portal + dashboard

Prepared by Abdul Hadhee | IT Executive. 17 Oct 2026. Research only: no live Zoho calls, no credentials, nothing deployed.
Evidence rule: VPS facts cite file:line or the command I ran; Zoho/Traefik claims cite a URL. Where the docs are silent I say "not stated".
SH and SPS figures are never summed.

## 0. Answer first

```
 Staff browser (HO / Kohalwila / Galle / phone)
        | HTTPS
        v
  Traefik (EasyPanel container, :443, Let's Encrypt)   <- rate limit, headers, optional IP allow-list
        | http://172.17.0.1:<port>
        v
  Portal (Node + Express + SQLite, PM2)                <- OWN accounts, sessions, roles, audit log
        |  server-side only
        v
  Zoho Inventory API (SPS org / SH org)                <- ONE service connection, tokens encrypted at rest
```

Recommendation:
1. **Login = own accounts (password + TOTP for managers/coordinators/admin).** "Sign in with Zoho" is an optional add-on later, not the foundation (reasons, section 2).
2. **Zoho API access is a separate thing from staff login.** The portal holds one least-scope service connection per Zoho org; staff never hold Zoho tokens. The portal's own audit log says who did what.
3. **Rizwan's temporary shared login:** one named, role-limited, expiring account, office-IP-only at Traefik, plus a "who is acting" name recorded on every action. It is a stop-gap and is labelled as weak (section 4).
4. **Hosting:** own PM2 service on its own subdomain behind Traefik, using the existing hand-written `custom.yaml` pattern; backups via SQLite `.backup` on a schedule (today there are none, section 6).

Earlier decisions this overrides (stated explicitly, as asked):
- "Zoho read-only everywhere" (old plan, `/root/CLAUDE.md` decisions 7 Oct and 8 Oct "Zoho stays read-only"): the new flow has the coordinators create the SPS SO and transfers for Galle/HO, so **some Zoho writes are now in scope**. That needs write scopes, which means a deliberate decision by the user (SPS) and the CEO (SH). Not decided here.
- "SH data via browser session, SH API requested later" (7 Oct): it still holds for **reading** SH until the SH admin grants API access. The research below assumes API access is eventually granted; it is not a given. Until then no SH write can be done by the portal.
- "Password login tunnel-only" and extension/userscript designs: not used here, per the brief.

## 1. How existing VPS services do auth (reference, not a frame)

| Service | Mechanism | Evidence | Reuse? |
|---|---|---|---|
| IT Utilities | username + password, **scrypt** with per-user salt, `timingSafeEqual`, JWT (12h per ARCHITECTURE) signed with `JWT_SECRET` from required env, stored client-side as Bearer | `/root/dev/IT_Utilities_Backend/src/utils/password.js:1-12`, `src/services/authService.js:7-27`, `src/config.js:44`, `src/middleware/auth.js:12-19` | Password hashing pattern yes. The Bearer-in-JS-storage pattern: no, use an HttpOnly cookie (section 3). |
| SH-IT Hub | in-memory sessions (8h), `sha256(pin+salt)` one round on short PINs (documented as weak) | `/root/Project Management/ARCHITECTURE.md:107-115` (scheme table), ARCHITECTURE.md:154 row 5 | No. Do not copy. |
| SH-IT Hub login limiter | per-IP failure limiter, folds IPv6 to /64, bounded memory, no global lockout; admin login returns one identical 401 and burns a dummy hash for unknown names | `/root/dev/SH-IT_Hub/backend/loginLimiter.js:1-26`, `adminLogin.js:1-36` | **Yes, reuse the idea / copy the module** (it has tests: `backend/test/loginLimiter.test.js`). |
| Hub | `app.set('trust proxy', 1)` so the real client IP comes through one proxy hop | `/root/dev/SH-IT_Hub/backend/server.js:27` | Yes, same setting (Traefik is one hop). |
| Employee Master | static shared Bearer `SERVICE_TOKEN`, machine-to-machine only | `/root/dev/employee-master-service/auth.js:1-30` | Only as the way the portal would **read** employee/manager data server-to-server, if the staff directory is sourced there. Not for humans. |
| Gazette Invoice | no login of its own; Traefik `basicAuth` in front | `/etc/easypanel/traefik/config/custom.yaml` (gazette-auth middleware) | Shows the pattern for edge auth. Too weak for the portal (one password, no identity). |

Observed gap: ARCHITECTURE.md:154 says "No backups of any database". Also `ufw status` returned "inactive" and `iptables -S` shows `-P INPUT ACCEPT` (commands run 17 Oct), while ARCHITECTURE.md:48 says Employee Master is "firewall to localhost" and `ss -ltn` shows 4200 on `0.0.0.0`. So "firewall protects it" is not currently true; the portal must not rely on it.

## 2. Login options compared

| Option | What it gives | Problems for this portal | Verdict |
|---|---|---|---|
| **A. Own accounts + TOTP** | Works for every person, incl. sales staff and Rizwan's team who may have no Zoho user. Roles and per-division scope (manager, coordinator, `division_pairs`) live in our DB where the dashboard already needs them. We control lockout, session length, audit. | We own password reset, enrolment, recovery codes. One new dependency for TOTP (a library) - **needs approval under the "new dependency" hard stop**; I have not checked which library to use. | **Primary.** |
| **B. Sign in with Zoho (Zoho Accounts OIDC)** | Identity from Zoho, no passwords stored. Zoho documents OIDC sign-in: request `scope=email`, discovery doc at `https://accounts.zoho.com/.well-known/openid-configuration`, ID token claims `sub`, `email`, `email_verified`, `name`; use `sub` as the stable id, not the email ([Zoho: Sign in using Zoho](https://www.zoho.com/accounts/protocol/oauth/sign-in-using-zoho.html)). | (1) The page does **not** say sign-in is limited to one Zoho organisation, and shows no org id claim, so the portal still needs its own allow-list and roles. (2) Not everyone is a Zoho user, and the user is Zoho admin for SPS only (`/root/CLAUDE.md` 7 Oct), so he cannot create SH Zoho users. (3) Whether Zoho can force MFA for those users is the Zoho org admin's setting, not something the portal can enforce - not verified. (4) The page does not name a userinfo endpoint; flow relies on the ID token. (5) Depends on Zoho being up to log in. | **Optional later** for people who have a Zoho user. Always map `sub` to a portal account that already exists and has a role. |
| **C. Google / Microsoft** | Familiar, strong MFA if the company tenant enforces it. | I found no evidence in the repo that staff have company Google/Microsoft accounts (mail is Bluehost IMAP per `/root/CLAUDE.md`). Needs an OAuth client registration at a third party and an admin there. Not researched further. | **Not recommended** unless the company already has a tenant. Ask the CEO. |
| **D. Office IP allow-list** | Cheap extra layer. Traefik v3.6.7 is running (`docker exec ... traefik version`), and its `ipAllowList` middleware matches the remote address by default; behind another proxy you must set `ipStrategy` ([Traefik ipAllowList](https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/ipallowlist/)). | Not identity. Fails for phones on mobile data and for anyone working from home; office public IPs may change (unknown for HO, Kohalwila, Galle - **to ask**). | **Use as a layer, never as the login.** Good fit for the shared account only (section 4). |

Why A over B as the base: the portal's real rules (who may accept for which division, who sees what) are roles in our own DB regardless of how a person proves identity. Adding B later only swaps "how you prove who you are", so choosing A first costs nothing.

### Account design (A)
- Table `users(id, email, display_name, role, scope, password_hash, totp_secret_enc, active, last_login)`, `sessions(id_hash, user_id, created, expires, ip, ua)`, `audit_log(...)`. Roles: `sales`, `stock_team`, `coordinator`, `manager`, `admin`.
- Passwords: scrypt as in IT Utilities (`utils/password.js:1-12`); minimum length 12 (the Hub's admin PIN policy already moved to 12: `adminLogin.js:12`).
- Session: random 256-bit id in a cookie flagged HttpOnly, Secure, SameSite=Lax; store only a hash of the id server-side; idle 8h / absolute 12h (the Hub uses 8h, IT Utilities 12h). Cookie rather than the IT Utilities Bearer token in script-readable storage - this is standard practice, not something I measured here.
- TOTP: required for `manager`, `coordinator`, `admin` (they approve and create SOs); optional for `sales` at first. Recovery codes printed once; reset only by admin. The TOTP secret is stored encrypted (section 5).
- Reuse the Hub's `loginLimiter.js` (per-IP, IPv6 /64) plus a per-account soft delay, and one identical failure message (`adminLogin.js:20-34`).
- Phones: nothing special, it is a normal responsive web app; the cookie works the same. Do not use IP allow-listing for these users.

## 3. Zoho API identity: separate from staff login

Facts from Zoho docs:
- Authorization endpoint `https://accounts.zoho.com/oauth/v2/auth`, token and refresh `.../oauth/v2/token`, revoke `.../oauth/v2/token/revoke`; header `Authorization: Zoho-oauthtoken <token>`, never a query param; scopes such as `ZohoInventory.salesorders.CREATE/READ/UPDATE/DELETE` and `ZohoInventory.transferorders.CREATE/READ/UPDATE/DELETE` ([Zoho Inventory API: OAuth](https://www.zoho.com/inventory/api/v1/oauth/)).
- Access token lasts 1 hour; with `access_type=offline` a refresh token is issued; the grant code is single-use and valid about 2 minutes ([Zoho web-app authorization](https://www.zoho.com/accounts/protocol/oauth/web-apps/authorization.html)). Note the Inventory page says 60 seconds; the two Zoho pages disagree, so treat the code as very short-lived.
- Refresh tokens "don't expire", but each re-consent creates a new one and at most 20 refresh tokens per user are kept, oldest deleted ([Inventory OAuth](https://www.zoho.com/inventory/api/v1/oauth/)). Refreshing is capped at 10 access tokens per 10 minutes ([Zoho access-token page](https://www.zoho.com/accounts/protocol/oauth/web-apps/access-token-expiry.html)) - so the portal must **cache one access token per org in memory and refresh on expiry**, never per request.
- Self Client: a client registered in the API console; the code is exchanged for tokens; code default expiry 3 minutes; refresh token does not expire ([Zoho Self Client](https://www.zoho.com/accounts/protocol/oauth/self-client/authorization-code-flow.html)). That page does not say it is meant for server-to-server, though the flow involves no redirect.
- Multi-DC: start at `accounts.zoho.com`, use the `api_domain` returned in the token response rather than hard-coding ([Zoho multi-DC](https://www.zoho.com/accounts/protocol/oauth/multi-dc/client-authorization.html)). Both orgs are US DC (task brief).
- Daily API limit by Inventory plan, per Zoho's KB: Free 1,000; Standard 2,500; Professional 5,000; Premium 75,000; Enterprise 10,000 ([Zoho KB](https://zstatic.zohostatic.com/inventory/kb/automation/per-day-api-limit.md)). The Premium/Enterprise ordering looks odd; I did not verify it. SPS's real figure is 7,500 (checked 7 Oct, in `/root/CLAUDE.md`), which matches none of these rows, so use the measured figure, not the table. SH: unknown.

Choice for the user (decision D-A below):
- **One service connection per org (recommended).** One dedicated Zoho user for the portal per org ("portal-service"), one Self Client or server-based client, least-scope (read + only the create scopes actually needed). Pros: only 1-2 refresh tokens to protect; call budget and the 10-per-10-minutes refresh cap are easy to control; works for staff without Zoho users. Cons: Zoho shows the service user as creator; the real person is only in **our** audit log. Mitigation: write the portal request number and the staff name into a Zoho reference/notes field if one exists (not verified which field; there is the existing "Clickup Link" SO field per `/root/CLAUDE.md` but I have not checked field permissions).
- **Per-user Zoho tokens.** Zoho shows the real creator. Cons: every user must be a Zoho user in the right org with the right role, many refresh tokens to store, 20-token cap per user, and most SH sales staff may not have SPS Zoho users. Not recommended.

Access prerequisites already known: the user is Zoho admin for SPS and can create the SPS client himself; **SH needs the SH admin (CEO)** to create the client and a service user (`/root/CLAUDE.md` 7 Oct). Whether a non-admin can register an API Console client for an org is not established here; ask when requesting.

## 4. Temporary shared login for Rizwan's team (until launch)

Constraint: they share one common login until the final demo/launch, then get individual logins. A shared login cannot attribute actions or carry per-person MFA, so the goal is to **limit what it can do, where it can be used, and for how long**.

```
 Rizwan's PC / office tablet --(office public IP)--> Traefik ipAllowList --> portal "stock_team_shared" account
                                                                              |- role: stock_team only (no admin, no approve, no user mgmt)
                                                                              |- every action prompts "Who is acting?" (pick from list) -> audit_log.actor_label
                                                                              |- expires on a fixed date; admin turns it off at launch
```

Controls, in order of value:
1. **Own account row, not the Traefik basicAuth trick.** The Gazette precedent (`custom.yaml` gazette-auth) gives one password and no identity, no lockout beyond rate limit. A real account gives a role, audit, session expiry and a kill switch.
2. **Role-limited:** `stock_team` can view, mark "in stock / fulfil", and "send to production". It cannot approve, create users, change settings, or see anything beyond the order queue. "Send to production" is a business-significant write, so it is logged with actor label and requires the actor pick.
3. **Office-IP only** for this account (check source IP in the app **and** an `ipAllowList` on a separate Traefik router if they have a fixed IP; with `ipStrategy` set correctly since Traefik is the first hop). The office public IPs of HO/Kohalwila are unknown - ask. If Rizwan's team sometimes uses phones, either give those individuals their own early accounts (best) or accept the shared account is office-only.
4. **"Who is acting" pick-list** (names of the real team) on each write. Not authentication - a colleague can pick someone else - so it is honest logging, and I will label it so in the UI and docs.
5. **Strong random password** (generated, 20+ chars, in the IT password register, not WhatsApp), rotated when anyone leaves the team, never reused with the 13 Oct common passwords.
6. **Hard expiry:** `expires_at` on the account (set to the launch date), plus a reminder in the project notes. Disabled by admin at launch; individual accounts created before that.
7. **Rate limit + lockout** using the Hub limiter; alert on failures.
8. **Better option if the team can bear it:** create their individual accounts now with a password but **no TOTP requirement** (stock_team only), and skip the shared login entirely. The brief says they use one login until launch, so I treat the shared account as the instruction and flag this as an alternative worth raising with Rizwan.

Residual risk, stated plainly: until individual logins exist, an action by the shared account cannot be tied to one person with certainty.

## 5. Hosting behind Traefik / EasyPanel, tokens and secrets

### Traefik / EasyPanel
- Traefik 3.6.7 runs as the `easypanel-traefik` container publishing 80 and 443; EasyPanel is on :3000 (`docker ps`, 17 Oct). Hand-written routing lives in `/etc/easypanel/traefik/config/custom.yaml` (its header says EasyPanel rewrites only `main.yaml`), and the container reaches the host at 172.17.0.1.
- Existing pattern to copy (read from that file): a router per host, e.g. `Host(`dx.standard-holdings.lk`)`, `entryPoints: [https]`, `tls: {certResolver: letsencrypt}`, middlewares such as `dx-ratelimit` (60/min, burst 30) and a headers middleware with `stsSeconds`.
- Proposed: a new subdomain (name to be chosen by the user; DNS record needed) with `portal-ratelimit`, `portal-headers` (HSTS), and the portal service at `http://172.17.0.1:<port>`.
- **Port:** not chosen here. Listening now (from `ss -ltn`): 3000, 3001, 3005, 4100, 4200, 4310, 4710, 5001, 8080, 8765 on all interfaces, and 127.0.0.1: 4199, 4601, 4711, 6969, 9333-9336. 4300 and 4400 are claimed per the brief. Pick at build time after re-running `ss -ltn`.
- **Binding:** existing services bind `0.0.0.0` (Hub `server.js:1601`, HOST default), which with an inactive ufw and `INPUT ACCEPT` leaves them reachable on the public IP directly, bypassing Traefik's TLS and middlewares. For the portal, bind to the docker bridge address Traefik reaches (172.17.0.1 per the doctrine, to be verified with `ip addr show docker0`) rather than `0.0.0.0`, so only Traefik can reach it. A host firewall rule is the user's call (infrastructure change, out of scope here).
- `app.set('trust proxy', 1)` as the Hub does, so rate limiting sees the client IP from `X-Forwarded-For`. Because Traefik is a trusted hop and the port is not public, the header is trustworthy; if the port were public an attacker could spoof it.
- Secure cookie works because TLS ends at Traefik; the portal sees HTTP. Hence trust proxy must be correct or the `Secure` cookie flag will not be set by some libraries.
- Is the portal a separate service or inside production-dashboard? Q8 on 2 Oct said inventory is separate; for this portal the brief says "standalone portal and dashboard". Not decided here; the auth design works either way.

### Secrets and Zoho tokens at rest
- Secrets in a `.env` outside the git repo (the repos already use `dotenv`: `employee-master-service/auth.js:9`); never in source or logs. `required('JWT_SECRET')` style fail-fast at startup is already the IT Utilities convention (`src/config.js:44`).
- Zoho client secret + refresh token: stored **encrypted** in the portal DB (or only in `.env` for one-per-org) using AES-256-GCM with a key held in env, not in the DB file. Reason: a stolen DB backup should not equal Zoho write access. Access token kept in memory only.
- TOTP secrets encrypted the same way. Password hashes are one-way (scrypt).
- The refresh token is the crown jewel: it does not expire (Zoho Self Client page above), so rotation means revoking at `.../oauth/v2/token/revoke` and re-issuing. Document that in the runbook. Re-consent adds a token (20 cap) so avoid casual re-consent.
- Least privilege: request only the scopes the flow needs. I cannot say which exact scopes cover reading item stock by location and creating transfer orders without reading the Inventory API reference per endpoint; the Inventory OAuth page lists items/salesorders/transferorders/inventoryadjustments groups only. Verify each endpoint's required scope in the API docs before requesting.
- Separate tokens per org (SPS 843825512, SH 843061977), separate DB columns, never mixed in one request path.
- Logging: never log the Authorization header, the code, or token responses.
- Processes run as root (ARCHITECTURE.md:156 row 10). Running the portal as an unprivileged user would be better; PM2 setup for that is a separate decision.

## 6. Backups
Today: no scheduled database backup (ARCHITECTURE.md:154). `shdeploy` backs up the DB at deploy time (per `/root/.claude/CLAUDE.md` section 4b), and `/root/backups` holds only two manual snapshots from 12 Sep. A deploy-time backup is not enough for a system holding orders and audit logs.
- Use SQLite's online backup (`sqlite3 db ".backup 'file'"`), as the engineering doctrine requires - not `cp`, because of WAL.
- Nightly backup to a dated file, keep 14 daily + 8 weekly, then copy **off the server** (same Contabo box is not a backup). Target not chosen; options are the Hetzner Storage Box / Backblaze already costed in the mail-storage reports (`/root/Project Management/reports/2026-09-27-mail-storage/`), but I have not checked their fit for this. Encrypt the copy.
- Because the DB holds encrypted tokens, **back up the encryption key separately** (sealed IT register); the backup alone must not suffice to read them, and losing the key means re-doing the Zoho consent.
- Test a restore once before launch.

## 7. Decisions for the user
- **D-A Zoho identity:** one service connection per org (recommended) vs per-user tokens. Includes accepting that Zoho shows the service user as creator.
- **D-B Write scopes:** approve SPS (and, via the CEO, SH) write scopes. This reverses the "read-only everywhere" rule.
- **D-C Login base:** own accounts + TOTP (recommended), with optional "Sign in with Zoho" later; confirm no company Google/Microsoft tenant exists.
- **D-D TOTP library:** approve one new dependency (not yet chosen or checked).
- **D-E Shared login:** accept the stop-gap in section 4, or give Rizwan's team individual accounts now. Provide office public IPs for HO, Kohalwila and Galle (not known to me) and the launch date for the expiry.
- **D-F Hosting:** subdomain name; whether to bind to the docker bridge only; who changes `custom.yaml` and DNS (the human, per the hard stops).
- **D-G Off-site backup target.**

## 8. Not verified (do not treat as fact)
- Whether Zoho sign-in can be limited to one organisation, and whether the org's Zoho MFA can be enforced (not stated on the OIDC page).
- Exact Zoho Inventory scopes per endpoint; SH's daily API limit; the Premium 75,000 vs Enterprise 10,000 ordering in the KB table.
- Whether a non-admin can register an API Console client.
- Authorization-code lifetime (docs say 2 min and 60 s on different pages).
- Office public IPs and whether they are static.
- docker0 address and that Traefik can reach a service bound only there.
