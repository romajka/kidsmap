// Playwright CLI run-code payload for final-source head and keyboard acceptance.
async (page) => {
const origin='http://127.0.0.1:8781';
await page.context().unroute('**/*');
await page.context().route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.origin===origin)return route.continue();
  if(url.hostname==='kidsmap.az')return route.fulfill({response:await route.fetch({url:origin+url.pathname+url.search})});
  if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
  return route.fulfill({status:200,contentType:'application/javascript',body:''});
});
const paths=await(await page.request.get(origin+'/fixtures')).json();
const rows=[];
for(const lang of ['az','ru','en'])for(const kind of ['fallback','complete','closed','organization','activity']){
  const response=await page.goto(origin+paths[lang][kind],{waitUntil:'networkidle'});
  rows.push({lang,kind,status:response.status(),canonical:await page.locator('link[rel="canonical"]').getAttribute('href'),schema:await page.locator('script[type="application/ld+json"]').evaluateAll(nodes=>nodes.map(n=>JSON.parse(n.textContent)))});
}
await page.setViewportSize({width:1280,height:900});
await page.goto(origin+paths.az.fallback,{waitUntil:'networkidle'});
await page.locator('.km-lang-btn').focus();await page.keyboard.press('Enter');
await page.waitForFunction(()=>{const node=document.querySelector('.km-dropdown-lang');return getComputedStyle(node).visibility==='visible' && Number(getComputedStyle(node).opacity)>.98;});
const desktop={expanded:await page.locator('.km-lang-btn').getAttribute('aria-expanded')};
await page.keyboard.press('Tab');desktop.firstLink=await page.evaluate(()=>document.activeElement?.getAttribute('hreflang'));
await page.keyboard.press('Tab');desktop.secondLink=await page.evaluate(()=>document.activeElement?.getAttribute('hreflang'));
await Promise.all([page.waitForURL('**/ru/place/**',{waitUntil:'domcontentloaded'}),page.keyboard.press('Enter')]);await page.waitForLoadState('networkidle');
desktop.switchedTo=page.url();desktop.shellLanguage=await page.locator('html').getAttribute('lang');
await page.setViewportSize({width:390,height:900});await page.goto(origin+paths.en.fallback,{waitUntil:'networkidle'});
await page.locator('#km-burger-open').focus();await page.keyboard.press('Enter');
await page.waitForFunction(()=>document.activeElement?.id==='km-burger-close');
const mobile={open:await page.locator('#km-mobile-drawer').getAttribute('aria-hidden')};
await page.locator('.km-drawer-lang-btn[hreflang="ru"]').focus();await Promise.all([page.waitForURL('**/ru/place/**',{waitUntil:'domcontentloaded'}),page.keyboard.press('Enter')]);await page.waitForLoadState('networkidle');
mobile.switchedTo=page.url();mobile.shellLanguage=await page.locator('html').getAttribute('lang');
return {rows,desktop,mobile};
}
