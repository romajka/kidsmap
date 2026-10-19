from pathlib import Path
Q=Path(__file__).resolve().parent
base=(Q/'flows-template.js').read_text();header=base[:base.index("const a=await page('author')")]
t=(Q.parents[1]/'docs/qa/module09-2026-10-10-r1/site-finish.js').read_text();t=t[t.index("const a=await page('author')"):];t=t.replace("await m.locator('a.nav-link').filter({hasText:'Модерация'}).click();","await m.locator('a.nav-link').filter({hasText:'Модерация'}).click();")
(Q/'site-finish-template.js').write_text(header+t)
