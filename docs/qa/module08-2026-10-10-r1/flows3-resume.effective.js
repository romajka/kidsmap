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
 const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'admin',lang:'ru',width:1440,...x});
 const setup=async(role,width=1440)=>{const c=await original.context().browser().newContext({viewport:{width,height:950}});contexts.push(c);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(9000);await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors[role].username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);return p;};
 const shot=async(p,name)=>{await p.screenshot({path:D+name+'.png',fullPage:false,animations:'disabled',timeout:15000});return name+'.png';};
 const state=async p=>(await p.request.get(B+'/qa/state/')).json();
 const save=async(p,selector)=>{await p.locator(selector).filter({visible:true}).first().click();await p.waitForLoadState('domcontentloaded');await p.waitForTimeout(200);};
 const a=await setup('admin'),v=await setup('volunteer',390);
 for(const lang of ['ru','az','en']){const s=await state(a),org=s.organizations.find(o=>o.name_az==='Uydurma QA08 native new '+lang),rev=s.revisions.find(r=>r.organization_id===org?.id);add('new-org-final-state-readback',org?.status==='draft'&&rev?.status==='declined'&&rev?.review_note==='SYNTHETIC QA08 final decline '+lang,{lang,organization:org?.id,revision:rev?.id,note:'Fresh readback only; original flows3 lost its observation array after screenshot timeout. Existing PNGs retained.'});}
 for(const kind of ['event','specialist'])try{
  await a.goto(B+'/ru/admin/catalog/'+kind+'/1/change/');
  if(kind==='event')await a.locator('[data-km-admin-step-link][href="#media"]').click();
  else {const section=await a.locator('[name=status]').evaluate(e=>e.closest('section')?.id);if(section)await a.locator('.km-specialist-nav a[href="#'+section+'"]').click();}
  await a.locator('[name=status]').selectOption('rejected');
  const reason=a.locator('[name=rejection_reason]');if(!await reason.isVisible()){
   const details=await reason.evaluate(e=>({detail:e.closest('details')?.className,section:e.closest('section')?.id}));
   if(details.detail)await a.locator('details').filter({has:reason}).locator('summary').click();
   else if(details.section)await a.locator('[href="#'+details.section+'"]').filter({visible:true}).first().click();
  }
  await reason.fill('SYNTHETIC QA08 custom moderation refusal');await save(a,'[name=_save], [name=_continue]');let s=await state(a),table=kind==='event'?'events':'specialists';add(kind+'-native-reject-custom-reason',s[table][0].status==='rejected'&&s[table][0].rejection_reason==='SYNTHETIC QA08 custom moderation refusal',{screenshot:await shot(a,kind+'-custom-rejected-resume'),url:a.url(),ui:(await a.locator('body').innerText()).slice(-1700)});
  await a.goto(B+'/ru/admin/catalog/'+kind+'/');await a.locator('[name=_selected_action]').first().check();await save(a,'[data-bulk-submit=mark_pending]');s=await state(a);add(kind+'-native-resubmit',s[table][0].status==='pending'&&s[table][0].rejection_reason==='',{screenshot:await shot(a,kind+'-resubmitted-resume')});
  await a.locator('[name=_selected_action]').first().check();await save(a,'[data-bulk-submit=mark_published]');s=await state(a);add(kind+'-native-approve',s[table][0].status==='published',{state:s[table][0],screenshot:await shot(a,kind+'-approved-resume')});
 }catch(e){rows.push({id:kind+'-moderation-harness',status:'NOT RUN',error:String(e),url:a.url(),ui:(await a.locator('body').innerText()).slice(-1700)});try{await shot(a,kind+'-moderation-resume-error');}catch{}}
 try{
  const vb=await setup('volunteer_b',390);const url=B+'/ru/admin/volunteer/'+F.places.foreign+'/edit/';await vb.goto(url);await vb.locator('[data-editor-expand]').click();await vb.locator('[name=name_az]').fill('SYNTHETIC revoked stale unsaved');
  await a.goto(B+'/ru/admin/catalog/staffaccessuser/'+F.actors.volunteer_b.id+'/change/');await a.locator('#tab-staff-role').click();await a.locator('#id_admin_role').selectOption('moderator');await save(a,'form[action$="/role/"] button[type=submit]');const before=await state(a);await save(vb,'[name=action][value=draft]');add('role-revocation-open-editor-denied',(await vb.locator('body').innerText()).includes('403')&&JSON.stringify(before)===JSON.stringify(await state(a)),{role:'former-volunteer',width:390,screenshot:await shot(vb,'volunteer-role-revoked-403'),url:vb.url()});const r=await vb.request.get(url,{maxRedirects:0});add('role-revocation-fresh-GET',r.status()===403,{role:'former-volunteer',http:r.status()});
 }catch(e){rows.push({id:'role-revocation-harness',status:'NOT RUN',error:String(e),url:a.url(),ui:(await a.locator('body').innerText()).slice(-1500)});try{await shot(a,'role-revocation-resume-error');}catch{}}
 try{
  await v.goto(B+'/ru/admin/volunteer/');const form=v.locator('form[action$="/'+F.places.delete+'/delete/"]');const before=await state(a);v.once('dialog',d=>d.dismiss());await form.locator('button').click();add('draft-delete-confirm-cancel',JSON.stringify(before)===JSON.stringify(await state(a)),{role:'volunteer',width:390,screenshot:await shot(v,'draft-delete-cancel')});let message='';v.once('dialog',async d=>{message=d.message();await d.accept();});await save(v,'form[action$="/'+F.places.delete+'/delete/"] button');const s=await state(a);add('draft-delete-confirm-accepted',Boolean(s.places.find(p=>p.id===F.places.delete).deleted_at)&&!s.places.find(p=>p.id===F.places.delete).is_active&&Boolean(message),{role:'volunteer',width:390,dialog:message,screenshot:await shot(v,'draft-delete-success')});
  await v.reload();add('draft-delete-reload-absent',await v.locator('form[action$="/'+F.places.delete+'/delete/"]').count()===0,{role:'volunteer',width:390});
 }catch(e){rows.push({id:'draft-delete-harness',status:'NOT RUN',error:String(e),url:v.url()});try{await shot(v,'draft-delete-resume-error');}catch{}}
 const s=await state(a);await a.request.get(B+'/qa/version/');for(const c of contexts)await c.close();return{rows,final_state:s};
}
