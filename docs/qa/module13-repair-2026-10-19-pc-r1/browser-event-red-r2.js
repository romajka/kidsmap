async original=>{
 const B='http://127.0.0.1:33810',rows=[],errors=[],pageerrors=[],c=await original.context().browser().newContext({viewport:{width:1440,height:950}}),p=await c.newPage();
 try{
  await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
  p.on('pageerror',e=>pageerrors.push(String(e)));
  const s=await(await c.request.get(B+'/qa/m13/state/')).json();
  await p.goto(B+'/qa/m13/login/owner/');
  await p.goto(B+'/ru/account/places/events/'+s.ids.event+'/manage/');
  const before=await p.locator('[name=start_datetime]').inputValue();
  await p.locator('[name=start_datetime]').fill('2026-11-02T12:00');
  await p.locator('[name=end_datetime]').fill('2026-11-02T13:00');
  await p.locator('[name=reason]').fill('Fictional Module13 native reschedule');
  const [res]=await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'),p.locator('button[formaction$="/reschedule/"]').click()]);
  await p.waitForLoadState('domcontentloaded');
  rows.push({id:'native-reschedule',checks:{redirect:res.status()===302,new_interval:(await p.locator('[name=start_datetime]').inputValue()).includes('2026-11-02')},before});
  for(const lang of ['az','ru','en']){
   await p.goto(B+s.urls[lang].organization);
   const missing=await p.locator('a[href="'+s.urls[lang].event+'"]').count()===0;
   rows.push({id:'historical-bug-'+lang,checks:{rescheduled_event_is_missing:missing}});
   await p.screenshot({path:'/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1/png/event-red-'+lang+'.png',fullPage:true});
  }
 }catch(e){errors.push(String(e))}finally{await c.close()}
 return{rows,errors,pageerrors,expected:'RED reproduction: missing from organization is observed defect, not accepted product behavior'};
}
