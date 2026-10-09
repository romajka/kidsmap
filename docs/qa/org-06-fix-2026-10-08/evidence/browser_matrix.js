async original=>{
const base='http://localhost:8788',browser=original.context().browser(),rows=[],errors=[],network=[];
const copy={ru:{prefix:'/ru',label:'Название организации (AZ)',ruLabel:'Название организации (RU)',phone:'Телефон',conflict:'Изменения уже сохранены в другой вкладке',link:'Открыть актуальные данные'},az:{prefix:'',label:'Təşkilatın adı (AZ)',ruLabel:'Təşkilatın adı (RU)',phone:'Telefon',conflict:'Dəyişikliklər artıq başqa tabda',link:'Aktual məlumatları aç'},en:{prefix:'/en',label:'Organization name (AZ)',ruLabel:'Organization name (RU)',phone:'Phone',conflict:'Changes have already been saved in another tab',link:'Open current data'}};
const good={name_az:'ORG06 Valid AZ',name_ru:'ORG06 Valid RU',name_en:'ORG06 Valid EN',description_az:'ORG06 synthetic description',phone:'+994501234567',whatsapp:'',website:'https://example.invalid/'};
async function submit(p,selector,values,allowInvalid=false){const form=p.locator(selector);await form.evaluate((f,{values,allowInvalid})=>{f.noValidate=allowInvalid;for(const [n,v]of Object.entries(values)){if(allowInvalid)f.elements[n].removeAttribute('maxlength');f.elements[n].value=v;}f.elements.name_ru.dispatchEvent(new Event('input',{bubbles:true}));},{values,allowInvalid});const nav=p.waitForNavigation({waitUntil:'load'}),response=p.waitForResponse(r=>r.request().method()==='POST'&&r.request().isNavigationRequest());await form.locator('button[type=submit]').click();const result=await response;await nav;return result.status();}
for(const [index,lang]of ['ru','az','en'].entries())for(const width of [360,390,768,1024,1280,1440]){
const cfg=copy[lang],c=await browser.newContext({viewport:{width,height:950},reducedMotion:'reduce'}),p=await c.newPage();p.on('pageerror',e=>errors.push({lang,width,error:String(e)}));p.on('response',r=>{if(r.status()>=400)network.push({lang,width,status:r.status(),url:r.url().split('?')[0]})});await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());const check=(id,ok,detail={})=>rows.push({id:id+'-'+lang+'-'+width,status:ok?'PASS':'FAIL',...detail});
try{
await p.goto(base+'/qa/');await p.getByRole('button',{name:'Войти: demo_owner',exact:true}).click();await p.goto(base+cfg.prefix+'/account/organizations/create/');
check('create-native-400',await submit(p,'[data-org-create-form]',{...good,name_az:''},true)===400);
check('create-localized-label',(await p.locator('.km-form-error-summary__field-label').innerText()).includes(cfg.label));check('create-preserved-input',await p.locator('[data-org-create-form] [name=name_ru]').inputValue()===good.name_ru);
check('create-summary-focus-existing-gap',await p.evaluate(()=>document.activeElement.id)==='form-error-summary',{scope:'existing creation accessibility gap; not changed in ORG06'});await p.locator('#form-error-summary').focus();await p.keyboard.press('Tab');await p.keyboard.press('Enter');check('create-keyboard-target',await p.evaluate(()=>document.activeElement.id)==='id_name_az');
check('create-width',await p.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth));
if(width===390||width===1440){await p.locator('#form-error-summary').evaluate(el=>{el.focus();el.scrollIntoView({block:'center'})});await p.screenshot({path:'output/playwright/org06-fix-20261008/create-'+lang+'-'+width+'.png'});}
await p.goto(base+cfg.prefix+'/account/organizations/'+(50+index)+'/');
check('editor-native-400',await submit(p,'[data-org-edit-form]',{...good,name_ru:'R'.repeat(256),phone:'P'.repeat(51)},true)===400);
const summary=await p.locator('#org-editor-errors').innerText();check('editor-localized-fields',summary.includes(cfg.ruLabel)&&summary.includes(cfg.phone)&&!summary.includes('Name ru:'));
check('editor-bound-retained',await p.locator('[data-org-edit-form] [name=name_ru]').inputValue()==='R'.repeat(256));await p.keyboard.press('Tab');await p.keyboard.press('Enter');check('editor-keyboard-target',await p.evaluate(()=>document.activeElement.id)==='id_name_ru');
check('editor-width',await p.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth));
if(width===390||width===1440){await p.locator('#org-editor-errors').evaluate(el=>{el.focus();el.scrollIntoView({block:'center'})});await p.screenshot({path:'output/playwright/org06-fix-20261008/editor-'+lang+'-'+width+'.png'});}
const path=base+cfg.prefix+'/account/organizations/'+(53+index)+'/';await p.goto(path+'?current=1');const other=await c.newPage();await other.goto(path+'?current=1');const oldVersion=await other.locator('[name=revision_version]').inputValue();const winner='ORG06 Winner '+lang+' '+width,loser='ORG06 Loser '+lang+' '+width;
check('winning-submit',await submit(p,'[data-org-edit-form]',{...good,name_ru:winner})===302);
check('losing-409',await submit(other,'[data-org-edit-form]',{...good,name_ru:loser})===409);
check('conflict-localized',(await other.locator('#org-editor-errors').innerText()).includes(cfg.conflict)&&!(await other.locator('#org-editor-errors').innerText()).includes('Candidate version conflict.'));
check('conflict-bound-cas-retained',await other.locator('[name=name_ru]').inputValue()===loser&&await other.locator('[name=revision_version]').inputValue()===oldVersion);
check('conflict-width',await other.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth));
if(width===390||width===1440){await other.locator('#org-editor-errors').evaluate(el=>{el.focus();el.scrollIntoView({block:'center'})});await other.screenshot({path:'output/playwright/org06-fix-20261008/conflict-'+lang+'-'+width+'.png'});}
const link=other.locator('[data-org-current-link]');check('current-link-copy',await link.innerText()===cfg.link&&await link.getAttribute('rel')==='noopener');
await other.keyboard.press('Tab');check('current-link-keyboard-focus',await other.evaluate(()=>document.activeElement.hasAttribute('data-org-current-link')));const popupPromise=other.waitForEvent('popup');await other.keyboard.press('Enter');const current=await popupPromise;await current.waitForLoadState('load');
check('current-newtab-winner',current.url().endsWith('?current=1')&&await current.locator('[name=name_ru]').inputValue()===winner&&await current.locator('[data-org-current-data]').count()===1);
check('loser-original-tab-kept',await other.locator('[name=name_ru]').inputValue()===loser);
check('repeat-stale-rejected',await submit(other,'[data-org-edit-form]',{...good,name_ru:loser})===409);
await current.reload();check('winner-still-current',await current.locator('[name=name_ru]').inputValue()===winner);
}catch(e){check('matrix-harness',false,{error:String(e).slice(0,240)});}finally{await c.close();}}
return{rows,errors,network};}
