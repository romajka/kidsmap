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
  const width=390,pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width,height:950}}),p=await c.newPage(),guest=await original.context().browser().newContext({viewport:{width,height:950}}),g=await guest.newPage();for(const ctx of [c,guest])await ctx.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(13000);const add=(id,ok,role,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width,...x});
  try{
   await p.goto(B+pre+'auth/login/');await p.locator('[name=username]').fill(F.actors.person.email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>u.pathname.includes('/account/')),p.locator('.auth-form button[type=submit]:visible').click()]);await p.goto(B+pre+'account/specialists/'+F.specialist+'/certificates/');let form=p.locator('form:has([name=document_id][value="'+F.documents.public_certificate.id+'"])');await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),form.locator('button[type=submit]').click()]);await p.reload();const doc=(await(await p.request.get(B+'/qa/state/')).json()).documents.find(x=>x.id===F.documents.public_certificate.id);const denied=await g.request.get(B+pre+'specialists/documents/'+doc.id+'/download/',{maxRedirects:0});add('person-native-revoke-consent-reload',!doc.is_published&&denied.status()===404,'person',{http:denied.status(),screenshot:'certificate-private-'+lang+'-390.png'});await p.screenshot({path:D+'certificate-private-'+lang+'-390.png',fullPage:true});
   form=p.locator('form:has([name=document_id][value="'+doc.id+'"])');await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),form.locator('button[type=submit]').click()]);await p.reload();const now=(await(await p.request.get(B+'/qa/state/')).json()).documents.find(x=>x.id===doc.id),allowed=await g.request.get(B+pre+'specialists/documents/'+doc.id+'/download/');add('person-native-public-consent-reload',now.is_published&&now.opted_in_by_id===F.actors.person.id&&allowed.status()===200,'person',{http:allowed.status(),screenshot:'certificate-public-'+lang+'-390.png'});await p.screenshot({path:D+'certificate-public-'+lang+'-390.png',fullPage:true});
   await g.goto(B+pre+'specialists/');const link=g.locator('.km-card-name a').filter({hasText:'Fictional QA07 Person'});const href=await link.getAttribute('href');await g.goto(B+href);const html=await g.content(),downloads=await g.locator('a[href*="/documents/"]').evaluateAll(es=>es.map(x=>x.getAttribute('href')));add('public-HTML-only-consented-certificate',downloads.length===1&&downloads[0].includes('/'+doc.id+'/download/')&&!html.includes('specialist-documents/')&&!html.includes('SYNTHETIC QA07 identity')&&!html.includes('SYNTHETIC QA07 private_certificate'),'anonymous',{url:href,downloads,screenshot:'specialist-public-privacy-'+lang+'-390.png'});await g.screenshot({path:D+'specialist-public-privacy-'+lang+'-390.png',fullPage:true});
  }catch(e){rows.push({id:'privacy-flow-harness-error',status:'NOT RUN',role:'QA',lang,width,error:String(e)});}await c.close();await guest.close();
 }return{rows};
}
