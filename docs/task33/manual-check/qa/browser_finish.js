async page => {
 const origin='http://127.0.0.1:8780',errors=[],failed=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push({message:m.text(),url:m.location().url});});
 page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()?.errorText}));
 const fixture=await(await page.request.get(origin+'/qa/fixtures.json')).json();
 await page.setViewportSize({width:1440,height:950});
 await page.goto(origin+'/ru/catalog/',{waitUntil:'networkidle'});
 await page.getByRole('button',{name:'Показать результаты на карте',exact:true}).click();
 await page.waitForLoadState('networkidle');
 await page.locator('[data-catalog-map-panel]').scrollIntoViewIfNeeded();
 await page.locator('.catalog-map-empty').waitFor();
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/map.png',fullPage:false});
 const map={provider:await page.locator('[data-catalog-map-panel]').getAttribute('data-map-provider'),text:await page.locator('[data-catalog-map-panel]').innerText(),interactive_map:'NOT_TESTED_NO_GOOGLE_KEY',data:await page.locator('#catalog-map-data').textContent()};
 await page.goto(origin+'/qa/');await page.locator('#all-links a').first().waitFor();
 await page.getByRole('button',{name:'Войти: demo_owner',exact:true}).click();
 await page.goto(origin+fixture.links.ru.program,{waitUntil:'networkidle'});
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/program-editor.png',fullPage:true});
 await page.goto(origin+'/qa/');await page.getByRole('button',{name:'Выйти в гостя',exact:true}).click();
 await page.locator('#all-links a').first().waitFor();
 const first=page.locator('#step-1 input');await first.check();await page.reload();await page.locator('#all-links a').first().waitFor();
 const persistent=await first.isChecked();await first.uncheck();
 await page.getByLabel('Язык ссылок:').selectOption('en');
 const languageLinks=await page.locator('#all-links a').first().getAttribute('href')==='/en/';
 await page.getByLabel('Язык ссылок:').selectOption('ru');
 const assets=[];for(const img of await page.locator('#gallery img').all()){const src=await img.getAttribute('src');const r=await page.request.get(new URL(src,origin).href);assets.push({src,status:r.status()});}
 const layouts=[];for(const width of [320,390,768,1024,1440]){await page.setViewportSize({width,height:900});layouts.push(await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth})));}
 await page.locator('header').scrollIntoViewIfNeeded();await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/guide-desktop.png'});
 const report=await page.request.get(origin+'/qa/files/report/report.html');
 return {map,persistent,languageLinks,assets,layouts,report:report.status(),errors,failed,status:persistent&&languageLinks&&assets.every(a=>a.status===200)&&layouts.every(l=>l.scroll<=l.width)&&report.status()===200&&!errors.length&&!failed.length?'PASS':'REVIEW_REQUIRED'};
}
