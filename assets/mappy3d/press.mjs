import { chromium } from '/home/claude/reel/node_modules/playwright/index.mjs';
const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
p.on('pageerror', (e) => console.log('pageerror:', e.message)); p.on('console', (m) => m.type() === 'error' && console.log('console:', m.text()));
await p.goto('http://localhost:8765/index.html');
await p.waitForSelector('#load[hidden]', { state: 'attached', timeout: 30000 });
await p.waitForTimeout(1200);
const box = await p.locator('#mappy canvas').boundingBox();
const pts = { head: [0.5, 0.33], belly: [0.5, 0.66], miss: [0.05, 0.05] };
const shots = [];
for (const [n, [fx, fy]] of Object.entries(pts)) {
  const x = box.x + box.width * fx, y = box.y + box.height * fy;
  await p.mouse.move(x, y); await p.mouse.down(); await p.waitForTimeout(260);
  await p.screenshot({ path: `/home/claude/mappy3d/out/pr_${n}_down.png`, clip: { x: box.x - 20, y: box.y - 60, width: box.width + 40, height: box.height + 80 } });
  await p.mouse.up(); await p.waitForTimeout(650);
  await p.screenshot({ path: `/home/claude/mappy3d/out/pr_${n}_up.png`, clip: { x: box.x - 20, y: box.y - 60, width: box.width + 40, height: box.height + 80 } });
  await p.waitForTimeout(2200);
}
await b.close(); console.log('ok');
