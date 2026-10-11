async original=>{
 __QA10_COMMON__
 const trace=[];
 for(const lang of ['ru','az','en']){const{c,p}=await context('admin',lang);for(const width of [360,390,768,1024,1280,1440]){
 await p.setViewportSize({width,height:950});await visit(p,'/admin/catalog/sitegalleryimage/');const row=p.locator('.km-media-row[data-field=logo]');const before=(await state(p)).settings.logo;await row.locator('.km-media-delete-btn').click();await p.waitForTimeout(450);
 const modal=p.locator('.km-modal[aria-modal=true]');const t=[];
 for(let i=0;i<8;i++){await p.keyboard.press('Tab');t.push(await p.evaluate(()=>({tag:document.activeElement.tagName,cls:document.activeElement.className,text:document.activeElement.textContent.slice(0,90),inside:!!document.activeElement.closest('.km-modal')})));}
 await p.keyboard.press('Shift+Tab');t.push(await modal.evaluate(e=>({tag:document.activeElement.tagName,inside:e.contains(document.activeElement)})));add('delete-dialog-focus-trap-after-animation',t.every(x=>x.inside),{trace:t},'admin',lang,width,p.url(),await shot(p,'modal-focus-final-'+lang+'-'+width));
 await p.keyboard.press('Escape');await p.waitForTimeout(450);const remaining=await modal.count();const after=(await state(p)).settings.logo;
 add('delete-dialog-escape-after-animation',remaining===0&&after===before,{remaining,before,after,focus:await p.evaluate(()=>document.activeElement.className)},'admin',lang,width,p.url(),await shot(p,'modal-escape-final-'+lang+'-'+width));trace.push({lang,width,remaining,t});
 }await c.close();}
 const{c,p}=await context('admin');await visit(p,'/admin/catalog/organization/'+F.organization+'/change/');const org=await p.evaluate(()=>({url:location.href,forms:Array.from(document.forms).map(f=>({action:f.action,controls:Array.from(f.querySelectorAll('input,textarea,select,button')).map(e=>({tag:e.tagName,type:e.type,name:e.name,disabled:e.disabled,text:e.type==='submit'?e.textContent.slice(0,80):undefined}))})),links:Array.from(document.querySelectorAll('a')).filter(e=>/редакт|измен|edit/i.test(e.textContent)).map(e=>({text:e.textContent.trim(),href:e.getAttribute('href')}))}));
 await c.close();return{rows,trace,org};
}
