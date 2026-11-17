import { chromium } from '/home/claude/reel/node_modules/playwright/index.mjs';
import { spawn } from 'child_process';
const [,, url, out, secs = '23', fps = '30', W = '540', H = '760'] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage({ viewport: { width: +W, height: +H }, deviceScaleFactor: 2 });
p.on('console', (m) => { if (m.type() === 'error') console.log('console:', m.text()); });
p.on('pageerror', (e) => console.log('pageerror:', e.message));
await p.goto(url);
await p.waitForFunction(() => window.__ready && window.__ready(), null, { timeout: 30000 });
await p.waitForTimeout(600);
const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', fps, '-i', '-', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out]);
const n = Math.round(+secs * +fps); const t0 = Date.now();
for (let i = 0; i < n; i++) {
  await p.evaluate((dt) => window.__step(dt), 1 / +fps);
  const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
  ff.stdin.write(buf);
  if (i % 90 === 0) console.log('frame', i, '/', n, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
ff.stdin.end(); await new Promise((r) => ff.on('close', r)); await b.close(); console.log('done', out);
