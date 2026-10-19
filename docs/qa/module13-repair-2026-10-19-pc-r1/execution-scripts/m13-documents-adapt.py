from pathlib import Path
import subprocess
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
code="from pypdf import PdfWriter; w=PdfWriter();w.add_blank_page(width=200,height=200);w.add_metadata({'/Title':'FICTIONAL QA document'});w.write('"+str(Q/'assets/identity.pdf')+"')"
subprocess.run(['docker','exec','m13full-r1-app','python','-c',code],check=True)
t=(R/'docs/qa/module03-full-2026-10-13-r1/documents.js').read_text().replace('__BASE__','http://127.0.0.1:33810').replace('__HERE__',str(O)).replace('__ASSETS__',str(Q/'assets')).replace('/screenshots/','/png/')
a=t.index("await p.goto(base+'/ru/auth/login/');");b=t.index("}pages[role]=p;",a)
t=t[:a]+"await p.goto(base+'/qa/m13/login/'+({person:'member',moderator:'admin',network:'owner',employee:'editor'}[role])+'/');"+t[b:]
t=t.replace('/specialists/1/','/specialists/2/').replace("rows.push({id,status:ok?'PASS':'FAIL'","rows.push({id,checks:{ok},status:ok?'PASS':'FAIL'")
(O/'browser-private-documents.js').write_text(t)
