"""Repair our own QA selectors from freshly inspected DOM, never app code."""
from pathlib import Path
here=Path(__file__).resolve().parent
p=here/'media.js';s=p.read_text(encoding='utf-8')
old="await trigger.first().click();await p.locator('input[type=file][name^=\"gallery-\"]').last().setInputFiles(assets+'/'+file);"
new="const [chooser]=await Promise.all([p.waitForEvent('filechooser'),trigger.first().click()]);await chooser.setFiles(assets+'/'+file);"
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
p=here/'matrix.js';s=p.read_text(encoding='utf-8')
old="await a.locator('.km-admin-lang-btn').click();await Promise.all([a.waitForNavigation({waitUntil:'domcontentloaded'}),a.locator('button[name=language][value=\"'+lang+'\"]').click()]);"
new="if(await a.locator('html').getAttribute('lang')!==lang){await a.locator('.km-admin-lang-btn').click();await Promise.all([a.waitForNavigation({waitUntil:'domcontentloaded'}),a.locator('.km-admin-lang-switch-form').filter({has:a.locator('[name=language][value=\"'+lang+'\"]')}).locator('button').click()]);}"
assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
print('QA selectors corrected from observed controls.')
