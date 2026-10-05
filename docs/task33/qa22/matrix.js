async(page)=>{
const origin='http://127.0.0.1:8782';
const events={errors:[],failed:[],badResponses:[],stubs:[]};
page.on('pageerror',error=>events.errors.push(String(error)));
page.on('console',message=>{if(message.type()==='error')events.errors.push(message.text());});
page.on('requestfailed',request=>events.failed.push({url:request.url(),error:request.failure()?.errorText}));
page.on('response',response=>{if(response.status()>=400)events.badResponses.push({url:response.url(),status:response.status()});});
await page.context().unroute('**/*');
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin===origin)return route.continue();
 if(url.hostname==='kidsmap.az')return route.fulfill({response:await route.fetch({url:origin+url.pathname+url.search})});
 events.stubs.push(url.origin+url.pathname);
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 return route.fulfill({status:200,contentType:'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa22/fixtures')).json();
const rows=[];
for(const width of[320,360,390,768,1024,1280,1440]){
 await page.setViewportSize({width,height:900});
 for(const actor of['public','author','owner','staff']){
  await page.request.get(origin+'/qa22/session/'+actor);
  for(const lang of['az','ru','en'])for(const kind of['place','activity','specialist','event']){
   const response=await page.goto(origin+fixtures.paths[lang][kind],{waitUntil:'networkidle'});
   await page.evaluate(()=>document.fonts.ready);
   const facts=await page.evaluate(()=>({lang:document.documentElement.lang,heading:document.querySelector('h1')?.innerText,body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,edit:!!document.querySelector('[data-review-edit]'),reply:!!document.querySelector('form[action$="/reply/"]'),report:!!document.querySelector('form[action$="/report/"]'),approve:!!document.querySelector('form[action$="/approve/"]'),candidate:!!document.querySelector('[data-candidate-id]'),ownCandidate:!!document.querySelector('[data-candidate-status]'),ownText:document.querySelector('#review-text')?.value,rating:document.querySelector('[data-review-rating]')?.textContent,icons:document.fonts.check('24px "Material Symbols Rounded"'),injected:!!window.__qa22Injected,forms:[...document.querySelectorAll('form')].map(form=>({action:form.action,method:form.method,hasCsrf:!!form.querySelector('[name="csrfmiddlewaretoken"]')}))}));
   const issues=[];
   if(response.status()!==200)issues.push('HTTP_'+response.status());
   if(facts.lang!==lang)issues.push('shell_language');
   const expectedHeading={az:'Rəylər',ru:'Отзывы',en:'Reviews'}[lang];
   if(!facts.heading?.startsWith(expectedHeading))issues.push('localized_heading');
   if(!facts.body.includes('QA22 APPROVED '+kind)||!facts.body.includes('QA22 PUBLIC REPLY '+kind))issues.push('approved_projection');
   if(facts.body.includes('QA22 PRIVATE REPORT'))issues.push('private_report_leaked');
   if(['public','owner'].includes(actor)&&facts.body.includes('QA22 PENDING'))issues.push('private_candidate_leaked');
   if(facts.edit!==(actor!=='public'))issues.push('auth_form');
   if(facts.reply!==(actor==='owner')||facts.report!==(actor==='owner'))issues.push('business_action_scope');
   if(facts.approve!==(actor==='staff')||facts.candidate!==(actor==='staff'))issues.push('reviewer_scope');
   if(actor==='author'&&(!facts.ownCandidate||!facts.ownText?.includes('QA22 PENDING '+kind)))issues.push('author_candidate');
   if(facts.forms.some(form=>form.method==='post'&&!form.hasCsrf))issues.push('missing_csrf');
   if(facts.scrollWidth>facts.viewport+1)issues.push('overflow');
   if(!facts.icons)issues.push('icons');
   if(facts.injected)issues.push('script_injected');
   rows.push({width,actor,lang,kind,status:response.status(),...facts,issues});
   if([390,1280].includes(width)&&['az','ru','en'].includes(lang)&&['place','activity'].includes(kind))await page.screenshot({path:'__QA22_EVIDENCE__/'+kind+'-'+actor+'-'+lang+'-'+width+'.png',fullPage:true});
  }
 }
 for(const actor of['author','owner']){
  await page.request.get(origin+'/qa22/session/'+actor);
  for(const lang of['az','ru','en']){
   const response=await page.goto(origin+fixtures.paths[lang].dashboard,{waitUntil:'networkidle'});
   const facts=await page.evaluate(()=>({body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,unsafeActions:[...document.querySelectorAll('form[action]')].filter(form=>/approve|reject|hide/.test(form.action)).map(form=>form.action),workflowLinks:[...document.querySelectorAll('a')].filter(node=>node.href.includes('/reviews/')&&node.href.includes('/target/')).map(node=>node.href)}));
   const issues=[];
   if(response.status()!==200)issues.push('HTTP_'+response.status());
   if(facts.scrollWidth>facts.viewport+1)issues.push('overflow');
   if(facts.unsafeActions.length)issues.push('business_moderation_controls');
   if(!facts.workflowLinks.length)issues.push('missing_workflow_link');
   if(actor==='owner'&&facts.body.includes('QA22 PENDING'))issues.push('private_candidate_leaked');
   rows.push({width,actor,lang,kind:'dashboard',status:response.status(),...facts,issues});
   if(lang==='en'&&[390,1280].includes(width))await page.screenshot({path:'__QA22_EVIDENCE__/dashboard-'+actor+'-'+width+'.png',fullPage:true});
  }
 }
 await page.request.get(origin+'/qa22/session/staff');
 for(const lang of['az','ru','en'])for(const kind of['place','activity','specialist','event']){
  await page.request.get(origin+'/qa22/session/staff?lang='+lang);
  const response=await page.goto(origin+fixtures.paths[lang].admin[kind],{waitUntil:'networkidle'});
  const facts=await page.evaluate(()=>({lang:document.documentElement.lang,body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,unsafeFields:[...document.querySelectorAll('input[name],textarea[name],select[name]')].filter(node=>['text','rating','status','is_approved','current_revision','candidate_revision'].includes(node.name)&&!node.disabled).map(node=>node.name),workflowLinks:[...document.querySelectorAll('a')].filter(node=>node.href.includes('/reviews/')&&node.href.includes('/target/')).map(node=>node.href)}));
  const issues=[];
  if(response.status()!==200)issues.push('HTTP_'+response.status());
  if(facts.lang!==lang)issues.push('admin_shell_language');
  if(facts.scrollWidth>facts.viewport+1)issues.push('overflow');
  if(facts.unsafeFields.length)issues.push('editable_history');
  if(!facts.workflowLinks.length)issues.push('missing_workflow_link');
  if(!facts.body.includes('QA22 APPROVED '+kind)||!facts.body.includes('QA22 PENDING '+kind))issues.push('history_missing');
  rows.push({width,actor:'staff',lang,kind:'admin-'+kind,status:response.status(),...facts,issues});
  if(lang==='en'&&[390,1280].includes(width))await page.screenshot({path:'__QA22_EVIDENCE__/admin-'+kind+'-'+width+'.png',fullPage:true});
 }
}
return{rows,total:rows.length,passed:rows.filter(row=>!row.issues.length).length,events};
}
