from pathlib import Path
p=Path(__file__).with_name('final-roundtrip.js')
s=p.read_text(encoding='utf-8')
s=s.replace("const logout=p.locator('form[action*=\"logout\"]');", "const logout=p.locator('form[action*=\"logout\"]').first();")
s=s.replace('await logout.evaluate(f=>f.requestSubmit());', "await p.setViewportSize({width:1280,height:950});await p.locator('.km-account-toggle').click();await logout.locator('button').click();")
p.write_text(s,encoding='utf-8')
