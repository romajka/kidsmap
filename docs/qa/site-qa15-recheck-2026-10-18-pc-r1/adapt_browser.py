from pathlib import Path
O=Path(__file__).resolve().parent
s=(O/'browser-red.js').read_text()
old="async function save(p){const post=p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path),nav=p.waitForNavigation({waitUntil:'domcontentloaded'});await p.locator('button[name=_continue]').click();const r=await post;await nav;return r.status();}"
new="""async function save(p){
 const button=p.locator('button[name=_continue]');
 const visible=await button.isVisible();p.site15SaveMethod=visible?'native button click':'native Enter in text input (existing mobile buttons hidden)';
 const action=()=>visible?button.click():p.locator('[name=footer_phone]').press('Enter');
 const [response]=await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path),p.waitForNavigation({waitUntil:'domcontentloaded'}),action()]);
 return response.status();
}"""
assert old in s;s=s.replace(old,new)
s=s.replace('let cell=0;',"let cell=0;for(const c of browser.contexts())if(c!==original.context())await c.close();")
s=s.replace('bfield,aStatus,bStatus,before','bfield,aStatus,bStatus,aInteraction:a.site15SaveMethod,bInteraction:b.site15SaveMethod,before')
(O/'browser-red-final.js').write_text(s)
print('New serialized native run; previous timeout evidence retained; mobile uses actual Enter, no forced or JS form submission')
