async original=>{
const B='http://127.0.0.1:39199',H='/home/ramin/kidsmap/docs/qa/access-qa06-fix-2026-10-15-r1',F=await(await original.request.get(B+'/qa/fixtures/')).json(),source=await(await original.request.get(B+'/qa/source/')).json(),rows=[],diagnostics=[],mode='GREEN';
const cells=mode==='RED'?[{lang:'ru',width:390,...F.red}]:F.cells;
for(const cell of cells){const{lang,width,email,user_id}=cell,pre=lang==='az'?'/':'/'+lang+'/',ctx=await original.context().browser().newContext({viewport:{width,height:950}}),p=await ctx.newPage();
await ctx.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
p.on('pageerror',e=>diagnostics.push({lang,width,kind:'pageerror',text:String(e).split('\n')[0]}));
p.on('requestfailed',r=>diagnostics.push({lang,width,kind:'requestfailed',local:r.url().startsWith(B),error:r.failure()?.errorText}));
p.on('console',m=>{if(m.type()==='error')diagnostics.push({lang,width,kind:'console',local:m.location().url.startsWith(B),expected_http_400:m.text().includes('400'),blocked_external:m.text().includes('ERR_FAILED')||m.text().includes('ERR_BLOCKED_BY_CLIENT')});});
const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',lang,width,detail});
const state=async()=>await(await p.request.get(B+'/qa/state/')).json();
const snap=async()=>{const s=await state();return{user:s.users.find(x=>x.id===user_id),deletion:s.deletions.find(x=>x.user_id===user_id)};};
const submit=async(form,keyboard=false)=>{const wait=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().startsWith(B));const nav=p.waitForEvent('domcontentloaded');if(keyboard)await p.locator('#id_typed_confirmation').press('Enter');else await form.locator('button[type=submit]:visible').click();const res=await wait;await nav;await p.waitForLoadState('networkidle');return res;};
const png=async(name)=>{const code=p.locator('#id_confirmation_code');await p.screenshot({path:H+'/screenshots/'+mode.toLowerCase()+'-'+name+'-'+lang+'-'+width+'.png',fullPage:true,animations:'disabled',mask:await code.count()?[code]:[]});};
const geometry=async()=>await p.locator('.account-deletion-card').evaluate(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,root:document.documentElement.scrollWidth,viewport:innerWidth};});
try{
await p.goto(B+pre+'auth/login/');await p.locator('#id_username').fill(email);await p.locator('#id_password').fill(F.password);const login=await submit(p.locator('.auth-form:visible'));add('native login with initial fictional verified fixture',login.status()===302&&new URL(p.url()).pathname.includes('/account/'));
await p.goto(B+pre+'account/deletion/');const req=await submit(p.locator('form:has([name=form_action][value=request])'));add('native deletion request reaches confirmation',req.status()===302&&await p.locator('#id_typed_confirmation').count()===1);const confirmURL=p.url();
const messages=(await(await p.request.get(B+'/qa/mail/')).json()).messages.filter(m=>m.to.includes(email)),letter=messages.at(-1),code=letter.body.match(/\b\d{6}\b/)[0],phrase=await p.locator('.account-deletion-phrase code').innerText();add('own local deletion letter matches recipient and supplies code',letter.to.includes(email)&&/^\d{6}$/.test(code));
let before=await snap();add('request starts active with five attempts and live own code',before.user.is_active&&before.deletion.status==='CONFIRMATION_SENT'&&before.deletion.attempts===5&&before.deletion.has_code);
await png('confirm');
if(mode==='RED'){
 const raw=' '+phrase+' ';await p.locator('#id_confirmation_code').fill(code);await p.locator('#id_typed_confirmation').fill(raw);const response=await submit(p.locator('.account-deletion-form')),after=await snap(),wire=new URLSearchParams(response.request().postData()).get('typed_confirmation');add('browser sends unmodified padded input',wire===raw);add('padded phrase must be denied and keep active account',response.status()===400&&after.user.is_active&&after.deletion.status==='CONFIRMATION_SENT',{http:response.status(),active:after.user.is_active,state:after.deletion.status});await png('result');
}else{
for(const[kind,raw]of Object.entries({leading:' '+phrase,trailing:phrase+' ',both:' '+phrase+' ',nbsp:'\u00a0'+phrase+'\u00a0'})){
 await p.locator('#id_confirmation_code').fill(code);await p.locator('#id_typed_confirmation').fill(raw);
 const response=await submit(p.locator('.account-deletion-form'),kind==='both'),after=await snap(),wire=new URLSearchParams(response.request().postData()).get('typed_confirmation');
 add(kind+': raw input sent unchanged',wire===raw);
 add(kind+': HTTP400 and exact phrase error',response.status()===400&&await p.locator('#id_typed_confirmation').getAttribute('aria-invalid')==='true');
 add(kind+': raw phrase and valid code preserved',await p.locator('#id_typed_confirmation').inputValue()===raw&&await p.locator('#id_confirmation_code').inputValue()===code);
 add(kind+': active state and code attempts unchanged',after.user.is_active&&after.deletion.status==='CONFIRMATION_SENT'&&after.deletion.attempts===5&&after.deletion.has_code);
 const error=await p.locator('#typed-confirmation-errors').innerText(),expected=source.translations[lang]['Введите фразу подтверждения точно так, как она показана.'];add(kind+': localized exact phrase error',error.includes(expected));
 const g=await geometry();add(kind+': error form fits viewport',g.root<=width+.5&&g.left>=-.5&&g.right<=width+.5,g);await png(kind);
}
await p.locator('#id_confirmation_code').focus();await p.keyboard.press('Tab');add('Tab reaches phrase',await p.locator('#id_typed_confirmation').evaluate(e=>e===document.activeElement));await p.keyboard.press('Tab');const focus=await p.locator('.account-deletion-form button[type=submit]').evaluate(e=>{const c=getComputedStyle(e);return{active:e===document.activeElement,visible:e.matches(':focus-visible'),outlineWidth:c.outlineWidth,outlineStyle:c.outlineStyle,shadow:c.boxShadow};});add('Tab reaches visible submit focus',focus.active&&focus.visible&&(parseFloat(focus.outlineWidth)>0&&focus.outlineStyle!=='none'||focus.shadow!=='none'),focus);await p.keyboard.press('Shift+Tab');add('Shift+Tab returns to phrase',await p.locator('#id_typed_confirmation').evaluate(e=>e===document.activeElement));
const wrong=String((Number(code)+1)%1000000).padStart(6,'0');await p.locator('#id_confirmation_code').fill(wrong);await p.locator('#id_typed_confirmation').fill(phrase);const negative=await submit(p.locator('.account-deletion-form')),bad=await snap();add('exact phrase with wrong code remains400',negative.status()===400&&await p.locator('#id_confirmation_code').getAttribute('aria-invalid')==='true');add('wrong code decrements only one attempt and keeps account active',bad.user.is_active&&bad.deletion.attempts===4&&bad.deletion.status==='CONFIRMATION_SENT'&&bad.deletion.has_code);add('wrong code error localized',(await p.locator('#confirmation-code-errors').innerText()).includes(source.translations[lang]['Неверный код подтверждения.']));await png('wrong-code');
await p.locator('#id_confirmation_code').fill(code);await p.locator('#id_typed_confirmation').fill(phrase);const good=await submit(p.locator('.account-deletion-form'),true),done=await snap();add('exact phrase and valid code schedule deletion',good.status()===302&&!done.user.is_active&&done.deletion.status==='SCHEDULED'&&!done.deletion.has_code);add('signed private status rendered',new URL(p.url()).pathname.includes('/account/deletion/status/')&&await p.locator('.account-deletion-card').count()===1);await png('scheduled');await p.goto(B+pre+'account/settings/');add('old session cannot open settings',new URL(p.url()).pathname.includes('/auth/login/'));const replay=await p.request.post(confirmURL,{form:{form_action:'confirm',confirmation_code:code,typed_confirmation:phrase},maxRedirects:0});add('replay cannot mutate scheduled state',(replay.status()===302||replay.status()===403)&&(await snap()).deletion.status==='SCHEDULED');
}
}catch(e){rows.push({id:'native harness must complete cell',status:'NOT RUN',lang,width,error:String(e).split('\n')[0]});}
await ctx.close();
}
return{mode,rows,diagnostics,source_strip:source.typed_confirmation_strip,policy:'SIMULATED only',setup:'initial fictional verified fixtures; actual UI login/request/confirm, own local letters',screenshots:'native mask only code field; no DOM/CSS mutation'};
}
