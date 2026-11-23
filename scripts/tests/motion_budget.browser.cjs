const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require('playwright');

test('only the endless effect stops offscreen and resumes on entry', async () => {
  const browser = await chromium.launch({ channel: process.env.CHROME_CHANNEL || undefined });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 750 } });
    await page.setContent(`<style>
      @keyframes loop { to { transform: rotate(1turn); } }
      @keyframes enter { to { color: red; } }
      #card { margin-top: 2000px; width: 120px; height: 120px; animation: loop 2s infinite, enter 460ms both; }
    </style><div id="panel"><div id="card">Test</div></div>`);
    await page.addStyleTag({ path: path.resolve(__dirname, '../../static/css/components/motion_budget.css') });
    await page.addScriptTag({ path: path.resolve(__dirname, '../../static/js/motion_budget.js') });
    const state = () => page.locator('#card').evaluate(el => Object.fromEntries(el.getAnimations().map(
      a => [a.animationName, a.playbackRate === 0 ? 'paused' : a.playState]
    )));
    await page.waitForFunction(() => {
      const a = document.getAnimations().find(a => a.animationName === 'loop');
      return a && (a.playState === 'paused' || a.playbackRate === 0);
    });
    await page.waitForFunction(() => document.getAnimations().some(a => a.animationName === 'enter' && a.playState === 'finished'), null, { timeout: 5000 });
    assert.equal((await state()).enter, 'finished', 'a card entrance must finish even when its decorative loop is frozen');
    await page.locator('#card').scrollIntoViewIfNeeded();
    await page.waitForFunction(() => document.getAnimations().some(a => a.animationName === 'loop' && a.playState === 'running' && a.playbackRate === 1));
    await page.locator('#panel').evaluate(el => { el.style.opacity = '0'; });
    await page.waitForFunction(() => document.getAnimations().some(a => a.animationName === 'loop' && (a.playState === 'paused' || a.playbackRate === 0)));
    await page.locator('#panel').evaluate(el => { el.style.opacity = '1'; });
    await page.waitForFunction(() => document.getAnimations().some(a => a.animationName === 'loop' && a.playState === 'running' && a.playbackRate === 1));
  } finally {
    await browser.close();
  }
});
