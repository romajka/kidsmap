from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(O/'browser-employee-revoke.js').read_text().replace("make('member')","make('editor')").replace("hasText:'m13_member'","hasText:'m13_editor'")
t=t.replace("await owner.waitForFunction(id=>!document.querySelector('[data-grant-row=\"'+id+'\"]'),grant)","await owner.waitForFunction(id=>document.querySelector('[data-grant-row=\"'+id+'\"]')?.textContent.includes('Приостановлен'),grant)")
t=t.replace("await owner.locator('[data-grant-row=\"'+grant+'\"]').count()===0","await owner.locator('[data-grant-row=\"'+grant+'\"] [data-team-operation]').count()===0")
(O/'browser-employee-revoke-r2.js').write_text(t)
(O/'browser-stock-auth-r2.js').write_text((O/'browser-stock-auth.js').read_text())
p=R/'.tmp/m13-stock-run.py';t=p.read_text().replace('shadow.mkdir();','shadow.mkdir(exist_ok=True);').replace("(Q/'stock-screenshots').mkdir();","(Q/'stock-screenshots').mkdir(exist_ok=True);");p.write_text(t)
(O/'evidence/access-fixture-note.md').write_text('Initial native role/revoke operations succeeded and grant history correctly remains Suspended. Initial observer expected row removal. Readback also wrongly assumed the member fixture had a direct Place1 grant; source seed-extra.py grants that only to editor/moderator. No audited grant was reactivated or repaired. Replay uses a fresh network grant for the existing editor actor whose direct Place1 grant was attested before setup, then native UI role/revoke and independent-right readback.\n')
