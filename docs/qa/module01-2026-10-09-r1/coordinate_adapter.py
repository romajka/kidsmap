from pathlib import Path
p=Path(__file__).with_name('owner-coordinate-roundtrip.js')
s=p.read_text(encoding='utf-8').replace("await p.locator('[name=lat]').fill", "const d=p.locator('[name=lat]').locator('xpath=ancestor::details');if(await d.getAttribute('open')===null)await d.locator(':scope > summary').click();await p.locator('[name=lat]').fill",1)
p.write_text(s,encoding='utf-8')
