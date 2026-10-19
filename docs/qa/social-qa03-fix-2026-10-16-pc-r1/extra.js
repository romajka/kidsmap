async(page)=>{
 const context=page.context(),a=context.pages()[0],origin='http://127.0.0.1:33271';
 const cases=[{"cell": 0, "kind": "place", "lang": "ru", "width": 360, "pk": 1, "url": "/ru/reviews/place/target/1/"}, {"cell": 18, "kind": "activity", "lang": "ru", "width": 360, "pk": 1, "url": "/ru/reviews/activity/target/1/"}, {"cell": 36, "kind": "event", "lang": "ru", "width": 360, "pk": 1, "url": "/ru/reviews/event/target/1/"}, {"cell": 54, "kind": "specialist", "lang": "ru", "width": 360, "pk": 1, "url": "/ru/reviews/specialist/target/1/"}],rows=[];let accessibility=null;
 const stable=s=>{const{retry_after,...rest}=s;return rest;};
 for(const item of cases){
  let before=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
  const b=await context.newPage(),events=[];
  await b.setViewportSize({width:360,height:844});await b.goto(origin+item.url);
  await b.getByRole('combobox').selectOption('2');await b.getByRole('textbox').fill('Supplementary accessible draft B');
  if(item.kind==='specialist'){
   await a.goto(origin+item.url);await a.getByRole('combobox').selectOption('5');await a.getByRole('textbox').fill('Latest private candidate A');
   await Promise.all([a.waitForNavigation({waitUntil:'domcontentloaded'}),a.locator('form[data-review-edit] button').click()]);
   const protectedA=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
   const [response]=await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.locator('form[data-review-edit] button').click()]);
   const afterConflict=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
   const heading=b.locator('#review-conflict-title');await heading.scrollIntoViewIfNeeded();await b.mouse.wheel(0,-160);await b.waitForTimeout(100);
   const reached=await heading.evaluate(el=>{const r=el.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return r.top>=0&&r.bottom<=innerHeight&&(el===hit||el.contains(hit));});
   const style=await b.locator('form[data-review-edit] button').evaluate(el=>{const s=getComputedStyle(el);return{color:s.color,background:s.backgroundColor,fontSize:s.fontSize,fontWeight:s.fontWeight};});
   const png='/mnt/c/kidsmap/.tmp/social03-pc-fix-r1/png/accessibility-heading-specialist.png';await b.screenshot({path:png});
   accessibility={item,checks:{actual409:response.status()===409,no_write:JSON.stringify(stable(protectedA))===JSON.stringify(stable(afterConflict)),heading_readable_after_native_scroll:reached},style,png};
   before=afterConflict;
  }
  await b.getByRole('textbox').fill('SIMULATED transport attempt');
  let intercepted=0;
  b.on('requestfailed',r=>events.push({url:r.url(),error:r.failure()?.errorText}));
  b.on('pageerror',e=>events.push({pageerror:e.message}));
  await b.route(origin+item.url,async route=>{if(route.request().method()==='POST'){intercepted++;await route.abort('failed');}else await route.continue();});
  let navigation_error=null;
  try{await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded',timeout:5000}),b.locator('form[data-review-edit] button').click()]);}catch(error){navigation_error=error.message;}
  await b.waitForTimeout(500);
  const after=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
  const png=`/mnt/c/kidsmap/.tmp/social03-pc-fix-r1/png/simulated-transport-${item.kind}.png`;
  await b.screenshot({path:png,fullPage:true});
  rows.push({item,simulated:'POST transport aborted by QA route before server delivery',checks:{one_explicit_attempt:intercepted===1,no_write:JSON.stringify(stable(before))===JSON.stringify(stable(after))},before,after,events,navigation_error,png});
  await b.close();
 }
 await a.goto(origin+cases[0].url);
 const colors=await a.locator('form[data-review-edit] button').evaluate(el=>{const s=getComputedStyle(el);return{color:s.color,background:s.backgroundColor,fontSize:s.fontSize,fontWeight:s.fontWeight};});
 return{transport:rows,accessibility,existing_normal_editor_button_style:colors,note:'Shared CSS unmodified; style sample is not a full WCAG audit'};
}
