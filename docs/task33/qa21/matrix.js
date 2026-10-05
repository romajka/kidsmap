// Playwright CLI run-code payload. Only synthetic loopback pages are visited.
async (page) => {
const origin = 'http://127.0.0.1:8781';
const events = { errors: [], failed: [], badResponses: [], stubs: [] };
await page.context().unroute('**/*');
page.on('pageerror', error => events.errors.push(String(error)));
page.on('console', message => { if (message.type() === 'error') events.errors.push(message.text()); });
page.on('requestfailed', request => events.failed.push({url:request.url(), error:request.failure()?.errorText}));
page.on('response', response => { if (response.status() >= 400) events.badResponses.push({url:response.url(),status:response.status()}); });
await page.context().route('**/*', async route => {
  const url = new URL(route.request().url());
  if (url.origin === origin) return route.continue();
  if (url.hostname === 'kidsmap.az') {
    const response = await route.fetch({url: origin + url.pathname + url.search});
    return route.fulfill({response});
  }
  events.stubs.push(url.origin + url.pathname);
  if (url.hostname === 'fonts.googleapis.com') {
    const response = await route.fetch({url: origin + '/qa-font.css'});
    return route.fulfill({response});
  }
  return route.fulfill({status:200,contentType:'application/javascript',body:''});
});
const paths = await (await page.request.get(origin + '/fixtures')).json();
const rows = [];
for (const width of [320,360,390,768,1024,1280,1440]) {
  await page.setViewportSize({width,height:900});
  for (const lang of ['az','ru','en']) {
    for (const kind of ['fallback','complete','closed','organization','activity']) {
      const response = await page.goto(origin + paths[lang][kind], {waitUntil:'networkidle'});
      await page.evaluate(() => document.fonts.ready);
      const facts = await page.evaluate(() => ({
        lang:document.documentElement.lang,
        canonical:document.querySelector('link[rel="canonical"]')?.href,
        alternates:[...document.querySelectorAll('head link[rel="alternate"][hreflang]')].map(n=>({lang:n.hreflang,url:n.href})),
        schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(n=>JSON.parse(n.textContent)),
        fallback:!!document.querySelector('[data-translation-fallback]'),
        closed:!!document.querySelector('[data-operating-state="closed"]'),
        injected:!!window.__qa21Injected,
        scrollWidth:document.documentElement.scrollWidth,
        viewport:window.innerWidth,
        body:document.body.innerText,
        heading:document.querySelector('h1')?.innerText,
        headings:[...document.querySelectorAll('h2')].map(n=>n.innerText),
        media:[...document.querySelectorAll('img')].filter(n=>n.src.includes('browser21-fixture.png')).map(n=>({url:n.src,loaded:n.complete && n.naturalWidth>0})),
        switches:[...document.querySelectorAll('.km-lang-option')].map(n=>({lang:n.hreflang,url:n.href})),
        iconsReady:document.fonts.check('24px "Material Symbols Rounded"'),
      }));
      const expectedLang = kind === 'complete' ? lang : 'az';
      const expectedAlternate = kind === 'complete' ? ['az','en','ru'] : ['az'];
      const alternateLang = facts.alternates.map(x=>x.lang).filter(x=>x!=='x-default').sort();
      const issues = [];
      if (response.status() !== 200) issues.push('HTTP_' + response.status());
      if (facts.lang !== lang) issues.push('shell_language');
      if (facts.canonical !== 'https://kidsmap.az' + paths[expectedLang][kind]) issues.push('canonical');
      if (JSON.stringify(alternateLang) !== JSON.stringify(expectedAlternate)) issues.push('hreflang');
      if (facts.fallback !== (lang !== 'az' && kind !== 'complete')) issues.push('fallback_notice');
      if (facts.closed !== (kind === 'closed')) issues.push('closed_notice');
      if (facts.injected) issues.push('script_injected');
      if (facts.scrollWidth > facts.viewport + 1) issues.push('overflow');
      if (!facts.iconsReady) issues.push('icons_font');
      if (facts.switches.length !== 3 || facts.switches.some(x => x.url !== 'https://kidsmap.az' + paths[x.lang][kind])) issues.push('switch_urls');
      const entitySchema = facts.schema.find(x => ['LocalBusiness','Organization','Course'].includes(x['@type']) && x.url === facts.canonical);
      if (!entitySchema || entitySchema.url !== facts.canonical) issues.push('entity_schema');
      const currencies=[];
      const collectCurrencies=value=>{if(!value||typeof value!=='object')return;if(value.priceCurrency)currencies.push(value.priceCurrency);for(const child of Object.values(value))collectCurrencies(child);};
      collectCurrencies(entitySchema);
      if(currencies.some(value=>value!=='AZN')) issues.push('currency');
      if(['fallback','complete','closed'].includes(kind) && entitySchema?.address?.addressCountry!=='AZ') issues.push('geography');
      if(['organization','activity'].includes(kind) && entitySchema && ['aggregateRating','startDate','endDate','geo'].some(key=>key in entitySchema)) issues.push('invented_entity_fact');
      if (kind === 'closed' && entitySchema && (entitySchema.offers || entitySchema.openingHours)) issues.push('closed_active_facts');
      if (kind === 'activity' && (!facts.body.includes('Şənbə 10:00') || !facts.body.includes('25'))) issues.push('activity_facts');
      if (['fallback','complete','closed'].includes(kind)) {
        const shell = {az:['Cədvəl','Rəylər','Əlaqə'],ru:['Расписание','Отзывы','Контакты'],en:['Schedule','Reviews','Contacts']}[lang];
        if (shell.some(text=>!facts.headings.some(heading=>heading.includes(text)))) issues.push('translated_shell');
      }
      if (kind === 'complete' && (!facts.body.includes('QA21 stable review text') || !facts.media.length || facts.media.some(x=>!x.loaded))) issues.push('review_media');
      rows.push({width,lang,kind,status:response.status(),...facts,issues});
      if ([320,390,1280].includes(width) && ['ru','en'].includes(lang)) {
        await page.screenshot({path:'__QA21_EVIDENCE__/' + kind + '-' + lang + '-' + width + '.png',fullPage:true});
      }
    }
  }
}
const legacy=[];
for (const lang of ['az','ru','en']) {
  const response=await page.goto(origin + paths[lang].legacy,{waitUntil:'networkidle'});
  legacy.push({lang,status:response.status(),url:page.url(),redirect:response.request().redirectedFrom()?.url(),pass:response.status()===200 && new URL(page.url()).pathname===paths[lang].fallback});
}
await page.setViewportSize({width:1280,height:900});
await page.goto(origin + paths.az.fallback,{waitUntil:'networkidle'});
await page.locator('.km-lang-btn').focus();
await page.keyboard.press('Enter');
const keyboard={expanded:await page.locator('.km-lang-btn').getAttribute('aria-expanded')};
await page.keyboard.press('Tab');
keyboard.firstLink=await page.evaluate(()=>document.activeElement?.getAttribute('hreflang'));
await page.keyboard.press('Escape');
keyboard.collapsed=await page.locator('.km-lang-btn').getAttribute('aria-expanded');
return {rows,legacy,keyboard,events,passed:rows.filter(x=>!x.issues.length).length,total:rows.length};
}
