// Do bo cuc that bang Playwright: mo trang khuon, tai cac moc t goi window.__seek(t), ghi moi phan tu CHU dang hien (bbox muc muc in that, opacity thuc, tran chu).
//   node do.mjs --trang=<html> --root=<thu muc goc phuc vu> --ra=<do.json> --t=0,0.3,... [--w=1080 --h=1920]
// Playwright lay tu cong-cu/node_modules (cung ban capture.mjs); PLAYWRIGHT_DIR de doi.
import { existsSync, createReadStream, statSync, writeFileSync, realpathSync } from 'node:fs';
import { pathToFileURL, fileURLToPath } from 'node:url';
import http from 'node:http';
import path from 'node:path';

const opt = Object.fromEntries(process.argv.slice(2).filter(a => a.startsWith('--')).map(a => { const i = a.indexOf('='); return [a.slice(2, i), a.slice(i + 1)]; }));
if (!opt.trang || !opt.root || !opt.ra || !opt.t) { console.error('usage: node do.mjs --trang=<html> --root=<dir> --ra=<do.json> --t=0,0.3 [--w --h]'); process.exit(2); }
const here = path.dirname(fileURLToPath(import.meta.url));
const pwDir = process.env.PLAYWRIGHT_DIR || path.resolve(here, '../../cong-cu/node_modules/playwright');
if (!existsSync(pwDir)) { console.error('thieu playwright: ' + pwDir + ' (npm ci --ignore-scripts trong cong-cu/)'); process.exit(2); }
const { chromium } = await import(pathToFileURL(path.join(pwDir, 'index.mjs')).href);
const W = +(opt.w || 1080), H = +(opt.h || 1920), TS = opt.t.split(',').map(Number);
const root = realpathSync(path.resolve(opt.root)), abs = realpathSync(path.resolve(opt.trang));
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.ttf': 'font/ttf' };
const server = http.createServer((req, res) => {
  let f = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://x').pathname));
  try { f = realpathSync(f); } catch { res.writeHead(404); return res.end(); }
  const r = path.relative(root, f);
  if (!r || r.startsWith('..') || path.isAbsolute(r) || statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(f).toLowerCase()] || 'application/octet-stream' });
  createReadStream(f).pipe(res);
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));
const url = `http://127.0.0.1:${server.address().port}/${path.relative(root, abs).split(path.sep).map(encodeURIComponent).join('/')}`;

const browser = await chromium.launch();
let loi = null;
try {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => { loi = loi || ('pageerror: ' + e.message); });
  page.on('requestfailed', r => { loi = loi || ('requestfailed: ' + r.url()); });
  page.on('response', r => { if (r.status() >= 400) loi = loi || ('HTTP ' + r.status() + ' ' + r.url()); });
  await page.goto(url);
  await page.waitForFunction('window.__ready===true', null, { timeout: 30000 });
  const mau = [];
  for (const t of TS) {
    const phan_tu = await page.evaluate((t) => {
      window.__seek(t);
      const cv = document.createElement('canvas').getContext('2d');
      const out = [];
      const dir = new Map();
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let n = w.nextNode(); n; n = w.nextNode()) {
        if (!n.nodeValue.trim()) continue;
        const e = n.parentElement;
        if (!e || e.closest('script,style')) continue;
        if (!dir.has(e)) dir.set(e, []);
        dir.get(e).push(n);
      }
      for (const [e, nodes] of dir) {
        const cs = getComputedStyle(e);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        let op = 1;
        for (let a = e; a; a = a.parentElement) op *= parseFloat(getComputedStyle(a).opacity);
        if (op < 0.05) continue;
        const rects = [];
        for (const n of nodes) { const r = document.createRange(); r.selectNodeContents(n); for (const q of r.getClientRects()) if (q.width > 0 && q.height > 0) rects.push(q); }
        if (!rects.length) continue;
        const x0 = Math.min(...rects.map(q => q.left)), x1 = Math.max(...rects.map(q => q.right));
        const y0 = Math.min(...rects.map(q => q.top)), y1 = Math.max(...rects.map(q => q.bottom));
        const chu = nodes.map(n => n.nodeValue.trim()).join(' ');
        // muc muc in that (khong phai o noi dung font): mot dong -> dung do ink cua canvas; nhieu dong -> giu o noi dung (an toan, nghiem hon)
        let ink = { x0, y0, x1, y1 }, ks = 1;
        const fs = parseFloat(cs.fontSize);
        const bs = parseFloat(cs.webkitTextStrokeWidth) || 0;
        if (rects.length === 1) {
          cv.font = `${cs.fontWeight} ${fs}px ${cs.fontFamily}`;
          cv.letterSpacing = cs.letterSpacing === 'normal' ? '0px' : cs.letterSpacing;
          let txt = chu;
          if (cs.textTransform === 'uppercase') txt = txt.toUpperCase();
          const m = cv.measureText(txt);
          const hh = m.fontBoundingBoxAscent + m.fontBoundingBoxDescent;
          const k = hh > 0 ? (y1 - y0) / hh : 1;
          const ya = y0 + (m.fontBoundingBoxAscent - m.actualBoundingBoxAscent) * k;
          const yb = y0 + (m.fontBoundingBoxAscent + m.actualBoundingBoxDescent) * k;
          if (isFinite(ya) && isFinite(yb) && yb > ya) { ink = { x0, y0: ya, x1, y1: yb }; ks = k; }
        }
        const m2 = (bs / 2) * ks;       // vien chu nhan theo ti le (khung co the dang thu nho)
        out.push({ id: e.id || (e.closest('[id]') || {}).id || '', lop: String(e.className || ''), chu,
          x0: +(ink.x0 - m2).toFixed(1), y0: +(ink.y0 - m2).toFixed(1), x1: +(ink.x1 + m2).toFixed(1), y1: +(ink.y1 + m2).toFixed(1),
          op: +op.toFixed(3), fs, sw: e.scrollWidth, cw: e.clientWidth, sh: e.scrollHeight, ch: e.clientHeight, dong: rects.length });
      }
      return out;
    }, t);
    mau.push({ t, phan_tu });
  }
  writeFileSync(opt.ra, JSON.stringify({ w: W, h: H, mau }, null, 1));
  if (loi) throw new Error(loi);
} catch (e) {
  console.error('do.mjs LOI: ' + e.message); await browser.close(); server.close(); process.exit(1);
}
await browser.close(); server.close();
console.log('do.json mau=' + TS.length);
