// Headless still renders of an assembled OBJ using the locally installed Google Chrome.
// Usage: node scripts/render_views.mjs --obj model/Mustang_160mm_assembled.obj --out previews/likeness
//        [--views side,front,rear,three] [--modes shaded,grey,flat,silhouette] [--w 1600] [--h 1000]
// The OBJ is loaded once; every view/mode is rendered from the same page.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, arr) => {
  if (x.startsWith('--')) a.push([x.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : 'true']);
  return a;
}, []));
const objAbs = path.resolve(ROOT, args.obj || 'model/Mustang_160mm_assembled.obj');
// Files outside the project (e.g. scratch tests) are served from a virtual /__obj__/ folder.
const external = !objAbs.startsWith(ROOT + path.sep);
const objUrl = external ? `/__obj__/${path.basename(objAbs)}` : '/' + path.relative(ROOT, objAbs).split(path.sep).join('/');
const out = path.resolve(ROOT, args.out || 'previews/likeness');
const views = (args.views || 'three,side,front,rear,rear34,top').split(',');
const modes = (args.modes || 'shaded').split(',');
const W = +(args.w || 1600), H = +(args.h || 1000);
const CHROME = args.chrome || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.obj': 'text/plain', '.mtl': 'text/plain', '.png': 'image/png' };
const WIDE = new Set(['side', 'sideR', 'top', 'wheel', 'wheelR']);   // 16:6.4 framing like the Blender side previews
const TALL = new Set(['side_persp']);                       // 4:3 like the phone photographs

const server = http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const file = pathname.startsWith('/__obj__/') ? path.join(path.dirname(objAbs), pathname.slice(9)) : path.join(ROOT, pathname);
  const allowed = file.startsWith(ROOT) || file.startsWith(path.dirname(objAbs));
  if (!allowed || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(0);
const port = server.address().port;

fs.mkdirSync(out, { recursive: true });
const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true, protocolTimeout: 600000,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox', `--window-size=${W},${H}`],
});
try {
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(`http://127.0.0.1:${port}/scripts/render/render.html?obj=${objUrl}`, { waitUntil: 'load' });
  await page.waitForFunction('window.__loaded === true || window.__error', { timeout: 300000 });
  const err = await page.evaluate('window.__error');
  if (err) throw new Error(`OBJ load failed: ${err}`);
  let n = 0;
  for (const mode of modes) for (const view of views) {
    const vh = WIDE.has(view) ? Math.round(W * 0.4) : TALL.has(view) ? Math.round(W * 0.75) : H;
    const { dataUrl, wheels } = JSON.parse(await page.evaluate((v, m, w, h) => window.renderView(v, m, w, h), view, mode, W, vh));
    const stem = path.join(out, `${view}${mode === 'shaded' ? '' : '_' + mode}`);
    fs.writeFileSync(stem + '.png', Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64'));
    if (TALL.has(view)) fs.writeFileSync(stem + '.json', JSON.stringify({ wheels }));
    n++;
  }
  console.log(`rendered ${n} images to ${path.relative(ROOT, out) || '.'}`);
} finally {
  await browser.close();
  server.close();
}
