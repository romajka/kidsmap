async(page)=>{
const origin='http://127.0.0.1:8788',events={errors:[],failed:[],staticFailures:[],stubs:[],expectedRejections:[]},checks=[],rows=[];
let phase='load',intentional400=false;const responses=[];
page.on('pageerror',e=>events.errors.push({error:String(e),phase,url:page.url()}));
page.on('console',m=>{if(m.type()==='error'){if(intentional400&&m.text().includes('400'))events.expectedRejections.push({error:m.text(),phase});else events.errors.push({error:m.text(),phase})}});
page.on('response',r=>{if(r.request().method()==='POST')responses.push({phase,status:r.status(),url:r.url()});if(r.status()>=400&&r.url().includes('/static/'))events.staticFailures.push({url:r.url(),status:r.status()})});
page.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText,phase}));
await page.context().unroute('**/*');await page.context().route('**/*',async route=>{
const u=new URL(route.request().url());if(u.origin===origin)return route.continue();events.stubs.push(u.origin);
if(u.pathname==='/qa-font.ttf')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.ttf'})});
if(u.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
return route.fulfill({status:200,contentType:u.pathname.endsWith('.css')?'text/css':'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa28/fixtures')).json();
const state=async()=> (await page.request.get(origin+'/qa28/targeted-state')).json();
await page.setViewportSize({width:1280,height:900});await page.request.get(origin+'/qa28/session/network_owner?lang=ru');
const response=await page.goto(origin+fixtures.paths.ru.program,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
rows.push({screen:'program_motion_diagnostic',actor:'network_owner',lang:'ru',width:1280,issues:response.status()===200?[]:['HTTP_'+response.status()]});
const before=await state();await page.locator('[name="name_az"]').fill('QA AUDIT MOTION CANDIDATE');
phase='native_missing_impact_400';intentional400=true;
await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(fixtures.paths.ru.program_save)),page.locator('main [name="submit"]').click()]);await page.waitForLoadState('networkidle');
await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
const impactState=await state();checks.push({check:'impact_rejection_preserves_published_and_candidate_state',pass:impactState.program_name===before.program_name&&impactState.revision_status===null});
const errorsAfterImpact=events.errors.slice();await page.screenshot({path:'__QA28_EVIDENCE__/program-motion-after-impact-rejection.png',fullPage:false});
intentional400=false;phase='native_valid_impact_redirect';await page.locator('[name="impact_confirmed"]').check();
await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(fixtures.paths.ru.program_save)),page.locator('main [name="submit"]').click()]);await page.waitForLoadState('networkidle');
await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
const after=await state();checks.push({check:'valid_edit_saved_candidate_and_preserves_approved',pass:after.revision_status==='pending'&&after.revision_payload.name_az==='QA AUDIT MOTION CANDIDATE'&&after.program_name===before.program_name});
await page.screenshot({path:'__QA28_EVIDENCE__/program-motion-after-valid-save.png',fullPage:false});
return {rows,checks,events,responses,errorsAfterImpact,businessStates:{before,impactState,after},purpose:'Bounded causal diagnostic, not counted as another final matrix context'};
}
