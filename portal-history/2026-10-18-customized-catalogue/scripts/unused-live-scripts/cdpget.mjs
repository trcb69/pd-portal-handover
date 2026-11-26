// GET-only Zoho Inventory fetcher via raw CDP. Usage: PORT=9335 ORG=843825512 node cdpget.mjs out.json path1 path2 ...
// Runs fetch() inside an existing inventory.zoho.com tab (no navigation, no close). ~1 req/1.2 s. Stops on 401/429.
import fs from 'node:fs';
const [out, ...paths] = process.argv.slice(2);
const PORT = process.env.PORT, ORG = process.env.ORG;
const tabs = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
const tab = tabs.find(t => t.type === 'page' && (process.env.TAB ? t.id === process.env.TAB : t.url.includes('inventory.zoho.com')));
if (!tab) { console.error('no inventory tab'); process.exit(2); }
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((ok, bad) => { ws.onopen = ok; ws.onerror = bad; });
let id = 0; const wait = new Map();
ws.onmessage = m => { const d = JSON.parse(m.data); if (wait.has(d.id)) { wait.get(d.id)(d); wait.delete(d.id); } };
const send = (method, params) => new Promise(r => { const i = ++id; wait.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => { if (wait.has(i)) { wait.delete(i); r({ timeout: true }); } }, 60000); });
const FN = `async u => { const ck = Object.fromEntries(document.cookie.split('; ').map(s => s.split(/=(.*)/s).slice(0, 2)));
  const r = await fetch(u, { headers: { 'X-ZCSRF-TOKEN': 'zomcsparam=' + (ck.zomcscook || ck.zomcsr) }, credentials: 'include' });
  return JSON.stringify({ st: r.status, body: await r.text() }); }`;
const res = fs.existsSync(out) ? JSON.parse(fs.readFileSync(out)) : {};
let n = 0;
for (const p of paths) {
  if (res[p]?.st === 200) continue;
  const u = `https://inventory.zoho.com/api/v1/${p}${p.includes('?') ? '&' : '?'}organization_id=${ORG}`;
  const d = await send('Runtime.evaluate', { expression: `(${FN})(${JSON.stringify(u)})`, awaitPromise: true, returnByValue: true });
  if (!d.result?.result?.value) { console.error('eval fail/timeout', JSON.stringify(d).slice(0,300)); break; }
  const r = JSON.parse(d.result.result.value);
  let body; try { body = JSON.parse(r.body); } catch { body = r.body.slice(0, 300); }
  res[p] = { st: r.st, body };
  if (r.st !== 200) console.error('HTTP', r.st, p, JSON.stringify(body).slice(0, 200));
  if (r.st === 429 || r.st === 401 || r.st === 403) break;
  if (++n % 20 === 0) fs.writeFileSync(out, JSON.stringify(res));
  await new Promise(s => setTimeout(s, 1200));
}
fs.writeFileSync(out, JSON.stringify(res));
console.log('saved', Object.keys(res).length, '->', out);
ws.close();
