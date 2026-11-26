// usage: node render.mjs in.html out.pdf [shots-prefix]
import { createRequire } from 'module';
const require = createRequire('/root/Project Management/reports/2026-09-27-explainer-video/motion/node_modules/');
const { chromium } = require('playwright');
const [,, inp, out, shots] = process.argv;
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 794, height: 1123 } });
await p.goto('file://' + inp, { waitUntil: 'networkidle' });
await p.evaluate(() => document.fonts.ready);
await p.emulateMedia({ media: 'print' });
// overflow check: any .page whose content exceeds its box
const over = await p.evaluate(() => [...document.querySelectorAll('.page')].map((s, i) => ({ i: i + 1, sh: s.scrollHeight, ch: s.clientHeight })).filter(x => x.sh > x.ch + 1));
console.log('overflow pages:', JSON.stringify(over));
await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true });
if (shots) {
  const n = await p.evaluate(() => document.querySelectorAll('.page').length);
  for (let i = 0; i < n; i++) await p.locator('.page').nth(i).screenshot({ path: `${shots}-p${i + 1}.png` });
  console.log('shots', n);
}
await b.close();
