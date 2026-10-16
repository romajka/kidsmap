async original=>{
const B='__BASE__',F=__FIXTURE__,browser=original.context().browser(),rows=[];
const c=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();
try{
await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill('owner@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));
for(const [lang,expected] of [['az',['Tədbirin redaktəsi','Tədbir formasının mərhələləri','İrəli']],['en',['Edit event','Event form steps','Next']]]){
await p.goto(B+(lang==='az'?'':'/'+lang)+'/account/places/events/'+F.event+'/edit/');
const badge=await p.locator('.org-status').innerText();const nav=await p.locator('[aria-label="'+expected[1]+'"]').count(),next=await p.getByRole('button',{name:expected[2],exact:true}).count();
rows.push({id:'event-owner-locale-'+lang,status:badge.trim()===expected[0]&&nav===1&&next>=1?'PASS':'FAIL',badge,nav,next});
}
}catch(e){return{rows,error:String(e)}}finally{await c.close()}
return{rows};}