async original=>{
const B='http://127.0.0.1:34169',H='/home/ramin/kidsmap/docs/qa/mod-qa02-fix-2026-10-15-r1',F=await(await original.request.get(B+'/qa/fixtures/')).json(),source=await(await original.request.get(B+'/qa/source/')).json(),rows=[],diagnostics=[];
const state=async()=>await(await original.request.get(B+'/qa/state/')).json(),before=await state();
for(const role of ['admin','reviewer']){
 const ctx=await original.context().browser().newContext(),p=await ctx.newPage();let lang='ru',width=1440;
 await ctx.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 p.on('pageerror',e=>diagnostics.push({role,lang,width,kind:'pageerror',text:String(e).split('\n')[0]}));
 p.on('requestfailed',r=>diagnostics.push({role,lang,width,kind:'requestfailed',local:r.url().startsWith(B+'/'),host:new URL(r.url()).host,error:r.failure()?.errorText}));
 p.on('console',m=>{if(m.type()==='error')diagnostics.push({role,lang,width,kind:'console',local:m.location().url.startsWith(B+'/'),text:m.text().replace(/https?:\S+/g,'[URL]')});});
 const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width,detail});
 const wait=async()=>await p.waitForLoadState('networkidle');
 const shot=async(tag)=>await p.screenshot({path:H+'/screenshots/'+role+'-'+lang+'-'+width+'-'+tag+'.png',fullPage:true,animations:'disabled'});
 try{
 await p.goto(B+'/ru/admin/login/?next=/ru/admin/volunteer/moderation/');await p.locator('[name=username]').fill(F.actors[role]);await p.locator('[name=password]').fill(F.password);await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/admin/volunteer/moderation/')),p.locator('form button[type=submit]').click()]);await wait();add('native authorized login',await p.locator('.km-volunteer h1').isVisible());
 for(lang of ['ru','az','en']){
  await p.locator('.km-admin-lang-btn').click();const f=p.locator('form.km-admin-lang-switch-form').filter({has:p.locator('input[name=language][value='+lang+']')});await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),f.locator('button[type=submit]').click()]);await wait();add('native menu selects actual locale',await p.locator('html').getAttribute('lang')===lang);
  const prefix=lang==='az'?'/':'/'+lang+'/';
  for(width of [360,390,768,1024,1280,1440]){
   try{
   await p.setViewportSize({width,height:950});await p.goto(B+prefix+'admin/volunteer/moderation/?entity=place&status=pending');await wait();const entry=p.locator('.km-volunteer-hub-table tbody a').filter({hasText:'QA media review'});add('pending queue exposes fixture',await entry.count()===1);
   await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/moderation/content/'+F.revision_id+'/')),entry.click()]);await wait();add('native queue detail uses actual locale',await p.locator('html').getAttribute('lang')===lang);
   const images=p.locator('.km-hub-media-comparison img');await images.evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode().catch(()=>{}))));const data=await images.evaluateAll(imgs=>imgs.map(i=>({src:i.getAttribute('src'),decoded:i.complete&&i.naturalWidth>0,alt:i.alt})));
   add('eight current candidate images decoded',data.length===8&&data.every(i=>i.decoded),{images:data.length,decoded:data.filter(i=>i.decoded).length});
   add('main cover gallery use exact own stored media URLs',JSON.stringify(data.map(x=>x.src).sort())===JSON.stringify(Object.values(F.media).map(x=>'/media/'+x).sort()));
   const gallery=await p.locator('.km-hub-media-comparison tbody tr').filter({has:p.locator('th',{hasText:source.translations[lang]['Галерея']})}).locator('img').evaluateAll(imgs=>imgs.map(i=>i.getAttribute('src')));
   add('gallery follows saved order on both sides',JSON.stringify(gallery)===JSON.stringify(['live-gallery-1','live-gallery-2','candidate-gallery-1','candidate-gallery-2'].map(k=>'/media/'+F.media[k])));
   const copy=await p.locator('.km-hub-media-comparison').innerText();add('localized gallery before after accessible labels',copy.includes(source.translations[lang]['Галерея'])&&data.every(x=>x.alt.includes(source.translations[lang]['Текущее фото'])||x.alt.includes(source.translations[lang]['Предложенное фото'])));
   add('raw media paths and dictionaries absent from comparison text',!copy.includes('places/')&&!copy.includes("'image':"));
   const geom=await p.locator('.km-hub-media-comparison').evaluate(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,viewport:innerWidth,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,images:[...e.querySelectorAll('img')].map(i=>{const q=i.getBoundingClientRect();return{left:q.left,right:q.right,width:q.width,height:q.height,fit:getComputedStyle(i).objectFit};})};});
   add('comparison and each photo fit viewport without horizontal clipping',geom.left>=-.5&&geom.right<=width+.5&&geom.scrollWidth<=geom.clientWidth+1&&geom.images.every(i=>i.left>=-.5&&i.right<=width+.5&&i.width>0&&i.height>0&&i.fit==='contain'),geom);
   const first=p.locator('.km-hub-media-comparison a').first();await p.locator('.km-volunteer > a').focus();await p.keyboard.press('Tab');const focus=await first.evaluate(e=>({active:e===document.activeElement,visible:e.matches(':focus-visible'),outline:getComputedStyle(e).outlineWidth}));add('native Tab reaches visible thumbnail focus',focus.active&&focus.visible&&parseFloat(focus.outline)>0,focus);
   await shot('focus');const [full]=await Promise.all([ctx.waitForEvent('page'),p.keyboard.press('Enter')]);await full.waitForLoadState('networkidle');await full.locator('img').first().waitFor();const decoded=await full.locator('img').first().evaluate(i=>i.decode().then(()=>i.naturalWidth>0).catch(()=>false));add('native Enter opens exact full image in new tab',full.url()===B+'/media/'+F.media['live-cover']&&decoded,{decoded});await full.close();await p.bringToFront();add('closing image keeps original thumbnail focus',await first.evaluate(e=>e===document.activeElement));
   await p.keyboard.press('Shift+Tab');add('native ShiftTab returns to moderation back link',await p.locator('.km-volunteer > a').evaluate(e=>e===document.activeElement));
   await p.locator('#hub-reason').focus();await p.keyboard.press('Tab');add('existing review actions remain keyboard reachable',await p.locator('button[name=action][value=approve]').evaluate(e=>e===document.activeElement&&e.matches(':focus-visible')));
   await p.reload();await wait();const again=p.locator('.km-hub-media-comparison img');await again.evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode().catch(()=>{}))));add('reload preserves all eight decoded comparisons',await again.count()===8&&await again.evaluateAll(imgs=>imgs.every(i=>i.complete&&i.naturalWidth>0)));if([390,1440].includes(width))await shot('reload');
   await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/admin/volunteer/moderation/')),p.locator('.km-volunteer > a').click()]);await wait();add('native back returns to queue',await p.locator('.km-volunteer-hub-table').isVisible());
   }catch(e){rows.push({id:'main cell completion',status:'NOT RUN',role,lang,width,error:String(e).split('\n')[0]});}
  }
 }
 }catch(e){rows.push({id:'role login completion',status:'NOT RUN',role,lang,width,error:String(e).split('\n')[0]});}
 await ctx.close();
}
const after=await state();rows.push({id:'read-only main matrix preserves all live candidate data',status:JSON.stringify(before)===JSON.stringify(after)?'PASS':'FAIL',detail:{before,after}});
return{rows,diagnostics,mode:'approved MOD-QA-02 native main matrix only',source_template_sha256:source.loaded_template_sha256};}
