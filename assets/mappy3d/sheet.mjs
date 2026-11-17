import { chromium } from '/home/claude/reel/node_modules/playwright/index.mjs';
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage({ viewport: { width: 540, height: 760 } });
p.on('pageerror', (e) => console.log('pageerror:', e.message));
await p.goto('http://localhost:8765/demo.html');
await p.waitForFunction(() => window.__ready && window.__ready());
const clips = await p.evaluate(() => window.__m.clips);
const want = process.argv[2] ? process.argv[2].split(',') : clips.map((c) => c[0]);
const names = await p.evaluate(() => Object.keys(window.__m._bones || {}));
console.log(clips.map((c) => c[0] + ':' + c[1].toFixed(1)).join(' '));
let i = 0;
for (const [n, d] of clips) { if (!want.includes(n)) continue;
  for (const f of [0.25, 0.5, 0.75]) {
    await p.evaluate(([n, t]) => { window.__m.lookAt(0, 0); window.__m.express('neutral'); window.__m.pose(n, t); }, [n, d * f]);
    await p.screenshot({ path: `/home/claude/mappy3d/out/ps_${String(i++).padStart(3, '0')}_${n}.png`, clip: { x: 60, y: 150, width: 420, height: 560 } });
  } }
await b.close();
