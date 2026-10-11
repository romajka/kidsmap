from pathlib import Path
p=Path(__file__).with_name('loading.js');s=p.read_text(encoding='utf-8').replace('place_ids=18','place_ids=19').replace("const click=p.locator('button[value=confirm]').click();", "await p.locator('button[value=confirm]').scrollIntoViewIfNeeded();await p.evaluate(()=>window.scrollBy(0,-120));const click=p.locator('button[value=confirm]').click({noWaitAfter:true});")
p.write_text(s,encoding='utf-8')
