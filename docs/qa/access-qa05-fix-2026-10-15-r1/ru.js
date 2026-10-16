async(page)=>{
const base='http://127.0.0.1:59697/',lang='ru',out='/home/ramin/kidsmap/docs/qa/access-qa05-fix-2026-10-15-r1/screenshots/';
const expected={ru:['Неверный код подтверждения.','Введите фразу подтверждения точно так, как она показана.'],az:['Yanlış təsdiq kodu.','Təsdiq ifadəsini göstərildiyi kimi dəqiq daxil edin.'],en:['Invalid confirmation code.','Enter the confirmation phrase exactly as shown.']}[lang];
const rows=[],completedCells=[],diagnostics={console:[],pageerrors:[],requestFailures:[],responses:[]};let width=0,phase='start';
const f=await(await page.request.get(base+'qa/fixtures/')).json(),prefix=lang==='az'?'':lang+'/';
function rec(name,ok,detail={}){rows.push({lang,width,phase,name,status:ok?'PASS':'FAIL',detail});}
function must(name,ok,detail={}){rec(name,ok,detail);if(!ok)throw Error(name);}
const safePath=url=>new URL(url).pathname.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/ig,'[OWN-ID]');
page.on('pageerror',e=>diagnostics.pageerrors.push(String(e).replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/ig,'[OWN-ID]')));
page.on('console',m=>{if(['warning','error'].includes(m.type()))diagnostics.console.push({type:m.type(),text:m.text().replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/ig,'[OWN-ID]')});});
page.on('requestfailed',r=>diagnostics.requestFailures.push({local:r.url().startsWith(base),error:r.failure()?.errorText}));
page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)diagnostics.responses.push({path:safePath(r.url()),status:r.status()});});
await page.context().route('**/*',r=>r.request().url().startsWith(base)||r.request().url().startsWith('data:')||r.request().url()==='about:blank'?r.continue():r.abort('blockedbyclient'));
async function submit(form){const nav=page.waitForEvent('domcontentloaded'),res=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().startsWith(base));await form.locator('button[type=submit]').press('Enter');const r=await res;await nav;await page.waitForLoadState('networkidle');return r.status();}
async function snapshot(name){await page.evaluate(async()=>{await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity).map(a=>a.finished));});await page.screenshot({path:out+lang+'-'+width+'-'+name+'.png',fullPage:true,animations:'disabled'});}
async function state(){return await(await page.request.get(base+'qa/state/')).json();}
try{
for(width of [360,390,768,1024,1280,1440]){
phase='request';await page.context().clearCookies();await page.setViewportSize({width,height:950});await page.goto(base+prefix+'auth/login/');await page.locator('#id_username').fill(f.users[lang+'_'+width].username);await page.locator('#id_password').fill(f.password);must('native login POST',await submit(page.locator('form.register-form'))===302);
await page.goto(base+prefix+'account/deletion/');must('real request form available under SIMULATED TEST_POLICY',await page.locator('input[name=form_action][value=request]').count()===1);
must('native request POST redirects',await submit(page.locator('form.account-deletion-actions'))===302);
must('request reaches confirmation',await page.locator('#id_confirmation_code').count()===1);
const username=f.users[lang+'_'+width].username;
const ownMail=async()=>await(await page.request.get(base+'qa/mailcode/'+encodeURIComponent(username)+'/')).json();
const ownState=async()=> (await state()).requests.find(r=>r.user===username);
const mail=await ownMail();must('own local letter code matches recipient and request hash',mail.available&&mail.matches_own_request&&/^\d{6}$/.test(mail.code||''));
const wrong=String((Number(mail.code)+1)%1000000).padStart(6,'0'),phrase=await page.locator('.account-deletion-phrase code').textContent();
const confirmUrl=page.url(),oldCookies=await page.context().cookies();
phase='wrong-code';await page.locator('#id_confirmation_code').fill(wrong);await page.locator('#id_typed_confirmation').fill(phrase);must('wrong code rejected HTTP400',await submit(page.locator('form.account-deletion-form'))===400);
const codeError=await page.locator('#confirmation-code-errors').innerText();rec('code error uses active language',codeError.trim()===expected[0],{text:codeError});must('code error field accessible and values preserved',await page.locator('#id_confirmation_code').getAttribute('aria-invalid')==='true'&&(await page.locator('#id_confirmation_code').inputValue())===wrong&&(await page.locator('#id_typed_confirmation').inputValue())===phrase);await snapshot('wrong-code');
phase='wrong-phrase';await page.locator('#id_typed_confirmation').fill('QA WRONG PHRASE');must('wrong phrase rejected HTTP400',await submit(page.locator('form.account-deletion-form'))===400);
const phraseError=await page.locator('#typed-confirmation-errors').innerText();rec('phrase error uses active language',phraseError.trim()===expected[1],{text:phraseError});must('phrase error field accessible and values preserved',await page.locator('#id_typed_confirmation').getAttribute('aria-invalid')==='true'&&(await page.locator('#id_confirmation_code').inputValue())===wrong&&(await page.locator('#id_typed_confirmation').inputValue())==='QA WRONG PHRASE');
const current=(await state()).requests.find(r=>r.user===f.users[lang+'_'+width].username);must('invalid inputs preserve active account and pending deletion with four attempts',current?.active&&current.status==='CONFIRMATION_SENT'&&current.attempts_left===4&&current.code_present);
await page.locator('#id_typed_confirmation').focus();await page.keyboard.press('Tab');must('keyboard can reach submit',await page.locator('.account-deletion-form button[type=submit]').evaluate(e=>document.activeElement===e));await snapshot('wrong-phrase');
rec('no horizontal page overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
phase='pre-confirm-cancel';
{const nav=page.waitForEvent('domcontentloaded');await page.locator('.account-deletion-form a.account-deletion-secondary').click();await nav;await page.waitForLoadState('networkidle');must('Cancel before confirm returns to settings',new URL(page.url()).pathname.endsWith('/account/settings/'));const q=await ownState();must('Cancel navigation keeps account active and pending',q.active&&q.status==='CONFIRMATION_SENT'&&q.attempts_left===4);}
await page.goto(confirmUrl);phase='correction-confirm';await page.locator('#id_confirmation_code').fill(mail.code);await page.locator('#id_typed_confirmation').fill(phrase);must('correct native confirmation redirects',await submit(page.locator('.account-deletion-form'))===302);
{const q=await ownState();must('only correct input schedules and disables with unusable password',q.status==='SCHEDULED'&&!q.active&&!q.password_usable&&!q.code_present&&q.attempts_left===0);}
phase='cancel-request';{const nav=page.waitForEvent('domcontentloaded');await page.locator('a[href*="/cancel/"]').click();await nav;await page.waitForLoadState('networkidle');}
must('native cancellation sends separate local letter',await submit(page.locator('.account-deletion-actions'))===200);
const cancelUrl=page.url(),cancelMail=await ownMail();must('cancellation local letter matches current request hash',cancelMail.available&&cancelMail.matches_own_request);
const wrongCancel=String((Number(cancelMail.code)+1)%1000000).padStart(6,'0');await page.locator('#id_confirmation_code').fill(wrongCancel);phase='cancel-wrong-code';must('wrong cancellation code denied400',await submit(page.locator('.account-deletion-form'))===400);
const cancelError=await page.locator('#cancellation-code-errors').innerText();must('shared cancellation error has exact active-language wording',cancelError.trim()===expected[0],{text:cancelError});must('cancellation code preserved and accessible',await page.locator('#id_confirmation_code').inputValue()===wrongCancel&&await page.locator('#id_confirmation_code').getAttribute('aria-invalid')==='true');
{const q=await ownState();must('wrong cancellation code does not restore account',q.status==='SCHEDULED'&&!q.active&&q.attempts_left===4);}
await snapshot('cancel-wrong-code');phase='cancel-correct';await page.locator('#id_confirmation_code').fill(cancelMail.code);must('correct cancellation redirects',await submit(page.locator('.account-deletion-form'))===302);
{const q=await ownState();must('cancellation restores account requiring a new password and clears code',q.status==='CANCELED'&&q.active&&!q.password_usable&&!q.code_present&&q.attempts_left===0);}
if([390,1440].includes(width))await snapshot('canceled');
const cookies=await page.context().cookies(),csrf=cookies.find(c=>c.name==='accessqa05fixr1_csrf').value;
const replay=await page.request.post(cancelUrl,{headers:{'X-CSRFToken':csrf},form:{form_action:'cancel',confirmation_code:cancelMail.code}});must('consumed cancellation code cannot be replayed',replay.status()===400);
{const q=await ownState();must('replay leaves restored state unchanged',q.status==='CANCELED'&&q.active&&!q.password_usable&&!q.code_present);}
phase='old-session';const oldCtx=await page.context().browser().newContext({viewport:{width,height:950}});await oldCtx.route('**/*',r=>r.request().url().startsWith(base)||r.request().url().startsWith('data:')?r.continue():r.abort('blockedbyclient'));await oldCtx.addCookies(oldCookies);const oldPage=await oldCtx.newPage();await oldPage.goto(base+prefix+'account/settings/');await oldPage.waitForLoadState('networkidle');must('old session remains invalid after cancellation',new URL(oldPage.url()).pathname.endsWith('/auth/login/'));await oldCtx.close();
completedCells.push({lang,width,states:['wrong-code','wrong-phrase','pre-confirm-cancel','correct-confirm','cancel-wrong-code','correct-cancel','code-replay','old-session']});

}
return {rows,completedCells,diagnostics,error:null,browser:page.context().browser().version()};
}catch(e){return {rows,completedCells,diagnostics,error:String(e).split('\n')[0],phase,width};}
}