async original=>{
const base='http://localhost:8788',browser=original.context().browser(),rows=[],errors=[],network=[],prefix={ru:'/ru',az:'',en:'/en'};
const names=['name_az','name_ru','name_en','phone','whatsapp','website','description_az'];
const values={name_az:'ORG05 Submitted AZ',name_ru:'R'.repeat(256),name_en:'E'.repeat(256),phone:'P'.repeat(51),whatsapp:'W'.repeat(51),website:'invalid URL',description_az:'ORG05 Submitted description'};
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
const c=await browser.newContext({viewport:{width,height:950},reducedMotion:'reduce'}),p=await c.newPage();
p.on('pageerror',e=>errors.push({lang,width,error:String(e)}));p.on('response',r=>{if(r.status()>=400)network.push({lang,width,status:r.status(),url:r.url()})});
await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
const check=(id,ok,detail={})=>rows.push({id:id+'-'+lang+'-'+width,status:ok?'PASS':'FAIL',...detail});
try{
 await p.goto(base+'/qa/');await p.getByRole('button',{name:'Войти: demo_owner',exact:true}).click();await p.goto(base+prefix[lang]+'/account/organizations/45/');
 await p.locator('[data-org-edit-form]').evaluate((form,values)=>{form.noValidate=true;for(const [name,value]of Object.entries(values)){form.elements[name].removeAttribute('maxlength');form.elements[name].value=value;}form.elements.name_ru.dispatchEvent(new Event('input',{bubbles:true}));
 const fields=Object.fromEntries(Object.keys(values).map(n=>[n,'OLD RECOVERY '+n]));sessionStorage.setItem('kidsmap:org:2:45:draft',JSON.stringify({source:form.dataset.sourceVersion,fields}));},values);
 const nav=p.waitForNavigation({waitUntil:'load'}),res=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/45/save/'));
 await p.locator('[data-org-edit-form] button[type=submit]').click();const response=await res;await nav;
 const state=await p.locator('[data-org-edit-form]').evaluate((form,names)=>({values:Object.fromEntries(names.map(n=>[n,form.elements[n].value])),invalid:names.filter(n=>form.elements[n].getAttribute('aria-invalid')==='true'),refs:names.filter(n=>form.elements[n].getAttribute('aria-invalid')==='true').map(n=>({name:n,description:form.elements[n].getAttribute('aria-describedby'),exists:(form.elements[n].getAttribute('aria-describedby')||'').split(' ').every(id=>document.getElementById(id)?.textContent.trim())})),errors:form.querySelectorAll('.org-field-error').length,summary:document.activeElement.id,local:JSON.parse(sessionStorage.getItem('kidsmap:org:2:45:draft')||'null'),geometry:{client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}}),names);
 check('native-400',response.status()===400,{statusCode:response.status()});
 check('five-errors-visible',state.errors===5&&state.invalid.length===5&&state.refs.every(x=>x.exists));
 check('posted-input-retained',names.every(n=>state.values[n]===values[n]));
 check('bound-recovery-replaced-old',names.every(n=>state.local?.fields[n]===values[n]));
 check('summary-focused',state.summary==='org-editor-errors');
 check('responsive',state.geometry.scroll<=state.geometry.client,{geometry:state.geometry});
 const expected={ru:'Исправьте ошибки в форме',az:'Formadakı səhvləri düzəldin',en:'Please correct the form errors'};check('summary-language',(await p.locator('#org-editor-errors').innerText()).includes(expected[lang]));
 if(width===390||width===1440){await p.screenshot({path:'output/playwright/org05-fix-20261008/errors-'+lang+'-'+width+'.png'});}
 await p.keyboard.press('Tab');const active=await p.evaluate(()=>document.activeElement.getAttribute('data-org-error-target'));await p.keyboard.press('Enter');
 check('keyboard-error-target',active==='id_name_ru'&&await p.evaluate(()=>document.activeElement.id)==='id_name_ru');
 if(width===390||width===1440)await p.screenshot({path:'output/playwright/org05-fix-20261008/field-'+lang+'-'+width+'.png'});
 await p.goto(base+prefix[lang]+'/account/organizations/45/');
 check('reload-input-restored',await p.locator('[data-org-edit-form] [name=name_ru]').inputValue()===values.name_ru&&await p.locator('[data-org-edit-form] [name=description_az]').inputValue()===values.description_az);
 }catch(e){check('matrix-harness',false,{error:String(e).slice(0,220)});}finally{await c.close();}
}
return{rows,errors,network};}
