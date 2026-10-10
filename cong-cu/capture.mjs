// Deterministic HTML -> video capture (Playwright + ffmpeg). Tested on macOS (M1 Pro), Playwright 1.63, ffmpeg 9.0.2.
//
// DUNG (usage):
//   node capture.mjs <trang.html|url> <out.mp4|out.mov|out.webm> [fps=30] [giay=3] [w=1080] [h=1920] [co...]
//   co (flags):
//     --alpha            nen trong suot (page gets ?alpha=1). Dung voi .mov (ProRes 4444) hoac .webm (VP9 alpha)
//     --jpeg             chup JPEG thay PNG (nhanh hon, khong alpha)
//     --gpu              Chromium day du (WebGL tren GPU Metal) thay cho headless-shell (SwiftShader CPU)
//     --root=DIR         thu muc goc de phuc vu file (mac dinh = thu muc chua trang). Trang co the dung ../fonts khi root cao hon
//     --stills=0.5,3,5.5 chi chup anh tinh PNG tai cac moc giay; <out> la tien to: out_0.50s.png ...
//     --workers=N        render song song N trinh duyet (moi cai 1 doan lien tiep), roi noi lai bang concat (khong nen lai)
//     --scale=2          dung trang theo w x h nhung xuat anh gap doi (vd 1080x1920 -> 2160x3840 = 4K doc)
//     --enc=vt           mp4 bang h264_videotoolbox (encoder phan cung macOS; -b:v 40M neu cao>=2160, 16M neu nho hon; -allow_sw 0).
//                        Chi cho .mp4. Mac dinh van la libx264 -preset slow -crf 18. Loi ro rang neu may khong co VideoToolbox.
//                        Do 4K60 6s 8 worker: libx264 36 s, vt 27 s (1080p chi chenh vai %). Cho 1 file giao khach van uu tien libx264.
//     --quiet            tat dong tien do (mac dinh: moi >=2 s in 1 dong ra stderr: [xong/tong] fps=.. ETA=..s, cong don moi worker)
//     --svgfix           opt-in: chen <style>svg text{text-rendering:geometricPrecision}</style> khi DOM san sang
//                        (chu SVG bi lech khi to tien scale; bai hoc motion-fx-lab). KHONG bat mac dinh -> khung cu khong doi.
//
// An toan khi loi (atomic): video ghi vao thu muc tam DOC QUYEN canh dich (mkdtemp .capture-tmp-XXXX, ten file co dinh an toan), chi rename
//   sang <out> o buoc CUOI CUNG khi MOI worker + concat + faststart xong va khong co loi trang nao (pageerror / request failed / HTTP>=400
//   / anh khong giai ma, ke ca SAU khung dau -> ABORT, khong ghi de dich). Loi / Ctrl-C -> kill ffmpeg, dong moi trinh duyet, cho moi worker
//   ket thuc (allSettled), xoa DUNG thu muc tam do, thoat != 0; file dich cu (neu co) giu nguyen. --stills ghi thang, khong qua file tam.
// WebGL: canvas webgl/webgl2 (trang chinh VA iframe) duoc ghi lai; sau MOI lan seek kiem isContextLost() -> ABORT (khong ra file) kem t va worker.
//   (8 SwiftShader song song co the mat context va ra khung trang khong bao loi.)  CHUA ho tro: OffscreenCanvas/WebGL tao trong Web Worker.
//
// Contract the page should follow (any of these are picked up automatically):
//   - CSS @keyframes / transitions / element.animate()  -> seeked via document.getAnimations()
//   - SVG SMIL                                          -> svg.setCurrentTime()
//   - GSAP: build ONE timeline with {paused:true} and expose it as window.__tl  (or expose window.__seek(t))
//   - rAF / performance.now / Date / setTimeout driven code (canvas, three.js, lottie-web, Motion JS loop)
//       -> driven by Playwright's fake clock (page.clock), advanced exactly to each frame time
//   - set window.__ready = false at the top, true when fonts/images/splits are done
import { chromium } from 'playwright';
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, createReadStream, statSync, writeFileSync, realpathSync, unlinkSync, renameSync, mkdtempSync, readdirSync, rmdirSync } from 'node:fs';
import http from 'node:http';
import path from 'node:path';

