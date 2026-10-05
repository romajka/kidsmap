async(page)=>{
const origin='http://127.0.0.1:8782',rows=[];
const events={errors:[],failed:[],badResponses:[]};
page.on('pageerror',error=>events.errors.push(String(error)));
page.on('console',message=>{if(message.type()==='error')events.errors.push(message.text());});
page.on('requestfailed',request=>events.failed.push({url:request.url(),error:request.failure()?.errorText}));
page.on('response',response=>{if(response.status()>=400)events.badResponses.push({url:response.url(),status:response.status()});});
await page.context().unroute('**/*');
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin===origin)return route.continue();
 if(url.hostname==='kidsmap.az')return route.fulfill({response:await route.fetch({url:origin+url.pathname+url.search})});
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 return route.fulfill({status:200,contentType:'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa22/fixtures')).json();
const labels={az:['KidsMap yoxlaması','Tarixçə','Xidmət məlumatları və göstəricilər'],ru:['Проверка KidsMap','История','Служебное и метрики'],en:['KidsMap review','History','Service details and metrics']};
for(const width of[320,390,1280]){
 await page.setViewportSize({width,height:900});
 for(const lang of['az','ru','en'])for(const kind of['place','activity','specialist','event']){
  await page.request.get(origin+'/qa22/session/staff?lang='+lang);
  const response=await page.goto(origin+fixtures.paths[lang].admin[kind],{waitUntil:'networkidle'});
  const facts=await page.evaluate(()=>({lang:document.documentElement.lang,body:document.body.innerText,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,workflow:document.querySelector('.field-review_workflow_link .readonly a')?.innerText.trim(),historyLabel:document.querySelector('.field-version_history label')?.innerText.trim().replace(/:$/,''),history:document.querySelector('.field-version_history')?.innerText}));
  const issues=[];
  if(response.status()!==200)issues.push('HTTP_'+response.status());
  if(facts.lang!==lang)issues.push('language');
  if(facts.scrollWidth>width+1)issues.push('overflow');
  for(const text of labels[lang])if(!facts.body.includes(text))issues.push('missing_label:'+text);
  if(facts.workflow!==labels[lang][0])issues.push('workflow_label');
  if(facts.historyLabel!==labels[lang][1])issues.push('history_label');
  if(!facts.history?.includes('QA22 APPROVED '+kind)||!facts.history?.includes('QA22 PENDING '+kind))issues.push('history_projection');
  rows.push({width,lang,kind,status:response.status(),...facts,issues});
  if(kind==='place'&&[390,1280].includes(width))await page.screenshot({path:'__QA22_EVIDENCE__/admin-place-'+lang+'-'+width+'.png',fullPage:true});
 }
}
return{rows,total:rows.length,passed:rows.filter(row=>!row.issues.length).length,events};
}
