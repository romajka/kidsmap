from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'admin-functional.js';s=p.read_text(encoding='utf-8')
s=s.replace("if(await a.locator('html').getAttribute('lang')!==lang){await Promise.all", "if(await a.locator('html').getAttribute('lang')!==lang){await a.locator('.km-admin-header__lang-btn').click();await Promise.all")
s=s.replace("if(await a.locator('html').getAttribute('lang')!=='ru')await Promise.all", "if(await a.locator('html').getAttribute('lang')!=='ru'){await a.locator('.km-admin-header__lang-btn').click();await Promise.all")
s=s.replace("locator('button').click()]);\n  for(const field", "locator('button').click()]);}\n  for(const field")
p.write_text(s,encoding='utf-8')
p=P/'public-native.js';s=p.read_text(encoding='utf-8')
s=s.replace("await catButton.click();await p.waitForTimeout(650)", "if(await catButton.isVisible())await catButton.click();else {const select=p.locator('#filters-form select[name=category]');if(!await select.isVisible())throw new Error('No visible category control located');await select.focus();await select.press('Space');await p.keyboard.press('Escape');await select.selectOption('ART');}await p.waitForTimeout(650)")
p.write_text(s,encoding='utf-8');print('Own QA: open admin language dropdown before choice; use rendered native category select on desktop.')
