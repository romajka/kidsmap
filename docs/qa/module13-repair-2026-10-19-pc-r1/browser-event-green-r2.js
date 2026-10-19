async original=>{
 const B='http://127.0.0.1:33810',rows=[],errors=[],pageerrors=[],badResponses=[],contexts=[],br=original.context().browser();
 async function make(role,lang='ru',width=1440){const c=await br.newContext({viewport:{width,height:950},userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36'});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());await c.addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);const p=await c.newPage();p.setDefaultTimeout(12000);p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.status()>=500)badResponses.push({status:r.status(),path:new URL(r.url()).pathname})});if(role)await p.goto(B+'/qa/m13/login/'+role+'/');return{c,p}}
 try{
  const owner=await make('owner'),s=await(await owner.c.request.get(B+'/qa/m13/state/')).json(),manage=B+'/ru/account/places/events/'+s.ids.event+'/manage/';
  await owner.p.goto(manage);await owner.p.locator('[name=start_datetime]').fill('2026-11-02T12:00');await owner.p.locator('[name=end_datetime]').fill('2026-11-02T13:00');await owner.p.locator('[name=reason]').fill('Native physical upcoming transfer');const[first]=await Promise.all([owner.p.waitForResponse(r=>r.request().method()==='POST'),owner.p.locator('button[formaction$="/reschedule/"]').click()]);await owner.p.waitForLoadState('domcontentloaded');rows.push({id:'physical-native-first-reschedule',checks:{saved:first.status()===302}});
  for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440]){
   const {p}=await make(null,lang,width);let res=await p.goto(B+s.urls[lang].organization);const link=p.locator('a[href="'+s.urls[lang].event+'"]');
   const checks={organization_ok:res.status()===200,event_link_visible:await link.count()>0,no_overflow:await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)};
   await link.first().focus();checks.keyboard_focus=await link.first().evaluate(e=>e===document.activeElement);await Promise.all([p.waitForURL(B+s.urls[lang].event),p.keyboard.press('Enter')]);await p.waitForLoadState('domcontentloaded');checks.same_event_url=new URL(p.url()).pathname===s.urls[lang].event;checks.new_date=await p.locator('body').innerText().then(t=>t.includes('02.11.2026'));
   checks.one_main=await p.locator('main').count()===1;checks.one_h1=await p.locator('h1').count()===1;
   await p.reload();checks.reload_ok=await p.locator('h1').count()===1;
   rows.push({id:'rescheduled-public',lang,width,checks});
   if(width===390||width===1440)await p.screenshot({path:'/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1/png/event-green-r2-'+lang+'-'+width+'.png',fullPage:true});
  }
  await owner.p.goto(manage);const stale=await owner.c.newPage();await stale.goto(manage);
  await owner.p.locator('[name=start_datetime]').fill('2026-11-03T12:00');await owner.p.locator('[name=end_datetime]').fill('2026-11-03T13:00');await owner.p.locator('[name=reason]').fill('Fictional repeated native transfer');
  const[res]=await Promise.all([owner.p.waitForResponse(r=>r.request().method()==='POST'),owner.p.locator('button[formaction$="/reschedule/"]').click()]);await owner.p.waitForLoadState('domcontentloaded');
  rows.push({id:'second-reschedule',checks:{redirect:res.status()===302,readback:(await owner.p.locator('[name=start_datetime]').inputValue()).includes('2026-11-03')}});
  await stale.locator('[name=reason]').fill('Fictional stale cancellation must fail');const[staleres]=await Promise.all([stale.waitForResponse(r=>r.request().method()==='POST'),stale.locator('button[formaction$="/cancel/"]').click()]);await stale.waitForLoadState('domcontentloaded');
  rows.push({id:'stale-native-cancel',checks:{conflict:staleres.status()===200&&await stale.locator('[data-error-code=stale_version]').count()===1,no_cancel:(await stale.locator('[name=start_datetime]').inputValue()).includes('2026-11-02')}});
  const guest=await make();await guest.p.goto(B+s.urls.az.organization);rows.push({id:'conflict-public-retained',checks:{still_upcoming:await guest.p.locator('a[href="'+s.urls.az.event+'"]').count()>0}});
  await owner.p.goto(manage);await owner.p.locator('[name=reason]').fill('Fictional explicit Module13 cancellation');const[cancel]=await Promise.all([owner.p.waitForResponse(r=>r.request().method()==='POST'),owner.p.locator('button[formaction$="/cancel/"]').click()]);await owner.p.waitForLoadState('domcontentloaded');rows.push({id:'native-cancel',checks:{redirect:cancel.status()===302,reschedule_disabled:await owner.p.locator('button[formaction$="/reschedule/"]').isDisabled()}});
  for(const lang of ['az','ru','en']){await guest.p.goto(B+s.urls[lang].organization);const absent=await guest.p.locator('a[href="'+s.urls[lang].event+'"]').count()===0;const r=await guest.p.goto(B+s.urls[lang].event);rows.push({id:'cancelled-public',lang,checks:{not_upcoming:absent,truthful_detail:r.status()===200,detail_retained:await guest.p.locator('h1').count()===1}})}
 }catch(e){errors.push(String(e))}finally{for(const c of contexts)await c.close()}
 return{rows,errors,pageerrors,badResponses};
}
