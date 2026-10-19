from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(R/'docs/qa/module03-full-2026-10-13-r1/claim-lifecycle.js').read_text().replace('__BASE__','http://127.0.0.1:33810').replace('__HERE__',str(O)).replace('/screenshots/','/png/')
a=t.index("await p.goto(B+'/ru/auth/login/');");b=t.index('return p;}',a);t=t[:a]+"await p.goto(B+'/qa/m13/login/'+({author:'owner',moderator:'admin',claimant:'editor'}[role])+'/');"+t[b:]
t=t.replace("rows.push({id,status:ok?'PASS':'FAIL'","rows.push({id,checks:{ok},status:ok?'PASS':'FAIL'")
t=t.replace("const m=await login('moderator');await status(m,'published');", "const m=await login('moderator');await status(m,'published');const publicPath=await m.locator('[data-main-photo-root] a.km-media-main__view').getAttribute('href');")
t=t.replace("B+'/ru/specialists/synthetic-module03-proposed-person/'","B+publicPath")
(O/'browser-native-claim.js').write_text(t)
