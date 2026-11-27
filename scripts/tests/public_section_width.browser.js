// Run with Playwright run-code on a local public page.
async page => {
  const aligned = (report) => {
    const viewport = document.documentElement.clientWidth;
    const gutter = viewport < 768 ? 16 : Math.max(30, (viewport - 1300) / 2);
    const selectors = [
      '#km-site-header', '.site-footer', '.site-shell > main',
      '.page-home main > section', '.sp-directory-head', '.km-specialists-layout',
      '.sp-detail > header', '.detail-wrap', '.catalog-layout', '.km-afisha-hero',
      '.event-poster', '.km-suggest--page', '.org-hero', '.public-org-hero-card',
      '.pg-hero', '.faq-hero', '.legal-hero-card', '.rules-hero', '.rules-hero-card',
      '.typed-reviews', '.register-frame', '.about-page-wrapper > section',
      '.add-place-wrapper > section', '.contacts-page-wrapper > section',
      'main > .site-reviews-page', 'main > .place-reviews-page', 'main > .seo-landing-hero',
    ];
    const problems = [];
    if (!document.querySelector('#km-site-header')) problems.push('missing public header');
    for (const el of document.querySelectorAll(selectors.join(','))) {
      const box = el.getBoundingClientRect();
      if (!box.width || !box.height) continue;
      if (Math.abs(box.left - gutter) > 1 || Math.abs(viewport - box.right - gutter) > 1) {
        problems.push([el.classList[0] || el.tagName, box.left, viewport - box.right]);
      }
    }
    if (document.documentElement.scrollWidth > viewport + 1) problems.push('horizontal overflow');
    return report ? problems : problems.length === 0;
  };
  for (const width of [320, 390, 767, 768, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({width, height: 900});
    try {
      await page.waitForFunction(aligned, false, {timeout: 3500});
    } catch {
      throw new Error(page.url() + ' at ' + width + 'px: ' + JSON.stringify(await page.evaluate(aligned, true)));
    }
  }
}
