async original=>{
 const B='http://localhost:8821',D='C:/kidsmap/docs/qa/module08-2026-10-10-r1/screenshots/',F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa08_owner",
      "email": "owner08@example.invalid"
    },
    "outsider": {
      "id": 2,
      "username": "qa08_outsider",
      "email": "outsider08@example.invalid"
    },
    "volunteer": {
      "id": 3,
      "username": "qa08_volunteer",
      "email": "volunteer08@example.invalid"
    },
    "volunteer_b": {
      "id": 4,
      "username": "qa08_volunteer_b",
      "email": "volunteer_b08@example.invalid"
    },
    "moderator": {
      "id": 5,
      "username": "qa08_moderator",
      "email": "moderator08@example.invalid"
    },
    "reviewer": {
      "id": 6,
      "username": "qa08_reviewer",
      "email": "reviewer08@example.invalid"
    },
    "reviewer_b": {
      "id": 7,
      "username": "qa08_reviewer_b",
      "email": "reviewer_b08@example.invalid"
    },
    "staff": {
      "id": 8,
      "username": "qa08_staff",
      "email": "staff08@example.invalid"
    },
    "admin": {
      "id": 9,
      "username": "qa08_admin",
      "email": "admin08@example.invalid"
    }
  },
  "places": {
    "live": 1,
    "batch_ready": 2,
    "volunteer": 3,
    "foreign": 4,
    "revoke": 5,
    "delete": 6,
    "batch_bad": 7
  },
  "organizations": {
    "flow": 1,
    "reject": 2,
    "conflict": 3,
    "filler3": 4,
    "filler4": 5,
    "filler5": 6,
    "filler6": 7,
    "filler7": 8,
    "filler8": 9,
    "filler9": 10,
    "filler10": 11,
    "filler11": 12,
    "filler12": 13,
    "filler13": 14,
    "filler14": 15,
    "filler15": 16,
    "filler16": 17,
    "filler17": 18,
    "filler18": 19,
    "filler19": 20,
    "filler20": 21,
    "filler21": 22,
    "filler22": 23,
    "filler23": 24,
    "filler24": 25,
    "filler25": 26,
    "filler26": 27,
    "filler27": 28,
    "filler28": 29,
    "filler29": 30,
    "filler30": 31,
    "filler31": 32
  },
  "revisions": {
    "live": 1,
    "revoke": 2,
    "flow": 3,
    "reject": 4,
    "conflict": 5,
    "filler3": 6,
    "filler4": 7,
    "filler5": 8,
    "filler6": 9,
    "filler7": 10,
    "filler8": 11,
    "filler9": 12,
    "filler10": 13,
    "filler11": 14,
    "filler12": 15,
    "filler13": 16,
    "filler14": 17,
    "filler15": 18,
    "filler16": 19,
    "filler17": 20,
    "filler18": 21,
    "filler19": 22,
    "filler20": 23,
    "filler21": 24,
    "filler22": 25,
    "filler23": 26,
    "filler24": 27,
    "filler25": 28,
    "filler26": 29,
    "filler27": 30,
    "filler28": 31,
    "filler29": 32,
    "filler30": 33,
    "filler31": 34
  },
  "event": 1,
  "specialist": 1,
  "private_document": 1,
  "synthetic_only": true
},rows=[],contexts=[];
 const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',lang:'ru',width:390,...x});
 const setup=async(role,width=390)=>{const c=await original.context().browser().newContext({viewport:{width,height:950}});contexts.push(c);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(10000);await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors[role].username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);return p;};
 const capture=async(p,name)=>{await p.screenshot({path:D+name+'.png',fullPage:true,animations:'disabled'});return name+'.png';};
 const state=async p=>(await p.request.get(B+'/qa/state/')).json();
 const clickSave=async(p,value)=>{await p.locator('[name=action][value='+value+']').click();await p.waitForLoadState('domcontentloaded');await p.waitForTimeout(120);};
 let v,a;
 try{
  v=await setup('volunteer');a=await setup('admin',1440);const url=B+'/ru/admin/volunteer/'+F.places.volunteer+'/edit/';await v.goto(url);const before=await state(a);
  add('volunteer-no-protected-controls',await v.locator('[name=owner],[name=status],[name=is_active],[name=created_by]').count()===0,{role:'volunteer'});
  await v.locator('[data-editor-expand]').click();await v.locator('[name=name_az]').fill('Uydurma QA08 actual volunteer photo');await v.locator('[name=photo]').setInputFiles('C:/kidsmap/.tmp/module08-20261010-r1/assets/candidate.png');await clickSave(v,'draft');let s=await state(a);let rev=s.revisions.find(r=>r.place_id===F.places.volunteer);add('volunteer-native-photo-draft',rev?.status==='draft'&&s.places.find(p=>p.id===F.places.volunteer).photo===before.places.find(p=>p.id===F.places.volunteer).photo,{role:'volunteer',state:rev});
  await v.reload();add('volunteer-draft-reload',(await v.locator('[name=name_az]').inputValue())==='Uydurma QA08 actual volunteer photo',{role:'volunteer',screenshot:await capture(v,'volunteer-draft-reloaded')});
  const tab=await v.context().newPage();tab.setDefaultTimeout(10000);await tab.goto(url);await tab.locator('[data-editor-expand]').click();await v.locator('[data-editor-expand]').click();await v.locator('[name=description_az]').fill('Uydurma təzə təsvir. '.repeat(30));await clickSave(v,'draft');s=await state(a);
  await tab.locator('[name=name_az]').fill('SYNTHETIC stale unsaved input');await clickSave(tab,'draft');add('two-volunteer-tabs-stale-no-overwrite',JSON.stringify(await state(a))===JSON.stringify(s),{role:'volunteer',screenshot:await capture(tab,'volunteer-two-tabs-error')});add('stale-volunteer-input-preserved',(await tab.locator('[name=name_az]').inputValue())==='SYNTHETIC stale unsaved input',{role:'volunteer'});await tab.close();
  await v.reload();await clickSave(v,'submit');s=await state(a);rev=s.revisions.find(r=>r.place_id===F.places.volunteer);add('volunteer-native-submitted',rev?.status==='pending'&&s.places.find(p=>p.id===F.places.volunteer).name_az===before.places.find(p=>p.id===F.places.volunteer).name_az,{role:'volunteer',state:rev});
  await a.goto(B+'/ru/admin/volunteer/review/'+F.places.volunteer+'/');add('superadmin-legacy-stored-photo-preview',await a.locator('.km-volunteer img').count()>=2,{role:'admin',width:1440,screenshot:await capture(a,'volunteer-actual-photo-review')});
  await a.locator('[name=note]').fill('SYNTHETIC photos and requirements reviewed');await clickSave(a,'approve');s=await state(a);rev=s.revisions.find(r=>r.place_id===F.places.volunteer);const live=s.places.find(p=>p.id===F.places.volunteer);add('volunteer-photo-live-after-approval',rev.status==='approved'&&live.name_az==='Uydurma QA08 actual volunteer photo'&&live.photo!==before.places.find(p=>p.id===live.id).photo,{role:'admin',width:1440,after:live});
  const pub=await v.context().browser().newContext();contexts.push(pub);const pp=await pub.newPage();await pub.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const r=await pp.goto(B+'/place/'+live.id+'/');await pp.reload();add('volunteer-public-photo-reload',r.status()===200&&(await pp.locator('img').evaluateAll(es=>es.some(e=>e.getAttribute('src')?.includes('candidate')&&e.naturalWidth>0))),{role:'anonymous',width:1280,url:pp.url(),screenshot:await capture(pp,'volunteer-public-photo-reload')});
 }catch(e){rows.push({id:'volunteer-flow-harness',status:'NOT RUN',error:String(e),url:v?.url()});if(v)await capture(v,'volunteer-flow-harness-error');}
 try{
  a=a||await setup('admin',1440);await a.goto(B+'/ru/admin/catalog/place/');const old=await state(a);await a.locator('[name=_selected_action][value="'+F.places.batch_ready+'"]').check();await a.locator('[name=_selected_action][value="'+F.places.batch_bad+'"]').check();await capture(a,'batch-selected-preview');const posts=[];a.on('request',r=>{if(r.method()==='POST')posts.push(r.url())});await a.locator('[data-bulk-submit=mark_published]').click();await a.waitForLoadState('domcontentloaded');await a.waitForTimeout(150);const s=await state(a);add('batch-partial-quality-result',s.places.find(p=>p.id===F.places.batch_ready).status==='published'&&s.places.find(p=>p.id===F.places.batch_bad).status==='draft',{role:'admin',width:1440,posts,screenshot:await capture(a,'batch-partial-result')});add('batch-result-counts',/1/.test(await a.locator('body').innerText()),{role:'admin',width:1440,notice:(await a.locator('.messagelist,.alert').allTextContents()).join(' ')});
  for(const kind of ['event','specialist']){
   await a.goto(B+'/ru/admin/catalog/'+kind+'/');await a.locator('[name=_selected_action]').first().check();await capture(a,kind+'-bulk-selected');await a.locator('[data-bulk-submit=mark_rejected]').click();await a.waitForLoadState('domcontentloaded');await a.waitForTimeout(120);let s=await state(a);const table=kind==='event'?'events':'specialists';add(kind+'-native-rejected-with-default-reason',s[table][0].status==='rejected'&&Boolean(s[table][0].rejection_reason),{role:'admin',width:1440,state:s[table][0],screenshot:await capture(a,kind+'-rejected')});
   await a.locator('[name=_selected_action]').first().check();await a.locator('[data-bulk-submit=mark_pending]').click();await a.waitForLoadState('domcontentloaded');await a.waitForTimeout(120);s=await state(a);add(kind+'-native-resubmit-clears-reason',s[table][0].status==='pending'&&s[table][0].rejection_reason==='',{role:'admin',width:1440});
  }
 }catch(e){rows.push({id:'batch-flow-harness',status:'NOT RUN',error:String(e),url:a?.url()});if(a)await capture(a,'batch-flow-harness-error');}
 for(const c of contexts)await c.close();return{rows};
}