const args = process.argv.slice(2);
const opt = Object.fromEntries(args.filter(a => a.startsWith('--')).map(a => { const i = a.indexOf('='); return i < 0 ? [a.slice(2), true] : [a.slice(2, i), a.slice(i + 1)]; }));   // tach o dau '=' DAU TIEN (duong dan co the chua '=')
const [src, out, fpsS = '30', secS = '3', wS = '1080', hS = '1920'] = args.filter(a => !a.startsWith('--'));
if (!src || !out) { console.error('usage: node capture.mjs <page.html|url> <out.mp4|.mov|.webm> [fps] [seconds] [w] [h] [--alpha] [--jpeg] [--gpu] [--root=DIR] [--stills=t1,t2] [--workers=N] [--scale=2] [--enc=vt] [--quiet] [--svgfix]'); process.exit(2); }
const FPS = +fpsS, SECONDS = +secS, W = +wS, H = +hS;
const QUIET = !!opt.quiet, SVGFIX = !!opt.svgfix;
const ALPHA = !!opt.alpha, JPEG = !!opt.jpeg && !ALPHA;
const STILLS = typeof opt.stills === 'string' ? opt.stills.split(',').map(Number).filter(n => n >= 0).sort((a, b) => a - b) : null;

// Local files are served over http://127.0.0.1 — file:// blocks ES modules (CORS origin 'null'), importmaps, fetch() of JSON (Lottie), some fonts.
let server, url = src;
if (existsSync(src)) {
  const abs = realpathSync(path.resolve(src));
  const root = realpathSync(path.resolve(typeof opt.root === 'string' ? opt.root : path.dirname(abs)));
  const inside = (f) => { const r = path.relative(root, f); return r && !r.startsWith('..') && !path.isAbsolute(r); };
  if (!inside(abs)) { console.error('--root must contain the page'); process.exit(2); }
  const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
    '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.lottie': 'application/zip',
    '.riv': 'application/octet-stream', '.wasm': 'application/wasm', '.mp3': 'audio/mpeg', '.wav': 'audio/wav' };
  server = http.createServer((req, res) => {
    let f = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://x').pathname));
    try { f = realpathSync(f); } catch { res.writeHead(404); return res.end(); }        // resolve symlinks before the boundary check
    if (!inside(f) || statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': types[path.extname(f).toLowerCase()] || 'application/octet-stream' });
    createReadStream(f).pipe(res);
  }).listen(0, '127.0.0.1');
  await new Promise(r => server.once('listening', r));
  const rel = path.relative(root, abs).split(path.sep).map(encodeURIComponent).join('/');
  url = `http://127.0.0.1:${server.address().port}/${rel}`;
}
if (ALPHA) { const u = new URL(url); u.searchParams.set('alpha', '1'); url = u.toString(); }   // also for plain URLs

// frame schedule (integer ms => no float drift)
const times = STILLS ? STILLS.map(s => Math.round(s * 1000)) : Array.from({ length: Math.round(FPS * SECONDS) }, (_, i) => Math.round(i * 1000 / FPS));
const SCALE = Math.max(1, +opt.scale || 1);                       // --scale=2: dung trang 1080x1920, xuat 2160x3840 (4K doc)
const WORKERS = STILLS ? 1 : Math.max(1, Math.min(+opt.workers || 1, times.length));
const OW = W * SCALE, OH = H * SCALE;

