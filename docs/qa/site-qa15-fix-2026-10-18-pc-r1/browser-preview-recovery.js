async original=>{
const base='http://127.0.0.1:33500',O='/mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],local_errors=[],blocked=[],browser=original.context().browser(),path='/admin/catalog/sitefootersettings/1/change/';
let id=0;
try{
for(const lang of ['az','ru','en'])for(const width of [390,1440]){
 const c=await browser.newContext({viewport:{width,height:950},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
 const a=await c.newPage(),b=await c.newPage();for(const p of[a,b]){p.setDefaultTimeout(12000);p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(new URL(r.url()).hostname==='127.0.0.1'&&r.status()>=400&&r.status()!==409)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});}
 await a.goto(base+'/qa/site15/login/content/');const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await a.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
 const state=async()=>(await a.request.get(base+'/qa/site15/state/')).json();
 async function save(p){const button=p.locator('button[name=_continue]'),visible=await button.isVisible();const[r]=await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path),p.waitForNavigation({waitUntil:'domcontentloaded'}),visible?button.click():p.locator('[name=footer_phone]').press('Enter')]);return r.status();}
 await a.goto(base+path);await b.goto(base+path);const value='+99450270'+String(++id).padStart(3,'0'),draft='site15-explicit-'+id+'@example.invalid',oldToken=await b.locator('[name=settings_revision]').inputValue();
 await a.locator('[name=footer_phone]').fill(value);const aStatus=await save(a);await b.locator('[name=footer_email]').fill(draft);const bStatus=await save(b);const stored=await state();
 const link=b.locator('.km-place-form-alert a[target=_blank]');await link.focus();
 const popupPromise=c.waitForEvent('page');await b.keyboard.press('Enter');const fresh=await popupPromise;await fresh.waitForURL(base+path,{waitUntil:'domcontentloaded'});
 const currentPhone=await fresh.locator('[name=footer_phone]').inputValue(),currentEmail=await fresh.locator('[name=footer_email]').inputValue(),freshToken=await fresh.locator('[name=settings_revision]').inputValue(),originalStillBound=await b.locator('[name=footer_email]').inputValue();
 await fresh.locator('[name=footer_email]').fill(originalStillBound);const copiedStatus=await save(fresh),afterCopy=await state();
 const repeatedStatus=await save(b),afterRepeat=await state();
 rows.push({id:'explicit-new-tab-recovery',lang,width,aStatus,bStatus,copiedStatus,repeatedStatus,currentPhone,currentEmail,afterCopy,checks:{firstAndConflict:aStatus===302&&bStatus===409,currentVersionPhone:currentPhone===value,currentVersionHasSavedEmail:currentEmail===stored.footer_email,oldDraftRetained:originalStillBound===draft,freshRevision:freshToken!==oldToken,explicitCopySaves:copiedStatus===302&&afterCopy.footer_phone===value&&afterCopy.footer_email===draft,repeatedOldForm409:repeatedStatus===409,noRepeatMutation:JSON.stringify(afterCopy)===JSON.stringify(afterRepeat),noTokenRefresh:await b.locator('[name=settings_revision]').inputValue()===oldToken,oldDraftStillRetained:await b.locator('[name=footer_email]').inputValue()===draft}});
 await b.screenshot({path:O+'/png/preview-recovery-'+lang+'-'+width+'-old-draft.png',animations:'disabled'});await fresh.screenshot({path:O+'/png/preview-recovery-'+lang+'-'+width+'-fresh-saved.png',animations:'disabled'});await c.close();
}
return{rows,pageerrors,local_errors,blocked};
}catch(e){return{rows,pageerrors,local_errors,blocked,error:String(e)};}
}
