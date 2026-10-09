async(page)=> {
 const base='http://localhost:8784'; const role='owner';
 const ctx=await page.context().browser().newContext(); const p=await ctx.newPage(); p.setDefaultTimeout(4000); p.on('dialog',d=>d.accept().catch(()=>{}));
 await p.goto(base+'/qa/');await Promise.all([p.waitForNavigation(),p.getByRole('button',{name:'Войти: demo_'+(role==='owner'?'owner':'moderator'),exact:true}).press('Enter')]);
 const out=[];
 for(const lang of ['ru','az','en']) {
   await ctx.addCookies([{name:'django_language',value:lang,url:base}]);
   for(const width of [360,390,768,1440]) {await p.setViewportSize({width,height:900});
     for(const mode of ['new','edit']) {
       const path=role==='owner'?(lang==='az'?'':'/'+lang)+'/account/places/'+(mode==='new'?'create/?type=permanent&fresh=1':'6/edit/'):'/admin/catalog/place/'+(mode==='new'?'add/?type=permanent':'6/change/');
       const response=await p.goto(base+path,{waitUntil:'domcontentloaded',timeout:15000});await p.waitForFunction(role=>document.querySelector(role==='owner'?'.pc.pc-enhanced':'.km-pf.km-pf-entry-enhanced'),role);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(200);
       const data=await p.evaluate(role=>({lang:document.documentElement.lang,scrollWidth:document.documentElement.scrollWidth,width:innerWidth,form:!!document.querySelector(role==='owner'?'form[data-permanent-place-form]':'form#place_form'),nav:!!document.querySelector(role==='owner'?'[data-pc-section-select]':'[data-pf-section-select]'),exception:document.querySelector('.exception_value')?.textContent||null}),role);
       const screenshot=role+'-'+mode+'-'+lang+'-'+width+'.png';await p.screenshot({path:'/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/'+screenshot});
       out.push({role,mode,requestedLang:lang,width,url:p.url(),status:response.status(),...data,screenshot,pass:response.status()===200&&data.form&&data.nav&&data.lang===lang&&data.scrollWidth<=width+1});
     }
   }
 }
 await ctx.close();return out;
}