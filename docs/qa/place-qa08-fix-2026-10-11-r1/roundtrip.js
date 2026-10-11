async original=>{__COMMON__
const states=[];
try{
 for(const lang of ['ru','az','en']){
  const {c,p}=await context(lang,lang==='ru'?390:1440);
  try{
   const before=await state(p);
   await p.goto(B+F.public_urls[lang]);
   const publicBefore=await p.locator('body').innerText();
   add('Initial public address rendered',publicBefore.includes(before.live.address),{address:before.live.address,url:p.url()},lang,lang==='ru'?390:1440);
   await edit(p,lang);
   await p.locator('#id_region').selectOption('baku');
   await p.locator('#id_district').selectOption('baku_yasamal');
   await p.waitForTimeout(1700);
   const nav=p.waitForNavigation({waitUntil:'domcontentloaded'});
   await p.locator('[name=form_action][value=save_draft]').click({noWaitAfter:true});
   await nav;await p.reload({waitUntil:'domcontentloaded'});
   const capture=await shot(p,'district-saved-'+lang+(lang==='ru'?'-390':'-1440'));
   add('Native save/reload retains district machine code',await p.locator('#id_district').inputValue()==='baku_yasamal',{code:await p.locator('#id_district').inputValue(),url:p.url()},lang,lang==='ru'?390:1440,capture);
   const after=await state(p);states.push({lang,before,after});
   add('Native save keeps live location and candidate effective district',JSON.stringify(before.live)===JSON.stringify(after.live)&&after.candidate_effective_district==='baku_yasamal'&&after.candidate_effective_address===before.live.address,{before,after},lang,lang==='ru'?390:1440);
   await p.goto(B+F.public_urls[lang]);
   add('Public address remains unchanged after native save',await p.locator('body').innerText().then(t=>t.includes(before.live.address)),{address:before.live.address,url:p.url()},lang,lang==='ru'?390:1440,await shot(p,'public-after-'+lang+(lang==='ru'?'-390':'-1440')));
  }finally{await c.close();}
 }
 return{rows,states,consoleErrors,networkErrors,blocked};
}catch(e){return{rows,error:String(e),consoleErrors,networkErrors,blocked};}
}