// ---- encoder args (frames piped in, no temp PNGs). RGB -> YUV with the BT.709 matrix AND bt709 tags (ffmpeg 9 ignores -color_primaries/-color_trc) ----
const tag = 'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv';
const ext = path.extname(out).toLowerCase();
if (opt.enc !== undefined && opt.enc !== 'vt') { console.error(`--enc chi nhan 'vt' (nhan: ${opt.enc})`); process.exit(2); }
const VT = opt.enc === 'vt';
if (VT && (ext !== '.mp4' || ALPHA)) { console.error('--enc=vt chi dung cho .mp4 va khong kem --alpha (h264_videotoolbox khong co alpha / webm / prores 4444)'); process.exit(2); }
if (VT) {
  const r = spawnSync('ffmpeg', ['-hide_banner', '-encoders'], { encoding: 'utf8' });
  if (!/h264_videotoolbox/.test(r.stdout || '')) { console.error('--enc=vt: ffmpeg nay khong co encoder h264_videotoolbox (can macOS + ffmpeg build co VideoToolbox)'); process.exit(2); }
}
const mp4v = VT ? ['-c:v', 'h264_videotoolbox', '-allow_sw', '0', '-b:v', OH >= 2160 ? '40M' : '16M', '-profile:v', 'high']   // 40M/16M = de xuat, xem do thuc te khi kiem
                : ['-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-profile:v', 'high'];
const enc = ext === '.mov'
  ? ['-vf', `scale=out_color_matrix=bt709:out_range=tv,format=${ALPHA ? 'yuva444p10le' : 'yuv444p10le'},${tag}`, '-c:v', 'prores_ks', '-profile:v', '4444', '-vendor', 'apl0']
  : ext === '.webm'
  ? ['-vf', `scale=out_color_matrix=bt709:out_range=tv,format=${ALPHA ? 'yuva420p' : 'yuv420p'},${tag}`, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '24', '-row-mt', '1', ...(ALPHA ? ['-auto-alt-ref', '0'] : [])]
  : ['-vf', `scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,${tag}`, ...mp4v];

// ---- registry: moi thu can huy khi loi (trinh duyet, ffmpeg, worker) + THU MUC TAM DOC QUYEN cua chinh lan chay nay ----
// Moi file tam nam trong mkdtemp canh dich (ten co dinh, an toan: khong phu thuoc <out>, khong chua xuong dong / dau nhay) -> khong the dam vao file co san.
const liveBrowsers = new Set(), liveFF = new Set(), inflight = new Set();
let aborting = false, firstError = null, tmpDir = null;
const tmpPath = (name) => path.join(tmpDir, name);
function startFF(argv, stdio) {
  if (aborting) throw new Error('aborting');
  const ff = spawn('ffmpeg', argv, { stdio });
  const e = { ff, finished: false, stdinErr: null };
  e.done = new Promise((res, rej) => {
    ff.once('error', err => { e.finished = true; liveFF.delete(e); rej(new Error('ffmpeg: ' + err.message)); });          // spawn that bai (khong co ffmpeg...)
    ff.once('close', (c, sig) => { e.finished = true; liveFF.delete(e); c === 0 ? res() : rej(new Error('ffmpeg exit ' + (c ?? sig))); });
  });
  e.done.catch(() => {});             // tranh unhandled rejection; noi can no tu await e.done
  liveFF.add(e);
  return e;
}
const runFF = (argv, what) => startFF(argv, ['ignore', 'inherit', 'inherit']).done.catch(err => { throw new Error(`${what}: ${err.message}`); });
function startEncoder(file) {
  const e = startFF(['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', JPEG ? 'mjpeg' : 'png', '-i', '-',
    ...enc, '-r', String(FPS), file], ['pipe', 'inherit', 'inherit']);
  e.ff.stdin.on('error', err => { e.stdinErr = err; });          // EPIPE khi ffmpeg chet giua chung: khong de crash, bao qua writeFrame / e.done
  return e;
}
// ghi 1 khung vao ffmpeg; cho 'drain' NHUNG dung ngay khi ffmpeg ket thuc / loi (khong treo)
async function writeFrame(e, buf) {
  if (e.finished || e.stdinErr) { await e.done; throw new Error('ffmpeg ended early' + (e.stdinErr ? ': ' + e.stdinErr.message : '')); }   // await: lay loi that (exit code / spawn)
  if (e.ff.stdin.write(buf)) return;
  let onDrain;
  const drained = new Promise(r => { onDrain = r; e.ff.stdin.once('drain', r); });
  const ended = e.done.then(() => { throw new Error('ffmpeg ended early'); }); ended.catch(() => {});
  try { await Promise.race([drained, ended]); } finally { e.ff.stdin.off('drain', onDrain); }
  if (e.stdinErr) throw new Error('ffmpeg stdin: ' + e.stdinErr.message);
}
function cleanTmp() {                 // chi xoa noi dung thu muc tam do chinh lan chay nay mkdtemp (khong glob, khong cham file khac)
  if (!tmpDir) return;
  try { for (const f of readdirSync(tmpDir)) { try { unlinkSync(path.join(tmpDir, f)); } catch {} } rmdirSync(tmpDir); } catch {}
}
// dung moi thu NGAY (khong cho): danh dau huy, kill ffmpeg, dong trinh duyet. Khong don file (de allSettled xong moi don).
async function stopAll() {
  aborting = true;
  for (const e of [...liveFF]) { try { e.ff.kill('SIGKILL'); } catch {} }
  await Promise.allSettled([...liveBrowsers].map(b => b.close()));
}
async function abortAll() {
  await stopAll();
  await Promise.allSettled([...inflight]);                       // cho MOI worker ket thuc (ke ca worker dang launch) truoc khi don
  await Promise.allSettled([...liveFF].map(e => e.done));
  cleanTmp();
}
function fail(err) { if (!firstError) firstError = err; return stopAll(); }
// chay cac worker song song; 1 worker loi -> dung het, cho tat ca ket thuc (allSettled), nem loi DAU TIEN
async function runWorkers(jobs) {
  const ps = jobs.map(j => { const p = j().catch(async e => { await fail(e); throw e; }); inflight.add(p); p.catch(() => {}).finally(() => inflight.delete(p)); return p; });
  const res = await Promise.allSettled(ps);
  const bad = res.find(r => r.status === 'rejected');
  if (bad) throw firstError || bad.reason;
}

