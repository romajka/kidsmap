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
 const cases=[{lang:'ru',width:390,email:F.actors.person.email,password:'__LOCAL_PASSWORD__',cancel:false}];
 for(const item of cases){
  const {lang,width,email,password,cancel}=item,pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width,height:950}}),p=await c.newPage(),second=await original.context().browser().newContext({viewport:{width,height:950}}),q=await second.newPage();for(const ctx of [c,second])await ctx.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(14000);q.setDefaultTimeout(14000);const suffix=lang+'-'+width+('-person'),add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'own-deletion-fixture',lang,width,classification:'SIMULATED retention policy ADRP-TEST-01; actual UI/HTTP',...x}),shot=async(n)=>{const f=n+'-'+suffix+'.png';await p.screenshot({path:D+f,fullPage:true});return f;},state=async()=>(await(await p.request.get(B+'/qa/state/')).json()),mails=async()=>(await(await p.request.get(B+'/qa/mail/')).json()).messages.filter(x=>x.to.some(e=>e===email));
  const login=async(page)=>{await page.goto(B+pre+'auth/login/');await page.locator('[name=username]').fill(email);await page.locator('[name=password]').fill(password);await Promise.all([page.waitForURL(u=>u.pathname.includes('/account/')),page.locator('.auth-form button[type=submit]:visible').click()]);};
  try{
   await login(p);await login(q);await p.goto(B+pre+'account/notifications/');const actions=await p.locator('main form').evaluateAll(fs=>fs.map(f=>({action:f.getAttribute('action'),buttons:[...f.querySelectorAll('button')].map(b=>b.textContent.trim())})));add('recipient-inbox-no-reject-control',false,{classification:'ACTUAL missing UI controls, two synthetic invitations',actions,screenshot:await shot('recipient-pending-place-and-org')});await p.goto(B+pre+'account/deletion/');await Promise.all([p.waitForURL(u=>u.pathname.includes('/confirm/')),p.locator('form:has([name=form_action][value=request]) button').click()]);const confirmURL=p.url(),code=(await mails()).at(-1).body.match(/\b\d{6}\b/)[0],phrase=await p.locator('.account-deletion-phrase code').innerText();add('native-deletion-request',await p.locator('[name=confirmation_code]').count()>0,{screenshot:await shot('deletion-confirm-empty')});
   await p.locator('[name=confirmation_code]').fill(String((Number(code)+1)%1000000).padStart(6,'0'));await p.locator('[name=typed_confirmation]').fill(phrase);await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('.account-deletion-form button[type=submit]').click()]);await p.locator('[name=confirmation_code]').fill('');add('deletion-wrong-code-denied',p.url()===confirmURL&&await p.locator('[aria-invalid=true]').count()>0,{screenshot:await shot('deletion-code-error')});
   await p.locator('[name=confirmation_code]').fill(code);await p.locator('[name=typed_confirmation]').fill('NO');await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('.account-deletion-form button[type=submit]').click()]);await p.locator('[name=confirmation_code]').fill('');add('deletion-wrong-phrase-denied',p.url()===confirmURL&&await p.locator('[name=typed_confirmation][aria-invalid=true]').count()>0,{screenshot:await shot('deletion-phrase-error')});
   const before=await state(),u=before.users.find(x=>x.id===before.verified.find(v=>v.email===email)?.user_id);await p.locator('[name=confirmation_code]').fill(code);await p.locator('[name=typed_confirmation]').fill(phrase);await Promise.all([p.waitForURL(u=>u.pathname.includes('/status/')),p.locator('.account-deletion-form button[type=submit]').click()]);let s=await state(),deletion=s.deletions.filter(x=>x.user_id===u.id).at(-1);add('native-confirm-scheduled-account-inactive',deletion?.status==='SCHEDULED'&&!s.users.find(x=>x.id===u.id).is_active,{screenshot:await shot('deletion-scheduled')});add('deletion-invalidates-second-session',(await q.request.get(B+pre+'account/settings/',{maxRedirects:0})).status()===302,{width:'N/A HTTP'});add('scheduled-owner-data-retained-until-processing',JSON.stringify(before.places.filter(x=>x.owner_id===u.id))===JSON.stringify(s.places.filter(x=>x.owner_id===u.id)),{width:'N/A HTTP'});
   const statusURL=p.url();add('deletion-status-without-token-denied',(await p.request.get(statusURL.split('?')[0],{maxRedirects:0})).status()===404,{width:'N/A HTTP'});add('consumed-confirm-after-session-ended-denied',(await p.request.get(confirmURL,{maxRedirects:0})).status()===302,{width:'N/A HTTP'});
   if(cancel){await p.locator('a[href*="/cancel/"]').click();await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('form:has([name=form_action][value=send_code]) button').click()]);const cancelURL=p.url(),cc=(await mails()).at(-1).body.match(/\b\d{6}\b/)[0];await p.locator('[name=confirmation_code]').fill(cc);await Promise.all([p.waitForURL(u=>u.pathname.includes('/status/')),p.locator('.account-deletion-form button[type=submit]').click()]);s=await state();deletion=s.deletions.find(x=>x.id===deletion.id);add('native-cancel-restores-active',deletion.status==='CANCELED'&&s.users.find(x=>x.id===u.id).is_active,{screenshot:await shot('deletion-canceled')});
    const csrf=(await c.cookies()).find(x=>x.name==='module07_r1_csrf')?.value,replay=await p.request.post(cancelURL,{form:{csrfmiddlewaretoken:csrf,status_token:new URL(cancelURL).searchParams.get('token'),form_action:'cancel',confirmation_code:cc},maxRedirects:0});add('cancel-code-replay-denied',replay.status()===400&&(await state()).deletions.find(x=>x.id===deletion.id).status==='CANCELED',{http:replay.status(),width:'N/A HTTP'});
   }
  }catch(e){rows.push({id:'deletion-flow-harness-error',status:'NOT RUN',role:'QA',lang,width,error:String(e),url:p.url()});await p.locator('[name=confirmation_code]').fill('').catch(()=>{});await shot('deletion-harness-error');}await c.close();await second.close();
 }return{rows};
}
