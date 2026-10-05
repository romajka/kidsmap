async(page)=>{
 const origin='http://127.0.0.1:8786';const fixture=await(await page.request.get(origin+'/qa26/fixtures')).json();
 const context=await page.context().browser().newContext({timezoneId:'UTC'});
 await context.route('**/*',async route=>{const url=new URL(route.request().url());if(url.origin===origin)return route.continue();return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''})});
 const other=await context.newPage();await other.clock.install({time:new Date('2035-02-03T20:30:00Z')});
 await context.request.get(origin+'/qa26/session/owner?lang=en');await other.goto(origin+fixture.paths.en.create,{waitUntil:'networkidle'});
 await other.locator('[name="event_date"]').fill('2035-02-04');await other.locator('[name="start_time_input"]').fill('00:00');await other.locator('[name="end_date"]').fill('2035-02-04');await other.locator('[name="end_time_input"]').fill('01:00');await other.locator('[name="end_time_input"]').dispatchEvent('change');
 const facts=await other.evaluate(()=>({timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,now:new Date().toISOString(),date:document.querySelector('[name="event_date"]').value,dateValidation:document.querySelector('[name="event_date"]').validationMessage,startValidation:document.querySelector('[name="start_time_input"]').validationMessage,formValid:document.querySelector('[name="event_date"]').validity.valid}));
 await other.screenshot({path:'__QA26_EVIDENCE__/UTC-midnight-causal.png',fullPage:true});await context.close();
 return {facts,expected:'Baku local start2035-02-04T00:00+04 occurs before instant2035-02-03T20:30Z; date/start must be invalid',pastRejected:!!(facts.dateValidation||facts.startValidation)};
}
