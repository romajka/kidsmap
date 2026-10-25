const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const engines=require(process.env.KIDSMAP_PLAYWRIGHT_MODULE||'playwright');

async function launch(){const engine=process.env.KIDSMAP_BROWSER_ENGINE||'chromium';assert(['chromium','firefox','webkit'].includes(engine),'Supported browser engine');return engines[engine].launch({headless:true,...(process.env.KIDSMAP_BROWSER_EXECUTABLE?{executablePath:process.env.KIDSMAP_BROWSER_EXECUTABLE}:{})});}
async function context(browser,base,width=1440){
 assert(['127.0.0.1','localhost'].includes(new URL(base).hostname),'Only localhost QA is allowed');
 const c=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
 c.setDefaultTimeout(15000);c.setDefaultNavigationTimeout(30000);
 await c.route('**/*',route=>new URL(route.request().url()).origin===base?route.continue():route.abort('blockedbyclient'));
 return c;
}
async function login(c,fixture,role,lang='ru'){
 const p=await c.newPage(),admin=['admin','volunteer','volunteer_other'].includes(role),user=fixture.users[role==='volunteer'?'place_volunteer':role==='volunteer_other'?'place_volunteer_other':admin?'place_admin':role==='other'?'place_other':'place_owner'];
 await p.goto(fixture.origin+(admin?'/admin/login/?next=/admin/':`/${lang==='az'?'':lang+'/'}auth/login/`));
 await p.locator('[name=username]').fill(admin?user.username:user.email);
 await p.locator('[name=password]').fill(user.password);
 try { await Promise.all([p.waitForURL(url=>!url.pathname.includes('/login/')),p.locator('[name=password]').locator('xpath=ancestor::form').locator('button[type=submit],input[type=submit]').first().click()]); }
 catch(error){console.error('Login did not complete:',role,await p.locator('body').innerText());throw error;}
 return p;
}
async function reveal(locator){
 const phoneSlot=locator.locator('xpath=ancestor::*[@data-km-phone-slot][1]');
 if(await phoneSlot.count())for(let i=0;i<2&&!await phoneSlot.isVisible();i++)await phoneSlot.locator('xpath=ancestor::*[@data-km-phone-list][1]').locator('[data-km-phone-add]').click();
 const parents=await locator.locator('xpath=ancestor::details[not(@open)]').all();
 for(const parent of parents.reverse())await parent.locator(':scope > summary').click();
 const panel=locator.locator('xpath=ancestor::*[@data-km-language-panel][1]');
 if(await panel.count()&&!await panel.isVisible()){
  const language=await panel.getAttribute('data-km-language-panel');
  await panel.locator('xpath=ancestor::*[@data-km-language-group][1]').locator(`[data-km-language="${language}"]`).click();
 }
}
async function fill(p,selector,value){const l=p.locator(selector).first();await reveal(l);await l.fill(String(value));}
async function select(p,selector,value){
 const l=p.locator(selector).first();await reveal(l);
 const custom=l.locator('xpath=ancestor::div[contains(@class,"km-pf-native-select")][1]/following-sibling::div[contains(@class,"km-pf-picker-wrap")][1]');
 const segmented=l.locator('xpath=ancestor::div[contains(@class,"km-pf-native-select")][1]/following-sibling::div[contains(@class,"km-pf-segmented")][1]');
 if(await custom.count()){
  const label=await l.locator('option').evaluateAll((options,v)=>options.find(o=>o.value===v)?.textContent?.trim(),String(value));
  assert(label,`Option ${value} is available in ${selector}`);
  await custom.locator('.km-pf-picker-btn').click();
  await custom.locator('.km-pf-picker-item').filter({hasText:label}).first().click();
 }else if(await segmented.count()){
  await segmented.locator(`[data-value="${value}"]`).click();
 }else if((await l.getAttribute('class')||'').includes('select2-hidden-accessible')){
  const label=await l.locator('option').evaluateAll((options,v)=>options.find(o=>o.value===v)?.textContent?.trim(),String(value));
  assert(label,`Option ${value} is available in ${selector}`);
  const id=await l.getAttribute('id');
  await p.locator(`[id="select2-${id}-container"]`).click();
  await p.locator('.select2-results__option[role=option]').filter({hasText:label}).first().click();
 }else await l.selectOption(String(value));
}
function watch(p,base){const errors=[],requests=[];p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)requests.push({url:r.url(),status:r.status()});});return{errors,requests};}
async function inspect(p,out,name){fs.mkdirSync(out,{recursive:true});await p.screenshot({path:path.join(out,name+'.png'),fullPage:false});const overflow=await p.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+1);assert.equal(overflow,false,`${name}: horizontal overflow`);}
module.exports={assert,fs,path,launch,context,login,reveal,fill,select,watch,inspect};
