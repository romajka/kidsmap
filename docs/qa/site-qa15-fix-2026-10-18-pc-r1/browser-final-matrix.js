async original=>{
const base='http://127.0.0.1:33500',O='/mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1',baseline=__BASELINE__,rows=[],pageerrors=[],local_errors=[],blocked=[],console_errors=[],browser=original.context().browser();
const expected={ru:'Настройки изменились в другой вкладке. Ваш ввод не сохранён. Скопируйте нужные значения и откройте текущую версию отдельно.',en:'Settings changed in another tab. Your input has not been saved. Copy the values you need and open the current version separately.',az:'Parametrlər başqa vərəqdə dəyişdirilib. Daxil etdiyiniz məlumatlar yadda saxlanılmayıb. Lazım olan dəyərləri köçürün və cari versiyanı ayrıca açın.'};
const path='/admin/catalog/sitefootersettings/1/change/';let serial=0;
try{
for(const role of ['content','super']){
 const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});
 await c.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='127.0.0.1')return r.continue();blocked.push(u.hostname);return r.abort();});
 const a=await c.newPage(),b=await c.newPage();
 for(const p of [a,b]){p.setDefaultTimeout(12000);p.on('pageerror',e=>pageerrors.push({role,message:String(e)}));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});p.on('response',r=>{const u=new URL(r.url());if(u.hostname==='127.0.0.1'&&r.status()>=400&&r.status()!==409)local_errors.push({path:u.pathname,status:r.status()});});}
 await a.goto(base+'/qa/site15/login/'+role+'/');const state=async()=>(await a.request.get(base+'/qa/site15/state/')).json();
 async function save(p){const button=p.locator('button[name=_continue]');const visible=await button.isVisible();p.site15SaveMethod=visible?'native button':'native Enter';const [r]=await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path),p.waitForNavigation({waitUntil:'domcontentloaded'}),visible?button.click():p.locator('[name=footer_phone]').press('Enter')]);return r.status();}
 for(const lang of ['az','ru','en']){
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await a.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const width of [360,390,768,1024,1280,1440])for(const scenario of ['same','disjoint']){
   const id=++serial;for(const p of [a,b])await p.setViewportSize({width,height:950});await a.goto(base+path);await b.goto(base+path);
   const originalRevision=await b.locator('[name=settings_revision]').inputValue(),before=await state(),avalue='+99450150'+String(id).padStart(3,'0'),field=scenario==='same'?'footer_phone':'footer_email',draft=scenario==='same'?'+99450160'+String(id).padStart(3,'0'):'site15-green-b-'+id+'@example.invalid';
   await a.locator('[name=footer_phone]').fill(avalue);const aStatus=await save(a),afterA=await state();
   await b.locator('[name='+field+']').fill(draft);const bStatus=await save(b);await b.waitForTimeout(80);
   const afterB=await state(),alert=b.locator('.km-place-form-alert[role=alert]'),text=await alert.innerText(),bound=await b.locator('[name='+field+']').inputValue(),revision=await b.locator('[name=settings_revision]').inputValue();
   const alertFocused=await alert.evaluate(e=>e===document.activeElement),link=alert.locator('a[target=_blank]');
   await b.keyboard.press('Tab');const linkFocused=await link.evaluate(e=>e===document.activeElement),focusStyle=await link.evaluate(e=>({outline:getComputedStyle(e).outlineStyle,shadow:getComputedStyle(e).boxShadow}));
   const geometry=await b.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:innerWidth})),old=baseline.rows.find(x=>x.role===role&&x.lang===lang&&x.width===width).geometry;
   const layout=await alert.evaluate(e=>{const c=e.querySelector('.km-place-form-alert__content'),li=c.querySelector('.errorlist li'),a=c.querySelector('a'),cr=c.getBoundingClientRect(),lr=li.getBoundingClientRect(),ar=a.getBoundingClientRect();return{contentWidth:cr.width,messageWidth:lr.width,linkBelowMessage:ar.top>=lr.bottom-1,messageWithinContent:lr.left>=cr.left-1&&lr.right<=cr.right+1};});
   rows.push({layout,id,role,lang,width,scenario,aStatus,bStatus,interaction:b.site15SaveMethod,before,afterA,afterB,draft,bound,geometry,baseline:old,focusStyle,checks:{readableMessage:layout.messageWidth>=100,recoveryBelowMessage:layout.linkBelowMessage,messageWithinContent:layout.messageWithinContent,a302:aStatus===302,aStored:afterA.footer_phone===avalue,b409:bStatus===409,noRowFileLogWrite:JSON.stringify(afterA)===JSON.stringify(afterB),draftRetained:bound===draft,oldRevisionRetained:originalRevision===revision,language:await b.locator('html').getAttribute('lang')===lang,localizedConflict:text.includes(expected[lang]),alertFocused,linkKeyboard:linkFocused,visibleKeyboardFocus:focusStyle.outline!=='none'||focusStyle.shadow!=='none',safeRecoveryLink:await link.getAttribute('href')===path&&((await link.getAttribute('rel'))||'').includes('noopener'),noSuccess:await b.locator('.alert-success,.km-toast--success').count()===0,noNewOverflow:geometry.document<=Math.max(width,old.document)+1}});
   await b.screenshot({path:O+'/png/final-'+role+'-'+lang+'-'+width+'-'+scenario+'-conflict.png',animations:'disabled'});
  }
 }
 await c.close();
}
return{rows,pageerrors,local_errors,console_errors,blocked,scope:'72 native same/disjoint two-tab cases; all writes on own fixtureDB, synthetic role login only'};
}catch(e){return{rows,pageerrors,local_errors,console_errors,blocked,error:String(e)};}
}
