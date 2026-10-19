async (page) => {
  await page.context().route('**/*', route => {
    const u = new URL(route.request().url());
    return u.hostname === '127.0.0.1' && u.port === '33304' ? route.continue() : route.abort('blockedbyclient');
  });
  await page.goto('http://127.0.0.1:33304/qa/login/unread/');
  return {info:await (await page.request.get('http://127.0.0.1:33304/qa/info/')).json(),browser:page.context().browser().version()};
}
