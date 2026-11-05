/*
 * მართეოს პრეზენტაციის MP4 ვიდეოდ ჩაწერა (კადრ-კადრ, ზუსტი დროით).
 *
 * საჭიროა: Node.js, Playwright (npm i playwright && npx playwright install chromium) და ffmpeg.
 * გაშვება პროექტის საქაღალდიდან:
 *   node tools/render-video.js                # -> video/marteo.mp4 (1920x1080, 30fps)
 *   node tools/render-video.js out.mp4 60     # სხვა ფაილი / 60fps
 *
 * ვირტუალური საათი: JS ტაიმერები (Playwright clock) და CSS ანიმაციები (Web Animations API)
 * ერთად მიიწევს წინ თითო კადრზე, ამიტომ ვიდეო სრულიად გლუვია კომპიუტერის სიჩქარის მიუხედავად.
 */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.resolve(process.argv[2] || path.join(ROOT, 'video', 'marteo.mp4'));
const FPS = Number(process.argv[3]) || 30;
const W = 1920, H = 1080;

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.css': 'text/css' };
function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); return rsp.end(); }
      rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(rsp);
    }).listen(0, () => res(srv));
  });
}

(async () => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const srv = await serve();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.clock.install({ time: 0 });
  await page.clock.pauseAt(1000); // time only moves when we call runFor()
  await page.goto(`http://localhost:${srv.address().port}/index.html`, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: '.ui,.flash{display:none!important}.player{cursor:none}' });
  await page.evaluate(async () => {
    for (const w of [400, 500, 600, 700, 800]) await document.fonts.load(`${w} 40px "Noto Sans Georgian"`, 'აბგ');
    await document.fonts.ready;
  });

  const total = await page.evaluate(() => Array.from(document.querySelectorAll('.slide'))
    .reduce((s, el) => s + (+el.getAttribute('data-duration') || (window.MARTEO_CONFIG || {}).slideDuration || 6000), 0));
  const frames = Math.round(total / 1000 * FPS) - 2; // stop just before the loop restarts
  const fadeOut = (frames / FPS - 0.7).toFixed(2);
  console.log(`slides total ${total / 1000}s -> ${frames} frames @ ${FPS}fps`);

  // let the page finish starting, then restart slide 1 so recording begins exactly at t = 0
  await page.clock.runFor(500);
  await page.evaluate(() => {
    window.MarteoPresentation.go(0);
    window.__vt = 0;
    window.__sync = () => {
      for (const a of document.getAnimations()) {
        if (a.__born === undefined) { a.__born = window.__vt; a.pause(); }
        a.currentTime = window.__vt - a.__born;
      }
    };
  });

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-vf', `fade=t=in:st=0:d=0.5,fade=t=out:st=${fadeOut}:d=0.7`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });

  const step = 1000 / FPS;
  for (let i = 0; i < frames; i++) {
    await page.clock.runFor(step);
    await page.evaluate(s => { window.__vt += s; window.__sync(); }, step);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (FPS * 5) === 0) console.log(`  ${(i / FPS).toFixed(0)}s / ${(total / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close(); srv.close();
  console.log('done ->', OUT);
})().catch(e => { console.error(e); process.exit(1); });
