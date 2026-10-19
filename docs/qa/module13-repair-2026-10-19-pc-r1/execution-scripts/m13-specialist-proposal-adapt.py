from pathlib import Path
import shutil
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';shutil.copyfile(Q/'assets/event-photo.png',Q/'assets/photo.png')
t=(R/'docs/qa/module03-full-2026-10-13-r1/lifecycle.js').read_text().replace('__BASE__','http://127.0.0.1:33810').replace('__HERE__',str(O)).replace('__ASSETS__',str(Q/'assets')).replace('/screenshots/','/png/')
a=t.index("await p.goto(base+'/ru/auth/login/');");b=t.index("await p.goto(base+'/ru/account/specialists/proposals/new/');",a);t=t[:a]+"await p.goto(base+'/qa/m13/login/owner/');"+t[b:]
t=t.replace("rows.push({id,status:ok?'PASS':'FAIL'","rows.push({id,checks:{ok},status:ok?'PASS':'FAIL'")
t=t.replace('Synthetic module03 proposed person','M13 Proposed Fictional Person')
(O/'browser-specialist-proposal.js').write_text(t)
