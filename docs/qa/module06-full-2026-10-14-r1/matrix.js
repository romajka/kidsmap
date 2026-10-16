async original=>{
 const B='__BASE__',D='__HERE__/screenshots/',F=__FIXTURES_JSON__,rows=[],diagnostics=[];
 const add=(id,ok,meta)=>rows.push({id,status:ok?'PASS':'FAIL',role:'anonymous',...meta});
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  const c=await original.context().browser().newContext({viewport:{width,height:950}});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(6500);const errors=[],blocked=[];
  p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(['error','warning'].includes(m.type()))errors.push(m.type()+': '+m.text());});p.on('requestfailed',r=>blocked.push({url:r.url().replace(/\?.*/,''),local:r.url().startsWith(B),reason:r.failure()?.errorText}));p.on('response',r=>{if(r.status()>=400&&r.url().startsWith(B))errors.push('HTTP '+r.status()+' '+r.url());});
  const prefix=lang==='az'?'/':'/'+lang+'/',urls=F.urls[lang];
  const states=[['home',prefix],['catalog',prefix+'catalog/'],['organizations',prefix+'organizations/'],['organization-detail',urls.organization],['specialists',prefix+'specialists/'],['specialist-detail',urls.specialist],['events',prefix+'events/'],['event-detail',urls.events.Scheduled],['event-cancelled',urls.events.Cancelled],['place-long-fallback',urls.places.LongFallback],['activity',prefix+'activities/'+F.groups.Younger.activity+'/'],['empty',prefix+'catalog/?q=NO_MATCH_QA06_zzz']];
  try{
   for(const [state,url] of states){
    const response=await p.goto(B+url,{waitUntil:'domcontentloaded'});await p.waitForTimeout(230);
    if(state==='home'){const pause=p.locator('[data-rail-toggle]');if(await pause.count())await pause.first().click();}
    const screenshot=state+'-'+lang+'-'+width+'.png';await p.screenshot({path:D+screenshot,fullPage:true,animations:'disabled'});
    const evidence=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,mainText:document.querySelector('main')?.innerText.slice(0,1100),h1:document.querySelector('h1')?.innerText,lang:document.documentElement.lang,brokenLocalImages:[...document.images].filter(x=>x.src.startsWith(location.origin)&&x.complete&&!x.naturalWidth).map(x=>x.getAttribute('src')),fallback:[...document.querySelectorAll('[lang="az"]')].slice(0,8).map(x=>x.textContent.slice(0,80))}));
    add(state+'-render',response.status()===200&&Boolean(evidence.mainText)&&!evidence.mainText.includes('HIDDEN06_'),{lang,width,url:p.url(),screenshot,evidence});
    add(state+'-root-overflow',evidence.scroll<=width+1,{lang,width,url:p.url(),screenshot,scrollWidth:evidence.scroll});
    add(state+'-local-images',evidence.brokenLocalImages.length===0,{lang,width,screenshot,broken:evidence.brokenLocalImages});
    if(state==='catalog'){
     await p.locator('[data-sort-trigger]').click();await p.screenshot({path:D+'sort-open-'+lang+'-'+width+'.png'});await p.keyboard.press('Escape');
     await p.waitForTimeout(300);add('sort-Escape',await p.locator('[data-sort-trigger]').getAttribute('aria-expanded')==='false',{lang,width,screenshot:'sort-open-'+lang+'-'+width+'.png'});
     if(width<=768&&await p.locator('[data-filters-open]').first().isVisible()){
      await p.locator('[data-filters-open]').first().click();await p.screenshot({path:D+'filters-open-'+lang+'-'+width+'.png'});await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');const focus=await p.evaluate(()=>({tag:document.activeElement.tagName,outline:getComputedStyle(document.activeElement).outlineStyle,shadow:getComputedStyle(document.activeElement).boxShadow,inDrawer:!!document.activeElement.closest('[data-filters-drawer]')}));await p.keyboard.press('Escape');
      add('drawer-keyboard-Escape',await p.locator('[data-filters-open]').first().getAttribute('aria-expanded')==='false',{lang,width,screenshot:'filters-open-'+lang+'-'+width+'.png',focus});
     }
     await p.locator('[data-catalog-map-open]').click();await p.waitForTimeout(350);const text=await p.locator('[data-catalog-map]').innerText();await p.screenshot({path:D+'map-sdk-absent-'+lang+'-'+width+'.png'});
     add('map-SDK-absence-graceful',text.length>0&&!text.includes('undefined'),{lang,width,url:p.url(),screenshot:'map-sdk-absent-'+lang+'-'+width+'.png',text,classification:'SIMULATED blocked SDK'});await p.locator('[data-catalog-map-close]').click();
     add('map-close',!(await p.locator('[data-catalog-map-panel]').isVisible()),{lang,width});
    }
   }
  }catch(e){await p.screenshot({path:D+'matrix-harness-error-'+lang+'-'+width+'.png',fullPage:true});rows.push({id:'matrix-harness-error',status:'NOT RUN',role:'anonymous',lang,width,error:String(e),url:p.url()});}
  diagnostics.push({lang,width,errors,failedRequests:blocked});await c.close();
 }
 return{browser:original.context().browser().version(),rows,diagnostics};
}
