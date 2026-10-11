from pathlib import Path
p=Path(__file__).resolve().parent/'map-browser.js';s=p.read_text(encoding='utf-8').replace("prefix+'catalog/?q=Aurora'","prefix+'catalog/?category=SPRT'").replace("await p.locator('.kidsmap-marker-button').first().click()","await p.locator('.kidsmap-marker-button').last().click()")
p.write_text(s,encoding='utf-8');print('Map QA: shared-venue query includes both matching members; coincident pointer uses visually topmost native marker.')
