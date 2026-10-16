async (page) => {
 await page.context().route('**/*',route=>{
  const url=route.request().url();
  if(url.startsWith('http://127.0.0.1:57061/')||url.startsWith('data:')||url==='about:blank')return route.continue();
  return route.abort('blockedbyclient');
 });
 await page.goto('http://127.0.0.1:57061/ru/auth/login/');
 return {title:await page.title(),browser:page.context().browser().version(),url:page.url()};
}
