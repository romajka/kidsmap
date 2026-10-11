async original=>{
 const B='http://localhost:8820',F={
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
},rows=[];
 for(const lang of ['ru','az','en'])for(const role of ['owner','network','admin']){
  const pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext(),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(10000);const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width:'N/A HTTP',...x}),state=async()=>(await(await p.request.get(B+'/qa/state/')).json());
  try{await p.goto(B+pre+'auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('auth/login')),p.locator('.auth-form button[type=submit]:visible').click()]);const csrf=(await c.cookies()).find(x=>x.name==='module07_r1_csrf')?.value,before=await state(),post=async(path,data,token=csrf)=>p.request.post(B+pre+path,{data,headers:token?{'X-CSRFToken':token}:{},maxRedirects:0});
   if(role==='network'){
    const path='account/business/team/organization/'+F.organization+'/grant/',grant=before.org_grants.find(x=>x.id===F.organization_grant);let r=await post(path,{grant_id:grant.id,expected_version:grant.version,role:'EDITOR',actions:['ownership.transfer']});add('organization-owner-only-action-cannot-grant',r.status()===400,{http:r.status()});r=await post(path,{grant_id:grant.id,expected_version:grant.version,active:true});add('suspended-grant-needs-explicit-confirmation',r.status()===400,{http:r.status()});r=await post('account/business/team/place/'+F.places.branch+'/grant/',{grant_id:F.membership,expected_version:1,role:'EDITOR'});add('nested-grant-ID-target-mismatch-denied',r.status()===403,{http:r.status()});r=await post('account/business/team/organization/'+F.organization+'/invite/',{email:'csrf-json07@example.invalid',role:'EDITOR',scope:'all_network',place_ids:[]},null);add('team-JSON-CSRF-denied',r.status()===403,{http:r.status()});
   }
   if(role==='admin'){for(const [type,id] of [['place',F.places.owner],['organization',F.organization]]){const path='account/business/team/'+type+'/'+id+'/invite/',r=await post(path,{email:'admin-ungranted07@example.invalid',role:'EDITOR',scope:'all_network',place_ids:[]});add('administrator-no-business-owner-only-team-'+type,r.status()===403,{http:r.status()});}}
   const path='account/business/team/'+(role==='owner'?'organization/'+F.organization:'place/'+F.places.owner)+'/invite/',r=await p.request.get(B+pre+path,{maxRedirects:0});add('team-mutation-GET-denied',r.status()===405,{http:r.status()});add('contract-denials-no-side-effects',JSON.stringify(before)===JSON.stringify(await state()));
  }catch(e){rows.push({id:'api-contracts-harness-error',status:'NOT RUN',role,lang,width:'N/A HTTP',error:String(e)});}await c.close();
 }return{rows};
}
