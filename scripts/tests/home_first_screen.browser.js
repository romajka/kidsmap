// Run on a populated local homepage with at least two hero slides and a map.
async page => {
  await page.setViewportSize({width: 1440, height: 400});
  await page.emulateMedia({reducedMotion: 'no-preference'});

  let releaseSlider;
  const sliderGate = new Promise(resolve => { releaseSlider = resolve; });
  const sliderRoute = '**/home_hero_slider.js*';
  await page.route(sliderRoute, async route => {
    await sliderGate;
    await route.continue();
  });

  const providerRoute = /maps\.googleapis\.com\/maps\/api\/js|unpkg\.com\/leaflet@[^/]+\/dist\/leaflet\.css/;
  let requests = 0;
  function countProvider(request) {
    if (providerRoute.test(request.url())) requests++;
  }
  page.on('request', countProvider);
  await page.route(providerRoute, route => route.fulfill({
    contentType: route.request().resourceType() === 'script' ? 'application/javascript' : 'text/css',
    body: '',
  }));

  try {
    await page.reload({waitUntil: 'domcontentloaded'});
    const photo = page.locator('.home-hero-photo-main img').first();
    await photo.evaluate(img => img.decode());
    const firstPaint = await photo.evaluate(img => {
      const hints = document.head.querySelectorAll('link[rel=preload][as=image]');
      const preload = [...hints].find(link => matchMedia(link.media || 'all').matches && (img.srcset
        ? link.imageSrcset === img.srcset && link.imageSizes === img.sizes
        : link.href === img.currentSrc));
      for (let el = img; el; el = el.parentElement) {
        const style = getComputedStyle(el);
        if (style.visibility !== 'visible' || style.opacity !== '1') return false;
      }
      return img.getBoundingClientRect().width > 0 && img.fetchPriority === 'high'
        && preload?.fetchPriority === 'high';
    });
    if (!firstPaint) throw new Error('First photo must be visible and preloaded before slider JS');

    releaseSlider();
    await page.waitForFunction(() => document.querySelector('[data-home-hero-slider-dot].is-running'));
    const animates = await photo.evaluate(img => [img, img.closest('figure')].some(
      el => getComputedStyle(el).animationName !== 'none'));
    if (animates) throw new Error('Mount restarted the first photo animation');

    const map = page.locator('#home-map');
    await page.waitForFunction(() => document.querySelector('#home-map')?.dataset.mapBootstrapStarted);
    await page.evaluate(() => scrollTo({top: 20, behavior: 'instant'}));
    if (await map.evaluate(el => el.getBoundingClientRect().top < innerHeight + 280)) {
      throw new Error('The fixture needs the map below the initial viewport');
    }
    await page.waitForTimeout(1200); // Allow the former 900ms provider timer to fire.
    if (requests) throw new Error('Map provider requested while far below viewport');

    await Promise.all([page.waitForRequest(providerRoute), map.scrollIntoViewIfNeeded()]);
    if (requests !== 1) throw new Error('Expected one provider request near the map');

    await page.locator('[data-home-hero-slider-next]').click();
    const incoming = page.locator('[data-home-hero-slide]').nth(1);
    if (!await incoming.evaluate(el => el.classList.contains('is-active')
      && getComputedStyle(el.querySelector('figure')).animationName !== 'none')) {
      throw new Error('Next slide did not animate');
    }
  } finally {
    releaseSlider();
    page.off('request', countProvider);
    await page.unroute(sliderRoute);
    await page.unroute(providerRoute);
  }
}
