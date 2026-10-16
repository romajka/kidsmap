async(page)=>{
const base='http://127.0.0.1:38969/',lang='ru',out='/home/ramin/kidsmap/docs/qa/access-qa05-recheck-2026-10-15-r1/screenshots/';
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
async function snapshot(name){if(![390,1440].includes(width))return;await page.evaluate(async()=>{await Promise.allSettled(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity).map(a=>a.finished));});await page.screenshot({path:out+lang+'-'+width+'-'+name+'.png',fullPage:true,animations:'disabled'});}
async function state(){return await(await page.request.get(base+'qa/state/')).json();}
try{
for(width of [360,390,768,1024,1280,1440]){
phase='request';await page.context().clearCookies();await page.setViewportSize({width,height:950});await page.goto(base+prefix+'auth/login/');await page.locator('#id_username').fill(f.users[lang+'_'+width].username);await page.locator('#id_password').fill(f.password);must('native login POST',await submit(page.locator('form.register-form'))===302);
await page.goto(base+prefix+'account/deletion/');must('real request form available under SIMULATED TEST_POLICY',await page.locator('input[name=form_action][value=request]').count()===1);
must('native request POST redirects',await submit(page.locator('form.account-deletion-actions'))===302);
must('request reaches confirmation',await page.locator('#id_confirmation_code').count()===1);
const mail=await(await page.request.get(base+'qa/mailcode/')).json();must('own local filebased letter contains six-digit code',mail.available&&/^\d{6}$/.test(mail.code||''));
const wrong=String((Number(mail.code)+1)%1000000).padStart(6,'0'),phrase=await page.locator('.account-deletion-phrase code').textContent();
phase='wrong-code';await page.locator('#id_confirmation_code').fill(wrong);await page.locator('#id_typed_confirmation').fill(phrase);must('wrong code rejected HTTP400',await submit(page.locator('form.account-deletion-form'))===400);
const codeError=await page.locator('#confirmation-code-errors').innerText();rec('code error uses active language',lang==='ru'?codeError.includes('Неверный код подтверждения.'):!/[А-Яа-яЁё]/.test(codeError),{text:codeError});must('code error field accessible and values preserved',await page.locator('#id_confirmation_code').getAttribute('aria-invalid')==='true'&&(await page.locator('#id_confirmation_code').inputValue())===wrong&&(await page.locator('#id_typed_confirmation').inputValue())===phrase);await snapshot('wrong-code');
phase='wrong-phrase';await page.locator('#id_typed_confirmation').fill('QA WRONG PHRASE');must('wrong phrase rejected HTTP400',await submit(page.locator('form.account-deletion-form'))===400);
const phraseError=await page.locator('#typed-confirmation-errors').innerText();rec('phrase error uses active language',lang==='ru'?phraseError.includes('Введите фразу подтверждения точно так, как она показана.'):!/[А-Яа-яЁё]/.test(phraseError),{text:phraseError});must('phrase error field accessible and values preserved',await page.locator('#id_typed_confirmation').getAttribute('aria-invalid')==='true'&&(await page.locator('#id_confirmation_code').inputValue())===wrong&&(await page.locator('#id_typed_confirmation').inputValue())==='QA WRONG PHRASE');
const current=(await state()).requests.find(r=>r.user===f.users[lang+'_'+width].username);must('invalid inputs preserve active account and pending deletion with four attempts',current?.active&&current.status==='CONFIRMATION_SENT'&&current.attempts_left===4&&current.code_present);
await page.locator('#id_typed_confirmation').focus();await page.keyboard.press('Tab');must('keyboard can reach submit',await page.locator('.account-deletion-form button[type=submit]').evaluate(e=>document.activeElement===e));await snapshot('wrong-phrase');
rec('no horizontal page overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));completedCells.push({lang,width,states:['wrong-code','wrong-phrase']});
}
return {rows,completedCells,diagnostics,error:null,browser:page.context().browser().version()};
}catch(e){return {rows,completedCells,diagnostics,error:String(e).split('\n')[0],phase,width};}
}