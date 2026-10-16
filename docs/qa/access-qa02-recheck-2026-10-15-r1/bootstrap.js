async (page) => {
 await page.context().route('**/*',route=>{
  const u=route.request().url();if(u.startsWith('http://127.0.0.1:57239/')||u.startsWith('data:')||u==='about:blank')return route.continue();return route.abort('blockedbyclient');
 });
 await page.goto('http://127.0.0.1:57239/ru/auth/login/');return {title:await page.title(),browser:page.context().browser().version(),url:page.url()};
}
