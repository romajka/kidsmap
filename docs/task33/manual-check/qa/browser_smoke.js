async page => {
 const origin='http://127.0.0.1:8780',errors=[],failed=[],checks=[],screens=[];
 page.on('pageerror',e=>errors.push({type:'pageerror',message:String(e)}));
 page.on('console',m=>{if(m.type()==='error')errors.push({type:'console',message:m.text(),url:m.location().url});});
 page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()?.errorText}));
 const fixture=await (await page.request.get(origin+'/qa/fixtures.json')).json();
 const login=async role=>{
  await page.goto(origin+'/qa/');await page.locator('#all-links a').first().waitFor();
  await page.getByRole('button',{name:role==='guest'?'Выйти в гостя':'Войти: demo_'+role,exact:true}).click();
  await page.locator('#all-links a').first().waitFor();
  if(role!=='guest'&&!await page.locator('header').innerText().then(t=>t.includes('demo_'+role)))throw new Error('Role login failed '+role);
 };
 const inspect=async(role,key,lang='ru',expected=[200])=>{
  const path=fixture.links[lang][key];const r=await page.request.get(origin+path,{maxRedirects:expected.includes(302)?0:20});
  const location=r.headers().location||'';
  checks.push({role,key,lang,url:path,status:r.status(),location,pass:expected.includes(r.status())&&(!expected.includes(302)||location===fixture.links[lang].places)});
 };
 const shot=async(key,file,width=1440)=>{
  await page.setViewportSize({width,height:950});const r=await page.goto(origin+fixture.links.ru[key],{waitUntil:'networkidle'});
  await page.evaluate(()=>document.fonts.ready);
  const facts=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,h1:document.querySelector('h1')?.textContent.trim(),mains:document.querySelectorAll('main').length}));
  await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/'+file+'.png',fullPage:true});
  screens.push({key,file,width,status:r.status(),facts});
 };
 await login('guest');
 for(const lang of ['az','ru','en'])for(const key of ['home','catalog','place','place2','organization','activity','art','unclassified','specialists','specialist','zero','events','event_physical','event_online','event_cancelled','event_moved','about','faq','contacts'])await inspect('guest',key,lang);
 await inspect('guest','event_draft','ru',[404]);
 await shot('catalog','catalog-desktop');await shot('catalog','catalog-mobile',390);
 await shot('organization','organization');await shot('art','activity');await shot('specialist','specialist');await shot('events','events');
 await login('owner');
 for(const key of ['account','places','organizations','org_edit','place_edit','place2_edit','program','event_edit','new_event','inbox','team','org_specialists'])await inspect('owner',key);
 await inspect('owner','foreign_edit','ru',[302]);
 await shot('program','program-editor');await shot('event_edit','event-editor');
 await login('manager');await inspect('manager','place_edit');await inspect('manager','place2_edit','ru',[302]);await inspect('manager','foreign_edit','ru',[302]);
 await login('person');for(const key of ['person_edit','person_certificates','person_invitations','inbox'])await inspect('person',key);
 await login('moderator');for(const key of ['moderation','review_index'])await inspect('moderator',key);
 const admin=await page.request.get(origin+'/admin/');checks.push({role:'moderator',key:'admin',status:admin.status(),pass:admin.status()===200});
 await login('parent');for(const key of ['favorites','review','profile','inbox'])await inspect('parent',key);
 await login('outsider');await inspect('outsider','foreign_edit');await inspect('outsider','claim');
 await login('volunteer');const volunteer=await page.request.get(origin+'/admin/volunteer/');checks.push({role:'volunteer',key:'volunteer',status:volunteer.status(),pass:volunteer.status()===200});
 await login('guest');await page.setViewportSize({width:390,height:900});await page.goto(origin+'/qa/');await page.locator('#all-links a').first().waitFor();
 const guide=await page.evaluate(()=>({steps:document.querySelectorAll('.step').length,links:document.querySelectorAll('#all-links a').length,width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/guide-mobile.png',fullPage:false});
 return {checks,screens,guide,errors,failed,status:checks.every(c=>c.pass)&&errors.length===0&&screens.every(s=>s.status===200&&s.facts.scrollWidth<=s.width)&&guide.scrollWidth<=guide.width?'PASS':'REVIEW_REQUIRED'};
}
