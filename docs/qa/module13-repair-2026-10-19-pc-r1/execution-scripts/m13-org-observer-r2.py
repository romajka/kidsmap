from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1')
t=(O/'browser-organization-flow.js').read_text().replace("await p.goto(B+'/ru/account/organizations/create/');","await p.goto(B+'/ru/account/organizations/create/');for(const summary of await p.locator('details:not([open]) > summary').all())await summary.click();")
t=t.replace("await p.locator('[data-confirm-form] [name=consent]').isRequired?.()??await p.locator('[data-confirm-form] [name=consent]').getAttribute('required')!==null","await p.locator('[data-confirm-form] [name=consent]').getAttribute('required')!==null")
(O/'browser-organization-flow-r2.js').write_text(t)
