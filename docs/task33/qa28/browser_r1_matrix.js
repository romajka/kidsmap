async(page)=>{
const origin='http://127.0.0.1:8788';
const events={errors:[],failed:[],staticFailures:[],stubs:[],expectedRejections:[]};
let expectedNotFound=false;
page.on('pageerror',error=>events.errors.push(String(error)));
page.on('console',message=>{if(message.type()==='error'){
 if(expectedNotFound&&message.text().includes('404'))events.expectedRejections.push(message.text());
 else events.errors.push(message.text());
}});
page.on('requestfailed',request=>events.failed.push({url:request.url(),error:request.failure()?.errorText}));
page.on('response',response=>{if(response.status()>=400&&response.url().includes('/static/'))events.staticFailures.push({url:response.url(),status:response.status()});});
await page.context().unroute('**/*');
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin===origin)return route.continue();
 if(url.hostname==='kidsmap.az')return route.fulfill({response:await route.fetch({url:origin+url.pathname+url.search})});
 events.stubs.push(url.origin+url.pathname);
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa28/fixtures')).json();
const roles=['parent','standalone_owner','network_owner','selected_manager','all_network','volunteer','moderator'];
const rows=[];const checks=[];
for(const mode of ['all','off']){
 if(mode==='off')await page.request.post(origin+'/qa28/cohort-off?token='+fixtures.token);
 for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const role of roles){
  await page.setViewportSize({width,height:900});
  await page.request.get(origin+'/qa28/session/'+role+'?lang='+lang);
  const response=await page.goto(origin+fixtures.paths[lang][role],{waitUntil:'networkidle'});
  await page.evaluate(()=>document.fonts.ready);
  const facts=await page.evaluate(()=>({lang:document.documentElement.lang,heading:document.querySelector('h1')?.innerText,body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,icons:document.fonts.check('24px "Material Symbols Rounded"'),svgIcons:[...document.querySelectorAll('svg.kv-icon')].filter(icon=>icon.getBoundingClientRect().width>0&&icon.getBoundingClientRect().height>0&&icon.querySelector('path,circle,rect')).length,approve:!!document.querySelector('form[action$="/approve/"]'),candidate:!!document.querySelector('[data-candidate-id]'),ownCandidate:!!document.querySelector('[data-candidate-status]'),sections:document.querySelectorAll('[data-place-section]').length,csrf:[...document.querySelectorAll('form[method="post"]')].every(form=>!!form.querySelector('[name="csrfmiddlewaretoken"]'))}));
  const issues=[];
  if(response.status()!==200)issues.push('HTTP_'+response.status());
  if(facts.lang!==lang)issues.push('shell_language');
  if(!facts.heading)issues.push('heading_missing');
  if(facts.scrollWidth>facts.viewport+1)issues.push('overflow');
  if(role==='volunteer'){if(facts.svgIcons<1)issues.push('volunteer_svg_missing');}
  else if(!facts.icons)issues.push('font_missing');
  if(!facts.csrf)issues.push('missing_csrf');
  if(['parent','moderator'].includes(role)&&!facts.body.includes('QA23 APPROVED REVIEW'))issues.push('approved_review_missing');
  if(role==='moderator'&&(!facts.approve||!facts.candidate))issues.push('reviewer_controls_missing');
  if(role==='parent'&&facts.approve)issues.push('parent_can_moderate');
  if(role==='standalone_owner'&&facts.sections!==4)issues.push('continuous_sections');
  if(['network_owner','selected_manager','all_network'].includes(role)&&!facts.body.includes('QA23 SELECTED BRANCH'))issues.push('selected_branch_missing');
  if(role==='selected_manager'&&facts.body.includes('QA23 FUTURE BRANCH'))issues.push('foreign_branch_leaked');
  if(['network_owner','all_network'].includes(role)&&!facts.body.includes('QA23 FUTURE BRANCH'))issues.push('future_branch_missing');
  if(role==='volunteer'&&!facts.body.includes('QA23 VOLUNTEER'))issues.push('volunteer_work_missing');
  let organizationGeometry=null;
  if(['network_owner','selected_manager','all_network'].includes(role)){
   organizationGeometry=await page.evaluate(()=>{
    const rect=element=>{const r=element.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width}};
    const tabs=document.querySelector('.org-tabs');
    return{hero:rect(document.querySelector('.org-hero')),primaryAction:rect(document.querySelector('.org-hero .account-btn-action')),tabs:rect(tabs),tabCount:tabs.querySelectorAll('a').length,sections:[...document.querySelectorAll('.org-section')].map(rect)};
   });
   if([organizationGeometry.hero,organizationGeometry.primaryAction,organizationGeometry.tabs,...organizationGeometry.sections].some(rect=>rect.left < -1||rect.right>width+1))issues.push('organization_content_clipped');
   await page.locator('.org-tabs a').first().focus();
   for(let tab=1;tab<organizationGeometry.tabCount;tab++)await page.keyboard.press('Tab');
   const tabReachability=await page.evaluate(()=>{
    const tabs=document.querySelector('.org-tabs'),last=tabs.querySelector('a:last-child'),r=last.getBoundingClientRect(),container=tabs.getBoundingClientRect();
    return{focused:document.activeElement===last,left:r.left,right:r.right,containerLeft:container.left,containerRight:container.right,scrollLeft:tabs.scrollLeft,scrollWidth:tabs.scrollWidth,clientWidth:tabs.clientWidth,visible:r.left>=Math.max(0,container.left)-1&&r.right<=Math.min(innerWidth,container.right)+1};
   });
   const tabPass=tabReachability.focused&&tabReachability.visible;
   checks.push({check:'organization_last_tab_keyboard',mode,width,role,lang,pass:tabPass,...tabReachability});
   if(!tabPass)issues.push('organization_last_tab_unreachable');
  }
  rows.push({mode,width,lang,role,status:response.status(),...facts,organizationGeometry,issues});
  if(mode==='all'&&lang==='ru'&&width===390)await page.screenshot({path:'__QA28_EVIDENCE__/'+role+'-ru-390.png',fullPage:true});
  if(mode==='all'&&width===390){
   await page.keyboard.press('Tab');
   const focused=await page.evaluate(()=>({tag:document.activeElement?.tagName,visible:!!document.activeElement?.getClientRects().length}));
   checks.push({check:'keyboard_focus',role,lang,pass:focused.visible&&focused.tag!=='BODY'});
  }
  if(mode==='all'&&width===390&&['selected_manager','all_network'].includes(role)){
   expectedNotFound=role==='selected_manager';
   const branchResponse=await page.goto(origin+fixtures.paths[lang].future,{waitUntil:'networkidle'});
   expectedNotFound=false;
   checks.push({check:'future_branch_acl',role,lang,status:branchResponse.status(),pass:branchResponse.status()===(role==='selected_manager'?404:200)});
  }
  if(mode==='off'&&width===390){
   await page.goto(origin+fixtures.paths[lang].write,{waitUntil:'networkidle'});
   const csrf=await page.locator('[name="csrfmiddlewaretoken"]').first().getAttribute('value');
   const blocked=await page.request.post(origin+fixtures.paths[lang].write,{form:{csrfmiddlewaretoken:csrf,rating:'5',text:'SHOULD NEVER BE SAVED',author_name:'Synthetic blocked actor'},headers:{Origin:origin}});
   const payload=await blocked.json();
   checks.push({check:'off_write_503',role,lang,status:blocked.status(),pass:blocked.status()===503&&payload.code==='r1_writes_paused'&&blocked.headers()['retry-after']==='60'});
  }
 }
}
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const screen of ['catalog','detail','map']){
 await page.setViewportSize({width,height:900});await page.request.get(origin+'/qa28/session/parent?lang='+lang);
 const target=fixtures.paths[lang][screen==='map'?'catalog':screen]+(screen==='map'?'?view=map':'');
 const response=await page.goto(origin+target,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
 await page.waitForFunction(()=>[...document.querySelectorAll('.panel.reveal-item')].every(e=>getComputedStyle(e).opacity==='1'),null,{timeout:7000});
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,title:document.title,heading:document.querySelector('h1')?.innerText,
  viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,body:document.body.innerText,
  canonical:document.querySelector('link[rel="canonical"]')?.href,
  alternates:[...document.querySelectorAll('link[rel="alternate"][hreflang]')].map(e=>({lang:e.hreflang,url:e.href})),
  schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>JSON.parse(e.textContent)),
  privateLinks:[...document.querySelectorAll('a[href]')].filter(e=>/protected_docs|specialist-documents|private-media/.test(e.href)).length,
  noindex:[...document.querySelectorAll('meta[name="robots"]')].some(e=>e.content.includes('noindex'))}));
 const issues=[];if(response.status()!==200)issues.push('HTTP_'+response.status());if(facts.lang!==lang)issues.push('language');
 if(facts.scrollWidth>width+1)issues.push('overflow');if(!facts.heading||!facts.title)issues.push('missing_title_heading');
 if(!facts.canonical||new URL(facts.canonical).hostname!=='kidsmap.az')issues.push('canonical');
 if(!['az','ru','en'].every(l=>facts.alternates.some(e=>e.lang===l)))issues.push('hreflang');
 if(facts.privateLinks||facts.body.includes('QA23 PENDING REVIEW'))issues.push('public_private_leak');
 if(screen==='detail'&&!facts.schema.length)issues.push('detail_schema');
 if(screen==='map'){
  const toggle=page.locator('.results-map-toggle');
  if(await toggle.count()){await toggle.click();checks.push({check:'rendered_map_open',screen,lang,width,pass:await page.locator('#catalog-map-panel').isVisible()});if(lang==='ru'&&[390,1440].includes(width))await page.screenshot({path:'__QA28_EVIDENCE__/public-map-open-'+width+'.png',fullPage:false});await page.locator('[data-catalog-map-close]').click();checks.push({check:'rendered_map_close',screen,lang,width,pass:!await page.locator('#catalog-map-panel').isVisible()})}else checks.push({check:'rendered_map_open',screen,lang,width,pass:false,reason:'map toggle missing'});
  const map=await page.request.get(origin+fixtures.paths[lang].map_api);const payload=await map.json();
  checks.push({check:'local_map_api',screen,lang,width,pass:map.status()===200&&typeof payload==='object'});
 }
 const control=page.locator('main input:visible,main button:visible,main a[href]:visible').first();
 if(await control.count()){await control.focus();checks.push({check:'public_focus',screen,lang,width,pass:await control.evaluate(e=>document.activeElement===e)});await page.keyboard.press('Tab');checks.push({check:'public_tab',screen,lang,width,pass:await page.evaluate(()=>document.activeElement!==document.body&&scrollX===0)})}
 rows.push({screen,role:'public',actor:'parent',mode:'public',lang,width,status:response.status(),issues,facts});
 if(lang==='ru'&&[390,1440].includes(width))await page.screenshot({path:'__QA28_EVIDENCE__/public-'+screen+'-'+width+'.png',fullPage:true});
}
for(const lang of ['az','ru','en']){
 await page.setViewportSize({width:390,height:900});await page.request.get(origin+'/qa28/session/parent?lang='+lang);
 await page.goto(origin+fixtures.paths[lang].fallback_detail,{waitUntil:'networkidle'});
 const fallback=await page.evaluate(()=>({lang:document.documentElement.lang,alternates:[...document.querySelectorAll('link[rel="alternate"][hreflang]')].map(e=>e.hreflang),canonical:document.querySelector('link[rel="canonical"]')?.href,title:document.title}));
 checks.push({check:'AZ_only_place_hreflang_honest',lang,width:390,pass:fallback.lang===lang&&fallback.alternates.includes('az')&&!fallback.alternates.includes('ru')&&!fallback.alternates.includes('en')&&!!fallback.canonical&&!!fallback.title});
}
const invariant=await(await page.request.get(origin+'/qa28/invariants')).json();
checks.push({check:'off_preserves_new_records',pass:invariant.unchanged});
return {rows,total:rows.length,passed:rows.filter(row=>!row.issues.length).length,checks,checksPassed:checks.filter(row=>row.pass).length,events};
}
