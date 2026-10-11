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
},rows=[],diag=[];
 for(const lang of ['ru','az','en'])for(const role of ['anonymous','author','person','owner','network','employee','outsider','volunteer','moderator','reviewer','staff','admin']){
  const prefix=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext(),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(9000);
  const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width:'N/A HTTP',...x});
  try{
   await p.goto(B+prefix+'auth/login/');if(role!=='anonymous'){await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>u.pathname.includes('/account/')),p.locator('.auth-form button[type=submit]:visible').click()]);}
   const before=await (await p.request.get(B+'/qa/state/')).json();
   for(const [key,d] of Object.entries(F.documents)){
    const url=prefix+'specialists/documents/'+d.id+'/download/',r=await p.request.get(B+url),allowed=key==='public_certificate'||role==='reviewer'||role==='admin'||(role==='person'&&key!=='other_identity')||(role==='outsider'&&key==='other_identity');
    add('document-'+key,r.status()===(allowed?200:404),{url,http:r.status(),expected:allowed?200:404,headers:allowed?{cache:r.headers()['cache-control'],disposition:r.headers()['content-disposition'],nosniff:r.headers()['x-content-type-options']}:undefined});
    if(allowed)add('document-private-response-headers',r.headers()['cache-control']==='private, no-store'&&r.headers()['x-content-type-options']==='nosniff'&&r.headers()['content-disposition']?.includes('attachment'),{entity:key,url});
    const media=await p.request.get(B+'/media/'+d.path);add('direct-private-media-denied',media.status()===404,{entity:key,http:media.status(),url:'/media/'+d.path});
   }
   const legacy=await p.request.get(B+'/media/protected_docs/specialists/qa07-legacy.txt');add('legacy-media-denied',legacy.status()===404,{http:legacy.status()});
   for(const label of ['owner','other','author','volunteer','volunteer_b','branch']){
    const pid=F.places[label],url=prefix+'account/places/'+pid+'/edit/',r=await p.request.get(B+url,{maxRedirects:0}),allowed=role==='admin'||(label==='owner'&&['owner','employee'].includes(role))||(label==='other'&&role==='outsider')||(label==='author'&&role==='author')||(label==='branch'&&['network','employee'].includes(role));
    const denied=[302,403,404].includes(r.status());add('place-edit-ACL',allowed?r.status()===200:denied,{entity:label,url,http:r.status(),expected:allowed?'200':'denied'});
   }
   for(const label of ['owner','other']){
    if(role==='admin'||(label==='owner'&&role==='owner')||(label==='other'&&role==='outsider'))continue;
    const url=prefix+'account/business/team/place/'+F.places[label]+'/invite/',csrf=(await c.cookies()).find(x=>x.name==='module07_r1_csrf')?.value;
    const r=await p.request.post(B+url,{headers:{'X-CSRFToken':csrf||'','Content-Type':'application/json'},data:{email:'ungranted07@example.invalid',role:'EDITOR',actions:['place.view','place.edit']}});add('foreign-place-team-mutation-denied',r.status()===403,{url,http:r.status()});
   }
   if(!['admin','network'].includes(role)){
    const url=prefix+'account/business/team/organization/'+F.organization+'/invite/',csrf=(await c.cookies()).find(x=>x.name==='module07_r1_csrf')?.value,r=await p.request.post(B+url,{headers:{'X-CSRFToken':csrf||'','Content-Type':'application/json'},data:{email:'ungrantedorg07@example.invalid',role:'EDITOR',scope:'all_network',place_ids:[]}});add('foreign-organization-team-denied',r.status()===403,{url,http:r.status()});
   }
   const after=await (await p.request.get(B+'/qa/state/')).json();add('denials-no-domain-side-effects',JSON.stringify(before)===JSON.stringify(after),{tracked:['users','verified','members','invitations','org_grants','org_invitations','places','documents','deletions']});
  }catch(e){rows.push({id:'acl-harness-error',status:'NOT RUN',role,lang,width:'N/A HTTP',error:String(e)});}
  await c.close();
 }
 return{rows,diagnostics:diag};
}
