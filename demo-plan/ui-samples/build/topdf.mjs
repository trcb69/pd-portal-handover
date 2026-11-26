// Turn the 5 canvas artboards into one PDF: strip the canvas wrapper, screenshot each at its size, place one per page.
// usage: node topdf.mjs   (paths are relative to this file)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'module';
const require = createRequire('/root/Project Management/reports/2026-09-27-explainer-video/motion/node_modules/');
const { chromium } = require('playwright');

const here = path.dirname(decodeURIComponent(new URL(import.meta.url).pathname));
const proj = path.join(here, '..', 'project');
const out = path.join(here, '..', '..', 'out', 'UI-Directions-2026-10-21.pdf');
const boards = [
  ['Main.dc.html', 1280, 820, '1 · Control room — management / GM'],
  ['Calm.dc.html', 1280, 820, '2 · Calm cards — production manager'],
  ['Conduit.dc.html', 1280, 820, '3 · IT Conduit brand — everyone'],
  ['Flow.dc.html', 1280, 820, '4 · Unit flow board — production floor'],
  ['Mobile.dc.html', 390, 844, '5 · Sales rep phone — order portal'],
];

const plain = (src) => src
  .replace(/<script src="\.\/support\.js"><\/script>/, '')
  .replace(/<script type="text\/x-dc"[\s\S]*?<\/script>/, '')
  .replace(/<\/?x-dc>/g, '')
  .replace(/<helmet>([\s\S]*?)<\/helmet>/, '$1');

const b = await chromium.launch();
const shots = [];
for (const [file, w, h, label] of boards) {
  const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  await p.setContent(plain(fs.readFileSync(path.join(proj, file), 'utf8')), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const buf = await p.screenshot({ clip: { x: 0, y: 0, width: w, height: h } });
  shots.push({ label, w, h, data: buf.toString('base64') });
  await p.close();
}
const pages = shots.map((s) => `<section><h2>${s.label}</h2><img src="data:image/png;base64,${s.data}" style="max-width:100%;max-height:170mm;${s.w < 600 ? 'height:170mm;' : 'width:100%;'}"></section>`).join('');
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@page{size:A4 landscape;margin:12mm}
body{margin:0;font:13px Inter,Arial,sans-serif;color:#111}
section{page-break-after:always;display:flex;flex-direction:column;align-items:center;gap:6mm}
h2{align-self:flex-start;margin:0;font:600 16px 'Space Grotesk',Arial,sans-serif}
img{border:1px solid #ddd}
</style></head><body>
<section style="justify-content:center;height:180mm"><h1 style="font:700 30px Arial,sans-serif;margin:0;align-self:flex-start">SH / SPS — 5 UI directions (samples)</h1>
<p style="align-self:flex-start;max-width:200mm">Quick sketches with sample data, for choosing a look before the real design. Pick one, mix (e.g. "3's colours with 2's cards"), or reject. 21 Oct 2026.</p>
<p style="align-self:flex-start">Prepared by Abdul Hadhee | IT Executive</p></section>
${pages}</body></html>`;
const pg = await b.newPage();
await pg.setContent(html, { waitUntil: 'load' });
await pg.pdf({ path: out, format: 'A4', landscape: true, printBackground: true });
await b.close();
console.log('written', out, shots.length, 'boards');
