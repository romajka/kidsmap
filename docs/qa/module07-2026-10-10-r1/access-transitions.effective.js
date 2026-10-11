async original=>{
 const B='http://localhost:8820',D='C:/kidsmap/docs/qa/module07-2026-10-10-r1/screenshots/',F={
  "actors": {
    "author": {
      "id": 1,
      "username": "qa07_author",
      "email": "author07@example.invalid"
    },
    "person": {
      "id": 2,
      "username": "qa07_person",
      "email": "person07@example.invalid"
    },
    "owner": {
      "id": 3,
      "username": "qa07_owner",
      "email": "owner07@example.invalid"
    },
    "network": {
      "id": 4,
      "username": "qa07_network",
      "email": "network07@example.invalid"
    },
    "employee": {
      "id": 5,
      "username": "qa07_employee",
      "email": "employee07@example.invalid"
    },
    "outsider": {
      "id": 6,
      "username": "qa07_outsider",
      "email": "outsider07@example.invalid"
    },
    "invitee": {
      "id": 7,
      "username": "qa07_invitee",
      "email": "invitee07@example.invalid"
    },
    "rejectee": {
      "id": 8,
      "username": "qa07_rejectee",
      "email": "rejectee07@example.invalid"
    },
    "cancelled": {
      "id": 9,
      "username": "qa07_cancelled",
      "email": "cancelled07@example.invalid"
    },
    "volunteer": {
      "id": 10,
      "username": "qa07_volunteer",
      "email": "volunteer07@example.invalid"
    },
    "volunteer_b": {
      "id": 11,
      "username": "qa07_volunteer_b",
      "email": "volunteer_b07@example.invalid"
    },
    "moderator": {
      "id": 12,
      "username": "qa07_moderator",
      "email": "moderator07@example.invalid"
    },
    "reviewer": {
      "id": 13,
      "username": "qa07_reviewer",
      "email": "reviewer07@example.invalid"
    },
    "staff": {
      "id": 14,
      "username": "qa07_staff",
      "email": "staff07@example.invalid"
    },
    "admin": {
      "id": 15,
      "username": "qa07_admin",
      "email": "admin07@example.invalid"
    },
    "delete_cancel": {
      "id": 16,
      "username": "qa07_delete_cancel",
      "email": "delete_cancel07@example.invalid"
    },
    "delete_final": {
      "id": 17,
      "username": "qa07_delete_final",
      "email": "delete_final07@example.invalid"
    },
    "expired": {
      "id": 18,
      "username": "qa07_expired",
      "email": "expired07@example.invalid"
    }
  },
  "places": {
    "owner": 1,
    "other": 2,
    "author": 3,
    "volunteer": 4,
    "volunteer_b": 5,
    "delete_cancel": 6,
    "delete_final": 7,
    "branch": 8
  },
  "organization": 1,
  "membership": 1,
  "organization_grant": 1,
  "specialist": 1,
  "other_specialist": 2,
  "documents": {
    "identity": {
      "id": 1,
      "path": "specialist-documents/497e02adf65e4ad9ae1e83cc6b6b2630.bin",
      "public_eligibility": false
    },
    "private_certificate": {
      "id": 2,
      "path": "specialist-documents/3cf048a6c015432683356bd984dc5020.bin",
      "public_eligibility": false
    },
    "public_certificate": {
      "id": 3,
      "path": "specialist-documents/b532be2893d24ca0b3a1fd1e91436869.bin",
      "public_eligibility": true
    },
    "no_consent": {
      "id": 4,
      "path": "specialist-documents/45ce00ef684c4776ab7b7ecc1ecb4752.bin",
      "public_eligibility": false
    },
    "pending_certificate": {
      "id": 5,
      "path": "specialist-documents/411a78b5637940ea86a4c3ff443e858a.bin",
      "public_eligibility": false
    },
    "other_identity": {
      "id": 6,
      "path": "specialist-documents/1b17a3ec626f4db7aa6c1908aeb872d4.bin",
      "public_eligibility": false
    }
  },
  "synthetic_only": true
},rows=[],contexts=[];
 const add=(id,ok,role,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang:'ru',width:390,...x}),state=async p=>(await(await p.request.get(B+'/qa/state/')).json());
 const actor=async(role)=>{const c=await original.context().browser().newContext({viewport:{width:390,height:950}});contexts.push(c);const p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(13000);await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/')),p.locator('.auth-form button[type=submit]:visible').click()]);return p;};
 const post=async(p,path,data)=>p.request.post(B+path,{data,headers:{'X-CSRFToken':(await p.context().cookies()).find(x=>x.name==='module07_r1_csrf')?.value},maxRedirects:0});
 const shot=async(p,n)=>{await p.screenshot({path:D+n+'.png',fullPage:true});return n+'.png';};
 try{
  const owner=await actor('owner'),employee=await actor('employee'),network=await actor('network'),outsider=await actor('outsider');
  for(const [kind,place,grantId] of [['place',F.places.owner,F.membership],['organization',F.places.branch,F.organization_grant]]){
   await employee.goto(B+'/ru/account/places/'+place+'/edit/');add('pre-removal-'+kind+'-editor-open',await employee.locator('[name=name_az]').count()===1,'employee');const before=await state(owner);
   if(kind==='place'){await owner.goto(B+'/ru/account/places/team/');const form=owner.locator('form[action$="/members/'+grantId+'/remove/"]');await Promise.all([owner.waitForNavigation({waitUntil:'domcontentloaded'}),form.locator('button').click()]);}
   else{const grant=before.org_grants.find(x=>x.id===grantId),response=await post(network,'/ru/account/business/team/organization/'+F.organization+'/grant/',{grant_id:grant.id,expected_version:grant.version,active:false});add('organization-existing-employee-revoke-HTTP',response.status()===200,'network',{http:response.status(),width:'N/A HTTP'});}
   await employee.locator('[name=name_az]').fill('Uydurma withdrawn '+kind+' access');const [response]=await Promise.all([employee.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST'),employee.locator('button[type=submit][value=save_draft]').click()]);await employee.waitForTimeout(400);const after=await state(owner);add('removed-'+kind+'-stale-native-save-denied-input-preserved',response.status()===403&&JSON.stringify(before.places)===JSON.stringify(after.places)&&(await employee.locator('[name=name_az]').inputValue())==='Uydurma withdrawn '+kind+' access','employee',{http:response.status(),screenshot:await shot(employee,kind+'-stale-save-denied-ru-390')});const denied=await employee.request.get(B+'/ru/account/places/'+place+'/edit/',{maxRedirects:0});add('removed-'+kind+'-fresh-direct-URL-denied',[302,403,404].includes(denied.status()),'employee',{http:denied.status(),width:'N/A HTTP'});
  }
  const before=await state(owner),place=before.places.find(x=>x.id===F.places.owner);const foreign=await post(employee,'/ru/api/ownership/transfer/place/'+place.id+'/',{new_owner_id:F.actors.employee.id,expected_ownership_version:place.ownership_version});add('foreign-transfer-denied-no-side-effects',foreign.status()===403&&JSON.stringify(before)===JSON.stringify(await state(owner)),'employee',{width:'N/A HTTP',http:foreign.status()});
  const transfer=await post(owner,'/ru/api/ownership/transfer/place/'+place.id+'/',{new_owner_id:F.actors.outsider.id,expected_ownership_version:place.ownership_version});let s=await state(owner);add('owner-transfer-implemented-HTTP',transfer.status()===200&&s.places.find(x=>x.id===place.id).owner_id===F.actors.outsider.id,'owner',{width:'N/A HTTP',http:transfer.status(),classification:'Actual CSRF-protected endpoint; no native transfer UI exists'});const denied=await owner.request.get(B+'/ru/account/places/'+place.id+'/edit/',{maxRedirects:0});add('former-owner-direct-edit-denied',[302,403,404].includes(denied.status()),'former-owner',{width:'N/A HTTP',http:denied.status()});const newAccess=await outsider.request.get(B+'/ru/account/places/'+place.id+'/edit/',{maxRedirects:0});add('new-owner-direct-edit-allowed',newAccess.status()===200,'new-owner',{width:'N/A HTTP',http:newAccess.status()});
  const staleBefore=await state(owner),stale=await post(outsider,'/ru/api/ownership/transfer/place/'+place.id+'/',{new_owner_id:F.actors.owner.id,expected_ownership_version:place.ownership_version});add('stale-transfer-version-no-side-effects',stale.status()===400&&JSON.stringify(staleBefore)===JSON.stringify(await state(owner)),'new-owner',{width:'N/A HTTP',http:stale.status()});
  const returnTransfer=await post(outsider,'/ru/api/ownership/transfer/place/'+place.id+'/',{new_owner_id:F.actors.owner.id,expected_ownership_version:s.places.find(x=>x.id===place.id).ownership_version});add('return-owner-implemented-HTTP',returnTransfer.status()===200,'new-owner',{width:'N/A HTTP',http:returnTransfer.status()});
 }catch(e){rows.push({id:'access-transitions-harness-error',status:'NOT RUN',role:'QA',lang:'ru',width:390,error:String(e)});}finally{for(const c of contexts)await c.close();}return{rows};
}
