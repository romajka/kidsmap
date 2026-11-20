// Run via Playwright run-code on a local public page, with all sections enabled.
async page => {
  const header = page.locator('#km-site-header');
  const nav = header.locator('.km-nav-desktop');
  const burger = header.locator('#km-burger-open');
  const drawer = page.locator('#km-mobile-drawer');
  await page.evaluate(() => document.fonts.ready);

  async function checkRow() {
    await page.evaluate(() => new Promise(requestAnimationFrame));
    const problem = await header.evaluate(header => {
      const row = header.querySelector('.km-header-inner').getBoundingClientRect();
      const visible = el => el.getClientRects().length > 0 && getComputedStyle(el).visibility === 'visible';
      if (visible(header.querySelector('nav')) === visible(header.querySelector('#km-burger-open'))) {
        return 'expected one navigation mode';
      }
      if ([...header.querySelectorAll('[data-mlang]')].filter(visible).length !== 1) return 'expected one language picker';
      const title = header.querySelector('.km-brand-title');
      if (title.scrollWidth > title.clientWidth + 1) return 'wordmark clipped';
      const controls = [...header.querySelectorAll('a, button')].filter(visible);
      let previous;
      for (const control of controls) {
        const box = control.getBoundingClientRect();
        if (box.left < Math.max(0, row.left) - 1 || box.right > Math.min(innerWidth, row.right) + 1 ||
            box.top < row.top - 1 || box.bottom > row.bottom + 1 ||
            (previous && (box.left < previous.right - 1 || box.top >= previous.bottom))) {
          return 'control outside the header row: ' + control.className;
        }
        previous = box;
      }
      for (const label of header.querySelectorAll('.km-nav-item > span:last-of-type')) {
        const range = document.createRange();
        range.selectNodeContents(label);
        if (range.getClientRects().length > 1) return 'wrapped label: ' + label.textContent;
      }
      return '';
    });
    if (problem) throw new Error(page.url() + ' at ' + page.viewportSize().width + 'px: ' + problem);
  }

  const widths = [1200, 1217, 1218, 1280, 1329, 1330, 1366, 1440, 1920, 1199, 1073, 1024, 768, 440, 401, 390, 375, 360, 320];
  for (const top of [0, 240]) {
    await page.evaluate(top => window.scrollTo({top, behavior: 'instant'}), top);
    await page.waitForFunction(scrolled =>
      document.querySelector('#km-site-header').classList.contains('is-scrolled') === scrolled, top > 0);
    for (const width of widths) {
      await page.setViewportSize({width, height: 800});
      await checkRow();
    }
  }

  await page.setViewportSize({width: 1280, height: 800});
  await nav.waitFor({state: 'visible'});
  const account = header.locator('#account-menu-trigger');
  if (await account.count()) {
    await account.click();
    await header.locator('.km-user-card-name').waitFor({state: 'visible'});
    await page.keyboard.press('Escape');
  }
  await page.setViewportSize({width: 1440, height: 800});
  await nav.waitFor({state: 'visible'});
  const desktopLinks = await nav.locator('a[href]').evaluateAll(links => links.map(link => link.href));
  const enlargedText = await page.addStyleTag({content: 'html { font-size: 200%; }'});
  await checkRow();
  // This laptop width fits desktop links at the default text size.
  await page.setViewportSize({width: 1280, height: 800});
  await burger.waitFor({state: 'visible'});
  await checkRow();
  await enlargedText.evaluate(el => el.remove());
  await page.setViewportSize({width: 1440, height: 800});
  const narrowShell = await page.addStyleTag({content: 'body .site-shell { max-width: 960px; }'});
  await burger.waitFor({state: 'visible'});
  await checkRow();
  await burger.focus();
  await page.keyboard.press('Enter');
  await drawer.locator('#km-burger-close:focus').waitFor();
  for (const href of desktopLinks) {
    if (!await drawer.locator('a').evaluateAll((links, href) => links.some(link => link.href === href), href)) {
      throw new Error('Missing drawer link: ' + href);
    }
  }
  await page.keyboard.press('Escape');
  if (!await burger.evaluate(el => el === document.activeElement)) throw new Error('Drawer lost keyboard focus');
  await narrowShell.evaluate(el => el.remove());
  await nav.waitFor({state: 'visible'});
  await page.setViewportSize({width: 401, height: 800});
  const pageGutters = await page.addStyleTag({content: 'body .site-shell { width: calc(100% - 28px); }'});
  await checkRow();
  await pageGutters.evaluate(el => el.remove());
};
