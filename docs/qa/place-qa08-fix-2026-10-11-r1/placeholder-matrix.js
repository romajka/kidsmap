async original=>{__COMMON__
const labels={ru:'Выберите район',az:'Rayon seçin',en:'Select district'},states=[];
try{
 for(const lang of ['ru','az','en']){
  const {c,p}=await context(lang,390);
  try{
   const before=await state(p);
   await c.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='localhost'&&r.request().method()==='GET')return r.continue();blocked.push({method:r.request().method(),url:u.origin+u.pathname,reason:'SIMULATED unsaved; non-GET blocked after login'});return r.abort();});
   for(const width of [360,390,768,1024,1280,1440]){
    await p.setViewportSize({width,height:950});await edit(p,lang);
    const s=p.locator('#id_district'),label=(await s.locator('option[value=""]').innerText()).trim();
    const codes=await s.locator('option').evaluateAll(options=>options.map(o=>o.value));
    add('PLACE-QA-08 localized empty district option',label===labels[lang],{label,expected:labels[lang],url:p.url(),codes},lang,width);
    await s.scrollIntoViewIfNeeded();await s.click();await s.press('Escape');
    add('Native select opens and Escape retains focus',await s.evaluate(e=>document.activeElement===e),{url:p.url()},lang,width);
    await s.click();await s.press('Home');await s.press('Enter');
    add('Native keyboard selects empty district option',await s.inputValue()==='',{integration:'SIMULATED unsaved; non-GET blocked',url:p.url()},lang,width);
    await s.focus();
    const capture=await shot(p,'district-empty-'+lang+'-'+width);
    const geom=await s.evaluate(e=>{const r=e.getBoundingClientRect(),css=getComputedStyle(e);return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,viewport:innerWidth,document:document.documentElement.scrollWidth,focus:document.activeElement===e,outline:css.outline,boxShadow:css.boxShadow,disabled:e.disabled,selectedText:e.selectedOptions[0]?.textContent};});
    add('Empty district label visible and focused within viewport',geom.selectedText.trim()===labels[lang]&&geom.focus&&!geom.disabled&&geom.left>=0&&geom.right<=width+1&&geom.top>=0&&geom.bottom<=950&&geom.document<=width+1,{geometry:geom,integration:'SIMULATED unsaved',url:p.url()},lang,width,capture);
   }
   const after=await state(p);states.push({lang,before,after});
   add('Unsaved placeholder checks preserve candidate and live',JSON.stringify(before)===JSON.stringify(after),{before,after,integration:'SIMULATED unsaved; non-GET blocked'},lang,1440);
  }finally{await c.close();}
 }
 return {rows,states,consoleErrors,networkErrors,blocked};
}catch(e){return{rows,error:String(e),consoleErrors,networkErrors,blocked};}
}
