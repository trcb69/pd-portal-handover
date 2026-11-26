// Page a Zoho Inventory list (GET only, 1 req/1.2s) until rows older than CUTOFF. Saves one json file per page.
// Usage: node pager.mjs <module> <sort_column> <timefield> <cutoffISO> <outprefix> [extra query]
import fs from 'node:fs';
const [mod, sortc, tf, cutoff, prefix, extra=''] = process.argv.slice(2);
const tabs = await (await fetch('http://127.0.0.1:9335/json')).json();
const tab = tabs.find(t => t.type === 'page' && /inventory\.zoho\.com/.test(t.url));
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((ok, bad) => { ws.onopen = ok; ws.onerror = bad; });
let id = 0; const wait = new Map();
ws.onmessage = m => { const d = JSON.parse(m.data); if (wait.has(d.id)) { wait.get(d.id)(d); wait.delete(d.id); } };
const send = (method, params) => new Promise(r => { const i = ++id; wait.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const FN = `async u => { const ck = Object.fromEntries(document.cookie.split('; ').map(s => s.split(/=(.*)/s).slice(0, 2)));
  const r = await fetch(u, { method:'GET', headers: { 'X-ZCSRF-TOKEN': 'zomcsparam=' + (ck.zomcscook || ck.zomcsr) }, credentials: 'include' });
  return JSON.stringify({ st: r.status, body: await r.text() }); }`;
for (let page = 1; page < 400; page++) {
  const f = `${prefix}_p${String(page).padStart(3,'0')}.json`;
  let body;
  if (fs.existsSync(f)) body = JSON.parse(fs.readFileSync(f));
  else {
    const u = `https://inventory.zoho.com/api/v1/${mod}?per_page=200&page=${page}&sort_column=${sortc}&sort_order=D${extra}&organization_id=843825512`;
    const d = await send('Runtime.evaluate', { expression: `(${FN})(${JSON.stringify(u)})`, awaitPromise: true, returnByValue: true });
    const r = JSON.parse(d.result.result.value);
    if (r.st !== 200) { console.error('HTTP', r.st, f, r.body.slice(0,200)); process.exit(1); }
    body = JSON.parse(r.body); fs.writeFileSync(f, JSON.stringify(body));
    await new Promise(s => setTimeout(s, 1200));
  }
  const key = Object.keys(body).find(k => Array.isArray(body[k]));
  const rows = body[key]; const last = rows.at(-1);
  console.log(page, key, rows.length, last?.[tf]);
  if (!rows.length || !body.page_context.has_more_page || (last[tf] && last[tf] < cutoff)) break;
}
console.log('DONE', mod, sortc);
ws.close();
