async original=>{
 const base='http://localhost:8788',browser=original.context().browser(),rows=[],errors=[],network=[];
 const check=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',...detail});
 async function context(options={}){const c=await browser.newContext({viewport:{width:1440,height:950},reducedMotion:'reduce',...options});await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());return c;}
 async function login(c,role='demo_owner'){const p=await c.newPage();p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.status()>=400)network.push({status:r.status(),url:r.url()})});await p.goto(base+'/qa/');await p.getByRole('button',{name:'Войти: '+role,exact:true}).click();return p;}
 async function submit(p,values,extra={}){await p.locator('[data-org-edit-form]').evaluate((f,{values,extra})=>{f.noValidate=true;for(const [n,v]of Object.entries({...values,...extra})){f.elements[n].removeAttribute('maxlength');f.elements[n].value=v;}f.elements.name_ru.dispatchEvent(new Event('input',{bubbles:true}));}, {values,extra});const nav=p.waitForNavigation({waitUntil:'load'}),response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/save/'));await p.locator('[data-org-edit-form] button[type=submit]').click();const r=await response;await nav;return r.status();}
 const good={name_az:'ORG05 Corrected AZ',name_ru:'ORG05 Исправлено',name_en:'ORG05 Corrected',phone:'+994501234567',whatsapp:'+994501234567',website:'https://example.invalid',description_az:'ORG05 synthetic corrected description'};
 let c=await context(),p=await login(c);
 try{
 await p.goto(base+'/ru/account/organizations/46/');
 for(let i=0;i<2;i++){const status=await submit(p,{...good,name_ru:'R'.repeat(256)});check('repeat-invalid-'+i,status===400&&await p.locator('#id_name_ru_error').count()===1);}
 check('corrected-submit',await submit(p,good)===302&&await p.locator('[data-org-edit-form]').count()===1);
 check('pending-not-live',(await p.locator('.org-alert--pending').innerText()).includes('Изменения отправлены на проверку')&&await p.locator('[data-org-edit-form] [name=name_ru]').inputValue()===good.name_ru);
 await p.locator('.org-alert--pending').scrollIntoViewIfNeeded();await p.screenshot({path:'output/playwright/org05-fix-20261008/success-ru-1440.png'});
 await p.reload();check('successful-reopen',await p.locator('[data-org-edit-form] [name=name_ru]').inputValue()===good.name_ru);
 const other=await c.newPage();await p.goto(base+'/ru/account/organizations/47/');await other.goto(base+'/ru/account/organizations/47/');
 check('winning-tab',await submit(p,{...good,name_ru:'ORG05 Winning tab'})===302);
 const status=await submit(other,{...good,name_ru:'ORG05 Losing tab'});
 check('stale-tab-409',status===409);
 check('stale-input-retained',await other.locator('[name=name_ru]').inputValue()==='ORG05 Losing tab');
 check('conflict-visible-focused',await other.locator('#org-editor-errors').count()===1&&await other.evaluate(()=>document.activeElement.id)==='org-editor-errors');
 await other.screenshot({path:'output/playwright/org05-fix-20261008/conflict-ru-1440.png'});await other.setViewportSize({width:390,height:950});await other.screenshot({path:'output/playwright/org05-fix-20261008/conflict-ru-390.png'});
 await other.goto(base+'/ru/account/organizations/47/');check('conflict-recovery-local-copy',await other.locator('[name=name_ru]').inputValue()==='ORG05 Losing tab');
 }catch(e){check('positive-conflict-harness',false,{error:String(e).slice(0,200)});}finally{await c.close();}
 c=await context();p=await login(c);const auth=await c.storageState();await c.close();c=await context({javascriptEnabled:false,storageState:auth});p=await c.newPage();
 try{await p.goto(base+'/ru/account/organizations/48/');check('nojs-native400',await submit(p,{...good,name_ru:'R'.repeat(256)})===400);check('nojs-inline-summary',await p.locator('#id_name_ru_error').count()===1&&await p.locator('#org-editor-errors').count()===1);await p.locator('#org-editor-errors a').focus();await p.keyboard.press('Enter');check('nojs-anchor-focus',await p.evaluate(()=>document.activeElement.id)==='id_name_ru');await p.locator('#org-editor-errors').scrollIntoViewIfNeeded();await p.screenshot({path:'output/playwright/org05-fix-20261008/nojs-ru-1440.png'});check('hidden-errors-visible',await submit(p,good,{expected_version:'bad',revision_version:'bad'})===400&&(await p.locator('#org-editor-errors').innerText()).includes('Expected version')&&await p.locator('#org-editor-errors a').count()===0);
 }catch(e){check('nojs-harness',false,{error:String(e).slice(0,200)});}finally{await c.close();}
 c=await context({viewport:{width:390,height:950}});p=await login(c);await c.addInitScript(()=>{Storage.prototype.getItem=function(){throw new DOMException('ORG05 disabled','SecurityError')};Storage.prototype.setItem=function(){throw new DOMException('ORG05 disabled','SecurityError')};});
 try{await p.goto(base+'/ru/account/organizations/49/');check('storage-unavailable-400',await submit(p,{...good,name_ru:'R'.repeat(256)})===400);check('storage-unavailable-retained',await p.locator('[name=name_ru]').inputValue()==='R'.repeat(256)&&await p.evaluate(()=>document.activeElement.id)==='org-editor-errors');check('storage-no-false-saved',(await p.locator('[data-draft-status]').innerText()).trim()==='');}catch(e){check('storage-harness',false,{error:String(e).slice(0,200)});}finally{await c.close();}
 c=await context();p=await login(c,'demo_parent');
 try{const r=await p.goto(base+'/ru/account/organizations/49/');check('foreign-get-404',r.status()===404&&await p.locator('[data-org-edit-form]').count()===0);await p.goto(base+'/qa/');const csrf=await p.locator('form[action="/qa/login/"] input[name=csrfmiddlewaretoken]').first().inputValue();const response=await c.request.post(base+'/ru/account/organizations/49/save/',{form:{...good,expected_version:'1',revision_version:'0',csrfmiddlewaretoken:csrf},headers:{Referer:base+'/qa/'},maxRedirects:0});check('foreign-post-404',response.status()===404,{statusCode:response.status()});}catch(e){check('foreign-harness',false,{error:String(e).slice(0,200)});}finally{await c.close();}
 return{rows,errors,network};
}
