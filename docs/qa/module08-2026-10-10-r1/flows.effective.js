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
 const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',lang:'ru',width:1440,...x});
 const setup=async role=>{const c=await original.context().browser().newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(10000);await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors[role].username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);return p;};
 const capture=async(p,name)=>{await p.screenshot({path:D+name+'.png',fullPage:true,animations:'disabled'});return name+'.png';};
 const state=async p=>(await p.request.get(B+'/qa/state/')).json();
 const decision=async(p,id,action,reason)=>{await p.goto(B+'/ru/admin/volunteer/moderation/content/'+id+'/');await p.locator('[name=reason]').fill(reason);await Promise.all([p.waitForLoadState('domcontentloaded'),p.locator('[name=action][value='+action+']').click()]);await p.waitForTimeout(150);};
 const rowRev=(s,id)=>s.revisions.find(r=>r.id===id);
 let a,v,b;
 try{
  a=await setup('reviewer');v=await setup('volunteer');b=await setup('reviewer_b');
  // Real two browser contexts hold the same pending version.
  const id=F.revisions.flow,url=B+'/ru/admin/volunteer/moderation/content/'+id+'/';
  await a.goto(url);await b.goto(url);const initial=await state(a);await capture(a,'flow-current-candidate-before');
  await a.locator('[name=reason]').fill('SYNTHETIC QA08 needs a clearer description');await Promise.all([a.waitForLoadState('domcontentloaded'),a.locator('[name=action][value=return]').click()]);await a.waitForTimeout(150);
  let s=await state(a);add('return-reason-preserves-live',rowRev(s,id).status==='rejected'&&s.organizations.find(o=>o.id===F.organizations.flow).name_az===initial.organizations.find(o=>o.id===F.organizations.flow).name_az,{role:'reviewer',state:rowRev(s,id)});
  await b.locator('[name=reason]').fill('SYNTHETIC stale second reviewer');const stale=await Promise.all([b.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/moderation/content/')),b.locator('[name=action][value=approve]').click()]);
  add('two-reviewers-stale-409',stale[0].status()===409&&JSON.stringify(await state(a))===JSON.stringify(s),{role:'reviewer_b',http:stale[0].status(),screenshot:await capture(b,'flow-stale-409')});
  await v.goto(B+'/ru/admin/volunteer/proposal/organization/'+F.organizations.flow+'/');add('returned-candidate-native-reload',(await v.locator('[name=name_az]').inputValue())==='Uydurma QA08 candidate flow',{role:'volunteer'});
  await v.locator('[name=name_az]').fill('Uydurma QA08 improved flow');await v.locator('[name=description_az]').fill('SYNTHETIC QA08 improved description');await Promise.all([v.waitForLoadState('domcontentloaded'),v.locator('[name=action][value=submit]').click()]);await v.waitForTimeout(150);
  s=await state(a);add('native-resubmit-pending',rowRev(s,id).status==='pending'&&s.organizations.find(o=>o.id===F.organizations.flow).name_az!=='Uydurma QA08 improved flow',{role:'volunteer',state:rowRev(s,id)});
  await decision(a,id,'approve','SYNTHETIC reviewed and accepted');s=await state(a);add('approve-live-candidate',rowRev(s,id).status==='approved'&&s.organizations.find(o=>o.id===F.organizations.flow).name_az==='Uydurma QA08 improved flow',{role:'reviewer',state:rowRev(s,id)});
  await a.goto(url);add('processed-actions-hidden',await a.locator('[name=action]').count()===0,{role:'reviewer',screenshot:await capture(a,'flow-approved-no-actions')});
  await v.goto(B+'/ru/admin/volunteer/proposal/organization/'+F.organizations.flow+'/');await v.locator('[name=description_az]').fill('SYNTHETIC QA08 post-publication candidate');await Promise.all([v.waitForLoadState('domcontentloaded'),v.locator('[name=action][value=submit]').click()]);await v.waitForTimeout(150);s=await state(a);add('published-edit-waits-moderation',s.organizations.find(o=>o.id===F.organizations.flow).description_az==='SYNTHETIC QA08 improved description'&&rowRev(s,id).payload.description_az==='SYNTHETIC QA08 post-publication candidate',{role:'volunteer'});
  await decision(a,id,'reject','SYNTHETIC final refusal with reason');s=await state(a);add('final-reject-live-preserved',rowRev(s,id).status==='declined'&&rowRev(s,id).review_note==='SYNTHETIC final refusal with reason'&&s.organizations.find(o=>o.id===F.organizations.flow).description_az==='SYNTHETIC QA08 improved description',{role:'reviewer'});
  await v.goto(B+'/ru/admin/volunteer/proposal/organization/'+F.organizations.reject+'/');await v.locator('[name=description_az]').fill('SYNTHETIC native withdrawn to draft');await Promise.all([v.waitForLoadState('domcontentloaded'),v.locator('[name=action][value=draft]').click()]);await v.waitForTimeout(150);s=await state(a);add('native-pending-to-draft',rowRev(s,F.revisions.reject).status==='draft',{role:'volunteer',state:rowRev(s,F.revisions.reject)});
  await v.reload();add('draft-reload-preserved',(await v.locator('[name=description_az]').inputValue())==='SYNTHETIC native withdrawn to draft',{role:'volunteer',screenshot:await capture(v,'flow-draft-reload')});
 }catch(e){rows.push({id:'organization-flow-harness',status:'NOT RUN',error:String(e),url:a?.url()});if(a)await capture(a,'flow-harness-error');}
 // Independent Place decision includes actual stored images and public readback.
 try{
  a=a||await setup('reviewer');const id=F.revisions.live;let s=await state(a);const old=s.places.find(p=>p.id===F.places.live);await a.goto(B+'/ru/admin/volunteer/moderation/content/'+id+'/');
  add('hub-photo-visual-preview',await a.locator('main img[src*="qa08-candidate"]').count()>0,{role:'reviewer',screenshot:await capture(a,'hub-photo-paths-only')});
  await a.goto(B+'/ru/admin/volunteer/review/'+F.places.live+'/');add('legacy-photo-visual-preview',await a.locator('main img[src*="qa08-candidate"]').count()>0,{role:'reviewer',screenshot:await capture(a,'legacy-photo-preview')});
  await decision(a,id,'approve','SYNTHETIC photo and name checked');s=await state(a);const live=s.places.find(p=>p.id===F.places.live);add('place-photo-gallery-atomic-approved',rowRev(s,id).status==='approved'&&live.photo==='places/qa08-candidate.png'&&live.name_az==='Uydurma QA08 candidate live'&&s.photos.some(p=>p.place_id===live.id&&p.image==='places/qa08-gallery.png'),{role:'reviewer',before:old,after:live});
  const pub=await a.goto(B+'/place/'+live.id+'/');await a.waitForTimeout(150);add('public-approved-photo-reload',pub.status()===200&&(await a.locator('img[src*="qa08-candidate"]').count())>0,{role:'anonymous-read',url:a.url(),screenshot:await capture(a,'public-approved-photo')});await a.reload();add('public-approved-reload',await a.locator('img[src*="qa08-candidate"]').count()>0,{role:'anonymous-read'});
 }catch(e){rows.push({id:'place-decision-harness',status:'NOT RUN',error:String(e),url:a?.url()});if(a)await capture(a,'place-flow-harness-error');}
 for(const c of contexts)await c.close();return{rows};
}
