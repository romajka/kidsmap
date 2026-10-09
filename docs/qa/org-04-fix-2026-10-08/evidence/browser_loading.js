async original=>{
const browser=original.context().browser(),base='http://localhost:8788',rows=[],errors=[];
for(const width of [390,1440]){
 const c=await browser.newContext({viewport:{width,height:950},reducedMotion:'reduce'}),p=await c.newPage(),observed=[];
 await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());p.on('pageerror',e=>errors.push(String(e)));
 p.on('console',m=>{if(m.text().startsWith('ORG04-loading:'))observed.push(JSON.parse(m.text().slice(14)));});
 try{
 await p.goto(base+'/qa/');await p.getByRole('button',{name:'Войти: demo_owner',exact:true}).click();await p.goto(base+'/ru/account/organizations/43/branches/74/detach-preview/');
 await p.evaluate(()=>{const form=document.querySelector('[data-confirm-form]');form.addEventListener('submit',()=>setTimeout(()=>console.log('ORG04-loading:'+JSON.stringify({disabled:form.querySelector('button[type=submit]').disabled,status:form.querySelector('[data-submit-status]').textContent})),20));});
 await p.route('**/detach-preview/',async r=>{if(r.request().method()!=='POST')return r.continue();const res=await r.fetch({maxRedirects:0});await p.waitForTimeout(800);await r.fulfill({response:res});});
 const nav=p.waitForNavigation({waitUntil:'load'});await p.locator('[name=consent]').check();await p.locator('[data-confirm-form] button[type=submit]').click();await nav;
 rows.push({id:'loading-and-repeat-button-'+width,status:observed.length===1&&observed[0].disabled&&observed[0].status.includes('Обработка')?'PASS':'FAIL',observed});
 rows.push({id:'loading-result-'+width,status:await p.locator('tr[data-result=already_detached]').count()===1?'PASS':'FAIL'});
 }catch(e){rows.push({id:'loading-harness-'+width,status:'FAIL',error:String(e).slice(0,240)});}finally{await c.close();}
}
return{rows,errors};}
