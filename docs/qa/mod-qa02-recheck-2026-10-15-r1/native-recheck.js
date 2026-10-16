async original=>{
const B='http://127.0.0.1:32937',H='/home/ramin/kidsmap/docs/qa/mod-qa02-recheck-2026-10-15-r1',F=await(await original.request.get(B+'/qa/fixtures/')).json(),rows=[],diagnostics=[];
const state=async()=>await(await original.request.get(B+'/qa/state/')).json(),before=await state();
for(const role of ['admin','reviewer']){
 const ctx=await original.context().browser().newContext(),p=await ctx.newPage();let lang='ru',width=1440;
 await ctx.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 p.on('pageerror',e=>diagnostics.push({role,lang,width,kind:'pageerror',error:String(e).split('\n')[0]}));
 p.on('requestfailed',r=>diagnostics.push({role,lang,width,kind:'requestfailed',local:r.url().startsWith(B+'/'),error:r.failure()?.errorText}));
 p.on('console',m=>{if(m.type()==='error')diagnostics.push({role,lang,width,kind:'console',local:m.location().url.startsWith(B+'/'),text:m.text().replace(/https?:\S+/g,'[URL]')});});
 const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width,detail});
 const wait=async()=>await p.waitForLoadState('networkidle');
 try{
  await p.goto(B+'/ru/admin/login/?next=/ru/admin/volunteer/moderation/');await p.locator('[name=username]').fill(F.actors[role]);await p.locator('[name=password]').fill(F.password);await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/admin/volunteer/moderation/')),p.locator('form button[type=submit]').click()]);await wait();add('native authorized role login',await p.locator('.km-volunteer h1').isVisible());
  for(lang of ['ru','az','en']){
   await p.locator('.km-admin-lang-btn').click();const f=p.locator('form.km-admin-lang-switch-form').filter({has:p.locator('input[name=language][value='+lang+']')});await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),f.locator('button[type=submit]').click()]);await wait();add('native language menu selects actual locale',await p.locator('html').getAttribute('lang')===lang);
   const prefix=lang==='az'?'/':'/'+lang+'/';
   for(width of [360,390,768,1024,1280,1440]){
    await p.setViewportSize({width,height:950});await p.goto(B+prefix+'admin/volunteer/moderation/?entity=place&status=pending');await wait();
    const entry=p.locator('.km-volunteer-hub-table tbody a').filter({hasText:'QA media review'});add('pending queue exposes actual fixture',await entry.count()===1);
    await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/moderation/content/'+F.revision_id+'/')),entry.click()]);await wait();
    add('native queue link opens authorized detail in actual locale',await p.locator('.km-volunteer h1').isVisible()&&await p.locator('html').getAttribute('lang')===lang,{path:new URL(p.url()).pathname,html_lang:await p.locator('html').getAttribute('lang')});
    const cells=await p.locator('.km-volunteer-comparison tbody tr').evaluateAll(rs=>rs.map(r=>({label:r.querySelector('th')?.textContent.trim(),values:[...r.querySelectorAll('td')].map(c=>c.textContent.trim()),images:r.querySelectorAll('img').length})));
    add('valid main cover gallery candidate reaches comparison',cells.length===3&&cells.some(c=>c.values[1]?.includes('mod02-candidate-main'))&&cells.some(c=>c.values[1]?.includes('mod02-candidate-cover'))&&cells.some(c=>c.values[1]?.includes('mod02-candidate-gallery-1')&&c.values[1]?.includes('mod02-candidate-gallery-2')),{fields:cells.map(c=>c.label),comparison_rows:cells.length});
    const n=await p.locator('.km-volunteer-comparison img').count();add('current and proposed photos render as eight images',n===8,{actual_images:n,expected_images:8});
    const gal=cells.find(c=>c.values[1]?.includes('mod02-candidate-gallery-1'));add('gallery exposes ordered visual preview',gal?.images===4,{actual_gallery_images:gal?.images??0,expected_gallery_images:4,raw_dict_text:!!gal?.values[1]?.includes("'image':")});
    const reason=p.locator('#hub-reason');await reason.focus();await p.keyboard.press('Tab');const focus=await p.locator('button[name=action][value=approve]').evaluate(e=>({active:e===document.activeElement,visible:e.matches(':focus-visible'),outline:getComputedStyle(e).outlineWidth}));add('existing review actions remain keyboard reachable',focus.active&&focus.visible,{...focus});
    await p.screenshot({path:H+'/screenshots/'+role+'-'+lang+'-'+width+'.png',fullPage:true,animations:'disabled'});
    await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/admin/volunteer/moderation/')),p.locator('.km-volunteer > a').click()]);await wait();add('native back link returns to queue',await p.locator('.km-volunteer-hub-table').isVisible());
   }
  }
 }catch(e){rows.push({id:'browser flow completion',status:'NOT RUN',role,lang,width,error:String(e).split('\n')[0]});}
 await ctx.close();
}
const after=await state();rows.push({id:'read-only detail preserves candidate live and gallery',status:JSON.stringify(before)===JSON.stringify(after)?'PASS':'FAIL',detail:{before,after}});
return{rows,diagnostics,mode:'PLAN MOD-QA-02; native staff recheck of canonical service-seeded draft/submitted fixture; author upload, approve/reject and postpatch NOT RUN',source_changes:[]};}
