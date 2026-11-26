// Read-only UI map of SPS Zoho Inventory via the signed-in itexe@ Chrome (:9335). Navigates only; never signs out or closes.
import { createRequire } from 'module';
const { chromium } = createRequire('/root/tools/zoho-itexe-browser/')('playwright');
const OUT = '/root/Project Management/reports/2026-10-08-pd-zoho-study/ui-map/';
const ORG = 'https://inventory.zoho.com/app/843825512#';
const b = await chromium.connectOverCDP('http://127.0.0.1:9335');
const page = b.contexts()[0].pages().find((p) => /zoho/.test(p.url()));
const calls = [];
page.on('request', (r) => { if (/\/api\/v1\//.test(r.url())) calls.push(r.method() + ' ' + r.url().replace(/organization_id=\d+/, 'organization_id=ORG').slice(0, 200)); });
const landmarks = () => page.evaluate(() => {
  const pick = (el) => ({ tag: el.tagName.toLowerCase(), id: el.id || null, cls: (el.className && el.className.baseVal === undefined ? String(el.className) : '').split(/\s+/).slice(0, 4).join(' '), test: el.getAttribute('data-test-id') || el.getAttribute('data-ember-action') && 'ember' || null, text: (el.innerText || '').trim().slice(0, 40) });
  const q = (s) => [...document.querySelectorAll(s)].slice(0, 6).map(pick);
  return { title: document.title, url: location.href, ember: !!window.Ember || !!document.querySelector('.ember-view'),
    header: q('header, .header, [class*="header"]'), tables: q('table'), rows: document.querySelectorAll('table tbody tr').length,
    testIds: [...new Set([...document.querySelectorAll('[data-test-id]')].map((e) => e.getAttribute('data-test-id')))].slice(0, 60),
    sidepanels: q('[class*="sidebar"], aside, nav') };
});
const steps = [['so-list', ORG + '/salesorders'], ['packages', ORG + '/packages'], ['shipments', ORG + '/shipments'], ['items', ORG + '/inventory/items']];
const res = {};
try {
  for (const [k, u] of steps) {
    calls.length = 0;
    await page.goto(u, { waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6000);
    await page.screenshot({ path: OUT + k + '.png' });
    res[k] = { ...(await landmarks()), apiCalls: [...calls] };
  }
  // open the first SO in the list
  calls.length = 0;
  await page.goto(ORG + '/salesorders'); await page.waitForTimeout(5000);
  const first = page.locator('table tbody tr').first();
  await first.click(); await page.waitForTimeout(6000);
  await page.screenshot({ path: OUT + 'so-detail.png' });
  res['so-detail'] = { ...(await landmarks()), apiCalls: [...calls] };
} catch (e) { res.error = String(e.message).slice(0, 500); }
await import('fs').then((fs) => fs.writeFileSync(OUT + 'landmarks.json', JSON.stringify(res, null, 1)));
console.log(Object.keys(res).join(','), res.error || 'ok');
await b.close(); // detaches only
