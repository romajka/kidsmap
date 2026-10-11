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
},rows=[];
 for(const lang of ['ru','az','en']){
  const pre=lang==='az'?'/':'/'+lang+'/';
  for(const role of ['anonymous','author','reviewer','admin']){
   const c=await original.context().browser().newContext({viewport:{width:1440,height:950}}),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(11000);const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width:'N/A HTTP',...x});
   try{
    if(role!=='anonymous'){await p.goto(B+pre+'auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/')),p.locator('.auth-form button[type=submit]:visible').click()]);}
    for(const [key,d] of Object.entries(F.documents)){const response=await p.request.get(B+pre+'specialists/documents/'+d.id+'/download/',{maxRedirects:0}),allowed=['reviewer','admin'].includes(role);add('post-deletion-download-'+key,response.status()===(allowed?200:404),{entity:key,http:response.status(),headers:allowed?{cache:response.headers()['cache-control'],nosniff:response.headers()['x-content-type-options']}:undefined});const direct=await p.request.get(B+'/media/'+d.path);add('post-deletion-private-media-'+key,direct.status()===404,{http:direct.status()});}
    if(role==='admin'){const response=await p.goto(B+pre+'admin/catalog/place/'+F.places.owner+'/change/');add('administrator-canonical-editor-allowed',response.status()===200,{width:1440,url:p.url(),screenshot:'administrator-editor-'+lang+'-1440.png'});await p.screenshot({path:D+'administrator-editor-'+lang+'-1440.png',fullPage:true});}
    if(role==='anonymous')for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});await p.goto(B+pre+'specialists/fictional-qa07-person/');const downloads=await p.locator('a[href*="/documents/"]').count(),g=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));add('post-person-deletion-public-certificate-absent',downloads===0,{width,geometry:g,screenshot:'post-deletion-public-person-'+lang+'-'+width+'.png'});await p.screenshot({path:D+'post-deletion-public-person-'+lang+'-'+width+'.png',fullPage:true});}
   }catch(e){rows.push({id:'final-browser-harness-error',status:'NOT RUN',role,lang,width:1440,error:String(e)});}await c.close();
  }
 }return{rows};
}
