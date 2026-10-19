from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1')
t=(O/'browser-organization-flow-r2.js').read_text().replace("for(const summary of await p.locator('details:not([open]) > summary').all())await summary.click();", "while(await p.locator('details:not([open]) > summary').count())await p.locator('details:not([open]) > summary').first().click();")
(O/'browser-organization-flow-r3.js').write_text(t)