// ---- tien do: cong don moi worker, >=2 s / dong ra stderr ----
const progress = { done: 0, total: STILLS ? 0 : times.length, t0: 0 };
let progTimer = null;
function progLine() {
  const el = (Date.now() - progress.t0) / 1000, fps = el > 0 ? progress.done / el : 0;
  const eta = fps > 0 ? Math.max(0, (progress.total - progress.done) / fps) : 0;
  process.stderr.write(`[${progress.done}/${progress.total}] fps=${fps.toFixed(1)} ETA=${eta.toFixed(0)}s\n`);
}
const noteFrame = () => { if (!progress.t0) { progress.t0 = Date.now(); if (!QUIET && !STILLS) progTimer = setInterval(progLine, 2000); } progress.done++; };

// ---- one worker = one browser rendering a contiguous chunk of frame times ----
// default = chromium-headless-shell (WebGL via SwiftShader CPU). --gpu = full Chromium 'new headless' (WebGL on Apple GPU via Metal; faster 3D)
let lateTotal = 0;
async function renderChunk(chunk, file, id) {
  const browser = await chromium.launch(opt.gpu ? { channel: 'chromium' } : {});
  liveBrowsers.add(browser);
  try {
    if (aborting) throw new Error('aborting');                    // huy xay ra trong luc launch: dong browser vua len (finally)
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE });
    const errs = [];
    page.on('pageerror', e => errs.push(String(e)));
    page.on('requestfailed', r => { if (!r.url().endsWith('/favicon.ico')) errs.push(`request failed: ${r.url()} (${r.failure()?.errorText})`); });
    page.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('/favicon.ico')) errs.push(`HTTP ${r.status()}: ${r.url()}`); });
    // WebGL: ghi lai moi context webgl/webgl2 (canvas + OffscreenCanvas) de kiem isContextLost() sau moi lan seek. Chay truoc script cua trang.
    await page.addInitScript(() => {
      window.__glCtx = [];
      const hook = (proto) => {
        if (!proto || !proto.getContext) return;
        const orig = proto.getContext;
        proto.getContext = function (type, ...rest) {
          const c = orig.call(this, type, ...rest);
          if (c && /^(experimental-)?webgl2?$/.test(String(type)) && !window.__glCtx.includes(c)) {
            window.__glCtx.push(c);
            try { this.addEventListener?.('webglcontextlost', () => { window.__glLost = true; }); } catch {}
          }
          return c;
        };
      };
      hook(window.HTMLCanvasElement?.prototype); hook(window.OffscreenCanvas?.prototype);
    });
    if (SVGFIX) await page.addInitScript(() => {
      const add = () => { const st = document.createElement('style'); st.textContent = 'svg text{text-rendering:geometricPrecision}'; (document.head || document.documentElement).appendChild(st); };
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add, { once: true }); else add();
    });
    // kiem MOI frame (main + iframe): init script ap cho ca iframe. OffscreenCanvas tao trong Web Worker thi CHUA ho tro (xem usage).
    const glLost = async () => { for (const fr of page.frames()) { try { if (await fr.evaluate(() => !!window.__glLost || (window.__glCtx || []).some(c => { try { return c.isContextLost(); } catch { return false; } }))) return true; } catch {} } return false; };
    await page.clock.install({ time: 0 });                // fake Date/perf.now/rAF/timers ...
    await page.clock.pauseAt(1000);                       // ... and freeze them BEFORE the page runs any script
    await page.goto(url, { waitUntil: 'load' });
    // Init phase. The clock is frozen, so timers never fire on their own: runFor(0) fires ZERO-delay timers
    // (setTimeout(fn,0), lottie 'DOMLoaded'...) without moving time. Pages must not need timers > 0 ms to become ready.
    const readyDeadline = Date.now() + 30000;
    while (true) {
      await page.clock.runFor(0);
      if (await page.evaluate(() => window.__ready !== false)) break;
      if (Date.now() > readyDeadline) throw new Error('window.__ready stayed false for 30s (init must not wait on timers > 0 ms)' + (errs.length ? '\nPage errors:\n' + errs.join('\n') : ''));
      await new Promise(r => setTimeout(r, 50));
    }
    await page.evaluate(() => document.fonts.ready);      // webfonts must be loaded before frame 0
    const badImgs = await page.evaluate(() => Promise.all([...document.images].map(i => i.decode().then(() => null, () => i.src))).then(a => a.filter(Boolean)));
    for (const s of badImgs) errs.push(`image failed to decode: ${s}`);
    if (errs.length) throw new Error('page not clean before frame 0:\n' + errs.join('\n'));

    const enc = file ? startEncoder(file) : null;
    let prev = 0;
    for (const tMs of chunk) {
      if (tMs > prev) { await page.clock.runFor(tMs - prev); prev = tMs; }   // a worker starting mid-video runs the clock up to its first frame
      await page.evaluate(async (t) => {
        // CSS + WAAPI: pause and seek every Animation. Ones alive at the first seek start at t=0;
        // ones that appear later (class toggled by a timer, element.animate() in a callback) start at the frame they are FIRST SEEN
        // -> with sparse --stills or --workers that moment differs from a single full render. Declare all animations at load to stay exact.
        const base = (window.__animBase ||= { first: true, map: new WeakMap(), late: 0 });
        for (const a of document.getAnimations()) {
          if (!base.map.has(a)) { base.map.set(a, base.first ? 0 : t); if (!base.first) base.late++; }
          a.pause(); a.currentTime = Math.max(0, t - base.map.get(a));
        }
        base.first = false;
        // SMIL (<animate>, <animateTransform>, <animateMotion>) is NOT in getAnimations() and ignores page.clock:
        for (const svg of document.querySelectorAll('svg:not(svg svg)')) { svg.pauseAnimations?.(); svg.setCurrentTime?.(t / 1000); }
        if (window.__seek) await window.__seek(t / 1000);                            // may be async (img.decode, video seek)
        else if (window.__tl) window.__tl.seek(t / 1000, false);                    // GSAP master timeline
      }, tMs);
      if (await glLost()) throw new Error(`WebGL context lost at t=${(tMs / 1000).toFixed(3)}s (worker ${id})`);
      if (errs.length) throw new Error(`page error after frame 0 at t=${(tMs / 1000).toFixed(3)}s (worker ${id}), khong ghi file:\n` + errs.join('\n'));
      if (!enc) {
        const f = `${out}_${(tMs / 1000).toFixed(2)}s.png`;
        writeFileSync(f, await page.screenshot({ type: 'png', omitBackground: ALPHA }));
        console.log('still', f);
      } else {
        const buf = await page.screenshot(JPEG ? { type: 'jpeg', quality: 92 } : { type: 'png', omitBackground: ALPHA });
        await writeFrame(enc, buf);
        noteFrame();
      }
    }
    if (await glLost()) throw new Error(`WebGL context lost before the end (worker ${id})`);
    if (errs.length) throw new Error(`page error (worker ${id}), khong ghi file:\n` + errs.join('\n'));      // loi trang CHAN rename: khong bao gio ghi de dich
    if (enc) { enc.ff.stdin.end(); await enc.done; }
    lateTotal += await page.evaluate(() => window.__animBase?.late || 0);
  } finally {
    await browser.close().catch(() => {});
    liveBrowsers.delete(browser);
  }
}

