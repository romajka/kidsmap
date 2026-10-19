from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(R/'docs/qa/module03-full-2026-10-13-r1/cooperation.js').read_text().replace('__BASE__','http://127.0.0.1:33810').replace('__HERE__',str(O)).replace('/screenshots/','/png/')
a=t.index("await p.goto(base+'/ru/auth/login/');");b=t.index('pages[role]=p;',a);t=t[:a]+"await p.goto(base+'/qa/m13/login/'+({network:'owner',person:'member',employee:'moderator'}[role])+'/');"+t[b:]
t=t.replace('/organizations/1/','/organizations/2/').replace('/specialists/1/','/specialists/2/').replace(".selectOption('1')",".selectOption('2')")
t=t.replace("rows.push({id,status:ok?'PASS':'FAIL'","rows.push({id,checks:{ok},status:ok?'PASS':'FAIL'")
needle="const denied=await network.goto"
t=t.replace(needle,"const cross=await(await network.context().request.get(base+'/qa/m13/cross/')).json();await network.goto(base+cross.urls.ru.organization);add('cooperation-active-public-organization',(await network.locator('body').innerText()).includes('M13 Confirmed Independent Person'),'network');"+needle)
(O/'browser-cooperation.js').write_text(t)
