async original=>{
__QA12_COMMON__
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
 const{c,p}=await context('admin',lang,width);await visit(p,'/admin/catalog/siteanalytics/?period=90');const target=p.locator('[data-period="7"]');await target.focus();const focus=await target.evaluate(e=>{const s=getComputedStyle(e);return{active:document.activeElement===e,outline:s.outlineStyle,width:s.outlineWidth,shadow:s.boxShadow};});
 await Promise.all([p.waitForURL('**/*period=7'),p.keyboard.press('Enter')]);await p.waitForLoadState('domcontentloaded');const active=await p.locator('[data-period="7"]').getAttribute('class');add('period-keyboard-enter',new URL(p.url()).searchParams.get('period')==='7'&&active.includes('is-active'),{focus,active},'admin',lang,width,p.url());await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');await p.keyboard.press('Space');await p.keyboard.press('Escape');await c.close();
}
return{rows,harnessCorrection:'Initial matrix waited old load state; this script waits new URL. No app assertion/source changes.'};
}
