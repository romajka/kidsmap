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
 for(const lang of ['ru','az','en'])for(const width of [390,1440]){
  const pre=lang==='az'?'/':'/'+lang+'/',email='qa07.'+lang+'.'+width+'@example.invalid',c=await original.context().browser().newContext({viewport:{width,height:950}}),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(14000);
  const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'registered-user',lang,width,...x});
  const shot=async(name)=>{const file=name+'-'+lang+'-'+width+'.png';await p.screenshot({path:D+file,fullPage:true});return file;};
  const mails=async()=> (await (await p.request.get(B+'/qa/mail/')).json()).messages.filter(x=>x.to.some(e=>e.toLowerCase()===email));
  const logout=async()=>{await p.locator('#account-menu-trigger').click();const btn=p.locator('form[action$="auth/logout/"] button:visible').first();await Promise.all([p.waitForURL(u=>u.pathname===pre),btn.click()]);};
  try{
   await p.goto(B+pre+'auth/register/?next='+encodeURIComponent(pre+'account/settings/'));for(const [name,value] of Object.entries({first_name:'Uydurma',last_name:'Sınaq',email:email.toUpperCase(),phone:'+994500000007',password1:'__LOCAL_PASSWORD__'+'Q',password2:'__LOCAL_PASSWORD__'+'Q'+'Mismatch'}))await p.locator('[name='+name+']').fill(value);await p.locator('[name=agreement]').check();await p.locator('form:has([name=password1]) button[type=submit]').click();await p.waitForTimeout(400);add('registration-mismatch-preserves-input',(await p.locator('[name=first_name]').inputValue())==='Uydurma'&&(await p.locator('[name=email]').inputValue()).toLowerCase()===email,{screenshot:await shot('register-error')});
   await p.locator('[name=password1]').fill('__LOCAL_PASSWORD__'+'Q');await p.locator('[name=password2]').fill('__LOCAL_PASSWORD__'+'Q');await p.locator('[name=agreement]').check();await Promise.all([p.waitForURL(u=>u.pathname.includes('verify-email')),p.locator('form:has([name=password1]) button[type=submit]').click()]);
   let messages=await mails(),code=messages.at(-1).body.match(/\b\d{6}\b/)[0];const state=await (await p.request.get(B+'/qa/state/')).json();const u=state.verified.find(x=>x.email===email);add('registration-email-normalized-inactive',Boolean(u)&&state.users.find(x=>x.id===u.user_id)?.is_active===false,{screenshot:await shot('verify-issued')});
   const wrong=String((Number(code)+1)%1000000).padStart(6,'0');await p.locator('form:has([name=code]) [name=code]').fill(wrong);await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('form:has([name=code]) button[type=submit]').click()]);await p.locator('[name=code]').fill('');add('verification-wrong-code-denied',p.url().includes('verify-email'),{screenshot:await shot('verify-error')});
   const count=messages.length;await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('form:has([name=form_action][value=resend]) button').click()]);add('verification-resend-cooldown',(await mails()).length===count);
   await p.locator('[name=code]').fill(code);await Promise.all([p.waitForURL(u=>u.pathname.includes('/account/')),p.locator('form:has([name=code]) button[type=submit]').click()]);await p.goto(B+pre+'account/settings/');add('verification-login-next',await p.locator('[name=first_name]').inputValue()==='Uydurma',{screenshot:await shot('registered-settings')});
   await p.locator('[name=first_name]').fill('UydurmaYenilənmiş');await p.locator('[name=last_name]').fill('SınaqYenilənmiş');await p.locator('[name=phone]').fill('+994500000077');await p.locator('[name=avatar]').setInputFiles('C:/kidsmap/.tmp/module07-20261010-r1/assets/avatar.png');await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('form:has([name=first_name]) button[type=submit]').click()]);await p.goto(B+pre+'account/settings/');add('profile-native-save-reload',(await p.locator('[name=first_name]').inputValue())==='UydurmaYenilənmiş'&&(await p.locator('[name=phone]').inputValue()).replace(/\D/g,'')==='994500000077',{screenshot:await shot('profile-reloaded')});
   await logout();const guest=await p.request.get(B+pre+'account/settings/',{maxRedirects:0});add('native-logout-session-ended',guest.status()===302);
   await p.goto(B+pre+'auth/verify-email/?email='+email);await p.locator('[name=code]').fill(code);await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('form:has([name=code]) button[type=submit]').click()]);await p.locator('[name=code]').fill('');add('consumed-code-not-login',p.url().includes('verify-email')&&(await p.request.get(B+pre+'account/',{maxRedirects:0})).status()===302,{screenshot:await shot('verify-replay-denied')});
   await p.goto(B+pre+'auth/password-reset/');await p.locator('[name=email]').fill(email);await Promise.all([p.waitForURL(u=>u.pathname.includes('password-reset/done')),p.locator('main form button[type=submit]').click()]);messages=await mails();const reset=messages.at(-1).body.match(/https?:\/\/[^\s<>]+\/auth\/reset\/[^\s<>]+/)[0];await shot('reset-sent');await p.goto(reset);await p.locator('[name=new_password1]').fill('__LOCAL_PASSWORD__'+'Reset');await p.locator('[name=new_password2]').fill('__LOCAL_PASSWORD__'+'Reset');await Promise.all([p.waitForURL(u=>u.pathname.includes('auth/reset/done')),p.locator('main form button[type=submit]').click()]);add('native-password-reset-complete',p.url().includes('auth/reset/done'),{screenshot:await shot('reset-complete')});await p.goto(reset);add('password-reset-link-replay-denied',await p.locator('[name=new_password1]').count()===0,{screenshot:await shot('reset-replay-denied')});
   await p.goto(B+pre+'auth/login/?next='+encodeURIComponent('https://example.invalid/escape'));await p.locator('[name=username]').fill(email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__'+'Reset');await Promise.all([p.waitForURL(u=>u.pathname.includes('/account/')),p.locator('.auth-form button[type=submit]:visible').click()]);add('native-login-normalized-safe-next',p.url().startsWith(B)&&p.url().includes('/account/'),{screenshot:await shot('login-safe-next')});await logout();
   await p.goto(B+pre+'auth/register/');for(const [name,value] of Object.entries({first_name:'Uydurma',last_name:'Sınaq',email:email.toUpperCase(),phone:'+994500000007',password1:'__LOCAL_PASSWORD__'+'Q',password2:'__LOCAL_PASSWORD__'+'Q'}))await p.locator('[name='+name+']').fill(value);await p.locator('[name=agreement]').check();await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('form:has([name=password1]) button[type=submit]').click()]);add('duplicate-registration-denied',await p.locator('[name=password1]').count()>0,{screenshot:await shot('register-duplicate-error')});
  }catch(e){rows.push({id:'auth-flow-harness-error',status:'NOT RUN',role:'QA',lang,width,error:String(e),url:p.url()});await p.locator('[name=code]').fill('').catch(()=>{});await p.screenshot({path:D+'auth-flow-error-'+lang+'-'+width+'.png',fullPage:true});}
  await c.close();
 }
 return{rows};
}
