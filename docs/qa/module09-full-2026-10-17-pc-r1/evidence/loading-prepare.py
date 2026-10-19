from pathlib import Path
Q=Path(__file__).resolve().parent;p=Q/'loading-template.js';t=p.read_text(encoding='utf-8-sig')
a="await p.goto(base+prefix+'/catalog/');const btn="
b="""await p.goto(base+prefix+'/catalog/');const burger=p.locator('#km-burger-open');if(await burger.isVisible()){await burger.focus();await p.keyboard.press('Enter');const opened=await burger.getAttribute('aria-expanded')==='true';await p.screenshot({path:dir+'drawer-'+lang+'-'+width+'.png'});await p.keyboard.press('Escape');rows.push({id:'mobile-drawer-keyboard',status:opened&&await burger.getAttribute('aria-expanded')==='false'?'PASS':'FAIL',lang,width,role:'author'});}const btn="""
assert a in t;t=t.replace(a,b);p.write_text(t)
