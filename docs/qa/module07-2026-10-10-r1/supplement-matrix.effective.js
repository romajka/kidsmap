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
},rows=[],diagnostics=[];
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  const pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width,height:950}}),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(13000);const pageerrors=[],consoleErrors=[],failed=[];p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});p.on('requestfailed',r=>failed.push({url:r.url().split('?')[0],local:r.url().startsWith(B),error:r.failure()?.errorText}));const add=(id,ok,role,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width,...x});
  const shot=async(n)=>{const f=n+'-'+lang+'-'+width+'.png';await p.screenshot({path:D+f,fullPage:true,animations:'disabled'});return f;};
  const capture=async(n,role)=>{const g=await p.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:innerWidth,broken:[...document.images].filter(e=>e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0&&getComputedStyle(e).visibility!=='hidden'&&e.complete&&!e.naturalWidth).map(e=>e.getAttribute('src'))}));add(n+'-geometry',g.scroll<=width+1&&g.broken.length===0,role,{geometry:g,screenshot:await shot(n)});};
  const login=async(role)=>{await p.goto(B+pre+'auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('auth/login')),p.locator('.auth-form button[type=submit]:visible').click()]);};
  const logout=async()=>{await p.goto(B+pre+'account/profile/');await p.locator(width<1200?'button[aria-controls="km-mobile-drawer"]':'#account-menu-trigger').click();await Promise.all([p.waitForURL(u=>u.pathname===pre),p.locator('form[action$="auth/logout/"] button:visible').first().click()]);};
  try{
   await p.goto(B+pre+'auth/register/');const agreement=p.locator('[name=agreement]');await agreement.focus();await p.keyboard.press('Space');add('register-Space-checkbox',await agreement.isChecked(),'anonymous');await p.keyboard.press('Space');await p.locator('[name=first_name]').focus();const posted=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/auth/register/'),{timeout:1800}).catch(()=>null);await p.keyboard.press('Enter');await posted;await p.waitForTimeout(350);await p.waitForLoadState('domcontentloaded');add('register-Enter-empty-validation',p.url().includes('/auth/register/')&&await p.locator(':invalid').count()>0,'anonymous');await capture('register-keyboard-invalid','anonymous');
   await login('owner');await p.goto(B+pre+'account/settings/');await capture('settings-visible-images','owner');await p.locator('[name=first_name]').fill('Uydurma '+('UzunAd '.repeat(17)));await p.locator('[name=last_name]').fill('Sınaq '+('UzunSoyad '.repeat(12)));await capture('settings-long-visible-images','owner');await p.goto(B+pre+'account/places/team/');await capture('place-team-filled','owner');const bounds=await p.locator('.owner-team-item').evaluateAll(es=>es.map(e=>({left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width,title:e.querySelector('h3')?.textContent.trim()})));add('place-team-items-contained',bounds.every(e=>e.left>=0&&e.right<=width),'owner',{bounds,screenshot:'place-team-filled-'+lang+'-'+width+'.png'});const tf=p.locator('.owner-team-invite-form');await tf.locator('[name=place]').selectOption(String(F.places.owner));await tf.locator('[name=email]').fill(F.actors.owner.email);await tf.locator('[name=role]').focus();await p.keyboard.press('Space');await p.keyboard.press('ArrowDown');await p.keyboard.press('Escape');await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),tf.locator('button[type=submit]').click()]);add('place-team-self-invite-error',await p.locator('.flash-error').count()>0,'owner',{screenshot:await shot('place-team-self-error')});await capture('place-team-error','owner');await logout();
   await login('network');await p.goto(B+pre+'account/organizations/'+F.organization+'/');await capture('organization-team-filled','network');const team=p.locator('[data-team-form]');const forms=await p.locator('form').evaluateAll(es=>es.map(f=>f.getAttribute('action')).filter(Boolean)),controls=await p.locator('[data-team-invitations] button,[data-team-invitations] form').count();add('organization-management-controls-missing',false,'network',{classification:'CONFIRMED rendered missing role/removal and cancellation controls; endpoint functionality tested separately',forms,invitationControls:controls,screenshot:'organization-team-filled-'+lang+'-'+width+'.png'});await team.locator('[name=email]').fill('network-negative07@example.invalid');await team.locator('[name=scope]').selectOption('selected_places');await p.route('**/account/business/team/organization/*/invite/',r=>r.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:'conflict'})}));await team.locator('button[type=submit]').click();await p.waitForTimeout(350);add('organization-409-preserves-input',(await team.locator('[name=email]').inputValue())==='network-negative07@example.invalid'&&!(await team.locator('button[type=submit]').isDisabled()),'network',{classification:'SIMULATED localhost 409; actual 409 contract separately checked',screenshot:await shot('org-team-conflict')});await capture('organization-conflict','network');await logout();
   await login('person');await p.goto(B+pre+'account/specialists/'+F.specialist+'/certificates/');await capture('private-certificates-workspace','person');
  }catch(e){rows.push({id:'supplement-matrix-harness-error',status:'NOT RUN',role:'QA',lang,width,error:String(e),url:p.url()});await shot('supplement-harness-error');}diagnostics.push({lang,width,pageerrors,consoleErrors,failed});await c.close();
 }return{rows,diagnostics};
}
