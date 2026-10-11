async original=>{
 const B='http://localhost:8821',F={
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
},rows=[];
 const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',width:null,...x});
 for(const role of ['anonymous','owner','outsider','volunteer','volunteer_b','moderator','reviewer','staff','admin']){
  const c=await original.context().browser().newContext(),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
  if(role!=='anonymous'){await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('.auth-form button[type=submit]:visible').click()]);}
  for(const lang of ['ru','az','en']){
   const pre=lang==='az'?'/':'/'+lang+'/',before=await (await p.request.get(B+'/qa/state/')).json();
   const tests=[['hub','admin/volunteer/moderation/',role==='admin'||role==='reviewer'||role==='moderator'?200:['anonymous','owner','outsider'].includes(role)?302:403],['hub-content','admin/volunteer/moderation/content/'+F.revisions.filler4+'/',role==='admin'||role==='reviewer'?200:role==='moderator'?404:['anonymous','owner','outsider'].includes(role)?302:403],['legacy-review','admin/volunteer/review/'+F.places.live+'/',role==='admin'?200:['anonymous','owner','outsider'].includes(role)?302:403],['foreign-volunteer-object','admin/volunteer/'+F.places.foreign+'/edit/',role==='volunteer_b'?200:role==='volunteer'?404:['anonymous','owner','outsider'].includes(role)?302:403],['private-doc','specialists/documents/'+F.private_document+'/download/',role==='admin'?200:role.startsWith('volunteer')?403:404]];
   for(const [id,path,expected] of tests){const r=await p.request.get(B+pre+path,{maxRedirects:0});add(id+'-HTTP',r.status()===expected,{role,lang,method:'GET',http:r.status(),expected,path});}
   if(['volunteer','volunteer_b','moderator','reviewer','staff','admin'].includes(role)){
    await p.goto(B+pre+'admin/');const csrf=(await c.cookies()).find(x=>x.name==='module08_r1_csrf')?.value;
    if(!['admin','reviewer'].includes(role)){const r=await p.request.post(B+pre+'admin/volunteer/moderation/content/'+F.revisions.filler4+'/',{form:{csrfmiddlewaretoken:csrf||'',action:'approve',version:'1',reason:'SYNTHETIC unauthorized'},maxRedirects:0});add('unauthorized-review-POST',r.status()===403||role==='moderator'&&r.status()===404,{role,lang,http:r.status()});}
    if(role==='volunteer'){const r=await p.request.post(B+pre+'admin/volunteer/'+F.places.foreign+'/edit/',{form:{csrfmiddlewaretoken:csrf||'',action:'draft',name_az:'SYNTHETIC foreign write'},maxRedirects:0});add('foreign-id-POST',r.status()===404,{role,lang,http:r.status()});}
   }
   const after=await (await p.request.get(B+'/qa/state/')).json();add('denied-requests-state-unchanged',JSON.stringify(before)===JSON.stringify(after),{role,lang,scope:'allowlisted content/revisions/photos/counts only; GET tracking/session not compared'});
  }
  await c.close();
 }
 // Actual canonical HTTP negative contracts with valid session + native CSRF.
 const c=await original.context().browser().newContext(),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors.admin.username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);
 for(const lang of ['ru','az','en']){
  const pre=lang==='az'?'/':'/'+lang+'/',id=F.revisions.filler4,path=B+pre+'admin/volunteer/moderation/content/'+id+'/';await p.goto(path);const csrf=(await c.cookies()).find(x=>x.name==='module08_r1_csrf')?.value,before=await (await p.request.get(B+'/qa/state/')).json();
  for(const [name,form,expected]of [['missing-reason',{action:'reject',version:1,reason:''},409],['stale-version',{action:'approve',version:0,reason:'SYNTHETIC stale'},409],['invalid-action',{action:'delete',version:1,reason:'SYNTHETIC invalid'},409],['processed-item',{action:'approve',version:1,reason:'SYNTHETIC replay'},409]]){const target=name==='processed-item'?B+pre+'admin/volunteer/moderation/content/'+F.revisions.flow+'/':path;const r=await p.request.post(target,{form:{csrfmiddlewaretoken:csrf,...form},maxRedirects:0});add(name+'-HTTP',r.status()===expected,{role:'admin',lang,http:r.status()});}
  const noCSRF=await p.request.post(path,{form:{action:'approve',version:1,reason:'SYNTHETIC no csrf'},maxRedirects:0});add('CSRF-rejected',noCSRF.status()===403,{role:'admin',lang,http:noCSRF.status()});add('negative-state-unchanged',JSON.stringify(before)===JSON.stringify(await (await p.request.get(B+'/qa/state/')).json()),{role:'admin',lang});
 }
 await c.close();return{rows};
}
