async(page)=>{
 const origin='http://127.0.0.1:8787',events={errors:[],failed:[],staticFailures:[],stubs:[],expectedErrors:[]};
 page.on('pageerror',e=>events.errors.push(String(e)));page.on('requestfailed',r=>events.failed.push(r.failure()?.errorText));page.on('response',r=>{if(r.status()>=400&&r.url().includes('/static/'))events.staticFailures.push({status:r.status(),url:r.url()})});
 await page.context().route('**/*',async route=>{const url=new URL(route.request().url());if(url.origin===origin)return route.continue();events.stubs.push(url.origin);if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});if(url.pathname==='/qa-font.ttf')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.ttf'})});return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''})});
 const fixture=await(await page.request.get(origin+'/qa27/fixtures')).json();await page.request.get(origin+'/qa27/session/public?lang=ru');await page.setViewportSize({width:1440,height:900});
 const params=new URLSearchParams({view:'calendar',month:fixture.date.slice(0,7),q:'QA27',category:fixture.ids.category,age_from:'6',age_to:'12',format:'physical'});
 const r=await page.goto(origin+fixture.paths.ru.landing+'?'+params,{waitUntil:'networkidle'});
 const mode=await page.locator('[data-events-mode="calendar"]').count(),calendar=await page.locator('#events-calendar').count();
 const chipHref=await page.locator('.events-quick-chips a').first().getAttribute('href');const chip=new URL(chipHref,page.url());const preserved=['q','category','age_from','age_to','format'].every(key=>chip.searchParams.get(key)===params.get(key));
 const checks=[{check:'HTTP_event_calendar_route',status:r.status(),pass:r.status()===200},{check:'calendar_mode_control_present',pass:mode>0},{check:'calendar_actual_month_present',pass:calendar>0},{check:'quick_chip_preserves_filters',pass:preserved,actual_params:Object.fromEntries(chip.searchParams)}];
 const issues=checks.filter(c=>!c.pass).map(c=>c.check);await page.screenshot({path:'__QA27_EVIDENCE__/calendar-red-1440.png',fullPage:true});
 return{runtime:fixture.runtime,total:1,passed:issues.length?0:1,checksPassed:checks.filter(c=>c.pass).length,checks,rows:[{screen:'calendar-red',actor:'public',lang:'ru',width:1440,status:r.status(),issues}],events,externalTransport:'External integrations/CDNs stubbed; actual local Django/CSS/JS with cached font.'};
}
