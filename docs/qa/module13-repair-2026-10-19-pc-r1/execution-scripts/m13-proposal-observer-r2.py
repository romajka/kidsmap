from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1')
t=(O/'browser-specialist-proposal.js').read_text();needle="await p.goto(base+'/ru/account/specialists/'+id+'/');add('author-cannot-person-edit',await p.locator('h1').innerText().then(t=>/404|найдена|tapılmadı/.test(t)).catch(()=>false));";assert needle in t
t=t.replace(needle,"const denied=await p.goto(base+'/ru/account/specialists/'+id+'/');add('author-cannot-person-edit',denied.status()===404&&await p.locator('[data-owner-step]').count()===0);")
t=t.replace('M13 Proposed Fictional Person','M13 Second Proposed Fictional Person');t=t.replace('/png/proposal-error-','/png/proposal-r2-error-');(O/'browser-specialist-proposal-r2.js').write_text(t)
(O/'evidence/proposal-observer-note.md').write_text('Initial proposed profile3 native creation/submission yielded actual404 for author person-editor access; historical H1 wording regex did not match current localized recovery page and falsely failed. Native HTTP404 retained in network evidence. r2 uses HTTP and absence of editor, with a fresh second synthetic proposal; no identity was granted by fixture repair.\n')