const t0 = Date.now();
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, async () => { console.error(`ABORT — ${sig}`); clearInterval(progTimer); await abortAll(); server?.close(); process.exit(130); });
try {
  if (STILLS) {
    await renderChunk(times, null, 0);
  } else {
    // thu muc tam doc quyen canh dich; moi trung gian nam trong do. Dich chi bi cham bang 1 lenh rename CUOI CUNG.
    tmpDir = mkdtempSync(path.join(path.dirname(path.resolve(out)), '.capture-tmp-'));
    let finalTmp;
    if (WORKERS === 1) {
      const a = tmpPath('a' + ext);
      await runWorkers([() => renderChunk(times, a, 0)]);
      if (ext !== '.webm') {
        // faststart cho file 1 luong (ban nhieu luong da co o buoc concat)
        finalTmp = tmpPath('fs' + ext);
        await runFF(['-y', '-loglevel', 'error', '-i', a, '-c', 'copy', '-movflags', '+faststart', finalTmp], 'faststart');
        unlinkSync(a);
      } else finalTmp = a;
    } else {
      // chia khung thanh WORKERS doan lien tiep -> moi doan 1 file -> noi bang concat (copy, khong nen lai)
      const per = Math.ceil(times.length / WORKERS);
      const chunks = Array.from({ length: WORKERS }, (_, k) => times.slice(k * per, (k + 1) * per)).filter(c => c.length);
      const parts = chunks.map((_, k) => `p${k}${ext}`);                                  // ten an toan, tuong doi trong tmpDir
      await runWorkers(chunks.map((c, k) => () => renderChunk(c, tmpPath(parts[k]), k)));
      writeFileSync(tmpPath('list.txt'), parts.map(p => `file '${p}'`).join('\n'));          // ten tuong doi so voi list.txt (concat -safe 0)
      finalTmp = tmpPath('final' + ext);
      await runFF(['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', tmpPath('list.txt'), '-c', 'copy', ...(ext === '.webm' ? [] : ['-movflags', '+faststart']), finalTmp], 'concat');
      for (const p of [...parts, 'list.txt']) unlinkSync(tmpPath(p));                      // don trung gian TRUOC rename cuoi
    }
    renameSync(finalTmp, out);                                                           // buoc cuoi cung, nguyen tu: moi thu tren da thanh cong
    try { rmdirSync(tmpDir); tmpDir = null; } catch {}
  }
} catch (e) {
  clearInterval(progTimer);
  console.error('ABORT — ' + (firstError || e).message);
  await abortAll();
  server?.close();
  process.exit(1);
}
clearInterval(progTimer);
if (!QUIET && !STILLS && progress.t0) progLine();
server?.close();
if (lateTotal) console.warn(`WARN: ${lateTotal} CSS/WAAPI animation(s) appeared after load; their start = first frame seen${STILLS || WORKERS > 1 ? ' (stills/workers may differ from a single full render — use 1 worker or declare animations at load)' : ''}.`);
console.log(STILLS ? `stills=${times.length}` : `frames=${times.length} ${OW}x${OH}@${FPS} workers=${WORKERS} -> ${out}`, `in ${((Date.now() - t0) / 1000).toFixed(1)}s`);

