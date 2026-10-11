async page => {
  await page.context().route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin === 'http://127.0.0.1:8821') return route.continue();
    return route.abort('blockedbyclient');
  });
  await page.setViewportSize({width:360,height:900});
  console.log('External browser transport blocked; viewport 360 x 900.');
}
