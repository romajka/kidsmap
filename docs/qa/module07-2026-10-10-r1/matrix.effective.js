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
  const pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width,height:950}}),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(10000);const errors=[],failed=[];p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('requestfailed',r=>failed.push({url:r.url().replace(/\?.*/,''),local:r.url().startsWith(B),error:r.failure()?.errorText}));
  const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',lang,width,role:'anonymous',...x});
  const capture=async(state,role='anonymous')=>{const file=state+'-'+lang+'-'+width+'.png';await p.screenshot({path:D+file,fullPage:true,animations:'disabled'});const g=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,text:document.querySelector('main')?.innerText.slice(0,550),broken:[...document.images].filter(x=>x.src.startsWith(location.origin)&&x.complete&&!x.naturalWidth).map(x=>x.getAttribute('src'))}));add(state+'-render',Boolean(g.text),{role,url:p.url(),screenshot:file});add(state+'-root-overflow',g.scroll<=width+1,{role,geometry:g,screenshot:file});add(state+'-images',g.broken.length===0,{role,broken:g.broken,screenshot:file});};
  try{
   for(const [state,path] of [['login','auth/login/'],['register','auth/register/'],['verify-empty','auth/verify-email/'],['reset-empty','auth/password-reset/'],['reset-invalid','auth/reset/invalid/invalid/']]){await p.goto(B+pre+path);await capture(state);}
   await p.goto(B+pre+'auth/login/');await p.locator('[name=username]').fill('missing07@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.auth-form button[type=submit]:visible').click();await p.waitForLoadState('domcontentloaded');add('login-error-retains-email',(await p.locator('[name=username]').inputValue())==='missing07@example.invalid');await capture('login-error');
   await p.locator('[name=username]').fill(F.actors.owner.email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>u.pathname.includes('/account/')),p.locator('.auth-form button[type=submit]:visible').click()]);
   for(const [state,path] of [['account','account/'],['profile','account/profile/'],['settings','account/settings/'],['team','account/places/team/'],['deletion','account/deletion/']]){await p.goto(B+pre+path);await capture(state,'owner');}
   const file=p.locator('[name=avatar]');await p.goto(B+pre+'account/settings/');const first=p.locator('[name=first_name]');await first.fill('Uydurma '+('UzunAd '.repeat(17)));await p.locator('[name=last_name]').fill('QA07 '+('UzunSoyad '.repeat(12)));await capture('settings-long-filled','owner');
   await first.focus();await first.press('Tab');await p.keyboard.press('Shift+Tab');const f=await first.evaluate(e=>({active:e===document.activeElement,outline:getComputedStyle(e).outlineStyle,outlineWidth:getComputedStyle(e).outlineWidth,shadow:getComputedStyle(e).boxShadow}));add('settings-keyboard-focus',f.active&&(f.outline!=='none'&&f.outlineWidth!=='0px'||f.shadow!=='none'),{role:'owner',focus:f});
   await p.goto(B+pre+'auth/login/'); // authenticated redirect; native logout via real UI form below
   await p.goto(B+pre+'account/profile/');const logout=p.locator('form[action$="auth/logout/"] button:visible');if(!(await logout.count())){const menu=p.locator('[data-mobile-menu-toggle],[data-menu-toggle]');if(await menu.count())await menu.first().click();}
   // Exact logout HTTP is checked separately; changing language/session via request is not counted as a UI transition.
   const csrf=(await c.cookies()).find(x=>x.name==='module07_r1_csrf')?.value;await p.request.post(B+pre+'auth/logout/',{form:{csrfmiddlewaretoken:csrf||''}});await p.goto(B+pre+'auth/login/');const forgot=p.getByRole('link',{name:lang==='ru'?'Забыли пароль?':lang==='az'?'Şifrəni unutmusunuz?':'Forgot password?'});if(await forgot.count()){await forgot.click();await p.waitForTimeout(250);await capture('reset-open');await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');await p.keyboard.press('Escape');await p.waitForTimeout(250);add('reset-modal-Escape',!(await p.locator('#resetPasswordModal').isVisible()),{url:p.url()});}
   await p.locator('form[action="/auth/google/"] button').click();await p.waitForLoadState('domcontentloaded');await capture('google-local-error');add('google-unconfigured-safe-local',p.url().startsWith(B)&&!(await p.locator('body').innerText()).includes('Traceback'),{classification:'ACTUAL disabled OAuth branch; real provider NOT RUN'});
  }catch(e){rows.push({id:'matrix-harness-error',status:'NOT RUN',lang,width,role:'QA',error:String(e),url:p.url()});await p.screenshot({path:D+'matrix-error-'+lang+'-'+width+'.png',fullPage:true});}
  diagnostics.push({lang,width,errors,failed});await c.close();
 }
 return{rows,diagnostics,browser:original.context().browser().version()};
}
