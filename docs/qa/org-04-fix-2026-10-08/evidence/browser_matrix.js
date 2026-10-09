async original=>{
const base='http://localhost:8788',browser=original.context().browser(),rows=[],errors=[],network=[];
const prefixes={ru:'/ru',az:'',en:'/en'};
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
 const c=await browser.newContext({viewport:{width,height:950},reducedMotion:'reduce'}),p=await c.newPage();
 p.on('pageerror',e=>errors.push({lang,width,error:String(e)}));p.on('response',r=>{if(r.status()>=400)network.push({lang,width,status:r.status(),url:r.url()})});
 await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
 try{
  await p.goto(base+'/qa/');await p.getByRole('button',{name:'Войти: demo_owner',exact:true}).click();
  for(const redacted of [false,true]){
   const url=base+prefixes[lang]+'/account/organizations/'+(redacted?'44/branches/82':'43/branches/74')+'/detach-preview/';
   const res=await p.goto(url);await p.locator('[data-confirm-form]').waitFor();
   const text=await p.locator('main').innerText(),geometry=await p.evaluate(()=>({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));
   rows.push({id:'review-'+(redacted?'private':'normal')+'-'+lang+'-'+width,status:res.status()===200&&geometry.scroll<=geometry.width?'PASS':'FAIL',lang,width,geometry});
   rows.push({id:'required-consent-'+(redacted?'private':'normal')+'-'+lang+'-'+width,status:await p.locator('[name=consent]').getAttribute('required')!==null&&await p.locator('[name=consent]').getAttribute('type')==='checkbox'&&await p.locator('[data-confirm-form] button').isEnabled()?'PASS':'FAIL'});
   if(redacted)rows.push({id:'private-no-metadata-'+lang+'-'+width,status:!text.includes('ORG04 PRIVATE SECRET')&&!text.includes('ORG04 PRIVATE ADDRESS')&&!text.includes('Archived network')&&await p.locator('tbody td strong').innerText()==='#82'?'PASS':'FAIL'});
   if(redacted){const expected={ru:'Карточка недоступна для просмотра. Подтверждение относится только к связи места.',az:'Məkan kartına baxmaq mümkün deyil.',en:'The place card is not available to view.'};rows.push({id:'private-copy-language-'+lang+'-'+width,status:text.includes(expected[lang])?'PASS':'FAIL'});}
   if(width===390||width===1440)await p.locator('main').screenshot({path:'output/playwright/org04-fix-20261008/review-'+(redacted?'private':'normal')+'-'+lang+'-'+width+'.png'});
  }
  await p.goto(base+prefixes[lang]+'/account/places/');
  const link=p.locator('a[href="'+prefixes[lang]+'/account/organizations/43/branches/74/detach-preview/"]');
  rows.push({id:'owner-places-review-link-'+lang+'-'+width,status:await link.count()===1&&await p.locator('form[action$="/branches/74/detach/"]').count()===0?'PASS':'FAIL'});
 }catch(e){rows.push({id:'matrix-harness-'+lang+'-'+width,status:'FAIL',error:String(e).slice(0,240)});}finally{await c.close();}
}
return {rows,errors,network};
}
