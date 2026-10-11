async original=>{
 const base='http://localhost:8813',c=await original.context().browser().newContext({reducedMotion:'reduce'}),p=await c.newPage(),rows=[],errors=[];
 await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());p.setDefaultTimeout(10000);p.on('dialog',d=>d.accept());p.on('pageerror',e=>errors.push(String(e)));
 const login=async role=>{await c.clearCookies();await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(role+'@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();};
 try{
  await login('moderator');await c.addCookies([{name:'django_language',value:'ru',url:base}]);
  for(const [name,lat,lng] of [['range','999','49.8671'],['zero-zero','0','0'],['half-pair','40.4093','']]){
   await p.goto(base+'/admin/catalog/place/3/change/');const t=p.locator('#location [data-place-section-toggle]');if(await t.getAttribute('aria-expanded')==='false')await t.click();await p.locator('[data-km-place-location-toggle]').click();await p.locator('[data-pf-coord-manual]').click();await p.locator('#id_lat').fill(lat);await p.locator('#id_lng').fill(lng);await p.locator('#id_lng').press('Tab');
   await Promise.all([p.waitForNavigation(),p.locator('[name=_continue]').first().click()]);
   const text=await p.locator('.errorlist,.errornote,.km-pf-field__error,.km-pf-errors,[data-place-error-summary]').allTextContents();
   const actualLat=await p.locator('#id_lat').inputValue(),actualLng=await p.locator('#id_lng').inputValue();const retained=name==='zero-zero'?actualLat!==''&&actualLng!==''&&Number(actualLat)===0&&Number(actualLng)===0:actualLat===lat;
   rows.push({id:'admin/coordinates/'+name,status:text.join('').trim().length>5&&retained?'PASS':'FAIL',role:'moderator',lang:'ru',width:390,lat:await p.locator('#id_lat').inputValue(),lng:await p.locator('#id_lng').inputValue(),errors:text});
   await p.setViewportSize({width:390,height:950});await p.locator('#location').scrollIntoViewIfNeeded();await p.screenshot({path:'C:/kidsmap/docs/qa/module01-2026-10-09-r2/screenshots/edge-admin-'+name+'-390.png'});
   await p.reload();
  }
  await login('owner');
  for(const lang of ['ru','az','en']){
   const prefix=lang==='az'?'':'/'+lang;await p.goto(base+prefix+'/account/places/create/?type=permanent&fresh=1');
   const options=await p.locator('[name=nature] option').allTextContents();
   rows.push({id:'owner/nature-choice-localization/'+lang,status:lang==='ru'||!options.some(x=>/[А-Яа-я]/.test(x))?'PASS':'FAIL',role:'owner',lang,width:390,options});
  }
  await p.goto(base+'/ru/account/places/2/edit/?fresh=1');const d=p.locator('[name=lat]').locator('xpath=ancestor::details');if(await d.getAttribute('open')===null)await d.locator(':scope > summary').click();await p.locator('[name=lat]').fill('40.4093');await p.locator('[name=lng]').fill('');
  const response=await Promise.all([p.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST'),p.locator('[name=form_action][value=save_draft]').click()]);const body=await response[0].json();
  rows.push({id:'owner/coordinate-half-pair-error',status:response[0].status()===422&&await p.locator('[name=lat]').inputValue()==='40.4093'?'PASS':'FAIL',role:'owner',lang:'ru',width:390,http:response[0].status(),errors:body.errors});
 }catch(e){rows.push({id:'edge-cases/stopped',status:'NOT RUN',reason:String(e),url:p.url()});}finally{await c.close();}
 return {rows,errors};
}
