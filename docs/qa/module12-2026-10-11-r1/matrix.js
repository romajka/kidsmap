async original=>{
__QA12_COMMON__
const network=[],consoleErrors=[];async function db(c){return(await c.request.get(B+'/qa/state/')).json();}
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
 const{c,p}=await context('owner',lang,width),lp=prefix(lang),before=await db(c);
 p.on('pageerror',e=>consoleErrors.push({lang,width,error:String(e)}));p.on('response',r=>{if(r.status()>=400&&new URL(r.url()).hostname==='localhost')network.push({lang,width,status:r.status(),url:r.url()});});
 for(const[state,id]of [['filled',1],['empty',2]]){
  const url=lp+'/account/places/'+id+'/analytics/',st=await visit(p,url),vals=await p.locator('.owner-analytics__grid article strong').allTextContents(),expected=['views','unique_visitors','favorites','contact_actions','directions'].map(k=>String(before.metrics[String(id)][k]));const g=await geometry(p),s=await shot(p,'owner-'+state+'-'+lang+'-'+width);
  add('owner-'+state+'-render',st===200,{http:st,values:vals},'owner',lang,width,p.url(),s);add('owner-'+state+'-db-ui-consistency',JSON.stringify(vals.map(x=>x.trim()))===JSON.stringify(expected),{actual:vals,expected},'owner',lang,width,p.url(),s);add('owner-'+state+'-geometry',g.document<=width+1,{geometry:g},'owner',lang,width,p.url(),s);
  if(state==='filled'){const small=await p.locator('.owner-analytics__grid small').allTextContents();add('owner-delta-language',lang!=='az'||!small.some(x=>x.includes('к прошлому периоду')),{text:small},'owner',lang,width,p.url(),s);}
 }
 await p.keyboard.press('Tab');const focus=await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e);return{tag:e.tagName,text:e.textContent.trim().slice(0,80),outline:s.outlineStyle,width:s.outlineWidth,shadow:s.boxShadow};});add('owner-tab-focus',focus.tag!=='BODY'&&(focus.outline!=='none'||focus.shadow!=='none'),{focus},'owner',lang,width,p.url());await p.keyboard.press('Shift+Tab');await p.keyboard.press('Escape');
 await p.goto('http://localhost:8830'+lp+'/account/places/1/analytics/');const dis=await shot(p,'owner-disabled-'+lang+'-'+width);add('owner-disabled-notice',await p.locator('.owner-analytics__notice').isVisible()&&await p.locator('.owner-analytics__grid').count()===0,{profile:'deliberate guard E103 silenced',SIMULATED:true},'owner',lang,width,p.url(),dis);
 await c.close();
 const ad=await context('admin',lang,width);
 for(const mode of ['disabled','filled','error']){
  const url='/admin/catalog/siteanalytics/?period=90'+(mode==='disabled'?'':'&qa_ga='+mode);const st=await visit(ad.p,url),g=await geometry(ad.p),s=await shot(ad.p,'admin-'+mode+'-'+lang+'-'+width),kpi=(await ad.p.locator('[data-kpi-value]').allTextContents()).map(x=>x.trim()),text=await ad.p.locator('body').innerText();
  add('admin-'+mode+'-render',st===200,{http:st,kpi,SIMULATED:mode!=='disabled'},'admin',lang,width,ad.p.url(),s);add('admin-'+mode+'-geometry',g.document<=width+1,{geometry:g,SIMULATED:mode!=='disabled'},'admin',lang,width,ad.p.url(),s);
  if(mode==='filled'){add('admin-90-range',kpi[0]!=='3650',{actual:kpi,period:90,mapped:'year',SIMULATED:true},'admin',lang,width,ad.p.url(),s);add('admin-chart-table-render',await ad.p.locator('#km-visits-chart').isVisible()&&await ad.p.locator('.km-top-places-table tbody tr').count()===1,{SIMULATED:true,chart:JSON.parse(await ad.p.locator('#km-visits-chart-data').textContent())},'admin',lang,width,ad.p.url(),s);}
  if(mode==='error')add('admin-backend-error-visible',text.includes('SIMULATED report backend unavailable'),{actualKpi:kpi,errorMessageVisible:text.includes('SIMULATED report backend unavailable'),SIMULATED:true},'admin',lang,width,ad.p.url(),s);
 }
 await ad.p.locator('[data-period="7"]').focus();await ad.p.keyboard.press('Enter');await ad.p.waitForLoadState('domcontentloaded');add('period-keyboard-enter',new URL(ad.p.url()).searchParams.get('period')==='7',{},'admin',lang,width,ad.p.url());await ad.p.keyboard.press('Tab');await ad.p.keyboard.press('Shift+Tab');await ad.p.keyboard.press('Escape');await ad.c.close();
 const guest=await context('guest',lang,width);const gb=await db(guest.c),st=await visit(guest.p,F.urls[lang].place),ga=await db(guest.c),s=await shot(guest.p,'public-card-'+lang+'-'+width),g=await geometry(guest.p);add('public-view-delta',ga.metrics['1'].views-gb.metrics['1'].views===1,{delta:ga.metrics['1'].views-gb.metrics['1'].views,before:gb.metrics['1'],after:ga.metrics['1']},'guest',lang,width,guest.p.url(),s);add('public-geometry',g.document<=width+1,{geometry:g},'guest',lang,width,guest.p.url(),s);await guest.c.close();
}
return{rows,consoleErrors,network,coverage:{languages:['ru','az','en'],widths:[360,390,768,1024,1280,1440],native:true,GA:'SIMULATED filled/error; real external NOT RUN'}};
}
